"""
Query (RAG) API Route
=====================

Exposes endpoints for asking questions against ingested documents.
Requires API key authentication.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_query_service, require_auth
from app.api.schemas import QueryRequest, QueryResponse
from app.db.database import get_db_session
from app.services.query_service import QueryService

router = APIRouter(prefix="/query", tags=["Query"])


@router.post(
    "",
    response_model=QueryResponse,
    summary="Ask a question against your documents",
    dependencies=[Depends(require_auth)],
)
async def query_documents(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db_session),
    query_service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    """
    RAG Search and Generation:
    1. Embeds the user question.
    2. Searches ChromaDB for matching text chunks.
    3. Prompts local Gemma3:4b LLM using context documents.
    4. Records logs and latency metrics.
    5. Returns answer alongside source context citations.
    """
    result = await query_service.process_query(
        db=db,
        question=payload.question,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
        similarity_threshold=payload.similarity_threshold,
    )
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        model=result["model"],
        query_time_ms=result["query_time_ms"],
    )


@router.get(
    "/logs",
    summary="Get recent query logs",
    dependencies=[Depends(require_auth)],
)
async def get_query_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """
    Retrieve historical query records and performance metrics.
    """
    from sqlalchemy import select
    from app.models.query_log import QueryLog

    stmt = select(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "question": log.question,
            "answer": log.answer,
            "sources": log.sources,
            "model": log.model,
            "query_time_ms": log.query_time_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

