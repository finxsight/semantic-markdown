"""Data models for Semantic Markdown (SMD) entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


@dataclass
class SentimentRecord:
    """A granular sentiment annotation tied to a specific excerpt.

    Attributes:
        excerpt: The text span this sentiment applies to.
        score: Numeric score 0.0–1.0 (0=negative, 0.5=neutral, 1.0=positive).
        label: Optional human-readable label (e.g. "positive", "cautious").
        confidence: Optional model confidence 0.0–1.0.
    """

    excerpt: str
    score: float
    label: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class EnrichmentHighlight:
    """A highlighted text span with optional sentiment annotation.

    Attributes:
        enrichment_id: Unique identifier for this enrichment item.
        text: The highlighted text content.
        sentiment: Optional sentiment score (0.0–1.0) for this highlight.
    """

    text: str
    sentiment: Optional[float] = None
    enrichment_id: Optional[str] = None


@dataclass
class BodySegment:
    """A typed segment within a block's body.

    The body is split into segments by triple-backtick fenced blocks.
    Raw markdown between fences becomes type="markdown".
    """

    type: str
    """Content type — "markdown" for raw text, or the label after ``` (e.g. "thought", "summary")."""

    content: str
    """The raw text content of this segment."""


@dataclass
class SMDBlock:
    """A single @block entity — the fundamental addressable unit in SMD."""

    block_id: str
    """Unique identifier for this block within its document."""

    header: dict[str, Any]
    """Parsed JSON header (all fields)."""

    raw_header: str
    """Raw JSON string as written in the file."""

    segments: List[BodySegment] = field(default_factory=list)
    """Parsed body as a list of typed segments."""

    body_text: str = ""
    """Raw body text (the full text after --- before next entity)."""

    @property
    def tags(self) -> List[str]:
        """Convenience accessor for the tags list."""
        return self.header.get("tags", [])

    @property
    def type(self) -> Optional[str]:
        """Convenience accessor for the block type."""
        return self.header.get("type") or self.header.get("block_type")

    @property
    def sentiment(self) -> Optional[Union[float, List[SentimentRecord]]]:
        """Access the block's sentiment data.

        Returns:
            A single float (legacy block-level sentiment) or a list of
            SentimentRecord objects (excerpt-level sentiment annotations).
            None if no sentiment field is present.
        """
        raw = self.header.get("sentiment")
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, list):
            return [
                SentimentRecord(
                    excerpt=r.get("excerpt", ""),
                    score=r.get("score", 0.5),
                    label=r.get("label"),
                    confidence=r.get("confidence"),
                )
                for r in raw
            ]
        return None

    @property
    def enrichment(self) -> dict[str, Any]:
        """Convenience accessor for raw enrichment data."""
        return self.header.get("enrichment", self.header.get("enrichments", {}))

    @property
    def highlights(self) -> List[EnrichmentHighlight]:
        """Parsed highlights from enrichment data.

        Returns a list of EnrichmentHighlight objects, each with text
        and optional sentiment score for color-coded display.
        """
        enr = self.enrichment
        raw = enr.get("highlights", [])
        if not raw:
            return []
        result: List[EnrichmentHighlight] = []
        for h in raw:
            if isinstance(h, str):
                result.append(EnrichmentHighlight(text=h))
            elif isinstance(h, dict):
                result.append(EnrichmentHighlight(
                    enrichment_id=h.get("enrichment_id"),
                    text=h.get("text", h.get("excerpt", "")),
                    sentiment=h.get("sentiment"),
                ))
        return result

    @property
    def key_takeaways(self) -> List[str]:
        """Convenience accessor for key takeaways in enrichment."""
        enr = self.enrichment
        return enr.get("key_takeaways", enr.get("key_takeaway", []))


@dataclass
class SMDDocument:
    """A parsed .smd file containing documents and blocks."""

    entities: List[SMDDocument | SMDBlock] = field(default_factory=list)
    """All top-level entities in order of appearance."""

    @property
    def blocks(self) -> List[SMDBlock]:
        """All blocks, recursively flattened."""
        result: List[SMDBlock] = []
        for e in self.entities:
            if isinstance(e, SMDBlock):
                result.append(e)
        return result

    @property
    def documents(self) -> List["SMDDocument"]:
        """All document entities."""
        return [e for e in self.entities if isinstance(e, SMDDocument)]

    def filter_by_tag(self, tag: str) -> List[SMDBlock]:
        """Return all blocks containing a specific tag."""
        return [b for b in self.blocks if tag in b.tags]

    def filter_by_type(self, block_type: str) -> List[SMDBlock]:
        """Return all blocks with a specific type."""
        return [b for b in self.blocks if b.type == block_type]

    def filter_by_tags(self, tags: List[str], mode: str = "any") -> List[SMDBlock]:
        """Return blocks matching a set of tags.

        Args:
            tags: List of tags to match.
            mode: "any" = block has at least one tag; "all" = block has every tag.

        Returns:
            Filtered list of blocks.
        """
        if mode == "any":
            return [b for b in self.blocks if any(t in b.tags for t in tags)]
        elif mode == "all":
            return [b for b in self.blocks if all(t in b.tags for t in tags)]
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'any' or 'all'.")

    def all_tags(self) -> List[str]:
        """Return all unique tags across all blocks, in order of first appearance."""
        seen: set[str] = set()
        result: List[str] = []
        for b in self.blocks:
            for t in b.tags:
                if t not in seen:
                    seen.add(t)
                    result.append(t)
        return result

    def tag_co_occurrence(self) -> dict[str, dict[str, int]]:
        """Build a tag co-occurrence matrix for clustering pipelines.

        Returns:
            Dict mapping each tag -> {other_tag: count}.
        """
        matrix: dict[str, dict[str, int]] = {}
        for block in self.blocks:
            tags = block.tags
            for t1 in tags:
                if t1 not in matrix:
                    matrix[t1] = {}
                for t2 in tags:
                    if t1 != t2:
                        matrix[t1][t2] = matrix[t1].get(t2, 0) + 1
        return matrix
