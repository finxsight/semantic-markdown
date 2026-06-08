"""
SMD Indexer — chunk SMD documents by Q&A threads, tags, and topic clusters.

Builds inverted indices for fast retrieval and discovers emergent topic
structures from tag co-occurrence patterns.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .models import SMDBlock, SMDDocument, EnrichmentHighlight


class QAPair:
    """A Q&A pair extracted from a transcript block."""

    def __init__(self, block: SMDBlock):
        self.block = block
        self.question: Optional[str] = None
        self.answer: Optional[str] = None
        self._parse_qa()

    def _parse_qa(self):
        """Split body into question and answer parts by speaker markers."""
        body = self.block.body_text
        # Split on **Speaker:** pattern
        parts = []
        current = ""
        for line in body.split("\n"):
            if line.startswith("**") and ":**" in line and current.strip():
                parts.append(current.strip())
                current = line + "\n"
            else:
                current += line + "\n"
        if current.strip():
            parts.append(current.strip())

        if len(parts) >= 2:
            self.question = parts[0]
            self.answer = "\n".join(parts[1:])
        elif len(parts) == 1:
            self.question = parts[0]
        else:
            self.question = body


class SMDIndexer:
    """Index an SMD document for retrieval and clustering.

    Usage:
        indexer = SMDIndexer(doc)
        threads = indexer.qa_threads()
        topics = indexer.topic_clusters()
        hits = indexer.search(["AI", "capex"])
    """

    def __init__(self, doc: SMDDocument):
        self._doc = doc
        self._tag_index: Dict[str, List[str]] = {}
        self._build_tag_index()

    def _build_tag_index(self):
        """Build inverted index: tag -> list of block_ids."""
        self._tag_index = defaultdict(list)
        for b in self._doc.blocks:
            for t in b.tags:
                self._tag_index[t].append(b.block_id)

    @property
    def doc(self) -> SMDDocument:
        return self._doc

    def qa_threads(self) -> List[QAPair]:
        """Extract Q&A pairs from blocks of type 'qa'.

        Returns a list of QAPair objects with parsed question/answer.
        """
        qa_blocks = self._doc.filter_by_type("qa")
        return [QAPair(b) for b in qa_blocks]

    def by_tag(self, tag: str) -> List[SMDBlock]:
        """All blocks containing a specific tag."""
        block_ids = self._tag_index.get(tag, [])
        return [b for b in self._doc.blocks if b.block_id in block_ids]

    def search(self, tags: List[str], mode: str = "any") -> List[SMDBlock]:
        """Find blocks matching a set of tags.

        Args:
            tags: Tags to search for.
            mode: "any" (default) or "all".

        Returns:
            Matching blocks sorted by position.
        """
        return self._doc.filter_by_tags(tags, mode)

    def tag_inverted_index(self) -> Dict[str, List[str]]:
        """Return the inverted index: tag -> list of block_ids."""
        return dict(self._tag_index)

    def topic_clusters(self, min_co_occurrence: int = 1) -> List[Dict[str, Any]]:
        """Discover topic clusters from tag co-occurrence.

        Uses the tag co-occurrence matrix to find groups of tags
        that frequently appear together.

        Args:
            min_co_occurrence: Minimum co-occurrence count to consider.

        Returns:
            List of cluster dicts with 'tags' and 'blocks' keys.
        """
        matrix = self._doc.tag_co_occurrence()
        clusters: List[Dict[str, Any]] = []
        visited: set[str] = set()

        # Simple connected-component clustering on co-occurrence graph
        for tag, neighbors in matrix.items():
            if tag in visited:
                continue
            cluster_tags = {tag}
            to_visit = [t for t, count in neighbors.items() if count >= min_co_occurrence]
            while to_visit:
                t = to_visit.pop()
                if t in cluster_tags:
                    continue
                cluster_tags.add(t)
                visited.add(t)
                if t in matrix:
                    for nt, count in matrix[t].items():
                        if count >= min_co_occurrence and nt not in cluster_tags:
                            to_visit.append(nt)

            visited.add(tag)

            if len(cluster_tags) >= 2:
                block_ids = set()
                for ct in cluster_tags:
                    block_ids.update(self._tag_index.get(ct, []))
                clusters.append({
                    "tags": sorted(cluster_tags),
                    "blocks": sorted(block_ids),
                })

        return clusters

    def chunk_by_position(self, chunk_size: int = 3) -> List[List[SMDBlock]]:
        """Split blocks into fixed-size chunks by position.

        Args:
            chunk_size: Number of blocks per chunk.

        Returns:
            List of block groups.
        """
        blocks = self._doc.blocks
        return [blocks[i:i + chunk_size] for i in range(0, len(blocks), chunk_size)]
