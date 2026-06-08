#!/usr/bin/env python3
"""
Annotate SMD transcript enrichments with character positions using rapidfuzz.

For each highlight text, fuzzy-finds its position in the block's body_text,
then stores start_char / end_char in the highlight JSON so the viewer can
render inline highlights.

Usage:
    python3 annotate_enrichments.py examples/transcript.smd [output.smd]
"""

import json
import re
import sys
from pathlib import Path

from rapidfuzz import fuzz


def find_best_span(body: str, query: str, margin: float = 0.3) -> dict:
    """
    Sliding-window fuzzy search for `query` in `body`.

    Returns dict with start_char, end_char, score (0-100).
    Returns start_char=0, end_char=0, score=0 if no good match found.
    """
    qlen = len(query)
    blen = len(body)

    if qlen == 0 or blen == 0:
        return {"start_char": 0, "end_char": 0, "score": 0}

    # Window size range: ±margin around query length
    min_win = max(5, int(qlen * (1 - margin)))
    max_win = min(blen, int(qlen * (1 + margin)))

    best_score = 0
    best_start = 0
    best_end = 0

    for win_size in range(min_win, max_win + 1, max(1, (max_win - min_win) // 10)):
        for start in range(0, blen - win_size + 1, max(1, win_size // 4)):
            window = body[start : start + win_size]
            score = fuzz.ratio(query, window)
            if score > best_score:
                best_score = score
                best_start = start
                best_end = start + win_size

    return {
        "start_char": best_start,
        "end_char": best_end,
        "score": best_score / 100.0,
    }


def annotate_smd(text: str, threshold: float = 0.55) -> str:
    """
    Parse SMD text, find highlight positions in body text, add start_char/end_char.
    Returns annotated SMD text.
    """
    # Match @block header+body: everything from @block\n through \n---\n then body until next @block or @document
    block_re = re.compile(
        r'(@block\n.*?\n---\n)(.*?)(?=\n@block|\n@document|\Z)',
        re.DOTALL
    )

    def process_block(match):
        header_block = match.group(1)   # "@block\n{...}\n---\n"
        body_text = match.group(2)      # body until next @block or EOF

        # Parse the header JSON - it's between the first \n and \n---\n
        hdr_start = header_block.index('\n') + 1
        hdr_end = header_block.index('\n---\n')
        hdr_json = header_block[hdr_start:hdr_end]

        try:
            header = json.loads(hdr_json)
        except json.JSONDecodeError:
            return header_block + body_text

        if "enrichments" not in header:
            return header_block + body_text

        modified = False
        for enrichment in header.get("enrichments", []):
            if not isinstance(enrichment, dict):
                continue
            highlights = enrichment.get("highlights", [])
            for hl in highlights:
                if not isinstance(hl, dict):
                    continue
                text_query = hl.get("text", "")
                if not text_query or "start_char" in hl:
                    continue

                span = find_best_span(body_text, text_query)
                if span["score"] >= threshold:
                    hl["start_char"] = span["start_char"]
                    hl["end_char"] = span["end_char"]
                    hl["match_score"] = round(span["score"], 3)
                    modified = True

        if modified:
            new_header = json.dumps(header, indent=4, ensure_ascii=False)
            return "@block\n" + new_header + "\n---\n" + body_text

        return header_block + body_text

    return block_re.sub(process_block, text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 annotate_enrichments.py <input.smd> [output.smd]", file=sys.stderr)
        sys.exit(1)

    inpath = Path(sys.argv[1])
    outpath = Path(sys.argv[2]) if len(sys.argv) > 2 else inpath

    text = inpath.read_text()
    annotated = annotate_smd(text)

    outpath.write_text(annotated)
    print(f"Annotated → {outpath}")

    # Report
    block_re = re.compile(r'@block\n(.*?)\n---\n', re.DOTALL)
    annotated_blocks = 0
    for m in block_re.finditer(annotated):
        try:
            hdr = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if hdr.get("enrichments"):
            annotated_blocks += 1
            for e in hdr["enrichments"]:
                for hl in e.get("highlights", []):
                    sc = hl.get("start_char", "MISSING")
                    ec = hl.get("end_char", "MISSING")
                    score = hl.get("match_score", "?")
                    print(f"  block {hdr['block_id']}: score={score} pos={sc}-{ec}  \"{hl['text'][:50]}...\"")
    print(f"Annotated {annotated_blocks} blocks")


if __name__ == "__main__":
    main()
