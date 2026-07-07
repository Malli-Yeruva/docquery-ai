"""
Sentence Embeddings Generator Module
====================================

Generates dense vector representations of text segments using the local SentenceTransformer model.
Loads and caches the model locally (defaults to all-MiniLM-L6-v2).
"""

from typing import Union
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocumentEmbedder:
    """
    Sentence-Transformers wrapper to generate vector embeddings.
    """

    _model: SentenceTransformer | None = None

    def __init__(self) -> None:
        """
        Initialize the embedding model client. Loads model lazily.
        """
        self._init_model()

    @classmethod
    def _init_model(cls) -> None:
        """Load the model into class memory if not already loaded (Singleton pattern)."""
        if cls._model is None:
            logger.info("loading_embedding_model", model_name=settings.embedding_model)
            try:
                cls._model = SentenceTransformer(settings.embedding_model)
                logger.info("embedding_model_loaded", dimension=settings.embedding_dimension)
            except Exception as e:
                logger.critical("embedding_model_load_failed", error=str(e))
                raise

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text segment.

        Args:
            text: A text snippet.

        Returns:
            A list of floats representing the embedding vector.
        """
        if not self._model:
            self._init_model()
        # model.encode returns a numpy array, we cast it to list[float]
        vector = self._model.encode(text, convert_to_numpy=True)  # type: ignore
        return vector.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embedding vectors for a batch of text segments.

        Args:
            texts: A list of text chunks.

        Returns:
            A list of lists of floats.
        """
        if not texts:
            return []
        if not self._model:
            self._init_model()
        vectors = self._model.encode(texts, convert_to_numpy=True)  # type: ignore
        return vectors.tolist()
