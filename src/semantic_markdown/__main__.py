"""
CLI entry point for Semantic Markdown.

Usage:
    python -m semantic_markdown <file.smd> [--json]

Examples:
    python -m semantic_markdown transcript.smd
    python -m semantic_markdown transcript.smd --json
"""

import json
import sys
from pathlib import Path

from .parser import parse_file, parse_smd, all_tags, tag_co_occurrence
from .parser import ParseError


def _serialize(doc):
    """Serialize a parsed document to a JSON-compatible dict."""
    items = []
    for entity in doc.entities:
        if hasattr(entity, "block_id"):  # SMDBlock
            items.append({
                "type": "block",
                "block_id": entity.block_id,
                "header": entity.header,
                "tags": entity.tags,
                "segments": [
                    {"type": s.type, "content": s.content}
                    for s in entity.segments
                ],
            })
        else:  # SMDDocument
            items.append({
                "type": "document",
                "header": entity.header,
                "blocks": _serialize(entity),
            })
    return items


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m semantic_markdown <file.smd> [--json]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    as_json = "--json" in sys.argv

    if not path.exists():
        # Try reading from stdin
        text = sys.stdin.read()
        doc = parse_smd(text)
    else:
        doc = parse_file(path)

    if as_json:
        data = _serialize(doc)
        print(json.dumps(data, indent=2))
    else:
        print(f"Document: {path.name if path.exists() else '<stdin>'}")
        print(f"  Entities: {len(doc.entities)}")
        print(f"  Blocks:   {len(doc.blocks)}")
        print(f"  Tags:     {all_tags(doc)}")
        print()

        for block in doc.blocks:
            tags = " ".join(f"#{t}" for t in block.tags[:5])
            more = " …" if len(block.tags) > 5 else ""
            sentiment = f" [{block.sentiment}]" if block.sentiment is not None else ""

            body_preview = block.body_text[:80].replace("\n", " ").strip()
            if len(block.body_text) > 80:
                body_preview += "…"

            print(f"  [{block.block_id}]{sentiment}  {tags}{more}")
            print(f"    {body_preview}")
            print()

        print(f"Tag co-occurrence matrix ({len(tag_co_occurrence(doc))} tags):")
        matrix = tag_co_occurrence(doc)
        for tag, neighbors in sorted(matrix.items()):
            top = sorted(neighbors.items(), key=lambda x: -x[1])[:3]
            if top:
                pairs = "  ".join(f"{t}({c})" for t, c in top)
                print(f"  {tag}: {pairs}")


if __name__ == "__main__":
    main()
