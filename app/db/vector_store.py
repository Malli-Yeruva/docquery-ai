"""
ChromaDB Vector Store Client Wrapper
====================================

Manages connections, collections, insertion, semantic search, and deletion
of document chunk embeddings using ChromaDB.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorStore:
    """
    Handles lower-level operations on the local ChromaDB database.
    """

    def __init__(self) -> None:
        """
        Initialize persistent ChromaDB client and retrieve/create the default collection.
        """
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # We specify cosine similarity space ("cosine") for distance matching
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug(
            "chroma_client_initialized",
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection_name,
        )

    def add_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """
        Add document text chunks and their embeddings into ChromaDB.

        Args:
            document_id: The SQLite ID of the document.
            document_name: Raw filename.
            chunks: List of text chunk strings.
            embeddings: List of embedding vectors matching chunks.
        """
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        logger.debug(
            "chroma_adding_chunks",
            document_id=document_id,
            chunk_count=len(chunks),
        )

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for similarity vectors matching the query.

        Args:
            query_embedding: The vector embedding of the user's question.
            top_k: Number of nearest matches to return.
            document_ids: Optional document filters.

        Returns:
            A list of dictionary objects holding chunk details, text, and cosine score.
        """
        where_filter = None
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            elif len(document_ids) > 1:
                where_filter = {"document_id": {"$in": document_ids}}

        logger.debug(
            "chroma_searching",
            top_k=top_k,
            filter_docs=document_ids,
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        # Chroma returns results nested inside lists
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        formatted_results = []
        ids = results["ids"][0]
        distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
        metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
        documents = results["documents"][0] if results["documents"] else [""] * len(ids)

        for i in range(len(ids)):
            # Chroma DB 'cosine' distance returns cosine distance (1 - similarity_score)
            # We want to convert distance to similarity: similarity = 1 - distance
            distance = distances[i]
            similarity = 1.0 - distance

            formatted_results.append(
                {
                    "id": ids[i],
                    "document_id": metadatas[i].get("document_id", ""),
                    "document_name": metadatas[i].get("document_name", ""),
                    "chunk_index": metadatas[i].get("chunk_index", 0),
                    "content": documents[i],
                    "similarity_score": max(0.0, min(1.0, similarity)),
                }
            )

        # Sort by similarity descending
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return formatted_results

    def delete_document(self, document_id: str) -> None:
        """
        Delete all vector entries associated with a document ID.
        """
        logger.info("chroma_deleting_document", document_id=document_id)
        self.collection.delete(where={"document_id": document_id})

    def heartbeat(self) -> bool:
        """
        Check connectivity/readiness of ChromaDB.
        """
        try:
            # heartbeat returns milliseconds epoch or errors
            hb = self.client.heartbeat()
            return hb > 0
        except Exception as e:
            logger.error("chroma_heartbeat_failed", error=str(e))
            return False
