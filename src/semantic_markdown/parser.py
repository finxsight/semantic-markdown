"""
SMD Parser — reference implementation (v0.2, FIRE-aligned).

Parses .smd text into lightweight namespace objects:

    @document { json }  [---]  [title preamble]
    @block { json }  [---]  body …

Block identity: ``_id`` (preferred), then ``block_id``, then ``id``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

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
    """Raised when two blocks in the same document share an id."""

    def __init__(self, block_id: str, line: int | None = None):
        self.block_id = block_id
        super().__init__(f"Duplicate block id: '{block_id}'", line=line)


class MalformedJsonError(ParseError):
    """Raised when a JSON header cannot be parsed."""

    def __init__(self, raw: str, inner: str, line: int | None = None):
        super().__init__(
            f"Malformed JSON header: {inner}\n  Raw header: {raw[:120]}",
            line=line,
        )


class MissingSeparatorError(ParseError):
    """Raised when @block JSON cannot be read."""

    def __init__(self, entity_type: str, block_id: str | None = None, line: int | None = None):
        suffix = f" ({block_id=})" if block_id else ""
        super().__init__(
            f"@{entity_type} missing valid JSON header{suffix}",
            line=line,
        )


_RE_DOC = re.compile(r"^@document\s*$", re.MULTILINE)
_RE_BLOCK = re.compile(r"^@block\s*$", re.MULTILINE)
_FENCED_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


def _extract_json_object(text: str) -> Tuple[Optional[str], int]:
    """Return (json_str, end_index_in_text) for a leading `{` object."""
    stripped = text.lstrip()
    if not stripped or stripped[0] != "{":
        return None, 0
    leading_ws = len(text) - len(stripped)
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(stripped):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return stripped[: i + 1], leading_ws + i + 1
    return None, 0


def _block_id_from_header(header: dict[str, Any]) -> Optional[str]:
    for key in ("_id", "block_id", "id"):
        val = header.get(key)
        if val is None or isinstance(val, bool):
            continue
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        s = str(val).strip()
        if s:
            return s
    return None


def _block_type_from_header(header: dict[str, Any]) -> Optional[str]:
    for key in ("section_type", "type", "block_type"):
        val = header.get(key)
        if val not in (None, ""):
            return str(val)
    return None


def _block(
    block_id: str,
    header: dict,
    raw_header: str,
    segments: list,
    body_text: str,
) -> SimpleNamespace:
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
        type=_block_type_from_header(header),
        sentiment=sentiment,
    )


def _document(header: dict | None = None, raw_header: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        kind="document",
        entities=[],
        header=header or {},
        raw_header=raw_header,
    )


def _finalize(doc: SimpleNamespace) -> SimpleNamespace:
    doc.blocks = [e for e in doc.entities if getattr(e, "kind", None) == "block"]
    doc.documents = [e for e in doc.entities if getattr(e, "kind", None) == "document"]
    if not getattr(doc, "header", None) and doc.documents:
        doc.header = doc.documents[0].header
    elif not getattr(doc, "header", None):
        doc.header = {}
    if not hasattr(doc, "preamble"):
        doc.preamble = ""
    return doc


def _seg(type: str, content: str) -> SimpleNamespace:
    return SimpleNamespace(type=type, content=content)


def _split_document(text: str) -> Tuple[Optional[dict], str, str, list[tuple[dict, str, str]]]:
    """Return (doc_header, doc_raw_header, preamble, blocks)."""
    doc_header: Optional[dict] = None
    doc_raw_header = ""
    preamble = ""
    blocks: list[tuple[dict, str, str]] = []

    rest = text
    doc_match = _RE_DOC.search(text)
    if doc_match:
        after_doc = text[doc_match.end() :]
        json_str, json_end = _extract_json_object(after_doc)
        if json_str is not None:
            doc_raw_header = json_str
            try:
                doc_header = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise MalformedJsonError(json_str, str(e))
            rest = after_doc[json_end:]
        else:
            rest = after_doc

        next_block = _RE_BLOCK.search(rest)
        if next_block:
            preamble = rest[: next_block.start()]
            rest = rest[next_block.start() :]
        else:
            preamble = rest
            rest = ""

    while rest:
        match = _RE_BLOCK.search(rest)
        if not match:
            break
        after_directive = rest[match.end() :]
        json_str, json_end = _extract_json_object(after_directive)
        if json_str is None:
            raise MissingSeparatorError("block")

        try:
            meta = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise MalformedJsonError(json_str, str(e))

        after_json = after_directive[json_end:]
        sep_match = re.match(r"\s*---\s*\n?", after_json)
        body_start = json_end + (sep_match.end() if sep_match else 0)

        next_block = _RE_BLOCK.search(after_directive, body_start)
        if next_block:
            body = after_directive[body_start : next_block.start()]
            rest = after_directive[next_block.start() :]
        else:
            body = after_directive[body_start:]
            rest = ""

        blocks.append((meta, json_str, body))

    return doc_header, doc_raw_header, preamble, blocks


def parse_smd(text: str) -> SimpleNamespace:
    """Parse a complete .smd document from a string."""
    doc = _document()
    doc.entities = []
    doc.preamble = ""

    doc_header, doc_raw, preamble, raw_blocks = _split_document(text)
    doc.preamble = preamble.strip()

    if doc_header is not None:
        sub = _document(doc_header, doc_raw)
        doc.entities.append(sub)
        doc.header = doc_header

    seen_ids: set[str] = set()
    for meta, raw_header, body_text in raw_blocks:
        block_id = _block_id_from_header(meta)
        if block_id is not None:
            if block_id in seen_ids:
                raise DuplicateBlockIdError(block_id)
            seen_ids.add(block_id)

        body_text = body_text.strip()
        segments = _parse_body_segments(body_text)
        block = _block(
            block_id=block_id or "",
            header=meta,
            raw_header=raw_header,
            segments=segments,
            body_text=body_text,
        )
        doc.entities.append(block)

    return _finalize(doc)


def parse_file(path: str | Path) -> SimpleNamespace:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SMD file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return parse_smd(text)


def _parse_body_segments(body: str) -> list:
    if not body:
        return []

    segments: list = []
    last_end = 0

    for match in _FENCED_BLOCK.finditer(body):
        start = match.start()
        if start > last_end:
            text = body[last_end:start]
            stripped = text.strip()
            if stripped:
                segments.append(_seg("markdown", text))

        seg_type = match.group(1) or "unknown"
        content = match.group(2)
        segments.append(_seg(seg_type, content))
        last_end = match.end()

    if last_end < len(body):
        text = body[last_end:]
        stripped = text.strip()
        if stripped:
            segments.append(_seg("markdown", text))

    return segments


# ---------------------------------------------------------------------------
# Collection-level helpers
# ---------------------------------------------------------------------------

def all_tags(doc: SimpleNamespace) -> list:
    seen: set[str] = set()
    result: list = []
    for b in doc.blocks:
        for t in b.tags:
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def filter_by_tag(doc: SimpleNamespace, tag: str) -> list:
    return [b for b in doc.blocks if tag in b.tags]


def filter_by_type(doc: SimpleNamespace, block_type: str) -> list:
    return [b for b in doc.blocks if b.type == block_type]


def filter_by_tags(doc: SimpleNamespace, tags: list, mode: str = "any") -> list:
    if mode == "any":
        return [b for b in doc.blocks if any(t in b.tags for t in tags)]
    if mode == "all":
        return [b for b in doc.blocks if all(t in b.tags for t in tags)]
    raise ValueError(f"Unknown mode: {mode}. Use 'any' or 'all'.")


def tag_co_occurrence(doc: SimpleNamespace) -> dict:
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
