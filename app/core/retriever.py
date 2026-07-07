"""
Semantic Document Retriever Module
==================================

Retrieves relevant document text chunks from ChromaDB using vector similarity search,
filtering results by cosine similarity threshold and document restriction limits.
"""

from app.config import get_settings
from app.config.logging_config import get_logger
from app.core.embedder import DocumentEmbedder
from app.db.vector_store import VectorStore

logger = get_logger(__name__)
settings = get_settings()


class DocumentRetriever:
    """
    Orchestrates vector embedding of queries and searching ChromaDB.
    """

    def __init__(self, vector_store: VectorStore, embedder: DocumentEmbedder) -> None:
        """
        Initialize the retriever with vector store and embedder dependencies.
        """
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(
        self,
        query_text: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
        similarity_threshold: float | None = None,
    ) -> list[dict]:
        """
        Retrieve document chunks semantically matching the query.

        Args:
            query_text: The user's search query / question.
            top_k: Max chunks to return (overrides default config top_k).
            document_ids: List of specific document IDs to search within (None searches all).
            similarity_threshold: Minimum similarity threshold (overrides default config).

        Returns:
            List of matching chunk dictionaries.
        """
        k = top_k or settings.top_k
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.similarity_threshold
        )

        logger.info(
            "retrieval_started",
            query=query_text,
            top_k=k,
            document_ids=document_ids,
            threshold=threshold,
        )

        # 1. Generate embedding for query
        query_vector = self.embedder.embed_text(query_text)

        # 2. Search in ChromaDB
        raw_results = self.vector_store.search(
            query_embedding=query_vector,
            top_k=k,
            document_ids=document_ids,
        )

        # 3. Filter by similarity threshold
        filtered_results = [
            chunk for chunk in raw_results if chunk["similarity_score"] >= threshold
        ]

        logger.info(
            "retrieval_completed",
            candidates_found=len(raw_results),
            filtered_count=len(filtered_results),
        )

        return filtered_results
