"""
Ollama LLM Generation Module
=============================

Interfaces with the local Ollama service to generate answers using the local LLM model
(defaults to gemma3:4b). Formats RAG context prompts with source citations.
"""

import httpx
import ollama

from app.config import get_settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocumentGenerator:
    """
    Interfaces with the local Ollama LLM service to answer questions.
    """

    def __init__(self) -> None:
        """
        Initialize the Ollama client wrapper.
        """
        self.client = ollama.Client(
            host=settings.ollama_base_url,
            timeout=settings.ollama_timeout,
        )
        self.async_client = ollama.AsyncClient(
            host=settings.ollama_base_url,
            timeout=settings.ollama_timeout,
        )

    def ping_ollama(self) -> bool:
        """
        Check if Ollama server is running and accessible.
        """
        try:
            # We can use standard HTTP client or list models to see if it pings
            self.client.list()
            return True
        except Exception as e:
            logger.error("ollama_ping_failed", error=str(e))
            return False

    async def generate_answer(self, question: str, chunks: list[dict]) -> str:
        """
        Query Ollama asynchronously to generate an answer based on RAG context chunks.

        Args:
            question: User's query.
            chunks: Relevant document context chunks.

        Returns:
            The generated response string.
        """
        prompt = self._build_prompt(question, chunks)

        logger.info(
            "llm_generation_started",
            model=settings.ollama_model,
            context_chunk_count=len(chunks),
        )

        try:
            response = await self.async_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={
                    "temperature": 0.2,  # Low temperature for factual RAG answers
                    "top_p": 0.9,
                },
            )
            answer = response.get("response", "").strip()
            logger.info("llm_generation_completed", model=settings.ollama_model)
            return answer
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            raise

    def _build_prompt(self, question: str, chunks: list[dict]) -> str:
        """
        Synthesize prompt combining the RAG system directives, text context chunks, and user query.
        """
        context_str = ""
        if not chunks:
            context_str = "No relevant context documents found in the database."
        else:
            context_blocks = []
            for i, chunk in enumerate(chunks, 1):
                doc_name = chunk.get("document_name", "Unknown File")
                idx = chunk.get("chunk_index", 0)
                content = chunk.get("content", "").strip()
                block = f"[{i}] File: {doc_name} (Chunk #{idx})\nContent: {content}"
                context_blocks.append(block)
            context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are an advanced AI assistant called DocQuery AI.\n"
            "Use the provided context blocks to answer the user's question truthfully and factually.\n"
            "If the context does not contain the answer, say: 'I don't have enough information in "
            "the uploaded documents to answer this question.' Do not make up facts or extrapolate.\n"
            "When referencing facts from the context, cite the corresponding file number (e.g., [1], [2], etc.) in your answer.\n"
            "Keep your response structured, concise, and clear.\n"
        )

        prompt = (
            f"{system_instruction}\n"
            f"--- Context ---\n"
            f"{context_str}\n"
            f"-----------------\n\n"
            f"Question: {question}\n"
            f"Answer: "
        )

        return prompt
