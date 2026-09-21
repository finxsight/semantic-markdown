# Semantic Markdown (SMD) — Specification v0.2

**Status:** Production format (FIRE)  
**Extension:** `.smd`  
**MIME (informal):** `text/vnd.semantic-markdown`  
**License:** Apache-2.0

---

## 1. Overview

An SMD file is one UTF-8 text document:

1. Optional **`@document`** — file-level JSON metadata and an optional **title preamble**.
2. Zero or more **`@block`** sections — JSON metadata + markdown body.

Each `@`-directive starts at the beginning of a line. JSON headers are a single object `{ ... }` immediately after the directive line. A line containing only `---` may appear after JSON to separate chrome from prose (common after `@document` and often after `@block`).

Line endings MAY be LF or CRLF; parsers normalize before splitting.

There is no required global schema file. Parsers treat unknown JSON keys as opaque application data.

---

## 2. File layout

```text
@document
{ "document_type": "background_research", "date": "2026-07-09" }
---
Optional document title (plain text, not a block)

@block
{ "_id": "8b1e2f4a-0c3d-4e5f-9a0b-1c2d3e4f5a6b", "section_type": "summary" }
---

Block body (markdown, fences, inline annotations)

@block
{ "_id": "2", "section_type": "observation" }
Body may follow JSON directly when --- is omitted
```

### 2.1 `@document`

- Appears at most once, usually at the top of the file.
- JSON holds file-level fields only (not block content).

| Key | Purpose |
|-----|---------|
| `document_type` | e.g. `background_research`, `earnings_transcript`, `wiki`, `annotations` |
| `date` / `datetime` | ISO date or timestamp |
| `calendar_period` | Period label when not inferable from filename |
| `read_only` | Viewer hint when true |

Additional keys (ticker, company name, viewer `styles` / `filters`, etc.) are allowed.

**Title preamble:** Text after `@document` JSON (and optional `---`) until the first `@block`. Shown as the document title in FIRE; not indexed as its own block.

### 2.2 `@block`

Each block is independently addressable.

| Key | Purpose |
|-----|---------|
| `_id` | **Required.** UUID string or numeric string (transcript ordering). Unique within the file. |
| `section_type` | Semantic section name (`summary`, `qa`, `observation`, `operator_comment`, …). |
| `datetime` | Block timestamp (often tool-assigned). |
| `sources` | List of source paths or URIs. |
| `tags` | String list for filters (#hashtags in body are also used in FIRE). |
| `indexing` | Nested object; FIRE flattens known keys onto the block header. |

**Body:** Markdown after the header region. Fenced code blocks (`` ```lang ``) are typed segments. FIRE also uses `:::figure` … `:::` plates and other app-specific fences.

### 2.3 Inline annotations

Analyst highlights embed in block bodies:

```text
=== {"comment":"Pricing power","sentiment_score":0.6} exact source phrase ===
```

- JSON object between `===` delimiters; `sentiment_score` typically −1..1.
- Marks MUST NOT overlap in FIRE tooling.
- PDF/HTML use sidecar `.annotations.smd` files with the same `@document` / `@block` shape.

Header-level highlight bundles are **not** part of v0.2; use inline marks or sidecars.

---

## 3. Parsing rules (normative)

1. Locate `@document` if present; parse the following JSON object with brace matching (strings and escapes respected).
2. **Preamble** = text from end of document JSON until the first line that is exactly `@block`.
3. For each `@block`: parse JSON object; optional whitespace and a `---` line; remainder of text until the next `@block` or EOF is the **body**.
4. If there is no `@document`, parsing begins at the first `@block`.
5. Duplicate `_id` values in one file are an error for writers and SHOULD be rejected by strict parsers.

---

## 4. Query and indexing

Applications index blocks by:

- `_id` (patch target)
- `document_type`, `section_type`, dates, `tags`, hashtags
- Full text of block bodies (see `SMDIndexer` in this repo)

Relationships are expressed via metadata, links in markdown, and app-level indexes — not via separate edge syntax in the file.

---

## 5. Reference implementation

This repository ships:

- `parse_smd` / `parse_file` — Python parser
- `index.html` — JS viewer for `examples/`
- `smd` CLI — structure dump
- `smd-mcp` — experimental agent harness

Split/serialize behavior SHOULD match FIRE `shell/lib/smd_blocks.py`; when in doubt, FIRE wins for product behavior.

---

## 6. Version history

- **v0.2 (2026-09)** — `@document` preamble, `_id`, `section_type`, `document_type`, optional block `---`, inline `===` annotations.
- **v0.1 (2026-06)** — Superseded public draft (graph-theory experiment; not used in FIRE).
