"""
FastAPI Dependencies
====================

WHY THIS EXISTS:
    FastAPI's dependency injection system lets you declare "this route
    needs X" and FastAPI will provide it automatically.

    Dependencies are functions that run BEFORE your route handler.
    They can:
    - Validate auth (see verify_api_key)
    - Provide database sessions
    - Inject service instances

HOW IT WORKS:
    @router.post("/query", dependencies=[Depends(require_auth)])
    async def query(request: QueryRequest):
        ...

    Before query() runs, require_auth() executes first.
    If it raises an exception, the route never executes.
"""

from fastapi import Depends

from app.api.auth import verify_api_key
from app.config import get_settings, Settings


async def require_auth(api_key: str = Depends(verify_api_key)) -> str:
    """
    Dependency that enforces API key authentication.

    Use this on any route that needs auth:
        @router.get("/protected", dependencies=[Depends(require_auth)])

    Returns:
        The validated API key.
    """
    return api_key


def get_app_settings() -> Settings:
    """
    Dependency that provides application settings.

    Usage:
        @router.get("/info")
        async def info(settings: Settings = Depends(get_app_settings)):
            return {"model": settings.ollama_model}
    """
    return get_settings()


# ── Lazy-loaded Service Singletons ───────────────────────────────────
from app.db.vector_store import VectorStore
from app.core.embedder import DocumentEmbedder
from app.core.chunker import TextChunker
from app.core.retriever import DocumentRetriever
from app.core.generator import DocumentGenerator
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.services.query_service import QueryService

_vector_store = None
_embedder = None
_chunker = None
_retriever = None
_generator = None
_doc_service = None
_ingest_service = None
_query_service = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_embedder() -> DocumentEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = DocumentEmbedder()
    return _embedder


def get_chunker() -> TextChunker:
    global _chunker
    if _chunker is None:
        _chunker = TextChunker()
    return _chunker


def get_retriever() -> DocumentRetriever:
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever(get_vector_store(), get_embedder())
    return _retriever


def get_generator() -> DocumentGenerator:
    global _generator
    if _generator is None:
        _generator = DocumentGenerator()
    return _generator


def get_document_service() -> DocumentService:
    global _doc_service
    if _doc_service is None:
        _doc_service = DocumentService(get_vector_store())
    return _doc_service


def get_ingestion_service() -> IngestionService:
    global _ingest_service
    if _ingest_service is None:
        _ingest_service = IngestionService(get_vector_store(), get_embedder(), get_chunker())
    return _ingest_service


def get_query_service() -> QueryService:
    global _query_service
    if _query_service is None:
        _query_service = QueryService(get_retriever(), get_generator())
    return _query_service

