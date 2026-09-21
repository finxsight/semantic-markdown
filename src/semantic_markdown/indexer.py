"""
SMD Indexer — chunk SMD documents into a SQLite index with full-text search.

Stores every block (chunk) with metadata — block_type, doc_type, date, tags —
and creates an FTS5 full-text index for instant keyword search.  This is the
reference implementation for how SMD documents become queryable databases
without an external ETL pipeline.

Architecture
------------
::

    ┌──────────────┐     parse     ┌──────────────┐     INSERT      ┌──────────┐
    │  .smd file   │──────────────▶│  SMDIndexer   │──────────────▶│  SQLite  │
    │              │               │               │               │  + FTS5  │
    └──────────────┘               └──────────────┘               └──────────┘
                                          │
                                          │ search("keyword")
                                          ▼
                                   ┌──────────────┐
                                   │  ranked hits │
                                   │  + metadata  │
                                   └──────────────┘

Usage
-----
::

    from semantic_markdown.indexer import SMDIndexer

    idx = SMDIndexer("chunks.db")
    idx.index_file("examples/AAPL_profile_with_chart.smd")
    idx.index_file("examples/Agilent_Transcript_1Q_2026.smd")

    # Full-text keyword search
    hits = idx.search("guidance margins")
    for h in hits:
        print(h.block_id, h.block_type, h.tags, h.snippet)

    # Metadata-filtered search
    hits = idx.search("revenue", doc_type="earnings_transcript",
                      block_type="qa", tags=["guidance"])

    # Faceted browsing
    print(idx.facets())  # doc_types, block_types, date range, all tags
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from .parser import parse_file


@dataclass
class SearchHit:
    """A single search result from the SQL index."""

    block_id: str
    block_type: str
    doc_id: str
    doc_type: str
    doc_date: str
    tags: List[str] = field(default_factory=list)
    content: str = ""
    snippet: str = ""
    rank: float = 0.0


# ======================================================================
# SMDIndexer
# ======================================================================


class SMDIndexer:
    """SQLite-backed chunk index with full-text keyword search.

    Creates two tables:

    ``chunks``
        block-level metadata (block_id, doc_id, doc_type, block_type,
        date, tags as JSON array, full content).

    ``chunks_fts``
        FTS5 virtual table over content for ranked full-text search.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Created if it doesn't exist.
        Use ``:memory:`` for an in-memory-only index.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self):
        """Create the chunks table and FTS index if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                block_id    TEXT NOT NULL,
                doc_id      TEXT NOT NULL,
                doc_type    TEXT,
                block_type  TEXT,
                doc_date    TEXT,
                tags        TEXT,   /* JSON array */
                content     TEXT,
                header_json TEXT,   /* full block header */
                UNIQUE(doc_id, block_id)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(
                content,
                content=chunks,
                content_rowid=id,
                tokenize='porter unicode61'
            );

            /* Keep FTS in sync */
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content)
                VALUES (new.id, new.content);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content)
                VALUES ('delete', old.id, old.content);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content)
                VALUES ('delete', old.id, old.content);
                INSERT INTO chunks_fts(rowid, content)
                VALUES (new.id, new.content);
            END;
        """)
        self._conn.commit()

    # ==================================================================
    # Indexing
    # ==================================================================

    def index_file(self, path: str | Path) -> int:
        """Parse an .smd file and insert all blocks into the index.

        Returns the number of blocks indexed.  Safe to call multiple
        times; duplicate (doc_id, block_id) pairs are ignored.
        """
        doc = parse_file(Path(path))
        return self._index_doc(doc)

    def _index_doc(self, doc: SimpleNamespace) -> int:
        """Insert a parsed document's blocks into the index."""
        doc_header = getattr(doc, "header", None) or (
            doc.entities[0].header if doc.entities else {}
        )
        doc_id = (
            doc_header.get("document_id")
            or doc_header.get("ticker")
            or doc_header.get("document_type")
            or "?"
        )
        doc_type = doc_header.get("document_type") or doc_header.get("type", "")
        doc_date = doc_header.get("date") or doc_header.get("created", "")

        count = 0
        for block in doc.blocks:
            tags_json = json.dumps(block.tags, ensure_ascii=False) if block.tags else "[]"
            header_json = json.dumps(block.header, ensure_ascii=False)
            content = block.body_text or ""

            try:
                before = self._conn.total_changes
                self._conn.execute(
                    """INSERT OR IGNORE INTO chunks
                       (block_id, doc_id, doc_type, block_type, doc_date,
                        tags, content, header_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(block.block_id),
                        str(doc_id),
                        doc_type,
                        block.type or "",
                        doc_date,
                        tags_json,
                        content,
                        header_json,
                    ),
                )
                if self._conn.total_changes > before:
                    count += 1
            except sqlite3.Error:
                pass

        self._conn.commit()
        return count

    # ==================================================================
    # Search
    # ==================================================================

    def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        block_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        doc_date_from: Optional[str] = None,
        doc_date_to: Optional[str] = None,
        limit: int = 50,
    ) -> List[SearchHit]:
        """Full-text keyword search with optional metadata filters.

        Parameters
        ----------
        query:
            Free-text keywords.  Supports FTS5 syntax: ``"phrase"``,
            ``term*``, ``term1 OR term2``, ``term1 AND term2``.  An
            empty string returns all blocks (subject to other filters).
        doc_type:
            Filter to a specific document type (e.g. "earnings_transcript").
        block_type:
            Filter to a specific block type (e.g. "qa", "operator_comment").
        tags:
            Return only blocks that have ALL of the given tags.
        doc_date_from:
            ISO date lower bound (inclusive).
        doc_date_to:
            ISO date upper bound (inclusive).
        limit:
            Maximum results.

        Returns
        -------
        List of SearchHit dataclasses, ranked by relevance.
        """
        wheres: List[str] = []
        params: List[Any] = []

        if query.strip():
            # FTS5 MATCH in the WHERE of the joined query
            wheres.append("chunks_fts MATCH ?")
            fts_query = _to_fts_query(query)
            params.append(fts_query)

        if doc_type:
            wheres.append("c.doc_type = ?")
            params.append(doc_type)

        if block_type:
            wheres.append("c.block_type = ?")
            params.append(block_type)

        if tags:
            for tag in tags:
                wheres.append("c.tags LIKE ?")
                params.append(f'%"{tag}"%')

        if doc_date_from:
            wheres.append("c.doc_date >= ?")
            params.append(doc_date_from)

        if doc_date_to:
            wheres.append("c.doc_date <= ?")
            params.append(doc_date_to)

        where_clause = " AND ".join(wheres) if wheres else "1=1"

        if query.strip():
            sql = f"""
                SELECT c.block_id, c.block_type, c.doc_id, c.doc_type, c.doc_date,
                       c.tags, c.content, c.header_json,
                       substr(c.content, 1, 200) AS snippet,
                       rank
                FROM chunks_fts f
                JOIN chunks c ON c.id = f.rowid
                WHERE {where_clause}
                ORDER BY rank
                LIMIT ?
            """
        else:
            sql = f"""
                SELECT c.block_id, c.block_type, c.doc_id, c.doc_type, c.doc_date,
                       c.tags, c.content, c.header_json,
                       substr(c.content, 1, 200) AS snippet,
                       0.0 AS rank
                FROM chunks c
                WHERE {where_clause}
                ORDER BY c.doc_date DESC, c.id
                LIMIT ?
            """

        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()

        return [_row_to_hit(r) for r in rows]

    # ==================================================================
    # Facets
    # ==================================================================

    def facets(self) -> dict:
        """Return facet counts for browsing the index without a query."""
        return {
            "total_chunks": self._conn.execute(
                "SELECT COUNT(*) FROM chunks"
            ).fetchone()[0],
            "doc_types": self._facet("doc_type"),
            "block_types": self._facet("block_type"),
            "date_range": self._date_range(),
            "all_tags": self._all_tags(),
        }

    def _facet(self, column: str) -> List[dict]:
        rows = self._conn.execute(
            f"SELECT {column}, COUNT(*) AS cnt FROM chunks "
            f"WHERE {column} != '' GROUP BY {column} ORDER BY cnt DESC"
        ).fetchall()
        return [{"value": r[0], "count": r[1]} for r in rows]

    def _date_range(self) -> dict:
        row = self._conn.execute(
            "SELECT MIN(doc_date), MAX(doc_date) FROM chunks"
        ).fetchone()
        return {"earliest": row[0], "latest": row[1]}

    def _all_tags(self) -> List[dict]:
        rows = self._conn.execute(
            "SELECT tags FROM chunks WHERE tags != '[]'"
        ).fetchall()
        counter: Dict[str, int] = {}
        for (tags_json,) in rows:
            try:
                for t in json.loads(tags_json):
                    counter[t] = counter.get(t, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass
        return sorted(
            [{"tag": k, "count": v} for k, v in counter.items()],
            key=lambda x: -x["count"],
        )

    # ==================================================================
    # Management
    # ==================================================================

    def close(self):
        """Close the database connection."""
        self._conn.close()

    def drop_all(self):
        """Delete all indexed data (tables are preserved)."""
        self._conn.execute("DELETE FROM chunks")
        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        """Raw SQLite connection for ad-hoc queries."""
        return self._conn


# ======================================================================
# Helpers
# ======================================================================


def _to_fts_query(raw: str) -> str:
    """Convert a user query string to FTS5 syntax.

    Each word is ANDed unless OR/AND is explicit.  Quotes produce
    phrase searches.  Asterisks produce prefix searches.
    """
    # Don't double-process if user gave FTS5 syntax
    if '"' in raw or '*' in raw or ' OR ' in raw.upper() or ' AND ' in raw.upper():
        return raw

    # Implicit AND between words
    return " AND ".join(raw.split())


def _row_to_hit(row: sqlite3.Row) -> SearchHit:
    """Convert a query result row to a SearchHit."""
    tags_raw = row["tags"] or "[]"
    try:
        tags = json.loads(tags_raw)
    except (json.JSONDecodeError, TypeError):
        tags = []

    return SearchHit(
        block_id=row["block_id"],
        block_type=row["block_type"] or "",
        doc_id=row["doc_id"],
        doc_type=row["doc_type"] or "",
        doc_date=row["doc_date"] or "",
        tags=tags,
        content=row["content"] or "",
        snippet=row["snippet"] or "",
        rank=round(row["rank"], 4) if row["rank"] else 0.0,
    )
