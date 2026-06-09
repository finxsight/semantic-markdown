"""
SMD Parser — reference implementation.

Parses .smd text into lightweight namespace objects.

Algorithm:
    1. Split input on lines starting with @document or @block
    2. For each raw entity, locate the first --- separator
    3. Parse the JSON header (text between @ line and ---)
    4. Parse the body into typed segments (markdown + fenced blocks)

The SMD format is self-describing — every entity carries its JSON header
plus raw body text.  No separate schema/model file is needed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

# ======================================================================
# Parse exceptions
# ======================================================================

class ParseError(Exception):
    """Raised when an SMD file cannot be parsed correctly."""

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        prefix = f"Line {line}: " if line is not None else ""
        super().__init__(f"{prefix}{message}")


class DuplicateBlockIdError(ParseError):
    """Raised when two blocks in the same document share a block_id."""

    def __init__(self, block_id: str, line: int | None = None):
        self.block_id = block_id
        super().__init__(f"Duplicate block_id: '{block_id}'", line=line)


class MalformedJsonError(ParseError):
    """Raised when a JSON header cannot be parsed."""

    def __init__(self, raw: str, inner: str, line: int | None = None):
        super().__init__(
            f"Malformed JSON header: {inner}\n  Raw header: {raw[:120]}",
            line=line,
        )


class MissingSeparatorError(ParseError):
    """Raised when a @block or @document has no --- separator."""

    def __init__(self, entity_type: str, block_id: str | None = None, line: int | None = None):
        suffix = f" ({block_id=})" if block_id else ""
        super().__init__(
            f"@{entity_type} missing '---' separator{suffix}",
            line=line,
        )


# Regex to match the start of an entity (@document or @block at line beginning)
_ENTITY_START = re.compile(r"^(?=@(?:document|block))", re.MULTILINE)

# Regex to find the first --- separator line
_SEPARATOR = re.compile(r"\n---\n")

# Regex to find fenced blocks: ```type\n...```
_FENCED_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


# ---------------------------------------------------------------------------
# Factory helpers — lightweight namespaces, no class definitions needed
# ---------------------------------------------------------------------------

def _block(block_id: str, header: dict, raw_header: str,
           segments: list, body_text: str) -> SimpleNamespace:
    """Create a lightweight block namespace with pre-computed convenience attrs."""
    sentiment = None
    raw_sent = header.get("sentiment")
    if isinstance(raw_sent, (int, float)):
        sentiment = float(raw_sent)
    return SimpleNamespace(
        kind="block",
        block_id=block_id,
        header=header,
        raw_header=raw_header,
        segments=segments,
        body_text=body_text,
        tags=header.get("tags", []),
        type=header.get("type") or header.get("block_type"),
        sentiment=sentiment,
    )


def _document(header: dict | None = None,
              raw_header: str = "") -> SimpleNamespace:
    """Create a lightweight document namespace."""
    return SimpleNamespace(
        kind="document",
        entities=[],
        header=header or {},
        raw_header=raw_header,
    )


def _finalize(doc: SimpleNamespace) -> SimpleNamespace:
    """Attach computed lists (blocks, documents) after all entities are added."""
    doc.blocks = [e for e in doc.entities if getattr(e, 'kind', None) == 'block']
    doc.documents = [e for e in doc.entities if getattr(e, 'kind', None) == 'document']
    return doc


def _seg(type: str, content: str) -> SimpleNamespace:
    """Create a lightweight body segment."""
    return SimpleNamespace(type=type, content=content)


def parse_smd(text: str) -> SimpleNamespace:
    """Parse a complete .smd document from a string.

    Args:
        text: Raw text content of an .smd file.

    Returns:
        A SimpleNamespace document with .entities, .blocks, .documents.

    Raises:
        ParseError: If the text cannot be parsed.
    """
    doc = _document()
    seen_ids: set[str] = set()

    # Step 1: Split on entity boundaries
    raw_entities = _ENTITY_START.split(text)

    for raw in raw_entities:
        # Fast empty check without stripping (which would remove trailing
        # newlines the separator regex needs).
        if not raw or raw.isspace():
            continue

        # Step 2: Determine entity type
        is_document = raw.startswith("@document")
        is_block = raw.startswith("@block")

        if not is_document and not is_block:
            # Text before first entity — skip
            continue

        entity_type = "document" if is_document else "block"

        # Step 3: Locate the --- separator
        sep_match = _SEPARATOR.search(raw)
        if sep_match is None:
            raise MissingSeparatorError(entity_type)

        # Step 4: Extract JSON header
        first_newline = raw.index("\n")
        header_text = raw[first_newline : sep_match.start()].strip()

        try:
            header: dict[str, Any] = json.loads(header_text)
        except json.JSONDecodeError as e:
            raise MalformedJsonError(header_text, str(e))

        # Step 5: Extract body
        body_text = raw[sep_match.end() :].strip()

        if is_document:
            # @document — create a nested document
            sub_doc = _document(header, header_text)
            sub_doc.entities = _parse_body_segments(body_text)
            _finalize(sub_doc)
            doc.entities.append(sub_doc)

        else:
            # @block
            block_id = header.get("block_id")
            if block_id is not None:
                if block_id in seen_ids:
                    raise DuplicateBlockIdError(block_id)
                seen_ids.add(block_id)

            segments = _parse_body_segments(body_text)
            block = _block(
                block_id=str(block_id) if block_id is not None else "",
                header=header,
                raw_header=header_text,
                segments=segments,
                body_text=body_text,
            )
            doc.entities.append(block)

    return _finalize(doc)


def parse_file(path: str | Path) -> SimpleNamespace:
    """Parse an .smd file from disk.

    Args:
        path: Path to the .smd file.

    Returns:
        A SimpleNamespace document with .entities, .blocks, .documents.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SMD file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return parse_smd(text)


def _parse_body_segments(body: str) -> list:
    """Split a block/document body into typed segments.

    Recognizes triple-backtick fenced blocks (```type ... ```).
    Everything else is treated as markdown.
    """
    if not body:
        return []

    segments: list = []
    last_end = 0

    for match in _FENCED_BLOCK.finditer(body):
        start = match.start()

        # Emit markdown segment before this fenced block
        if start > last_end:
            text = body[last_end:start]
            stripped = text.strip()
            if stripped:
                segments.append(_seg("markdown", text))

        # Emit fenced segment
        seg_type = match.group(1) or "unknown"
        content = match.group(2)
        segments.append(_seg(seg_type, content))

        last_end = match.end()

    # Emit remaining markdown after last fenced block
    if last_end < len(body):
        text = body[last_end:]
        stripped = text.strip()
        if stripped:
            segments.append(_seg("markdown", text))

    return segments


# ---------------------------------------------------------------------------
# Collection-level helpers (operate on a parsed document namespace)
# ---------------------------------------------------------------------------

def all_tags(doc: SimpleNamespace) -> list:
    """Return all unique tags across all blocks, in order of first appearance."""
    seen: set[str] = set()
    result: list = []
    for b in doc.blocks:
        for t in b.tags:
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def filter_by_tag(doc: SimpleNamespace, tag: str) -> list:
    """Return all blocks containing a specific tag."""
    return [b for b in doc.blocks if tag in b.tags]


def filter_by_type(doc: SimpleNamespace, block_type: str) -> list:
    """Return all blocks with a specific type."""
    return [b for b in doc.blocks if b.type == block_type]


def filter_by_tags(doc: SimpleNamespace, tags: list, mode: str = "any") -> list:
    """Return blocks matching a set of tags.

    Args:
        tags: List of tags to match.
        mode: "any" = block has at least one tag; "all" = block has every tag.
    """
    if mode == "any":
        return [b for b in doc.blocks if any(t in b.tags for t in tags)]
    elif mode == "all":
        return [b for b in doc.blocks if all(t in b.tags for t in tags)]
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'any' or 'all'.")


def tag_co_occurrence(doc: SimpleNamespace) -> dict:
    """Build a tag co-occurrence matrix for clustering pipelines.

    Returns:
        Dict mapping each tag -> {other_tag: count}.
    """
    matrix: dict = {}
    for block in doc.blocks:
        tags = block.tags
        for t1 in tags:
            if t1 not in matrix:
                matrix[t1] = {}
            for t2 in tags:
                if t1 != t2:
                    matrix[t1][t2] = matrix[t1].get(t2, 0) + 1
    return matrix
