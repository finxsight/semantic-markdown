# Semantic Markdown (SMD)

### A structured document format for a world shared by humans and machines

---

## Overview

A document should not be parsed into structure.

It should *be structured*.

Semantic Markdown (SMD) is a document format where writing, structure, and data are unified into a single native representation.

Instead of extracting meaning from text, SMD encodes meaning directly inside the document itself.

A document becomes one object across all systems:

- human-readable
- machine-structured
- database-indexable
- AI-native

---

## The Problem

Today, documents are not single systems.

They are translation pipelines.

A single piece of content is repeatedly transformed:

- Humans write text
- Systems chunk it
- Databases normalize or store it as blobs
- AI systems reconstruct meaning in context windows
- Applications rebuild structure for display

This creates fragmentation:

- loss of structure
- duplicated processing logic
- ambiguous meaning
- brittle pipelines
- inconsistent representations across systems

> A document is not stored. It is reconstructed differently by every system that touches it.

---

## The Representation Problem

Every system describes documents from a different perspective.

| System | Human Experience | Machine Interpretation | Database View | AI View |
|--------|------------------|------------------------|---------------|---------|
| Markdown | Clean readable text | Flat token stream | Unstructured blob | Chunked context windows |
| HTML | Rendered page | DOM tree | Stored markup string | Fragmented parsing |
| Notion | Block-based editor | Internal block graph | Proprietary JSON export | Partial structured chunks |
| ProseMirror | Rich editor canvas | Document tree (AST) | Serializable JSON AST | Node-level traversal |
| SQL / Databases | Tables and queries | Strict schema model | Normalized relations | Not document-native |
| Vector Databases | — | Embedding vectors | Dense representations | Similarity-only memory |

Each system optimizes one perspective.

None unify them.

---

## The Shift

SMD removes the need for translation layers.

A document is no longer converted into structure after creation.

Structure is written at creation time.

> Writing becomes modeling.  
> Documents become data.

Instead of:

> write → parse → chunk → embed → store → reconstruct

SMD enables:

> write → structure → use

---

## Core Principle

> Everything in SMD is explicit, ordered, and addressable.

There is no hidden structure outside the document itself.

---

## The Model

SMD is built from three primitives:

- documents
- blocks
- nodes


Document
├── metadata
└── blocks[]

Block
├── metadata
└── nodes[]

Node
├── type
├── value
└── metadata


That is the entire system.

---

## SMD Native Syntax

SMD uses Markdown-native semantic primitives instead of external serialization formats.

Structure is expressed directly inside the document.

---

## 1. Document

A document defines global identity and metadata.

```
@document {
  id: "et_0087",
  read_only: false,
  date: "2026-01-01",
  type: "earnings_transcript"
}
```

2. Block

A block is a semantic unit of meaning and a hard structural boundary.

Blocks use a decorator plus a mandatory fence delimiter.

```
@block {
  id: "qa-0042",
  tags: ["guidance", "revenue"]
}
---
```

Everything after --- belongs to this block until the next @block.

3. Nodes

Nodes are ordered, typed content units inside a block.

Nodes are expressed using fenced syntax except for markdown content

```
Analyst: Can you discuss guidance?
CEO: We expect steady growth next quarter.
```

---

## Node Rules

- Nodes are ordered
- Non markdown Node type is defined by fence language
- Nodes are atomic units of representation
- No hidden structure exists inside nodes

---

## Full Example

```
@document {
  id: "aapl-q3-2026",
  type: "transcript",
  date: "2026-01-01"
}

@block {
  id: "qa-0042",
  tags: ["guidance", "margins"]
}
---

Analyst: Can you discuss guidance?
CEO: We expect steady growth next quarter.

Analyst: What about margins?
CFO: We are focused on operational efficiency.
```

---

## Design Rules

- A document is a sequence of blocks
- A block is explicitly delimited
- Nodes are typed via fences
- Order is always meaningful
- Metadata is always structured
- No implicit structure exists outside the format

---

## What This Replaces

SMD replaces fragmented document pipelines:

- chunking strategies
- parsing layers
- embedding pipelines
- index construction logic
- rendering transformations

Instead, all systems operate on a single representation.

---

## What This Enables

When structure is native, documents become programmable.

SMD enables:

- Queryable notes without preprocessing
- Addressable transcripts (block-level retrieval)
- Research notebooks in a single format
- Composable knowledge systems for AI
- Retrieval over structured units instead of text chunks
- Systems that enrich documents instead of reconstructing them

---

## LLM-Native Design

SMD is designed for systems where documents are not static files, but active memory structures.

In these systems:

- nodes become atomic knowledge units
- blocks become reasoning contexts
- metadata becomes retrieval and linking signals

SMD acts as a shared storage layer for structured intelligence systems.

---

## Why This Works

Most document systems assume:

> Structure must be extracted from text.

SMD assumes:

> Structure should exist before interpretation.

This inversion removes an entire class of complexity.

---

## Mental Model

Think of SMD as:

- Markdown, but structured  
- JSON, but human-writable  
- Notion, but portable  
- A document, but queryable  
- A file, but also an API  

---

## Why Existing Systems Don’t Fully Solve This

SMD is not a new idea—it is a recombination of partial solutions.

| System | What it gets right | What it lacks |
|--------|--------------------|--------------|
| ProseMirror | Structured document tree | No semantic node/data standard |
| Notion | Block-based authoring | Not portable outside its ecosystem |
| Markdown | Human-readable simplicity | No native structure |
| HTML | Rich rendering model | Not a semantic storage format |
| JSON / ASTs | Fully structured data | Not human-writable as primary format |

Each solves a slice of the problem.

None unify:

> authoring + structure + portability + machine interpretability

---

## The Gap SMD Fills

SMD sits at the intersection:

- structured like ProseMirror  
- authored like Markdown  
- composable like JSON  
- modular like Notion blocks  
- portable like a file format  

But unlike each individually:

> Structure is not derived. It is written.

---

## Status

Draft specification.

Stable concept. Evolving implementation.

---

## Closing Principle

A document should not need to be reconstructed to be understood.

It should already know what it is.

---

## Project Status

This is an active research project. The specification is in **v0.2** and evolving.

- 📄 [Full Specification](SPECIFICATION.md)
- 🐍 [Python Reference Parser](src/parser.py)
- 📚 [Examples](examples/)
- 📝 arXiv paper forthcoming

---

## Citation

```bibtex
@software{semantic_markdown,
  title = {Semantic Markdown: A Block-Addressable Document Format
           for Human-Agent Collaboration},
  year = {2026},
  url = {https://github.com/your-org/semantic-markdown}
}
```

---

## License

MIT
