"""
Semantic Markdown (SMD) — Reference Parser Implementation.

A block-addressable document format for human-agent collaboration.

Exposed API:
    parse_smd(text: str) -> SMDDocument
    parse_file(path: str | Path) -> SMDDocument
    SMDDocument, SMDBlock, BodySegment
    SentimentRecord, EnrichmentHighlight
    SMDAgent — MCP-style agent for enriching documents
    ParseError
"""

from .parser import parse_smd, parse_file
from .models import SMDDocument, SMDBlock, BodySegment, SentimentRecord, EnrichmentHighlight
from .agent import SMDAgent
from .errors import ParseError

__all__ = [
    "parse_smd",
    "parse_file",
    "SMDDocument",
    "SMDBlock",
    "BodySegment",
    "SentimentRecord",
    "EnrichmentHighlight",
    "SMDAgent",
    "ParseError",
]
