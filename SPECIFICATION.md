# Semantic Markdown (SMD) — Specification v0.0

> A block-addressable document format for human-agent collaboration, with semantic overlays and emergent structure.

**Status:** Active Research  
**Last updated:** 2026-06-09  
**Extension:** `.smd`  
**MIME:** `text/vnd.semantic-markdown` (pending IANA registration)

---

## Table of Contents

- [0. Design Principles](#0-design-principles)
- [1. Primitives](#1-primitives)
- [2. Separator Rules](#2-separator-rules)
- [3. Formal Grammar (EBNF)](#3-formal-grammar-ebnf)
- [4. Body Content Parsing](#4-body-content-parsing)
- [5. Parser Algorithm](#5-parser-algorithm)
- [6. Identifiers](#6-identifiers)
- [7. Nesting Conventions](#7-nesting-conventions-not-format-rules)
- [8. Use Cases](#8-use-cases)
- [9. Viewer Semantics](#9-viewer-semantics-semantic-overlays)
- [10. Clustering Pipelines](#10-clustering-pipelines)
- [11. Comparison with Alternatives](#11-comparison-with-alternatives)
- [12. Error Handling](#12-error-handling)
- [13. Future Considerations](#13-future-considerations)
- [14. License](#14-license)

---

## 0. Design Principles

1. **Minimal primitives.** Two constructs (`@document`, `@block`), one separator (`---`). Everything else is convention.

2. **No built-in hierarchy.** Nesting, trees, graphs, timelines — all expressed through conventional use of `block_id`, `parent_id`, `tags`, and `type`. The format defines the alphabet; users define the grammar.

3. **Conventions over protocols.** The format does not enforce a nesting schema. An ecosystem of conventions can emerge (e.g., `block_level=N` tag, path-based IDs, parent pointers).

4. **Bottom-up discoverable.** Tags are free-form. Structure can emerge from clustering, not just from author intent.

5. **Triple-consumable.** Designed for humans (readable Markdown), agents (parseable JSON headers), and viewers (renderable semantic overlays).

---

## 1. Primitives

### 1.1 `@document`

The top-level container. A document has one JSON header and an optional Markdown body.

```
@document
{
    "document_id": "<string>",
    "schema_version": "<string>",
    "created": "<ISO 8601 timestamp>",
    "source": "<string>",
    "type": "<string>",
    "meta": { <any> }
}
---
<body (optional)>
```

**Fields:**

| Field | Requirement | Description |
|---|---|---|
| `document_id` | **REQUIRED** | Globally unique identifier. UUIDv7 recommended. |
| `schema_version` | RECOMMENDED | Format version for migration support. |
| `created` | RECOMMENDED | ISO 8601 timestamp of creation. |
| `source` | OPTIONAL | Origin of the document (e.g., filename, URL). |
| `type` | RECOMMENDED | Semantic type. Examples: `transcript`, `notebook`, `article`, `log`, `corpus`. |
| `meta` | OPTIONAL | Application-specific metadata object. |

The body is optional — a document may exist solely as a container for blocks.

### 1.2 `@block`

A content unit — the fundamental addressable entity in SMD.

```
@block
{
    "block_id": "<string>",
    "document_id": "<string>",
    "type": "<string>",
    "parent_id": "<string>",
    "created": "<ISO 8601 timestamp>",
    "position": <number>,
    "tags": ["<string>", ...],
    "sentiment": [
        {
            "excerpt": "<string>",
            "score": <number>,
            "label": "<string>",
            "confidence": <number>
        }
    ],
    "enrichment": {
        "highlights": ["<string>", ...],
        "entities": ["<string>", ...],
        "summary": "<string>",
        "key_takeaways": ["<string>", ...]
    },
    "meta": { <any> }
}
---
<body>
```

**Fields:**

| Field | Requirement | Description |
|---|---|---|
| `block_id` | **REQUIRED** | Unique within the containing document. |
| `document_id` | OPTIONAL | Reference to parent document. |
| `type` | RECOMMENDED | Semantic role of this block. Examples: `qa`, `entry`, `note`, `section`, `paragraph`, `summary`, `action_item`. |
| `parent_id` | OPTIONAL | Reference to parent block for tree/hierarchy conventions. |
| `created` | OPTIONAL | ISO 8601 timestamp. |
| `position` | OPTIONAL | Ordinal position within parent or document. |
| `tags` | OPTIONAL | Free-form string tags. No taxonomy required. Used for filtering, clustering, and overlays. |
| `sentiment` | OPTIONAL | A list of sentiment records, each tied to a specific excerpt. Each record has: `excerpt` (text span), `score` (0.0–1.0; 0=negative, 0.5=neutral, 1.0=positive), `label` (optional human-readable label), `confidence` (optional model confidence 0.0–1.0). Legacy single-float sentiment is also supported. |
| `enrichment` | OPTIONAL | Agent-generated or human-written enrichment data. Common fields: `highlights`, `entities`, `summary`, `key_takeaways`. |
| `meta` | OPTIONAL | Application-specific metadata. |

The body is **REQUIRED** for `@block` (may be empty string).

All enrichment, sentiment, highlights, and summary data MUST be placed in the block's JSON header. Do NOT use standalone triple-backtick fenced blocks (e.g. ` ```summary`, ` ```sentiment`) in the body to carry enrichment data — those are reserved for inline thinking/annotations that are part of the narrative content (e.g. ` ```thought`).

---

## 2. Separator Rules

### 2.1 Entity start

An SMD file is parsed by scanning for lines that match `^@document` or `^@block` at the start of a line.

### 2.2 Header–body separator

The **first** occurrence of `^---$` (three dashes on their own line) after the `@document`/`@block` line ends the JSON header and begins the body.

```
@block
{
    "block_id": "b-001"
}
---              ← separator (line containing only "---")
Content body     ← body (Markdown)
```

### 2.3 Body termination

A block/document body is terminated by:
- The next `@document` or `@block` line
- End of file

---

## 3. Formal Grammar (EBNF)

```ebnf
smd_file        = { entity } , EOF;

entity          = document | block;

document        = "@document", newline, json_header, separator, body;
block           = "@block", newline, json_header, separator, body;

json_header     = "{" , { any_character } , "}";
separator       = newline, "---", newline;
body            = { any_character };

newline         = "\n" | "\r\n";
any_character   = ? any Unicode character except EOF ?;
```

Note: The JSON header must be a valid JSON object as defined by [RFC 8259](https://tools.ietf.org/html/rfc8259).

---

## 4. Body Content Parsing

The body parser recognizes **triple-backtick fenced sections** with an optional content type label. The body is split into an ordered list of typed segments.

### 4.1 Markdown segments

Raw Markdown text between fenced blocks is parsed as `type: "markdown"`.

### 4.2 Fenced segments

Content between ` ```type ... ``` ` is extracted as a typed payload:

```
@block { "block_id": "b-001" }
---
Some markdown content...

```thought
This is my internal thinking about this topic.
```

```action_item
Review AMD MI350 benchmarks.
Assigned to: Bob
Due: 2026-07-01
```
```

The parser produces:

```json
[
  { "type": "markdown", "content": "Some markdown content...\n\n" },
  { "type": "thought", "content": "This is my internal thinking..." },
  { "type": "markdown", "content": "\n" },
  { "type": "action_item", "content": "Review AMD MI350 benchmarks..." }
]
```

---

## 5. Parser Algorithm

```
function parse_smd(text: string): Entity[] {
    entities = []

    // 1. Split on @document or @block at line start (positive lookahead)
    raw_blocks = text.split(/^(?=@(?:document|block))/m)

    for raw in raw_blocks:
        if raw matches "^@document" or raw matches "^@block":
            entity = {}

            // 2. Determine entity type
            entity.type = raw matches "@document" ? "document" : "block"

            // 3. Locate first --- separator
            sep_pos = raw.indexOf("\n---\n")
            if sep_pos == -1:
                raise ParseError("Missing '---' separator")

            // 4. Extract JSON header (between @ line and separator)
            header_start = raw.indexOf("\n") + 1
            header_text = raw[header_start:sep_pos].trim()
            entity.header = JSON.parse(header_text)

            // 5. Extract body (after separator)
            body_text = raw[sep_pos + 5:].trim()
            entity.segments = parse_body(body_text)

            entities.append(entity)

    return entities
}
```

**Time complexity:** O(n) — single pass, no backtracking.

---

## 6. Identifiers

### 6.1 `block_id`

- **REQUIRED** on every `@block`.
- MUST be unique within the containing document.
- RECOMMENDED conventions: UUIDv7 (time-sortable), slugs (`qa-0042`, `day-2026-01-15`), or path-like identifiers (`section/methodology/wacc`).

### 6.2 `document_id`

- **REQUIRED** on every `@document`.
- RECOMMENDED: UUIDv7 or a unique slug.

### 6.3 Referencing

Blocks reference each other via `parent_id` to form tree structures. The format does not enforce tree validity; it is a convention.

```
@block { "block_id": "ch-1", "type": "chapter" }
---
## Overview

@block { "block_id": "sec-1", "parent_id": "ch-1" }
---
### Details
```

---

## 7. Nesting Conventions (Not Format Rules)

SMD does not have built-in nesting. The following conventions are recognized patterns:

### 7.1 Explicit parent pointer

```smd
@block { "block_id": "sec-1-1", "parent_id": "ch-1" }
```

### 7.2 Tag-based level

```smd
@block { "block_id": "h1", "tags": ["block_level=1"] }
---
# Chapter 1

@block { "block_id": "h2", "tags": ["block_level=2"] }
---
## Section 1.1
```

A viewer can reconstruct a tree by grouping on `block_level`.

### 7.3 Path-based `block_id`

```smd
@block { "block_id": "2026/06/07/note-1" }
@block { "block_id": "section/methodology/wacc" }
```

The `/` separator is a convention — viewers MAY split on `/` to build a tree.

### 7.4 Namespaced tags

```smd
@block { "tags": ["section:intro"] }
@block { "tags": ["section:body", "sub:methodology"] }
```

Clustering pipelines can discover hierarchy from tag name conventions.

---

## 8. Use Cases

### 8.1 Earnings Transcript (Q&A blocks)

```smd
@document
{
    "document_id": "aapl-q3-2026",
    "type": "transcript",
    "source": "AAPL Q3 2026 Earnings Call",
    "created": "2026-06-07T18:30:00Z",
    "meta": {
        "ticker": "AAPL",
        "fiscal_quarter": "Q3",
        "fiscal_year": 2026
    }
}
---
@block
{
    "block_id": "qa-0001",
    "type": "qa",
    "position": 1,
    "tags": ["guidance", "revenue"],
    "speaker": "Analyst - Goldman Sachs",
    "sentiment": [
        {
            "excerpt": "Guidance beat consensus by ~2%. Services growth continues.",
            "score": 0.74,
            "label": "positive",
            "confidence": 0.88
        }
    ],
    "enrichment": {
        "highlights": ["Revenue guidance above consensus"],
        "entities": ["AAPL", "Services"],
        "summary": "Guidance beat consensus by ~2%. Services growth continues."
    }
}
---
**Michael Ng:** Can you talk about Q4 guidance?

**Luca Maestri:** We expect low double digits...

@block
{
    "block_id": "qa-0002",
    "type": "qa",
    "position": 2,
    "tags": ["AI", "capex"],
    "speaker": "Analyst - Morgan Stanley",
    "sentiment": [
        {
            "excerpt": "We're investing significantly...",
            "score": 0.91,
            "label": "very positive",
            "confidence": 0.95
        }
    ]
}
---
**Erik Woodring:** On AI capex?

**Tim Cook:** We're investing significantly...
```

### 8.2 Financial Notebook (day blocks)

One file, many dated entries:

```smd
@document
{
    "document_id": "research-aapl-2026",
    "type": "notebook",
    "title": "AAPL Research Notes"
}
---
@block
{
    "block_id": "day-2026-01-15",
    "type": "entry",
    "created": "2026-01-15",
    "tags": ["valuation", "dcf"],
    "meta": { "mood": "bullish" }
}
---
Updated DCF model today. WACC lowered to 9.2%.

**TODO:** Review Services revenue breakdown.

@block
{
    "block_id": "day-2026-03-22",
    "type": "entry",
    "created": "2026-03-22",
    "tags": ["ai", "capex", "valuation"],
    "meta": { "mood": "neutral" }
}
---
AI capex $15B announced.

```thought
This impacts FCF. Need to adjust model.
```
```

### 8.3 Collaborative Research (multi-author)

```smd
@document { "document_id": "semi-research", "type": "notebook" }
---
@block
{
    "block_id": "note-alice-001",
    "type": "note",
    "author": "Alice",
    "created": "2026-06-05",
    "tags": ["nvda", "datacenter"]
}
---
NVDA datacenter revenue grew 140% YoY.

```action_item
Review AMD MI350 benchmarks. Assigned to: Bob
```

@block
{
    "block_id": "note-bob-001",
    "type": "note",
    "author": "Bob",
    "created": "2026-06-06",
    "tags": ["amd", "mi350"],
    "meta": { "status": "in_progress" }
}
---
MI350 has 2.4 TB/s memory bandwidth vs NVDA 2.0 TB/s.
```

### 8.4 RAG Corpus (semantic chunks)

```smd
@document { "document_id": "fed-minutes-2026-05", "type": "corpus" }
---
@block
{
    "block_id": "sec-inflation",
    "tags": ["inflation", "cpi", "policy"],
    "enrichment": {
        "summary": "Fed expresses caution on inflation persistence",
        "entities": ["CPI", "PCE", "fed funds rate"]
    }
}
---
Participants noted that inflation remains elevated...

@block
{
    "block_id": "sec-labor",
    "tags": ["labor", "employment"],
    "enrichment": { "summary": "Labor market remains tight" }
}
---
The labor market remains tight...
```

---

## 9. Viewer Semantics (Semantic Overlays)

SMD is designed for **triple consumption**: humans, agents, and viewers. The JSON header provides rendering hints that enable visual features impossible in plain Markdown or JSON alone.

### 9.1 Tag-Based Filtering

A viewer MAY extract all `tags` arrays from block headers and present them as a filter interface.

```
┌─────────────────────────────────────────────┐
│  Filter: [All] [#valuation] [#ai] [#dcf]   │
├─────────────────────────────────────────────┤
│  Only blocks matching selected tags shown.  │
└─────────────────────────────────────────────┘
```

Blocks without matching tags are hidden. No parsing of the Markdown body is needed to build this filter.

### 9.2 Semantic Overlay Mapping

| Header Field | Visual Treatment |
|---|---|
| `sentiment` (0.0–1.0) | Color gradient: red (0) → yellow (0.5) → green (1.0). Applied as gutter stripe, background tint, or icon. |
| `tags` | Badge/chip per tag. Clickable to filter. |
| `enrichment.highlights` | Inline annotations, callout boxes, or sidebar list. |
| `enrichment.entities` | Hyperlinked symbols (e.g., `$AAPL`). Hover for context. |
| `meta.status` | Status icon: ✅ done, ⏳ in_progress, 🔴 blocked, 📝 draft. |
| `type` | Section heading icon or custom card style. |
| `author` | Color-coded by author. |
| `speaker` | Label prefix in transcript view. |

### 9.3 Concrete Viewer Example

```
┌──────────────────────────────────────────────────────┐
│  📈 [0.91]  #guidance #revenue  ✦ Revenue beat      │
│  ┌──────────────────────────────────────────────────┐│
│  │ **Analyst:** Great quarter. Can you talk about  ││
│  │ guidance?                                       ││
│  │                                                  ││
│  │ **CEO:** Revenue grew 12%...                    ││
│  └──────────────────────────────────────────────────┘│
│  ⟐ AAPL  ⟐ Services                                 │
└──────────────────────────────────────────────────────┘
```

### 9.4 Cross-Document Views

A viewer MAY aggregate blocks across multiple `.smd` files:

```
View: All blocks tagged #action_item across research-*.smd

┌─────────────────────────────────────────────┐
│ ⚠️ Review MI350 benchmarks          (2d ago)│
│ ⚠️ Update DCF model for AI capex    (1w ago)│
│ ⚠️ Check TSMC earnings date        (3d ago)│
└─────────────────────────────────────────────┘
```

Only the JSON headers need to be scanned — body parsing is optional for this view.

### 9.5 Viewer Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  .smd files   │────▶│  Parser (header  │────▶│  Viewer           │
│  (one or     │     │  + segment list)  │     │                   │
│  many)       │     │                   │     │  ┌─────────────┐  │
│              │     │  Header → overlay │     │  │ Tag filter  │  │
│              │     │  Body   → render  │     │  ├─────────────┤  │
│              │     │                   │     │  │ Block cards │  │
│              │     │                   │     │  │ w/ overlays │  │
│              │     │                   │     │  ├─────────────┤  │
│              │     │                   │     │  │ Cross-doc   │  │
│              │     │                   │     │  │ aggregator  │  │
└──────────────┘     └──────────────────┘     └───────────────────┘
```

The viewer is **stateless** — all rendering hints are in the file itself. No separate database query needed.

---

## 10. Clustering Pipelines

Because tags are free-form strings in JSON, SMD is naturally amenable to bottom-up structure discovery.

### 10.1 Tag clustering pipeline

```mermaid
flowchart LR
    A[SMD File] --> B[Extract block_id, tags[]]
    B --> C[Compute tag co-occurrence]
    C --> D[Cluster tags]
    D --> E[Suggest normalization]
    E --> F[Write back to meta.suggested_tags]
```

### 10.2 Example output

```
Input blocks:
  b1: ["dcf", "valuation", "wacc"]
  b2: ["dcf model", "valuation", "terminal growth"]
  b3: ["ai", "capex"]
  b4: ["ai", "nvda", "chip"]
  b5: ["amd", "mi350", "chip"]

Cluster 1: "valuation" → normalize "dcf", "dcf model" → "dcf"
Cluster 2: "ai_capex" → normalize "ai", "capex" → "ai_capex"
Cluster 3: "competition" → normalize "nvda", "amd", "mi350", "chip" → "competition"
```

### 10.3 Feedback loop

```smd
@block
{
    "block_id": "b1",
    "tags": ["dcf", "valuation"],
    "meta": {
        "suggested_tags": ["dcf"],       ← from clustering
        "cluster": "valuation_group"     ← from clustering
    }
}
```

No format changes needed — the pipeline writes into the existing `meta` or `enrichment` fields.

---

## 11. Comparison with Alternatives

| Feature | Plain MD | JSON | YAML+MD (Frontmatter) | MDX | SMD |
|---|---|---|---|---|---|
| Human-readable body | ✅ | ❌ | ✅ | ✅ | ✅ |
| Machine-parseable metadata | ❌ | ✅ | ✅ (file-level) | ❌ | ✅ (block-level) |
| Block-level addressing | ❌ | ❌ | ❌ | ❌ | ✅ (`block_id`) |
| Block-level tags | ❌ | ✅ | ❌ | ❌ | ✅ |
| Semantic overlays | ❌ | ❌ | ❌ | ❌ | ✅ |
| Emergent clustering | ❌ | Partial | ❌ | ❌ | ✅ |
| Agent enrichment slot | ❌ | ✅ | ❌ | ❌ | ✅ (`enrichment`) |
| Git-friendly | ✅ | ✅ | ✅ | ✅ | ✅ |
| No proprietary tools | ✅ | ✅ | ✅ | ❌ (JSX) | ✅ |
| Nesting conventions | ✅ (headings) | ✅ | ❌ | ✅ | ✅ (via `parent_id`, tags) |

---

## 12. Error Handling

| Condition | Behavior |
|---|---|
| `@block` with no `---` separator | Raise `ParseError`. Invalid document. |
| Malformed JSON in header | Raise `ParseError` with line number. |
| Duplicate `block_id` within document | Raise `ParseError`. |
| `@document` inside another document | Parsed as a new document (sequential, not nested). |
| Unknown fenced block type | Treated as plain markdown in body, but typed segment is still emitted. |
| Empty body | Valid. `segments` is an empty list. |

---

## 13. Future Considerations

| Topic | Notes |
|---|---|
| **Inline block references** | A syntax like `[b-001]` or `@ref(b-001)` to reference another block from within body text. |
| **Schema validation** | Optional JSON Schema per `type` to validate enrichment fields. |
| **Streaming** | Line-delimited SMD for real-time agent output (LLM streaming). |
| **Encryption per block** | Encrypted enrichment at the block level for sensitive metadata. |
| **Versioning** | Git-native diff at block granularity (block_id as anchor). |

---

## 14. License

This specification is released under the [MIT License](https://opensource.org/licenses/MIT).
