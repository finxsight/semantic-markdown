# Semantic Markdown (SMD)

**Block-addressable markdown for humans, agents, and apps.**

Extension: `.smd` · Spec: [SPECIFICATION.md](SPECIFICATION.md) · License: Apache-2.0

SMD is plain markdown split into **blocks**. Each block has a small JSON header (`@block`) for identity and indexing; the body stays readable prose, tables, and fenced segments. File-level context lives in `@document`. No sidecar metadata file and no post-hoc ETL.

Production use: [FIRE](https://github.com/finxsight/fire-app) (research workspace, publishing, Shared Research).

## Minimal example

```smd
@document
{
  "document_type": "background_research",
  "date": "2026-07-09"
}
---
Margin mix shift — working title

@block
{
  "_id": "8b1e2f4a-0c3d-4e5f-9a0b-1c2d3e4f5a6b",
  "section_type": "summary"
}
---

Revenue growth accelerated on **pricing** and mix. See #margins in the body.

@block
{
  "_id": "2",
  "section_type": "observation"
}
---

Management guided to steady growth next quarter.
```

- **Document title** — plain text between `@document` JSON and the first `@block` (not a block).
- **Block id** — `_id` (UUID or numeric string).
- **Section kind** — `section_type` (lowercase_with_underscores).
- **Topics** — `#hashtags` in markdown; optional `tags` in JSON.
- **Inline analyst marks** — `=== {"comment":"…","sentiment_score":0.4} highlighted phrase ===`

## Repository layout

| Path | Role |
|------|------|
| `SPECIFICATION.md` | Format rules (v0.2, aligned with FIRE) |
| `src/semantic_markdown/parser.py` | Reference parser |
| `src/semantic_markdown/indexer.py` | SQLite + FTS5 block index |
| `src/semantic_markdown/harness.py` | Agent + MCP tools (experimental) |
| `index.html` | Browser viewer for `examples/` |
| `examples/` | Sample `.smd` files |

## Quick start

```bash
python -m pip install -e .
python -m pytest tests/ -q
python -m http.server 8080   # open http://localhost:8080
```

```bash
python -m semantic_markdown examples/AAPL_profile_with_chart.smd
smd-mcp   # MCP server (requires mcp extra)
```

**Online viewer:** [finxsight.github.io/semantic-markdown](https://finxsight.github.io/semantic-markdown) (GitHub Pages from `master`).

## Design principles

1. **Write-time structure** — meaning is carried in headers and inline marks, not inferred later.
2. **Block is the unit** — address, filter, index, and patch one block without rewriting the file.
3. **Schema-free JSON** — reserved keys are conventions; apps may add fields.
4. **Human-first body** — agents and viewers consume the same file.

## Citation

```bibtex
@software{semantic_markdown,
  author = {Sandeep Muthangi},
  title = {Semantic Markdown: Block-Addressable Documents for Human--Agent Workflows},
  year = {2026},
  url = {https://github.com/finxsight/semantic-markdown}
}
```
