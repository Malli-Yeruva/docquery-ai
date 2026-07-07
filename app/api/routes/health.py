"""
Health Check Routes
===================

Exposes GET /health (liveness) and GET /ready (readiness).
Provides active check verify status of database, ChromaDB, and Ollama server connections.
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_generator, get_vector_store
from app.db.database import get_db_session
from app.api.schemas import HealthResponse, ReadinessResponse
from app.config import get_settings
from app.config.logging_config import get_logger
from app.core.generator import DocumentGenerator
from app.db.vector_store import VectorStore

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns 200 if the API server is running.",
)
async def health_check() -> HealthResponse:
    """
    Lightweight liveness check — just confirms the process is running.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Returns 200 if all dependencies (Ollama, ChromaDB, SQLite) are available.",
)
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    vector_store: VectorStore = Depends(get_vector_store),
    generator: DocumentGenerator = Depends(get_generator),
) -> ReadinessResponse:
    """
    Deep readiness check — verifies SQLite, ChromaDB, and Ollama connections.
    """
    checks = {
        "ollama": False,
        "chroma": False,
        "sqlite": False,
    }

    # 1. Check Ollama LLM Connection
    try:
        checks["ollama"] = generator.ping_ollama()
    except Exception as e:
        logger.error("readiness_ollama_failed", error=str(e))

    # 2. Check ChromaDB Collection Heartbeat
    try:
        checks["chroma"] = vector_store.heartbeat()
    except Exception as e:
        logger.error("readiness_chroma_failed", error=str(e))

    # 3. Check SQLite DB Connection
    try:
        await db.execute(text("SELECT 1"))
        checks["sqlite"] = True
    except Exception as e:
        logger.error("readiness_sqlite_failed", error=str(e))

    all_ready = all(checks.values())

    if not all_ready:
        logger.warning("readiness_check_failed", checks=checks)
        # Set response status code to 503 Service Unavailable if degraded
        response.status_code = 503

    return ReadinessResponse(
        status="ready" if all_ready else "degraded",
        checks=checks,
    )
