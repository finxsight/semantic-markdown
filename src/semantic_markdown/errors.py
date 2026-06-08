"""Custom exceptions for Semantic Markdown parsing."""


from typing import Optional


class ParseError(Exception):
    """Raised when an SMD file cannot be parsed correctly."""

    def __init__(self, message: str, line: Optional[int] = None):
        self.line = line
        prefix = f"Line {line}: " if line is not None else ""
        super().__init__(f"{prefix}{message}")


class DuplicateBlockIdError(ParseError):
    """Raised when two blocks in the same document share a block_id."""

    def __init__(self, block_id: str, line: Optional[int] = None):
        self.block_id = block_id
        super().__init__(f"Duplicate block_id: '{block_id}'", line=line)


class MalformedJsonError(ParseError):
    """Raised when a JSON header cannot be parsed."""

    def __init__(self, raw: str, inner: str, line: Optional[int] = None):
        super().__init__(
            f"Malformed JSON header: {inner}\n  Raw header: {raw[:120]}",
            line=line,
        )


class MissingSeparatorError(ParseError):
    """Raised when a @block or @document has no --- separator."""

    def __init__(self, entity_type: str, block_id: Optional[str] = None, line: Optional[int] = None):
        suffix = f" ({block_id=})" if block_id else ""
        super().__init__(
            f"@{entity_type} missing '---' separator{suffix}",
            line=line,
        )
