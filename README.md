# Semantic Markdown (SMD)

<div align="center">

[![Spec v0.0](https://img.shields.io/badge/spec-v0.0-3a6ea5?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![Status: Active Research](https://img.shields.io/badge/status-active_research-4caf50?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![arXiv](https://img.shields.io/badge/arXiv-coming_soon-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white&labelColor=1a1a2e)](.)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e)](.)
[![License](https://img.shields.io/badge/license-Apache_2.0-d22128?style=for-the-badge&labelColor=1a1a2e)](LICENSE)

</div>

<br>

<div align="center">

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     S E M A N T I C   M A R K D O W N                      ║
║                                                                            ║
║                       "The Document IS the Database"                       ║
║                                                                            ║
║                                                                            ║
║                                                                            ║
║                            W R I T E   O N C E                             ║
║                    C O N S U M E   E V E R Y W H E R E                     ║
║                                                                            ║
║              H U M A N S   •   A G E N T S   •   A P P S                   ║
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║      ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐               ║
║      │   HUMANS    │   │   AGENTS    │   │      APPS       │               ║
║      │             │   │             │   │                 │               ║
║      │ Readable    │   │ Query by    │   │ Filter by       │               ║
║      │ Markdown    │   │ tags, type, │   │ tags, topics,   │               ║
║      │             │   │ segment     │   │ sentiment       │               ║
║      │ Familiar    │   │ Structured  │   │ Rich views &    │               ║
║      │ Authoring   │   │ Metadata    │   │ navigation      │               ║
║      └─────────────┘   └─────────────┘   └─────────────────┘               ║
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  @document                                                                 ║
║  {                                                                         ║
║    type: "research_note",                                                  ║
║    ticker: "A",                                                            ║
║    sectors: ["Life Sciences", "Diagnostics"]                               ║
║  }                                                                         ║
║                                                                            ║
║  ---                                                                       ║
║                                                                            ║
║  @block                                                                    ║
║  {                                                                         ║
║    id: 1,                                                                  ║
║    type: "investment_thesis",                                              ║
║    topic: "Margin Expansion",                                              ║
║    tags: ["pricing", "margins"],                                           ║
║    sentiment: 0.72                                                         ║
║  }                                                                         ║
║                                                                            ║
║  Agilent continues to benefit from pricing power and                       ║
║  operating leverage. Management highlighted a 50bp margin                  ║
║  improvement driven by pricing actions and manufacturing                   ║
║  efficiencies.                                                             ║
║                                                                            ║
║  ---                                                                       ║
║                                                                            ║
║  @block                                                                    ║
║  {                                                                         ║
║    id: 2,                                                                  ║
║    type: "segment_analysis",                                               ║
║    segment: "Life Sciences & Diagnostics",                                 ║
║    tags: ["pharma", "growth"],                                             ║
║    highlights: ["Biologics demand remains strong"]                         ║
║  }                                                                         ║
║                                                                            ║
║  Revenue contribution by end market:                                       ║
║                                                                            ║
║  ```html                                                                   ║
║  <table>                                                                   ║
║    <tr><th>End Market</th><th>Growth</th></tr>                             ║
║    <tr><td>Pharma</td><td>+9%</td></tr>                                    ║
║    <tr><td>Diagnostics</td><td>+6%</td></tr>                               ║
║  </table>                                                                  ║
║  ```                                                                       ║
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║      One file. Human-readable. Machine-queryable. App-native.              ║
║                                                                            ║
║                   No ETL. No sidecar metadata.                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

</div>

<br>

---

## Overview

Semantic Markdown (SMD) is a document format where content and structure live in the same file.

Instead of inferring meaning after a document is written, SMD stores meaning directly alongside the content itself.

Every block carries its own structured metadata — tags, sentiment, entities, enrichments, summaries, or arbitrary JSON — while the body remains clean, readable Markdown.

One document. Three consumers:

- **Humans** — clean Markdown body
- **Agents** — parseable JSON headers with block-level enrichment
- **Viewers** — renderable semantic overlays (sentiment coloring, tag filters, highlights)

---

## Why Semantic Markdown?

Today, content, metadata, annotations, and AI enrichments are typically stored in different systems.

A document lives in Markdown.
Metadata lives in YAML.
Annotations live in a database.
Embeddings live in a vector store.
Application state lives somewhere else.

SMD collapses those layers into a single artifact.

The document becomes both the content and the structured representation of that content.

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

## Traditional Documents vs Semantic Documents

SMD removes translation layers. Structure is written at creation time.

Traditional:

> write → parse → chunk → infer → reconstruct

Semantic Markdown:

> write → structure → consume

---

## Core Principle

> Everything in SMD is explicit, ordered, and addressable.

There is no hidden structure outside the document itself.

---

## What This Enables

- **Queryable documents** without preprocessing — filter by tags, type, sentiment
- **Addressable retrieval** — fetch specific blocks by `block_id` instead of chunking
- **Agent-native enrichment** — LLMs can read, annotate, and save documents
- **Semantic overlays** — viewers render sentiment colors, tag badges, highlight callouts
- **Cross-document views** — aggregate blocks by tag across multiple `.smd` files
- **Bottom-up clustering** — discover emergent topics from tag co-occurrence

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
  "sentiment": 0.74,
  "entities":["AAPL"],
  "summary": "Positive guidance for Q4."
    
}
---
**Analyst:** Can you discuss guidance?

**CEO:** We expect steady growth next quarter.
```

### Typed Segments
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
  "tags": ["guidance"],
  "sentiment": 0.74,
  "entities": ["AAPL"],
  "summary": "Positive guidance."
}
---
**Analyst:** Can you discuss guidance?

**CEO:** We expect steady growth next quarter.
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
| Obsidian | Portable Markdown ecosystem | No semantic block schema |
| Jupyter Notebooks | Rich mixed-content documents | Not designed for semantic retrieval |

SMD sits at the intersection: structured like ProseMirror, authored like Markdown, composable like JSON, modular like Notion blocks, portable like a plain text file.

But unlike each individually:

> The document is the database.

---

## Why Not Frontmatter?

Frontmatter describes files.

SMD describes blocks.

Frontmatter provides file-level metadata.

SMD provides addressable semantic objects inside a document.

In SMD, every block can carry its own metadata, enrichments, tags, summaries, sentiment, entities, and application-specific state.

The unit of structure is not the file.

It is the block.

---

## Status

Experimental — active research project with a reference parser, viewer, and agent tooling.

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

---

SMD treats documents as first-class semantic objects.

Not text that must be interpreted later.

Not blobs that require reconstruction.

The document is the database.
