"""
SMD Parser — reference implementation.

Parses .smd text into SMDDocument / SMDBlock entities.

Algorithm:
    1. Split input on lines starting with @document or @block
    2. For each raw entity, locate the first --- separator
    3. Parse the JSON header (text between @ line and ---)
    4. Parse the body into typed segments (markdown + fenced blocks)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, List

from .errors import (
    DuplicateBlockIdError,
    MalformedJsonError,
    MissingSeparatorError,
    ParseError,
)
from .models import BodySegment, SMDBlock, SMDDocument


# Regex to match the start of an entity (@document or @block at line beginning)
_ENTITY_START = re.compile(r"^(?=@(?:document|block))", re.MULTILINE)

# Regex to find the first --- separator line
_SEPARATOR = re.compile(r"\n---\n")

# Regex to find fenced blocks: ```type\n...```
_FENCED_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


def parse_smd(text: str) -> SMDDocument:
    """Parse a complete .smd document from a string.

    Args:
        text: Raw text content of an .smd file.

    Returns:
        An SMDDocument containing all parsed entities.

    Raises:
        ParseError: If the text cannot be parsed.
    """
    doc = SMDDocument()
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
            # @document — create a nested SMDDocument
            sub_doc = SMDDocument()
            sub_doc.entities = _parse_body_segments(body_text)
            # Store header info directly on the document for access
            sub_doc.header = header  # type: ignore[attr-defined]
            sub_doc.raw_header = header_text  # type: ignore[attr-defined]
            doc.entities.append(sub_doc)

        else:
            # @block
            block_id = header.get("block_id")
            if block_id is not None:
                if block_id in seen_ids:
                    raise DuplicateBlockIdError(block_id)
                seen_ids.add(block_id)

            segments = _parse_body_segments(body_text)
            block = SMDBlock(
                block_id=str(block_id) if block_id is not None else "",
                header=header,
                raw_header=header_text,
                segments=segments,
                body_text=body_text,
            )
            doc.entities.append(block)

    return doc


def parse_file(path: str | Path) -> SMDDocument:
    """Parse an .smd file from disk.

    Args:
        path: Path to the .smd file.

    Returns:
        An SMDDocument containing all parsed entities.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SMD file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return parse_smd(text)


def _parse_body_segments(body: str) -> List[BodySegment]:
    """Split a block/document body into typed segments.

    Recognizes triple-backtick fenced blocks (```type ... ```).
    Everything else is treated as markdown.
    """
    if not body:
        return []

    segments: List[BodySegment] = []
    last_end = 0

    for match in _FENCED_BLOCK.finditer(body):
        start = match.start()

        # Emit markdown segment before this fenced block
        if start > last_end:
            text = body[last_end:start]
            stripped = text.strip()
            if stripped:
                segments.append(BodySegment(type="markdown", content=text))

        # Emit fenced segment
        seg_type = match.group(1) or "unknown"
        content = match.group(2)
        segments.append(BodySegment(type=seg_type, content=content))

        last_end = match.end()

    # Emit remaining markdown after last fenced block
    if last_end < len(body):
        text = body[last_end:]
        stripped = text.strip()
        if stripped:
            segments.append(BodySegment(type="markdown", content=text))

    return segments
