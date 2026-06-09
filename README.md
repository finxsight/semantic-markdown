# Semantic Markdown (SMD)

<div align="center">

[![Spec v0.1](https://img.shields.io/badge/spec-v0.1-3a6ea5?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![Status: Active Research](https://img.shields.io/badge/status-active_research-4caf50?style=for-the-badge&labelColor=1a1a2e)](SPECIFICATION.md)
[![arXiv](https://img.shields.io/badge/arXiv-coming_soon-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white&labelColor=1a1a2e)](.)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e)](.)
[![License](https://img.shields.io/badge/license-Apache_2.0-d22128?style=for-the-badge&labelColor=1a1a2e)](LICENSE)

</div>

<br>

<div align="center">

## The LLM Wiki Primitive

### SMD is not a document format.

### It is a persistent, addressable memory system for co-authored knowledge.

### In SMD, there are no pages.

### Only persistent, addressable memory blocks.

<br>

**Written once. Structured at write-time. Evolved continuously by agents.**

<br>

**A wiki where pages do not exist — only evolving memory.**

</div>

<br>

<div align="center">

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     S E M A N T I C   M A R K D O W N                      ║
║                                                                            ║
║                  "The Document IS the Memory Substrate"                    ║
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
║    One file. Persistent memory for humans, agents, and applications.       ║
║                                                                            ║
║         Write-time structure. No ETL. No sidecar metadata.                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

</div>

<br>

---

## Overview

SMD is the primitive layer of LLM-native knowledge systems.

LLM systems today simulate memory using external infrastructure — vector databases, context windows, retrieval pipelines. SMD removes the simulation. Memory becomes the document itself.

Meaning is not inferred after the fact — it is embedded at write time. Every block carries its own structured metadata — tags, sentiment, entities, enrichments, summaries, or arbitrary JSON — while the body stays human-readable markdown.

One artifact. Three surfaces:

- **Humans** — clean Markdown body
- **Agents** — parseable JSON headers with block-level enrichment
- **Viewers** — renderable semantic overlays (sentiment coloring, tag filters, highlights)

> SMD makes the document the smallest unit of intelligence infrastructure.

---

## Core Idea

> SMD is what a wiki becomes when memory is the primitive.

---

## System Definition

- A **document** is a container of memory
- A **block** is an addressable wiki node
- A **collection of documents** is a single evolving knowledge graph

---

## The Inversion

Traditional systems:

> Pages → Links → Wiki

SMD:

> Memory blocks → Documents → Emergent wiki graph

---

## The Thesis

> LLM systems do not need better retrieval.
> They need a native memory substrate.
>
> SMD is that substrate.

---

## SMD is Simultaneously Three Things

SMD operates as a single format interpreted through three layers:

### 1. Human Layer
> A readable, familiar Markdown document.

Authors write in plain Markdown. The JSON headers are lightweight and stay out of the way. No toolchain required.

### 2. Machine Layer
> A block-addressable structured graph.

Every block has a typed JSON header. Blocks are queried, filtered, and indexed by type, tags, sentiment, entities — without parsing the body.

### 3. Memory Layer
> Every block is a persistent memory unit that can be updated without rewriting the document.

Documents accumulate structured experience. Blocks become stable memory units that can be independently referenced. Metadata becomes traceable context attached to memory, not separate from it. Retrieval becomes context reconstruction, not search. Agents operate on shared persistent memory state via the document.

No decay models. No lifecycle states. No extra mechanics — just an interpretation shift.

---

## What Breaks Today

LLM systems simulate memory through fragmented infrastructure:

- Content lives in Markdown
- Metadata lives in YAML
- Annotations live in a database
- Embeddings live in a vector store
- Application state lives somewhere else

Each layer is a simulation. Together they reconstruct what was lost at write time.

SMD collapses all of it into one artifact: a document that IS its own memory.

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

The fundamental abstraction is not the document — it is the **addressable knowledge node graph emerging from blocks across documents**.

There is no hidden structure outside the document itself.

---

## SMD as a Memory Medium

SMD turns documents into persistent memory objects that accumulate structure over time.

- **Documents accumulate structured experience** — each enrichment pass adds memory without altering original content
- **Blocks become stable memory units** — independently addressable, retrievable by `block_id` without chunking heuristics
- **Metadata becomes traceable context** — tags, sentiment, entities, and summaries are attached to memory, not stored in a separate system
- **Retrieval becomes context reconstruction** — fetch specific blocks by type, tag, or sentiment instead of keyword search
- **Agents operate on shared persistent memory** — multiple agents can read, annotate, and evolve the same document over time
- **Cross-document memory views** — aggregate blocks by tag across multiple `.smd` files
- **Bottom-up knowledge emergence** — discover topics from tag co-occurrence across a corpus

### SMD is a Wiki Compiled from Memory, Not Pages

SMD documents are entry points into a shared, evolving knowledge graph.

- **A block is a wiki node** — independently addressable, typed, and enriched
- **A document is a local projection of the wiki** — one view into the graph
- **The wiki exists above documents, not inside them** — memory lives across files
- **Agents continuously expand and reorganize this graph** through enrichment

---

## Memory Representation: SMD vs Traditional Systems

> Unlike traditional systems where memory is reconstructed from logs or stored as compressed residues, SMD stores memory in its native form.

| System | Memory Representation |
|---|---|
| Logs / Databases | Memory reconstructed after the fact from event streams |
| Vector DBs | Memory stored as compressed semantic residues |
| **SMD** | **Memory stored natively as structured, addressable objects** |

This is the key distinction: SMD does not require reconstruction. The document *is* the memory, in the form it was written.

---

## SMD = LLM Wiki Primitive

SMD is the minimal system required for a wiki that agents can co-author.

Traditional wikis are human-written knowledge graphs.
SMD wikis are continuously computed memory graphs.

Traditional wikis assume:
- humans write pages
- links connect pages
- structure is manually curated

SMD inverts this:

- **blocks are generated and enriched continuously** — by humans and agents
- **structure emerges from metadata + embeddings + agent interaction** — not manual linking
- **links are implicit** in shared tags, entities, and semantic overlap
- **agents are first-class participants** in knowledge construction

In SMD, the wiki is not authored.

It is **computed and continuously evolved over a shared memory substrate**.

In SMD, there are no pages. There is only evolving state.

> **SMD is to wikis what ASTs are to code editors.**
>
> **SMD is a writable knowledge graph disguised as markdown.**

---

## Example: Querying SMD

Find all high-confidence margin-related insights:

```
filter:
  type = "investment_thesis"
  tags contains "margins"
  sentiment > 0.7
```

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

Typed segments provide multiple structured interpretations of a single block body without losing human readability.

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
- No required structural model exists outside the format
- Blocks are independently addressable — they can be read, enriched, and rewritten without affecting other blocks
- The block is the atomic unit of meaning, storage, retrieval, and enrichment

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

## Memory Interaction Model

Agents do not process documents. They interact with persistent memory objects.

```
1. OBSERVE  — Agent reads memory state via the harness
2. ENRICH   — Agent attaches new memory: sentiment, tags, entities, summaries
```

Over time, SMD documents converge into a **living wiki graph co-authored by humans and agents**.

The harness is the controlled boundary — every memory operation goes through typed tool calls. The LLM never touches the filesystem directly. Every enrichment is auditable and traceable.

---

## Use Cases

- **Agent knowledge bases** — wikis that agents read, write, and evolve over time
- **Earnings transcripts** — Q&A blocks with sentiment, speaker attribution, topic tags
- **Research notebooks** — dated entries with thought/action_item fenced blocks; incremental knowledge accumulation
- **RAG corpora** — pre-enriched semantic memory units with summaries and entities
- **Multi-agent collaboration** — blocks attributed by agent/author with auditable enrichment history
- **Financial dashboards** — block-level embeds (charts, widgets) alongside structured memory state
- **Personal knowledge graphs** — documents that grow into interconnected memory networks

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
| SQLite | Structured storage | Not human-authorable |
| Git | Versioned plain text | No semantic structure |

SMD sits at the intersection: structured like ProseMirror, authored like Markdown, composable like JSON, modular like Notion blocks, portable like a plain text file.

But unlike each individually:

> The document is the memory.

---

## Why Not Frontmatter?

Frontmatter describes files. SMD describes blocks.

Frontmatter provides file-level metadata. SMD provides addressable semantic objects inside a document.

In SMD, every block carries its own metadata, enrichments, tags, summaries, sentiment, entities, and application-specific state.

The unit of structure is not the file. It is the block.

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
  author = {Sandeep Muthangi},
  title = {Semantic Markdown: A Block-Addressable Memory Substrate
           for Human-Agent Knowledge Systems},
  year = {2026},
  url = {https://github.com/finxsight/semantic-markdown}
}
```

---

---

*Sandeep Muthangi*  
*Semantic Markdown (SMD), 2026*

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for full text.

---

A document is not text.

It is the smallest unit of intelligence infrastructure.

The document is the memory substrate.
