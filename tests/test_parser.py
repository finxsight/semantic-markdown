"""Tests for the Semantic Markdown reference parser."""

import json
import os
import sys
from pathlib import Path

# Add src to path so tests can run standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from semantic_markdown import parse_smd, ParseError, SMDDocument, SMDBlock


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_single_block():
    text = """@block
{
    "block_id": "b-001",
    "tags": ["test"]
}
---
Hello world
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].block_id == "b-001"
    assert doc.blocks[0].tags == ["test"]
    assert doc.blocks[0].body_text == "Hello world"


def test_single_document():
    text = """@document
{
    "document_id": "doc-001",
    "type": "test"
}
---
Some content
"""
    doc = parse_smd(text)
    assert len(doc.documents) == 1
    assert doc.documents[0].header["document_id"] == "doc-001"


def test_block_and_document():
    text = """@document
{
    "document_id": "doc-001"
}
---
@block
{
    "block_id": "b-001"
}
---
Hello
"""
    doc = parse_smd(text)
    assert len(doc.documents) == 1
    assert len(doc.blocks) == 1  # block inside document body is still parsed
    assert doc.blocks[0].block_id == "b-001"


def test_multiple_blocks():
    text = """@block
{
    "block_id": "b-001"
}
---
First block

@block
{
    "block_id": "b-002"
}
---
Second block
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 2
    assert doc.blocks[0].block_id == "b-001"
    assert doc.blocks[1].block_id == "b-002"
    assert "First" in doc.blocks[0].body_text
    assert "Second" in doc.blocks[1].body_text


# ---------------------------------------------------------------------------
# Body segments
# ---------------------------------------------------------------------------

def test_fenced_content():
    text = """@block
{
    "block_id": "b-001"
}
---
Markdown content

```thought
My internal thought
```

More markdown
"""
    doc = parse_smd(text)
    block = doc.blocks[0]
    assert len(block.segments) == 3
    assert block.segments[0].type == "markdown"
    assert "Markdown content" in block.segments[0].content
    assert block.segments[1].type == "thought"
    assert block.segments[1].content.strip() == "My internal thought"
    assert block.segments[2].type == "markdown"
    assert "More markdown" in block.segments[2].content


def test_empty_body():
    text = """@block
{
    "block_id": "b-001"
}
---
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].body_text == ""
    assert len(doc.blocks[0].segments) == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_missing_separator():
    text = """@block
{
    "block_id": "b-001"
}
no separator here
"""
    try:
        parse_smd(text)
        assert False, "Expected ParseError"
    except ParseError as e:
        assert "separator" in str(e)


def test_malformed_json():
    text = """@block
{
    "block_id": "b-001",
    invalid json
}
---
Hello
"""
    try:
        parse_smd(text)
        assert False, "Expected ParseError"
    except ParseError as e:
        assert "JSON" in str(e)


def test_duplicate_block_id():
    text = """@block
{
    "block_id": "b-001"
}
---
First

@block
{
    "block_id": "b-001"
}
---
Second
"""
    try:
        parse_smd(text)
        assert False, "Expected ParseError"
    except ParseError as e:
        assert "duplicate" in str(e).lower()


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------

def test_filter_by_tag():
    text = """@block
{
    "block_id": "b-001",
    "tags": ["ai", "ml"]
}
---
AI content

@block
{
    "block_id": "b-002",
    "tags": ["finance", "valuation"]
}
---
Finance content

@block
{
    "block_id": "b-003",
    "tags": ["ai", "robotics"]
}
---
More AI
"""
    doc = parse_smd(text)
    ai_blocks = doc.filter_by_tag("ai")
    assert len(ai_blocks) == 2
    assert ai_blocks[0].block_id == "b-001"
    assert ai_blocks[1].block_id == "b-003"

    finance_blocks = doc.filter_by_tag("finance")
    assert len(finance_blocks) == 1
    assert finance_blocks[0].block_id == "b-002"


def test_filter_by_type():
    text = """@block
{
    "block_id": "b-001",
    "type": "qa"
}
---
Q&A content

@block
{
    "block_id": "b-002",
    "type": "summary"
}
---
Summary content
"""
    doc = parse_smd(text)
    qa_blocks = doc.filter_by_type("qa")
    assert len(qa_blocks) == 1
    assert qa_blocks[0].block_id == "b-001"


def test_all_tags():
    text = """@block
{
    "block_id": "b-001",
    "tags": ["ai", "ml"]
}
---
First

@block
{
    "block_id": "b-002",
    "tags": ["finance", "ai"]
}
---
Second
"""
    doc = parse_smd(text)
    tags = doc.all_tags()
    assert len(tags) == 3
    assert tags == ["ai", "ml", "finance"]  # order of first appearance


def test_tag_co_occurrence():
    text = """@block
{
    "block_id": "b-001",
    "tags": ["ai", "ml", "python"]
}
---
First

@block
{
    "block_id": "b-002",
    "tags": ["ai", "python"]
}
---
Second

@block
{
    "block_id": "b-003",
    "tags": ["finance", "ml"]
}
---
Third
"""
    doc = parse_smd(text)
    matrix = doc.tag_co_occurrence()
    assert matrix["ai"]["ml"] == 1
    assert matrix["ai"]["python"] == 2
    assert matrix["finance"]["ml"] == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_blocks_in_document_header():
    text = """@document
{
    "document_id": "doc-001"
}
---
@block
{
    "block_id": "b-001",
    "tags": ["tag1"]
}
---
Block content
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].block_id == "b-001"
    assert doc.blocks[0].tags == ["tag1"]


def test_no_blocks():
    text = """@block
{
    "block_id": "b-001"
}
---
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 1


# ---------------------------------------------------------------------------
# Real file parsing
# ---------------------------------------------------------------------------

def test_parse_example_transcript():
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    transcript_file = examples_dir / "transcript.smd"
    if not transcript_file.exists():
        return  # skip if examples not present
    from semantic_markdown import parse_file
    doc = parse_file(transcript_file)
    assert len(doc.blocks) == 33
    assert doc.blocks[0].block_id == "0"
    assert doc.blocks[0].header.get("block_type") == "operator_comment"
    assert doc.blocks[1].block_id == "1"
    assert doc.blocks[1].header.get("block_type") == "business_update"
    assert doc.blocks[7].block_id == "7"
    assert doc.blocks[7].header.get("block_type") == "qa"
    assert doc.blocks[7].header.get("qa_thread_id") == "0"

    # Block 9 has enrichments
    assert "enrichments" in doc.blocks[9].header
    enr = doc.blocks[9].header["enrichments"]
    assert enr[0]["type"] == "highlight"
    assert enr[0]["topic"] == "Faster growth in 2H"
    assert len(enr[0]["highlights"]) == 3


def test_parse_example_notebook():
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    notebook_file = examples_dir / "notebook.smd"
    if not notebook_file.exists():
        return
    from semantic_markdown import parse_file
    doc = parse_file(notebook_file)
    assert len(doc.blocks) == 3
    assert doc.blocks[0].block_id == "day-2026-01-15"
    assert doc.blocks[1].block_id == "day-2026-03-22"
    assert doc.blocks[2].block_id == "day-2026-04-10"

    # Check tags
    assert "valuation" in doc.blocks[0].tags
    assert "capex" in doc.blocks[1].tags
    assert "nvda" in doc.blocks[2].tags

    # Type should be "entry"
    assert doc.blocks[0].type == "entry"

    # Should have fenced segments (thought blocks)
    assert len(doc.blocks[0].segments) > 1
    thought_segments = [s for s in doc.blocks[0].segments if s.type == "thought"]
    assert len(thought_segments) >= 1


# ---------------------------------------------------------------------------
# JSON round-trip via CLI
# ---------------------------------------------------------------------------

def test_json_serialization():
    text = """@block
{
    "block_id": "b-001",
    "tags": ["test"],
    "sentiment": 0.5
}
---
Hello
"""
    doc = parse_smd(text)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].header["sentiment"] == 0.5
    assert doc.blocks[0].body_text == "Hello"


if __name__ == "__main__":
    # Run all tests manually
    tests = [
        test_single_block,
        test_single_document,
        test_block_and_document,
        test_multiple_blocks,
        test_fenced_content,
        test_empty_body,
        test_missing_separator,
        test_malformed_json,
        test_duplicate_block_id,
        test_filter_by_tag,
        test_filter_by_type,
        test_all_tags,
        test_tag_co_occurrence,
        test_blocks_in_document_header,
        test_no_blocks,
        test_parse_example_transcript,
        test_parse_example_notebook,
        test_json_serialization,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
