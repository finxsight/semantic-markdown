"""
Semantic Markdown (SMD) — Reference Parser Implementation.

A block-addressable document format for human-agent collaboration.

The SMD format is self-describing — every entity carries its own JSON
header.  No separate schema/model file is needed.

Exposed API:
    parse_smd(text: str) -> SimpleNamespace
    parse_file(path: str | Path) -> SimpleNamespace
    all_tags, filter_by_tag, filter_by_type, filter_by_tags, tag_co_occurrence
    SMDAgent — MCP-style agent for enriching documents
    ParseError
"""

from .parser import (
    parse_smd, parse_file,
    all_tags, filter_by_tag, filter_by_type, filter_by_tags, tag_co_occurrence,
)
from .harness import SMDAgent
from .indexer import SMDIndexer, SearchHit
from .parser import ParseError

__all__ = [
    "parse_smd",
    "parse_file",
    "all_tags",
    "filter_by_tag",
    "filter_by_type",
    "filter_by_tags",
    "tag_co_occurrence",
    "SMDAgent",
    "SMDIndexer",
    "SearchHit",
    "ParseError",
]
