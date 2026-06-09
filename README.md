# Semantic Markdown (SMD)

<div align="center">

[![Spec v0.2](https://img.shields.io/badge/spec-v0.2-3a6ea5?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![Status: Draft](https://img.shields.io/badge/status-draft-ff6b35?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e)](.)
[![License](https://img.shields.io/badge/license-Apache_2.0-d22128?style=for-the-badge&labelColor=1a1a2e)](LICENSE)

</div>

<br>

<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           S E M A N T I C   M A R K D O W N                  ║
║                                                              ║
║            "The Document IS the Database"                    ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  @document { type:"earnings_transcript",                     ║
║              ticker:"A", schema:"0.2" }                      ║
║  ───                                                         ║
║    ┌ @block { id:2, type:"business_update" } ─┐              ║
║    │  **CEO:** Revenue grew 4.4% core,        │              ║
║    │  margins expanded, EPS of $1.36.         │              ║
║    └──────────────────────────────────────────┘              ║
║                                                              ║
║    ┌ @block { id:7, type:"qa",               ─┐              ║
║    │   enrichments: [{                         │              ║
║    │     topic: "Margins & leverage",          │              ║
║    │     highlights: [{                        │              ║
║    │       text:   "50bp improvement...",      │              ║
║    │       sentiment: 0.6                      │              ║
║    │     }]                                    │              ║
║    │   }]                                      │              ║
║    │  ───                                      │              ║
║    │  **Q:** What drove margins in Q1?         │              ║
║    │  **A:** We expect 50bp improvement,       │              ║
║    │  driven by pricing, volume & Ignite.      │              ║
║    └──────────────────────────────────────────┘              ║
║                                                              ║
║    ┌ @block { id:42, type:"research_note" } ───┐             ║
║    │  ## Key Findings                           │             ║
║    │                                            │             ║
║    │  Our analysis shows Infra spending          │             ║
║    │  accelerating across all three clouds.     │             ║
║    │                                            │             ║
║    │  ```html                                   │             ║
║    │  <table>                                   │             ║
║    │    <tr><th>AWS</th><td>+18%</td></tr>      │             ║
║    │    <tr><th>Azure</th><td>+21%</td></tr>    │             ║
║    │    <tr><th>GCP</th><td>+26%</td></tr>      │             ║
║    │  </table>                                  │             ║
║    │  ```                                       │             ║
║    │                                            │             ║
║    │  ```thought                                │             ║
║    │  Strength broad-based, not just AI.        │             ║
║    │  Watch capex-to-revenue ratio next qtr.    │             ║
║    │  ```                                       │             ║
║    └────────────────────────────────────────────┘             ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║    ONE FILE  ────▶  THREE CONSUMERS                          ║
║                                                              ║
║    ┌──────────┐   ┌──────────────┐   ┌──────────────────┐   ║
║    │  HUMANS  │   │   AGENTS     │   │    VIEWERS       │   ║
║    │          │   │   (LLMs)     │   │                  │   ║
║    │  Clean   │   │              │   │  Sentiment       │   ║
║    │  Markdown│   │  Typed JSON  │   │  colors          │   ║
║    │  body    │   │  headers     │   │                  │   ║
║    │          │   │              │   │  Block-type      │   ║
║    │  Familiar│   │  Tool-call   │   │  filters         │   ║
║    │  UX      │   │  API         │   │                  │   ║
║    │          │   │              │   │  Tag             │   ║
║    │          │   │              │   │  navigation      │   ║
║    └──────────┘   └──────────────┘   └──────────────────┘   ║
║                                                              ║
║   Write once. Structure everywhere. No ETL required.         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

</div>

<br>

---

## Overview

Semantic Markdown (SMD) is a document format where writing, structure, and data are unified into a single native representation.

Instead of extracting meaning from text, SMD encodes meaning directly inside the document. Every block carries its own JSON header — tags, sentiment, enrichment, metadata — while the body remains clean, readable Markdown.

One document. Three consumers:

- **Humans** — clean Markdown body
- **Agents** — parseable JSON headers with block-level enrichment
- **Viewers** — renderable semantic overlays (sentiment coloring, tag filters, highlights)

---

## The Problem

A single piece of content today passes through many systems:

- Humans write text
- Systems chunk it
- Databases store it as blobs
- AI systems reconstruct meaning from context windows
- Applications rebuild structure for display

This creates fragmentation: loss of structure, duplicated processing, ambiguous meaning, brittle pipelines.

> A document is not stored. It is *reconstructed differently* by every system that touches it.

---

## The Shift

SMD removes translation layers. Structure is written at creation time.

Instead of:

> write → parse → chunk → embed → store → reconstruct

SMD enables:

> write → structure → use

---

## Core Principle

> Everything in SMD is explicit, ordered, and addressable.

There is no hidden structure outside the document itself.

---

## Format

SMD has two primitives: `@document` and `@block`.

### `@document`
The top-level container with a JSON header and optional Markdown body.

```
@document
{
  "document_id": "aapl-q3-2026",
  "schema_version": "0.2",
  "type": "transcript",
  "created": "2026-01-01T00:00:00Z"
}
---
```

### `@block`
The fundamental addressable unit. Every block has a JSON header and a Markdown body, separated by `---`.

```
@block
{
  "block_id": "qa-0042",
  "type": "qa",
  "tags": ["guidance", "margins"],
  "sentiment": [
    {
      "excerpt": "We expect steady growth.",
      "score": 0.74,
      "label": "positive",
      "confidence": 0.88
    }
  ],
  "enrichment": {
    "highlights": ["Revenue guidance above consensus"],
    "entities": ["AAPL"],
    "summary": "CEO provides positive outlook on Q4."
  }
}
---
**Analyst:** Can you discuss guidance?

**CEO:** We expect steady growth next quarter.
```

### Body Segments
Block bodies are parsed into **typed segments**. Markdown text between fenced blocks is `type: "markdown"`. Triple-backtick fenced blocks with a type label become typed segments:

````
@block { "block_id": "note-001" }
---
Some markdown here.

```thought
This is my internal thinking about this topic.
```

```action_item
Review benchmarks. Assigned to: Bob
Due: 2026-07-01
```
````

Parses to: `[{type: "markdown", …}, {type: "thought", …}, {type: "markdown", …}, {type: "action_item", …}]`

---

## Full Example

```
@document
{
  "document_id": "aapl-q3-2026",
  "schema_version": "0.2",
  "type": "transcript",
  "created": "2026-01-01T00:00:00Z",
  "meta": {
    "ticker": "AAPL",
    "fiscal_quarter": "Q3"
  }
}
---

@block
{
  "block_id": "qa-0042",
  "type": "qa",
  "position": 1,
  "tags": ["guidance", "margins"],
  "sentiment": [
    {
      "excerpt": "We expect steady growth.",
      "score": 0.74,
      "label": "positive",
      "confidence": 0.88
    }
  ],
  "enrichment": {
    "highlights": ["Revenue guidance above consensus"],
    "entities": ["AAPL", "Services"],
    "summary": "Guidance beat consensus by ~2%."
  }
}
---
**Analyst:** Can you discuss guidance?

**CEO:** We expect steady growth next quarter.

**Analyst:** What about margins?

**CFO:** We are focused on operational efficiency.
```

---

## Design Rules

- A document is a container of blocks
- Every entity has a JSON header
- Header and body are separated by `---`
- Block bodies contain ordered typed segments (markdown + fenced blocks)
- Metadata is always structured JSON
- No implicit structure exists outside the format

---

## What This Enables

- **Queryable documents** without preprocessing — filter by tags, type, sentiment
- **Addressable retrieval** — fetch specific blocks by `block_id` instead of chunking
- **Agent-native enrichment** — LLMs can read, annotate, and save documents
- **Semantic overlays** — viewers render sentiment colors, tag badges, highlight callouts
- **Cross-document views** — aggregate blocks by tag across multiple `.smd` files
- **Bottom-up clustering** — discover emergent topics from tag co-occurrence

---

## Project Components

### Python Library

```bash
pip install semantic-markdown
```

| Component | Description |
|---|---|
| `parser.py` | Core SMD text → document parser. O(n), single pass. |
| `indexer.py` | `SMDIndexer` — chunking, sentiment-keyed storage, Q&A thread extraction, tag inverted index, topic clustering |
| `harness.py` | `SMD Agent Harness` — SMDAgent + MCP server; controlled LLM-document interface |

### CLI

```
smd <file.smd>     — parse and display SMD document structure
smd-mcp            — start the MCP server for LLM integration
```

### Viewer

`index.html` — a standalone browser viewer with embedded JS SMD parser. Features:

- Template picker sidebar (transcript, notebook, corpus)
- Tag-based filtering (clickable tag chips)
- Sentiment-colored block cards (red → yellow → green)
- Highlight annotations with sentiment bars
- Key takeaways, summaries, fenced segment rendering
- Paste-any-SMD text area for quick testing

```bash
python -m http.server 8080
# Open http://localhost:8080
```

### MCP Server (Agent Harness)

`harness.py` — the **SMD Agent Harness**: combines SMDAgent + MCP server into a single, auditable interface. The harness is the controlled boundary between an LLM and SMD documents — every read, write, and enrichment goes through typed tool calls. The LLM never touches the filesystem directly.

```bash
smd-mcp
```

12 tools: `read`, `search`, `add_enrichment`, `del_enrichment`, `edit_enrichment`, `write_sentiment`, `write_tags`, `filter_blocks`, `read_next_qa`, `read_next_block`, `read_document`, `save`

---

## Agent Workflow

```
1. Agent loads .smd file via the harness
2. Agent identifies topics, sentiment, entities
3. Agent calls write_sentiment(), add_enrichment(), write_tags()
4. Agent calls save() to write back enriched .smd
5. Viewer renders with color-coded sentiment and highlights
```

---

## Use Cases

- **Earnings transcripts** — Q&A blocks with sentiment, speaker attribution, topic tags
- **Research notebooks** — dated entries with thought/action_item fenced blocks
- **RAG corpora** — pre-enriched semantic chunks with summaries and entities
- **Multi-author collaboration** — blocks attributed by author with status tracking
- **Financial dashboards** — block-level embeds (charts, widgets) alongside structured data

---

## Why Existing Systems Don't Fully Solve This

| System | What it gets right | What it lacks |
|---|---|---|
| Markdown | Human-readable simplicity | No native structure |
| JSON / ASTs | Fully structured data | Not human-writable as primary format |
| YAML+MD (Frontmatter) | File-level metadata | No block-level addressing |
| Notion | Block-based authoring | Not portable outside its ecosystem |
| ProseMirror | Structured document tree | No semantic node/data standard |
| MDX | Markdown + components | Requires JSX toolchain |

SMD sits at the intersection: structured like ProseMirror, authored like Markdown, composable like JSON, modular like Notion blocks, portable like a plain text file.

But unlike each individually:

> The document is the database.

---

## Status

v0.2 — Draft specification with reference Python implementation and browser viewer.

- 📄 [Full Specification](SPECIFICATION.md)
- 🐍 [Parser](src/semantic_markdown/parser.py)
- 🔍 [Indexer](src/semantic_markdown/indexer.py)
- 🤖 [Agent Harness](src/semantic_markdown/harness.py)
- 🖥️ [Viewer](index.html)
- 📚 [Examples](examples/)

### Try the Viewer

**Online**: Enable GitHub Pages in [repo settings](https://github.com/finxsight/semantic-markdown/settings/pages) → deploy from `master` branch, `/ (root)` → visit `finxsight.github.io/semantic-markdown`

**Local**: `python -m http.server 8080` → open `http://localhost:8080`

The viewer loads `.smd` files from `examples/` and renders them with sentiment coloring, block-type filters, tag navigation, and topic highlighting.

---

## Citation

```bibtex
@software{semantic_markdown,
  title = {Semantic Markdown: A Block-Addressable Document Format
           for Human-Agent Collaboration},
  year = {2026},
  url = {https://github.com/finxsight/semantic-markdown}
}
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for full text.
