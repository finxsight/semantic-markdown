"""
SMD Agent — MCP-style interface for enriching SMD documents.

Exposes a unified search() entry point plus enrichment CRUD for
LLM agents to load, query, and enrich .smd documents.

Typical agent workflow:
    agent = SMDAgent()
    result = agent.search("transcript.smd")
    for block in result["blocks"]:
        agent.add_enrichment(block["block_id"], "highlights",
                             {"text": "...", "sentiment": 0.8})
    agent.save("enriched.smd")

search() interface
-----------------
    search("path")                     → load doc, return ALL blocks
    search("path/block_id")            → return just that block
    search("path/*?filters=k:v,...")   → return matching blocks
    search("path/block_id?filters=...")→ block if it matches filters

Every block in the result includes ``next_block_id`` and
``previous_block_id`` for document-order navigation.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from .models import SMDBlock, SMDDocument
from .parser import parse_smd, parse_file


class SMDAgent:
    """Agent for loading, searching, and enriching SMD documents.

    search(query) -> dict
        Unified entry point with URL-like syntax:
        - ``"path"`` — load document, return ALL blocks.
        - ``"path/block_id"`` — return a single block.
        - ``"path/*?filters=k:v,..."`` — return blocks matching filters.
        - ``"path/block_id?filters=..."`` — block only if it matches.

        Every block includes ``next_block_id`` and ``previous_block_id``
        for document-order navigation (None at edges).

    Enrichment CRUD
    ---------------
    add_enrichment(block_id, key, value, enrichment_id?) -> str | None
    del_enrichment(block_id, key, enrichment_id?) -> bool
    edit_enrichment(block_id, key, value, enrichment_id?) -> bool

    save(path?) -> Path
    """

    def __init__(self):
        self._doc: Optional[SMDDocument] = None
        self._source_path: Optional[Path] = None
        self._raw_text: Optional[str] = None
        self._loaded_path: Optional[str] = None

    # ==================================================================
    # Unified search
    # ==================================================================

    def search(self, query: str) -> dict:
        """Load/query an SMD document and return matching blocks.

        Syntax::

            "path/to/file.smd"                     → all blocks
            "path/to/file.smd/block_id"             → single block
            "path/to/file.smd/*?filters=k:v,..."     → filtered blocks
            "path/to/file.smd/block_id?filters=..."   → single + filter

        Filters
        -------
        Comma-separated ``key:value`` pairs.  A block matches when
        *every* filter matches its header.  For list fields (tags)
        the match is "value is in the list".

        Returns
        -------
        dict with keys::

            {
                "document": {document_id, type, source, schema_version,
                             block_count, all_tags, meta},
                "blocks": [{block_id, type, speaker, tags, header, body,
                            enrichment, next_block_id, previous_block_id}, ...],
                "query": {path, block_id, filters}
            }
        """
        path, block_id, raw_filters = _parse_search(query)

        if path != self._loaded_path:
            self._load(path)
            self._loaded_path = path

        if self._doc is None:
            return _empty_result(path, block_id, raw_filters)

        filters = _parse_filters(raw_filters)
        all_blocks = self._doc.blocks
        n = len(all_blocks)

        if block_id is not None:
            idx = _index_of(self._doc, block_id)
            if idx is None:
                return _empty_result(path, block_id, raw_filters)
            block = all_blocks[idx]
            if not _matches_all(block, filters):
                return _empty_result(path, block_id, raw_filters)
            result_blocks = [_serialize_block(block, idx, n, all_blocks)]
        else:
            result_blocks = [
                _serialize_block(b, i, n, all_blocks)
                for i, b in enumerate(all_blocks)
                if _matches_all(b, filters)
            ]

        return {
            "document": _doc_summary(self._doc),
            "blocks": result_blocks,
            "query": {
                "path": path,
                "block_id": block_id,
                "filters": raw_filters,
            },
        }

    def _load(self, path_str: str) -> None:
        """Load an .smd file path into self._doc."""
        p = Path(path_str)
        if p.exists():
            self._source_path = p
            self._raw_text = p.read_text(encoding="utf-8")
            self._doc = parse_file(p)
        else:
            self._source_path = None
            self._raw_text = path_str
            self._doc = parse_smd(path_str)

    # ==================================================================
    # read() — simplified LLM-friendly block traversal
    # ==================================================================

    def read(self, query: str, limit: Optional[int] = None,
             offset: int = 0) -> List[dict]:
        """Read blocks from an SMD document in a flat, LLM-friendly format.

        Syntax::

            "path/to/file.smd"          → all blocks + document header
            "path/to/file.smd/*"        → same as above
            "path/to/file.smd/block_id"  → single block + document header
            "path/to/file.smd/*?limit=5" → first 5 blocks + document header

        Returns
        -------
        A flat list::

            [
                {"type": "document", "content": [{"type": "json", "text": "..."}]},
                {"type": "block", "block_id": "0", "header": {...}, "content": [
                    {"type": "markdown", "text": "raw body text..."},
                ]},
                ...
            ]

        Each block's body is returned as a single raw markdown segment.
        Block metadata (block_type, qa_thread_id, enrichments, etc.) is
        included in the ``header`` field.
        """
        path, block_id, raw_params = _parse_read_query(query)
        params = parse_qs(raw_params) if raw_params else {}

        if path != self._loaded_path:
            self._load(path)
            self._loaded_path = path

        if self._doc is None:
            return []

        all_blocks = self._doc.blocks

        # --- Build document entry ---
        doc_entry = _build_doc_entry(self._doc)
        result: List[dict] = [doc_entry]

        # --- Resolve blocks to return ---
        if block_id is not None:
            idx = _index_of(self._doc, block_id)
            if idx is not None:
                result.append(_build_block_entry(all_blocks[idx]))
            return result

        # Apply limit / offset from params or from explicit args
        limit_val = limit
        offset_val = offset
        if "limit" in params:
            limit_val = int(params["limit"][0])
        if "offset" in params:
            offset_val = int(params["offset"][0])

        target_blocks = all_blocks
        if offset_val:
            target_blocks = target_blocks[offset_val:]
        if limit_val is not None:
            target_blocks = target_blocks[:limit_val]

        for b in target_blocks:
            result.append(_build_block_entry(b))

        return result

    # ==================================================================
    # Enrichment CRUD
    # ==================================================================

    def add_enrichment(
        self, block_id: str, key: str, value: Any, enrichment_id: Optional[str] = None
    ) -> Optional[str]:
        """Add an enrichment item to a block.

        For ``highlights`` this appends to the list with an auto-generated
        ``enrichment_id`` if none is provided.  For other keys this sets
        the value directly.
        """
        if self._doc is None:
            return None

        block = _get_block(self._doc, block_id)
        if block is None:
            return None

        enr = block.header.setdefault("enrichment", {})

        if key == "highlights":
            highlights: list = enr.setdefault("highlights", [])
            eid = enrichment_id or uuid.uuid4().hex[:12]
            if isinstance(value, dict):
                item = {"enrichment_id": eid, **value}
            elif isinstance(value, str):
                item = {"enrichment_id": eid, "text": value}
            else:
                item = {"enrichment_id": eid, "text": str(value)}
            highlights.append(item)
            return eid
        else:
            enr[key] = value
            return None

    def del_enrichment(
        self, block_id: str, key: str, enrichment_id: Optional[str] = None
    ) -> bool:
        """Delete an enrichment item from a block.

        If ``enrichment_id`` is provided and ``key`` is "highlights", only
        the matching highlight is removed.  Otherwise the entire *key* is
        removed from enrichment.
        """
        if self._doc is None:
            return False

        block = _get_block(self._doc, block_id)
        if block is None:
            return False

        enr = block.header.get("enrichment", {})
        if key not in enr:
            return True

        if enrichment_id is not None and key == "highlights":
            highlights: list = enr["highlights"]
            enr["highlights"] = [
                h for h in highlights
                if not (isinstance(h, dict) and h.get("enrichment_id") == enrichment_id)
            ]
            return True
        else:
            del enr[key]
            return True

    def edit_enrichment(
        self, block_id: str, key: str, value: Any, enrichment_id: Optional[str] = None
    ) -> bool:
        """Edit an existing enrichment item on a block.

        If ``enrichment_id`` is provided and ``key`` is "highlights", the
        matching highlight is updated in-place.  Otherwise the entire *key*
        value is replaced.
        """
        if self._doc is None:
            return False

        block = _get_block(self._doc, block_id)
        if block is None:
            return False

        enr = block.header.setdefault("enrichment", {})

        if enrichment_id is not None and key == "highlights":
            highlights: list = enr.get("highlights", [])
            for i, h in enumerate(highlights):
                if isinstance(h, dict) and h.get("enrichment_id") == enrichment_id:
                    if isinstance(value, dict):
                        highlights[i] = {**h, **value}
                    else:
                        highlights[i] = {**h, "text": str(value)}
                    return True
            return False
        else:
            enr[key] = value
            return True

    # ==================================================================
    # Serialization & save
    # ==================================================================

    def to_smd_text(self) -> str:
        """Serialize the current document state back to .smd format."""
        if self._raw_text is not None:
            return self._rebuild_from_raw()
        return self._serialize_from_blocks()

    def _rebuild_from_raw(self) -> str:
        """Rebuild .smd text by replacing modified block headers in-place."""
        result = self._raw_text
        for block in self._doc.blocks:
            new_header = json.dumps(block.header, indent=4, ensure_ascii=False)
            old_header = block.raw_header.strip()
            if old_header in result:
                result = result.replace(old_header, new_header, 1)
        return result

    def _serialize_from_blocks(self) -> str:
        """Serialize purely from the parsed model (fallback)."""
        parts: List[str] = []
        for entity in self._doc.entities:
            if isinstance(entity, SMDBlock):
                header_json = json.dumps(entity.header, indent=4, ensure_ascii=False)
                body = entity.body_text or ""
                parts.append(f"@block\n{header_json}\n---\n{body}\n")
            elif isinstance(entity, SMDDocument):
                hdr = getattr(entity, "header", None)
                raw = getattr(entity, "raw_header", None) or (
                    json.dumps(hdr, indent=4, ensure_ascii=False) if hdr else "{}")
                body = getattr(entity, "body_text", "") or ""
                parts.append(f"@document\n{raw}\n---\n{body}\n")
        return "\n".join(parts)

    def save(self, path: Optional[str] = None) -> Path:
        """Write the modified document to disk."""
        out = Path(path) if path else self._source_path
        if out is None:
            raise ValueError("No output path specified and no source path available")
        text = self.to_smd_text()
        out.write_text(text, encoding="utf-8")
        return out


# ======================================================================
# read() helpers — parse query, build LLM-friendly entries
# ======================================================================


def _parse_read_query(query: str) -> tuple:
    """Parse a read query into (path, block_id, query_string).

    Examples:
        "foo/bar.smd"              → ("foo/bar.smd", None, None)
        "foo/bar.smd/*"            → ("foo/bar.smd", None, None)
        "foo/bar.smd/42"           → ("foo/bar.smd", "42", None)
        "foo/bar.smd/*?limit=5"    → ("foo/bar.smd", None, "limit=5")
        "foo/bar.smd/42?limit=1"   → ("foo/bar.smd", "42", "limit=1")
    """
    qs = ""
    if "?" in query:
        query, qs = query.split("?", 1)

    if "/" in query:
        *path_parts, last = query.rsplit("/", 1)
        path = "/".join(path_parts)
        if "." in last:
            # last has an extension → it's the filename
            return (query, None, qs or None)
        if last == "*":
            # wildcard → path is the directory part
            return (path, None, qs or None)
        # last is a block_id
        return (path, last, qs or None)

    return (query, None, qs or None)


def _build_doc_entry(doc: SMDDocument) -> dict:
    """Build the document-level entry with header as JSON content."""
    doc_header = {}
    for e in doc.entities:
        if hasattr(e, "header") and isinstance(e, SMDDocument):
            doc_header = e.header
            break
    header_json = json.dumps(doc_header, indent=2, ensure_ascii=False) if doc_header else "{}"
    return {
        "type": "document",
        "content": [{"type": "json", "text": header_json}],
    }


def _build_block_entry(block: SMDBlock) -> dict:
    """Build a block entry — body delivered as raw markdown, with block metadata."""
    body = block.body_text.strip()
    return {
        "type": "block",
        "block_id": block.block_id,
        "header": block.header,
        "content": [{"type": "markdown", "text": body}] if body else [],
    }


# ======================================================================
# search() helpers — parse, filter, serialise
# ======================================================================

def _parse_search(query: str) -> tuple:
    """Parse a search query into (path, block_id, filters_string).

    Examples:
        "foo/bar.smd"              → ("foo/bar.smd", None, None)
        "foo/bar.smd/42"           → ("foo/bar.smd", "42", None)
        "foo/bar.smd/*?filters=k:v" → ("foo/bar.smd", None, "k:v")
        "foo/bar.smd/42?filters=k:v" → ("foo/bar.smd", "42", "k:v")
    """
    qs = ""
    if "?" in query:
        query, qs = query.split("?", 1)

    raw_filters = None
    if qs:
        params = parse_qs(qs)
        raw_filters = params.get("filters", [None])[0]

    if "/" in query:
        *path_parts, last = query.rsplit("/", 1)
        if last == "*":
            return ("/".join(path_parts), None, raw_filters)
        if "." not in last:
            return ("/".join(path_parts), last, raw_filters)

    return (query, None, raw_filters)


def _parse_filters(raw) -> list:
    """Parse "k1:v1,k2:v2" into [(k1,v1), (k2,v2)]."""
    if not raw:
        return []
    result = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            result.append((k.strip(), v.strip()))
    return result


def _matches_all(block: SMDBlock, filters: list) -> bool:
    """Return True if the block matches ALL filters."""
    for key, want in filters:
        # Resolve "type" to both "type" and "block_type" headers
        hdr_val = block.header.get(key)
        if hdr_val is None and key == "type":
            hdr_val = block.header.get("block_type")
        if isinstance(hdr_val, list):
            if str(want) not in [str(x) for x in hdr_val]:
                return False
        elif hdr_val is not None:
            if str(hdr_val) != str(want):
                return False
        else:
            return False
    return True


def _serialize_block(block: SMDBlock, idx: int, total: int, all_blocks: list) -> dict:
    """Convert a block to dict with next_block_id / previous_block_id."""
    enr = _ensure_dict(block.header.get("enrichment",
                      block.header.get("enrichments", {})))
    return {
        "block_id": block.block_id,
        "type": block.type,
        "speaker": block.header.get("speaker", ""),
        "tags": block.tags,
        "header": block.header,
        "body": block.body_text.strip(),
        "enrichment": enr,
        "next_block_id": all_blocks[idx + 1].block_id if idx + 1 < total else None,
        "previous_block_id": all_blocks[idx - 1].block_id if idx > 0 else None,
    }


def _doc_summary(doc: SMDDocument) -> dict:
    """Build document metadata dict."""
    doc_header = {}
    for e in doc.entities:
        if hasattr(e, "header"):
            doc_header = e.header
            break
    return {
        "document_id": doc_header.get("document_id", ""),
        "type": doc_header.get("type", ""),
        "source": doc_header.get("source", ""),
        "schema_version": doc_header.get("schema_version", ""),
        "block_count": len(doc.blocks),
        "all_tags": doc.all_tags(),
        "meta": doc_header.get("meta", {}),
    }


def _empty_result(path, block_id, filters) -> dict:
    """Return an empty result dict."""
    return {
        "document": None,
        "blocks": [],
        "query": {"path": path, "block_id": block_id, "filters": filters},
    }


# ======================================================================
# Module-level helpers
# ======================================================================

def _ensure_dict(value: Any) -> dict:
    """Coerce enrichment value to a dict, handling list/None gracefully."""
    if isinstance(value, dict):
        return value
    return {}


def _match_id(a: Any, b: Any) -> bool:
    """Compare two block ids, handling int/str coercion."""
    if a == b:
        return True
    try:
        return str(a) == str(b)
    except (TypeError, ValueError):
        return False


def _get_block(doc: SMDDocument, block_id: str) -> Optional[SMDBlock]:
    """Find a block by id within a parsed document."""
    return next((b for b in doc.blocks if _match_id(b.block_id, block_id)), None)


def _index_of(doc: SMDDocument, block_id: Any) -> Optional[int]:
    """Return the index of a block in doc.blocks, or None."""
    for i, b in enumerate(doc.blocks):
        if _match_id(b.block_id, block_id):
            return i
    return None
