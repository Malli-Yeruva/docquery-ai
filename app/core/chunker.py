"""
Recursive Text Chunker Module
==============================

Splits long documents into smaller, overlapping text chunks to ensure context window
limits of embedding/LLM models are not exceeded, while retaining logical structure.
"""

from app.config import get_settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TextChunker:
    """
    Recursive character text splitter designed to divide text into digestible chunks
    using semantic separators (paragraphs, newlines, sentences, words).
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """
        Initialize chunker with configurable limits.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Shared overlap size between adjacent chunks.
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Enforce that overlap is less than chunk size
        if self.chunk_overlap >= self.chunk_size:
            logger.warning(
                "chunker_overlap_too_large",
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )
            self.chunk_overlap = int(self.chunk_size * 0.2)

        # Logical separators ordered from highest structure to lowest structure
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """
        Splits input text recursively by separators.

        Args:
            text: Large raw text string to split.

        Returns:
            List of text chunks.
        """
        if not text.strip():
            return []

        # Recursively split the text using separators list
        split_docs = self._recursive_split(text, self.separators)

        # Merge segments into reasonable size chunks with overlap
        chunks = self._merge_splits(split_docs)

        logger.debug(
            "text_chunked",
            input_length=len(text),
            chunk_count=len(chunks),
            avg_chunk_length=round(sum(len(c) for c in chunks) / len(chunks), 1) if chunks else 0,
        )

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """
        Recursively split text by subsequent separators if too large.
        """
        # If the text is already smaller than chunk size, no more splitting needed
        if len(text) <= self.chunk_size:
            return [text]

        # Get next separator
        if not separators:
            # No separators left, force hard slice
            chunks = []
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunks.append(text[i : i + self.chunk_size])
            return chunks

        separator = separators[0]
        next_separators = separators[1:]

        # Split text by current separator
        if separator == "":
            # Character-by-character split
            splits = list(text)
        else:
            splits = text.split(separator)

        # Process each split segment
        result_splits = []
        for i, split in enumerate(splits):
            # If we split by separator (like \n), we want to append it back unless it is the last split
            segment = split
            if separator != "" and i < len(splits) - 1:
                segment += separator

            if len(segment) <= self.chunk_size:
                result_splits.append(segment)
            else:
                # Recurse with remaining separators on this segment
                result_splits.extend(self._recursive_split(segment, next_separators))

        return result_splits

    def _merge_splits(self, splits: list[str]) -> list[str]:
        """
        Merge small text splits into chunks of target size, ensuring the overlap.
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_len = len(split)

            # If a single split is larger than chunk_size, we just add it by itself
            if split_len > self.chunk_size:
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                    current_chunk = []
                    current_length = 0
                chunks.append(split.strip())
                continue

            # Check if adding this split exceeds our chunk_size limit
            if current_length + split_len > self.chunk_size:
                # Store the current complete chunk
                chunks.append("".join(current_chunk).strip())

                # Roll back current chunk to accommodate overlap
                overlap_chunk = []
                overlap_length = 0

                # Work backwards to collect splits for the overlap
                for segment in reversed(current_chunk):
                    if overlap_length + len(segment) > self.chunk_overlap:
                        break
                    overlap_chunk.insert(0, segment)
                    overlap_length += len(segment)

                current_chunk = overlap_chunk
                current_length = overlap_length

            current_chunk.append(split)
            current_length += split_len

        # Append last remaining chunk
        if current_chunk:
            chunks.append("".join(current_chunk).strip())

        # Clean empty chunks
        return [c for c in chunks if c]
