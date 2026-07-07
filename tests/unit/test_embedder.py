"""
Unit Tests for DocumentEmbedder
===============================
"""

from unittest.mock import MagicMock, patch
from app.core.embedder import DocumentEmbedder


@patch("app.core.embedder.SentenceTransformer")
def test_embedder_mocked(mock_transformer_cls):
    """Test generating embeddings with a mocked SentenceTransformer model."""
    mock_instance = MagicMock()
    # Mock return values for encode (single encoding and batch encoding)
    mock_instance.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    mock_transformer_cls.return_value = mock_instance

    embedder = DocumentEmbedder()

    # Verify single embedding
    vec = embedder.embed_text("hello text")
    assert vec == [0.1, 0.2, 0.3]
    mock_instance.encode.assert_called_with("hello text", convert_to_numpy=True)

    # Verify batch embedding
    mock_instance.encode.return_value = MagicMock(tolist=lambda: [[0.1], [0.2]])
    vecs = embedder.embed_documents(["doc1", "doc2"])
    assert vecs == [[0.1], [0.2]]
    mock_instance.encode.assert_called_with(["doc1", "doc2"], convert_to_numpy=True)
