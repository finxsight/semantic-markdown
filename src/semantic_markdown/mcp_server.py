#!/usr/bin/env python3
"""MCP Server for Semantic Markdown (SMD) Agent.

Exposes SMDAgent tools via the Model Context Protocol so an LLM
can load, query, and enrich .smd documents through tool-calling.

Tools: read, search, add_enrichment, del_enrichment, edit_enrichment, save.

read() syntax (URL-like):
    "path/to/file.smd"             -> all blocks + document header
    "path/to/file.smd/*"           -> same
    "path/to/file.smd/block_id"     -> single block + document header
    "path/to/file.smd/*?limit=5"    -> paginated blocks

Returns a flat list of {type, block_id?, content} objects where content
is an array of typed segments ({type, text, ...}) suitable for LLM traversal.

Usage:
    PYTHONPATH=src python3.12 -m semantic_markdown.mcp_server
"""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .agent import SMDAgent

# ======================================================================
# Global state — one agent instance shared across all tool calls
# ======================================================================

_agent = SMDAgent()

# ======================================================================
# FastMCP server
# ======================================================================

mcp = FastMCP("SMD Agent")


# ======================================================================
# Tool: read
# ======================================================================

@mcp.tool()
def read(
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
    return _agent.read(query, limit=limit, offset=offset)


# ======================================================================
# Tool: search
# ======================================================================

@mcp.tool()
def search(query: str) -> dict:
    """Load/query an SMD document and return matching blocks.

    Call this FIRST before any other tool.  Uses URL-like syntax:

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
    return _agent.search(query)


# ======================================================================
# Tool: add_enrichment
# ======================================================================

@mcp.tool()
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
    # Parse JSON if value looks like a JSON object/array
    parsed = _try_parse_json(value)
    return _agent.add_enrichment(block_id, key, parsed, enrichment_id)


# ======================================================================
# Tool: del_enrichment
# ======================================================================

@mcp.tool()
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
    return _agent.del_enrichment(block_id, key, enrichment_id)


# ======================================================================
# Tool: edit_enrichment
# ======================================================================

@mcp.tool()
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
    return _agent.edit_enrichment(block_id, key, parsed, enrichment_id)


# ======================================================================
# Tool: save
# ======================================================================

@mcp.tool()
def save(path: Optional[str] = None) -> str:
    """Save the modified document to disk.

    Args:
        path: Output file path.  Defaults to the original source path.

    Returns:
        The absolute path to the written file.
    """
    out = _agent.save(path)
    return str(out.resolve())





# ======================================================================
# Helpers
# ======================================================================

def _try_parse_json(raw: str) -> Any:
    """Try to parse a string as JSON; fall back to the raw string."""
    if not isinstance(raw, str):
        return raw
    stripped = raw.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or \
       (stripped.startswith("[") and stripped.endswith("]")):
        try:
            import json
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass
    return raw


# ======================================================================
# Entry point
# ======================================================================

def main():
    """Entry point for console_scripts."""
    mcp.run()


if __name__ == "__main__":
    main()
