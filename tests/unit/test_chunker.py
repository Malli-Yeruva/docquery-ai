"""
Unit Tests for TextChunker
==========================
"""

from app.core.chunker import TextChunker


def test_chunker_basic_split():
    """Verify text splitter creates chunks matching parameters."""
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = "This is a very long string that should get split into multiple small segments."
    chunks = chunker.split_text(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 50


def test_chunker_respects_separators():
    """Splitting should respect logical paragraph/sentence endings."""
    chunker = TextChunker(chunk_size=30, chunk_overlap=5)
    text = "Paragraph 1 content.\n\nParagraph 2 content has some other text."
    chunks = chunker.split_text(text)

    assert len(chunks) >= 2
    assert "Paragraph 1 content." in chunks[0]
