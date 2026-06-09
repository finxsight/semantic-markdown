#!/usr/bin/env python3
"""
SMD Agent Harness — a controlled interface between LLMs and SMD documents.

This module combines the SMDAgent (document loading, querying, enrichment)
with an MCP server that exposes those capabilities as discrete, auditable
tools.  An LLM connected via MCP never touches the filesystem directly —
every read, write, and enrichment goes through this harness.

Architecture
------------
::

    ┌──────┐  MCP tools   ┌───────────────┐  method calls  ┌──────────┐
    │ LLM  │──────────────│  FastMCP       │───────────────│ SMDAgent │
    │      │◀─────────────│  (this file)   │◀──────────────│ (in mem) │
    └──────┘  flat results │               │  state + rules │          │
                           └───────────────┘                └──────────┘

Why a harness?
--------------
Without a harness, an LLM given filesystem access could:

- Overwrite the original document
- Corrupt block headers with malformed JSON
- Delete blocks or reorder them unintentionally
- Leak enrichment data into the body text

The harness enforces:

- **Controlled reads** — blocks returned as flat, paginated lists;
  the LLM never sees raw file bytes.
- **Controlled writes** — enrichment is written through typed CRUD
  methods that validate structure (highlights get auto-generated IDs,
  sentiment arrays keep their schema, etc.).
- **Explicit save** — modifications are staged in memory; nothing hits
  disk until ``save()`` is called.
- **Audit trail** — every mutation goes through a single agent instance,
  making it easy to log or revert changes.

This is the same pattern used by Cursor, Claude Code, and other
agentic coding tools: the model proposes, the harness disposes.

Usage
-----
::

    # As an MCP server (LLM integration)
    smd-mcp

    # Programmatic use
    from semantic_markdown.harness import SMDAgent

    agent = SMDAgent()
    result = agent.search("transcript.smd")
    for block in result["blocks"]:
        agent.add_enrichment(block["block_id"], "highlights",
                             {"text": "Key insight", "sentiment": 0.8})
    agent.save("enriched.smd")

Tools exposed via MCP
---------------------
``read``, ``search``, ``add_enrichment``, ``del_enrichment``,
``edit_enrichment``, ``write_sentiment``, ``write_tags``,
``filter_blocks``, ``read_next_qa``, ``read_next_block``,
``read_document``, ``save``
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from .parser import parse_smd, parse_file, all_tags


# ======================================================================
# SMDAgent — in-memory document state + controlled operations
# ======================================================================

class SMDAgent:
    """Agent for loading, searching, and enriching SMD documents.

    All document access flows through this class.  There is no direct
    filesystem I/O exposed to the caller except through the explicit
    ``save()`` method.

    search(query) -> dict
        Unified entry point with URL-like syntax:
        - ``"path"`` — load document, return ALL blocks.
        - ``"path/block_id"`` — return a single block.
        - ``"path/*?filters=k:v,..."`` — return blocks matching filters.
        - ``"path/block_id?filters=..."`` — block only if it matches.

        Every block includes ``next_block_id`` and ``previous_block_id``
        for document-order navigation (None at edges).

    read(query, limit?, offset?) -> list
        LLM-friendly flat list of document + block entries with typed
        content segments.  Supports pagination via limit/offset.

    Enrichment CRUD
    ---------------
    add_enrichment(block_id, key, value, enrichment_id?) -> str | None
    del_enrichment(block_id, key, enrichment_id?) -> bool
    edit_enrichment(block_id, key, value, enrichment_id?) -> bool

    write_sentiment(block_id, excerpts) -> bool
    write_tags(block_id, tags) -> bool

    filter_blocks(filters) -> list
    read_next_qa(block_id) -> dict | None
    read_next_block(block_id) -> dict | None
    read_document() -> dict

    save(path?) -> Path
    """

    def __init__(self):
        self._doc: Optional[SimpleNamespace] = None
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
    # Sentiment & tags
    # ==================================================================

    def write_sentiment(self, block_id: str, excerpts: List[dict]) -> bool:
        """Write sentiment annotations to a block.

        Args:
            block_id: Target block id.
            excerpts: List of {excerpt, score, label, confidence} dicts.

        Returns:
            True if the block was found and updated.
        """
        if self._doc is None:
            return False
        block = _get_block(self._doc, block_id)
        if block is None:
            return False
        block.header["sentiment"] = excerpts
        return True

    def write_tags(self, block_id: str, tags: List[str]) -> bool:
        """Replace the tags list on a block.

        Args:
            block_id: Target block id.
            tags: New list of tag strings.

        Returns:
            True if the block was found and updated.
        """
        if self._doc is None:
            return False
        block = _get_block(self._doc, block_id)
        if block is None:
            return False
        block.header["tags"] = tags
        return True

    # ==================================================================
    # Block navigation helpers
    # ==================================================================

    def filter_blocks(self, filters: str) -> List[dict]:
        """Return blocks matching filters (without reloading the document).

        Args:
            filters: Comma-separated ``key:value`` pairs.

        Returns:
            List of matching block dicts with next/prev navigation.
        """
        if self._doc is None:
            return []
        parsed = _parse_filters(filters)
        all_blocks = self._doc.blocks
        n = len(all_blocks)
        return [
            _serialize_block(b, i, n, all_blocks)
            for i, b in enumerate(all_blocks)
            if _matches_all(b, parsed)
        ]

    def read_next_qa(self, block_id: str) -> Optional[dict]:
        """Return the next Q&A block after the given block_id."""
        if self._doc is None:
            return None
        idx = _index_of(self._doc, block_id)
        if idx is None:
            return None
        all_blocks = self._doc.blocks
        n = len(all_blocks)
        for i in range(idx + 1, n):
            b = all_blocks[i]
            if b.header.get("type") == "qa":
                return _serialize_block(b, i, n, all_blocks)
        return None

    def read_next_block(self, block_id: str) -> Optional[dict]:
        """Return the next block (any type) after the given block_id."""
        if self._doc is None:
            return None
        idx = _index_of(self._doc, block_id)
        if idx is None or idx + 1 >= len(self._doc.blocks):
            return None
        all_blocks = self._doc.blocks
        n = len(all_blocks)
        return _serialize_block(all_blocks[idx + 1], idx + 1, n, all_blocks)

    def read_document(self) -> dict:
        """Return document-level metadata for the currently loaded document."""
        if self._doc is None:
            return {"document": None}
        return {"document": _doc_summary(self._doc)}

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
            if entity.kind == "block":
                header_json = json.dumps(entity.header, indent=4, ensure_ascii=False)
                body = entity.body_text or ""
                parts.append(f"@block\n{header_json}\n---\n{body}\n")
            elif entity.kind == "document":
                hdr = getattr(entity, "header", None)
                raw = getattr(entity, "raw_header", None) or (
                    json.dumps(hdr, indent=4, ensure_ascii=False) if hdr else "{}")
                body = getattr(entity, "body_text", "") or ""
                parts.append(f"@document\n{raw}\n---\n{body}\n")
        return "\n".join(parts)

    def save(self, path: Optional[str] = None) -> Path:
        """Write the modified document to disk.

        This is the ONLY method that touches the filesystem for writes.
        All enrichment mutations are staged in memory until this is called.
        """
        out = Path(path) if path else self._source_path
        if out is None:
            raise ValueError("No output path specified and no source path available")
        text = self.to_smd_text()
        out.write_text(text, encoding="utf-8")
        return out


# ======================================================================
# MCP Server — wraps SMDAgent as discrete tools for LLM consumption
# ======================================================================

# Global agent instance shared across all tool calls.
# A single instance means mutations accumulate and save() writes
# everything at once — the LLM's "working copy" pattern.
_agent: SMDAgent | None = None


def _get_agent() -> SMDAgent:
    """Lazy singleton agent instance."""
    global _agent
    if _agent is None:
        _agent = SMDAgent()
    return _agent


# Tool implementations (plain functions — registered with FastMCP lazily)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Tool: read
# ----------------------------------------------------------------------

def _tool_read(
    query: str,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list:
    """Load an SMD document and return blocks in an LLM-friendly flat list.

    Call this FIRST before any other tool.  Uses URL-like syntax::

        "path/to/file.smd"              -> all blocks + document header
        "path/to/file.smd/*"            -> all blocks + document header
        "path/to/file.smd/block_id"      -> single block + document header
        "path/to/file.smd/*?limit=5"     -> first 5 blocks + document header
        "path/to/file.smd/*?offset=3"    -> skip first 3 blocks

    Returns
    -------
    A flat list of entries::

        [
            {"type": "document", "content": [{"type": "json", "text": "..."}]},
            {"type": "block", "block_id": "0", "content": [
                {"type": "speaker", "speaker": "Operator", "text": "..."},
                {"type": "markdown", "text": "..."},
            ]},
            ...
        ]

    Content segment types: ``speaker`` (attributed to **Name:** marker,
    with ``speaker`` field), ``narrative`` (text without speaker marker),
    ``markdown``, ``fenced`` (code blocks).

    Args:
        query: URL-like query string (see syntax above).
        limit: Optional max number of blocks to return (default: all).
        offset: Optional number of blocks to skip (default: 0).

    Returns:
        List of entry dicts (document entry + block entries).
    """
    return _get_agent().read(query, limit=limit, offset=offset)


# ----------------------------------------------------------------------
# Tool: search
# ----------------------------------------------------------------------

def search(query: str) -> dict:
    """Load/query an SMD document and return matching blocks.

    Call this FIRST before any other tool.  Uses URL-like syntax::

        "path/to/file.smd"                     -> all blocks
        "path/to/file.smd/block_id"             -> single block
        "path/to/file.smd/*?filters=k:v,..."     -> filtered blocks
        "path/to/file.smd/block_id?filters=..."  -> single + filter

    Every block includes ``next_block_id`` and ``previous_block_id``
    for document-order navigation.

    Args:
        query: URL-like query string (see syntax above).

    Returns:
        dict with ``document`` (metadata), ``blocks`` (list of block
        dicts), and ``query`` (parsed query info).
    """
    return _get_agent().search(query)


# ----------------------------------------------------------------------
# Tool: add_enrichment
# ----------------------------------------------------------------------

def add_enrichment(
    block_id: str,
    key: str,
    value: str,
    enrichment_id: Optional[str] = None,
) -> Optional[str]:
    """Add an enrichment item to a block.

    For *highlights*: appends to the highlights list.  An auto-generated
    enrichment_id is assigned unless you provide one.  *value* can be a
    JSON string like ``{"text":"...", "sentiment":0.8}`` or plain text.

    For other keys (summary, key_takeaways, entities): sets the value.

    Args:
        block_id: Target block id.
        key: Enrichment field ("highlights", "summary", "key_takeaways", ...).
        value: JSON string or plain text.
        enrichment_id: Optional explicit id for the highlight.

    Returns:
        The enrichment_id (string) if key is "highlights", else None.
        Returns None on failure.
    """
    parsed = _try_parse_json(value)
    return _get_agent().add_enrichment(block_id, key, parsed, enrichment_id)


# ----------------------------------------------------------------------
# Tool: del_enrichment
# ----------------------------------------------------------------------

def del_enrichment(
    block_id: str,
    key: str,
    enrichment_id: Optional[str] = None,
) -> bool:
    """Delete an enrichment item from a block.

    If *enrichment_id* is given and key is "highlights", removes only
    that specific highlight.  Otherwise removes the entire key.

    Args:
        block_id: Target block id.
        key: Enrichment field name.
        enrichment_id: Optional specific highlight id to remove.

    Returns:
        True if deletion succeeded (or nothing to delete).
    """
    return _get_agent().del_enrichment(block_id, key, enrichment_id)


# ----------------------------------------------------------------------
# Tool: edit_enrichment
# ----------------------------------------------------------------------

def edit_enrichment(
    block_id: str,
    key: str,
    value: str,
    enrichment_id: Optional[str] = None,
) -> bool:
    """Edit an existing enrichment item on a block.

    If *enrichment_id* is given and key is "highlights", merges *value*
    into the matching highlight.  Otherwise replaces the entire key.

    Args:
        block_id: Target block id.
        key: Enrichment field name.
        value: New value (JSON string or plain text).
        enrichment_id: Optional specific highlight id to edit.

    Returns:
        True if edit succeeded, False if block/highlight not found.
    """
    parsed = _try_parse_json(value)
    return _get_agent().edit_enrichment(block_id, key, parsed, enrichment_id)


# ----------------------------------------------------------------------
# Tool: write_sentiment
# ----------------------------------------------------------------------

def write_sentiment(block_id: str, excerpts: str) -> bool:
    """Write sentiment annotations to a block.

    Args:
        block_id: Target block id.
        excerpts: JSON array of {excerpt, score, label, confidence} objects.

    Returns:
        True if the block was found and updated.
    """
    parsed = _try_parse_json(excerpts)
    if not isinstance(parsed, list):
        parsed = [parsed]
    return _get_agent().write_sentiment(block_id, parsed)


# ----------------------------------------------------------------------
# Tool: write_tags
# ----------------------------------------------------------------------

def write_tags(block_id: str, tags: str) -> bool:
    """Replace the tags list on a block.

    Args:
        block_id: Target block id.
        tags: JSON array of tag strings, e.g. '["guidance", "margins"]'.

    Returns:
        True if the block was found and updated.
    """
    parsed = _try_parse_json(tags)
    if not isinstance(parsed, list):
        parsed = [parsed]
    return _get_agent().write_tags(block_id, parsed)


# ----------------------------------------------------------------------
# Tool: filter_blocks
# ----------------------------------------------------------------------

def filter_blocks(filters: str) -> list:
    """Return blocks matching filters from the currently loaded document.

    Does NOT reload the document — uses the in-memory copy.

    Args:
        filters: Comma-separated ``key:value`` pairs (e.g. "type:qa,tags:guidance").

    Returns:
        List of matching block dicts with next/prev navigation.
    """
    return _get_agent().filter_blocks(filters)


# ----------------------------------------------------------------------
# Tool: read_next_qa
# ----------------------------------------------------------------------

def read_next_qa(block_id: str) -> Optional[dict]:
    """Return the next Q&A block after the given block_id.

    Args:
        block_id: The current block id to search forward from.

    Returns:
        The next Q&A block dict, or None if no more Q&A blocks follow.
    """
    return _get_agent().read_next_qa(block_id)


# ----------------------------------------------------------------------
# Tool: read_next_block
# ----------------------------------------------------------------------

def read_next_block(block_id: str) -> Optional[dict]:
    """Return the next block (any type) after the given block_id.

    Args:
        block_id: The current block id to search forward from.

    Returns:
        The next block dict, or None if at end of document.
    """
    return _get_agent().read_next_block(block_id)


# ----------------------------------------------------------------------
# Tool: read_document
# ----------------------------------------------------------------------

def read_document() -> dict:
    """Return document-level metadata for the currently loaded document.

    Returns:
        dict with document metadata (id, type, block_count, all_tags, etc.).
    """
    return _get_agent().read_document()


# ----------------------------------------------------------------------
# Tool: save
# ----------------------------------------------------------------------

def save(path: Optional[str] = None) -> str:
    """Save the modified document to disk.

    This is the ONLY tool that writes to the filesystem.  All enrichment
    mutations (add_enrichment, write_sentiment, write_tags, etc.) are
    staged in memory until this is called.

    Args:
        path: Output file path.  Defaults to the original source path.

    Returns:
        The absolute path to the written file.
    """
    out = _get_agent().save(path)
    return str(out.resolve())


# ======================================================================
# Lazy MCP server builder — only imports mcp when the server is started
# ======================================================================

def _build_mcp():
    """Build and return a FastMCP server with all tools registered.

    FastMCP is imported lazily here so that ``SMDAgent`` and the parser
    can be used without the ``mcp`` package installed.  Only ``smd-mcp``
    requires it.
    """
    from mcp.server.fastmcp import FastMCP  # lazy import

    mcp = FastMCP("SMD Agent Harness")

    # Register all tool functions with the MCP server
    mcp.tool()(_tool_read)
    mcp.tool()(search)
    mcp.tool()(add_enrichment)
    mcp.tool()(del_enrichment)
    mcp.tool()(edit_enrichment)
    mcp.tool()(write_sentiment)
    mcp.tool()(write_tags)
    mcp.tool()(filter_blocks)
    mcp.tool()(read_next_qa)
    mcp.tool()(read_next_block)
    mcp.tool()(read_document)
    mcp.tool()(save)

    return mcp


# ======================================================================
# Entry point
# ======================================================================

def main():
    """Entry point for console_scripts (smd-mcp)."""
    _build_mcp().run()


if __name__ == "__main__":
    main()

def _try_parse_json(raw: str) -> Any:
    """Try to parse a string as JSON; fall back to the raw string."""
    if not isinstance(raw, str):
        return raw
    stripped = raw.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or \
       (stripped.startswith("[") and stripped.endswith("]")):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass
    return raw


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
            return (query, None, qs or None)
        if last == "*":
            return (path, None, qs or None)
        return (path, last, qs or None)

    return (query, None, qs or None)


def _build_doc_entry(doc: SimpleNamespace) -> dict:
    """Build the document-level entry with header as JSON content."""
    doc_header = {}
    for e in doc.entities:
        if hasattr(e, "kind") and e.kind == "document":
            doc_header = e.header
            break
    header_json = json.dumps(doc_header, indent=2, ensure_ascii=False) if doc_header else "{}"
    return {
        "type": "document",
        "content": [{"type": "json", "text": header_json}],
    }


def _build_block_entry(block: SimpleNamespace) -> dict:
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


def _matches_all(block: SimpleNamespace, filters: list) -> bool:
    """Return True if the block matches ALL filters."""
    for key, want in filters:
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


def _serialize_block(block: SimpleNamespace, idx: int, total: int, all_blocks: list) -> dict:
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


def _doc_summary(doc: SimpleNamespace) -> dict:
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
        "all_tags": all_tags(doc),
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


def _get_block(doc: SimpleNamespace, block_id: str) -> Optional[SimpleNamespace]:
    """Find a block by id within a parsed document."""
    return next((b for b in doc.blocks if _match_id(b.block_id, block_id)), None)


def _index_of(doc: SimpleNamespace, block_id: Any) -> Optional[int]:
    """Return the index of a block in doc.blocks, or None."""
    for i, b in enumerate(doc.blocks):
        if _match_id(b.block_id, block_id):
            return i
    return None


# ======================================================================
# Entry point
# ======================================================================

def main():
    """Entry point for console_scripts (smd-mcp)."""
    mcp.run()


if __name__ == "__main__":
    main()
