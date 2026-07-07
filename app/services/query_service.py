"""
Query Service Module
====================

Orchestrates RAG flow: embeds user query, runs semantic search retrieve,
passes context to Ollama generator, logs history, and reports latency performance metrics.
"""

import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.config.logging_config import get_logger
from app.core.generator import DocumentGenerator
from app.core.retriever import DocumentRetriever
from app.models.query_log import QueryLog

logger = get_logger(__name__)
settings = get_settings()


class QueryService:
    """
    Combines retrieval and generation to process natural language questions.
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        generator: DocumentGenerator,
    ) -> None:
        """
        Inject retriever and generator dependencies.
        """
        self.retriever = retriever
        self.generator = generator

    async def process_query(
        self,
        db: AsyncSession,
        question: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
        similarity_threshold: float | None = None,
    ) -> dict:
        """
        Execute RAG process query flow and log transactions.

        Args:
            db: Async SQLite session.
            question: Text query from user.
            top_k: Max chunks to retrieve.
            document_ids: Restrict search scope to these document IDs.
            similarity_threshold: Minimum cosine similarity filter.

        Returns:
            Dictionary matching the QueryResponse API structure.
        """
        start_time = time.perf_counter()
        logger.info("query_processing_started", question=question, filter_docs=document_ids)

        # 1. Retrieve semantic matches from ChromaDB
        retrieved_chunks = self.retriever.retrieve(
            query_text=question,
            top_k=top_k,
            document_ids=document_ids,
            similarity_threshold=similarity_threshold,
        )

        # 2. Invoke Ollama model to generate answer using retrieved contexts
        try:
            answer = await self.generator.generate_answer(
                question=question,
                chunks=retrieved_chunks,
            )
        except Exception as e:
            logger.error("query_generation_failed", error=str(e))
            answer = (
                "An error occurred while generating the answer. Please check if "
                "the local Ollama instance is running and healthy."
            )

        duration_ms = (time.perf_counter() - start_time) * 1000
        query_time_ms = round(duration_ms, 2)

        # Map retrieved chunks to source dict structure
        # SourceChunk format: document_id, document_name, chunk_index, content, similarity_score
        sources = [
            {
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "similarity_score": chunk["similarity_score"],
            }
            for chunk in retrieved_chunks
        ]

        # 3. Log query audit transaction in SQLite database
        query_log = QueryLog(
            question=question,
            answer=answer,
            sources=sources,
            model=settings.ollama_model,
            query_time_ms=query_time_ms,
        )

        try:
            db.add(query_log)
            await db.commit()
            logger.info("query_transaction_logged", latency_ms=query_time_ms)
        except Exception as e:
            await db.rollback()
            logger.error("query_log_write_failed", error=str(e))
            # Proceed to return result to user even if audit logger fails

        return {
            "answer": answer,
            "sources": sources,
            "model": settings.ollama_model,
            "query_time_ms": query_time_ms,
        }
