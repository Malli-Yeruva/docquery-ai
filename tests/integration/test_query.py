"""
Integration Tests for QueryService
==================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.database import Base
from app.services.query_service import QueryService
from app.models.query_log import QueryLog


@pytest.mark.asyncio
async def test_query_service_flow():
    """Verify semantic search query flow logs transactions to SQLite."""
    # Use in-memory SQLite for testing
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Mock components
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        {
            "document_id": "doc123",
            "document_name": "test.txt",
            "chunk_index": 0,
            "content": "relevant chunk content",
            "similarity_score": 0.85,
        }
    ]

    mock_generator = AsyncMock()
    mock_generator.generate_answer.return_value = "The generated answer from LLM."

    service = QueryService(
        retriever=mock_retriever,
        generator=mock_generator,
    )

    async with TestSessionLocal() as session:
        result = await service.process_query(
            db=session,
            question="What is the test answer?",
        )

        assert result["answer"] == "The generated answer from LLM."
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_id"] == "doc123"

        # Verify query log exists in database
        from sqlalchemy import select
        stmt = select(QueryLog)
        db_result = await session.execute(stmt)
        log = db_result.scalar_one_or_none()
        
        assert log is not None
        assert log.question == "What is the test answer?"
        assert log.answer == "The generated answer from LLM."
        assert log.sources[0]["document_id"] == "doc123"

    await test_engine.dispose()
