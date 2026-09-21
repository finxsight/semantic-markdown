#!/usr/bin/env python3
"""Rewrite examples/*.smd to normative v0.2 headers (run once, then delete if desired)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from semantic_markdown.parser import _split_document  # noqa: E402


def _migrate_doc(header: dict) -> dict:
    out = dict(header)
    if "document_type" not in out and "type" in out:
        out["document_type"] = out.pop("type")
    out.pop("schema_version", None)
    filters = []
    for f in out.get("filters") or []:
        if not isinstance(f, dict):
            continue
        f = dict(f)
        if f.get("key") == "block_type":
            f["key"] = "section_type"
        if "enrichments" in str(f.get("key", "")):
            continue
        filters.append(f)
    if filters:
        out["filters"] = filters
    elif "filters" in out:
        del out["filters"]

    styles = []
    for s in out.get("styles") or []:
        if not isinstance(s, dict):
            continue
        s = dict(s)
        match = dict(s.get("match") or {})
        key = match.get("key", "")
        if "enrichments" in str(key):
            continue
        if match.get("key") == "block_type":
            match["key"] = "section_type"
        s["match"] = match
        styles.append(s)
    if styles:
        out["styles"] = styles
    elif "styles" in out:
        del out["styles"]
    return out


def _migrate_block(header: dict) -> dict:
    out = dict(header)
    if "_id" not in out and "block_id" in out:
        out["_id"] = out.pop("block_id")
    if "section_type" not in out and "block_type" in out:
        out["section_type"] = out.pop("block_type")
    out.pop("enrichments", None)
    out.pop("enrichment", None)
    out.pop("block_id", None)
    out.pop("block_type", None)
    return out


def _clean_preamble(preamble: str) -> str:
    lines = preamble.replace("\r\n", "\n").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and lines[0].strip() == "---":
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and lines[-1].strip() == "---":
        lines.pop()
    return "\n".join(lines).strip()


def migrate_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    doc_header, _doc_raw, preamble, raw_blocks = _split_document(text)
    parts: list[str] = []

    if doc_header is not None:
        doc_header = _migrate_doc(doc_header)
        parts.append("@document\n")
        parts.append(json.dumps(doc_header, indent=4))
        parts.append("\n---\n")
        pre = _clean_preamble(preamble)
        if pre:
            parts.append(pre)
            parts.append("\n\n")

    for meta, _raw, body in raw_blocks:
        meta = _migrate_block(meta)
        parts.append("@block\n")
        parts.append(json.dumps(meta, indent=4))
        parts.append("\n---\n")
        parts.append(body.rstrip("\n"))
        parts.append("\n")

    return "".join(parts)


def main() -> None:
    for path in sorted((ROOT / "examples").glob("*.smd")):
        original = path.read_text(encoding="utf-8")
        migrated = migrate_text(original)
        path.write_text(migrated, encoding="utf-8", newline="\n")
        print("migrated", path.name)


if __name__ == "__main__":
    main()
