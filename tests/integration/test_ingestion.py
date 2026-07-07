"""
Integration Tests for IngestionService
======================================
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.database import Base
from app.services.ingestion_service import IngestionService
from app.models.document import Document


@pytest.mark.asyncio
async def test_ingestion_service_flow():
    """Verify raw file parsing, chunking, database mapping and commit."""
    # Use in-memory SQLite for testing database transactions
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Mock components
    mock_vector_store = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed_documents.return_value = [[0.1, 0.2]]
    
    # We use a simple chunker
    from app.core.chunker import TextChunker
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)

    service = IngestionService(
        vector_store=mock_vector_store,
        embedder=mock_embedder,
        chunker=chunker,
    )

    file_content = b"This is a test document text that will be processed by RAG ingestion service."
    
    async with TestSessionLocal() as session:
        doc = await service.ingest_document(
            db=session,
            file_content=file_content,
            filename="hello.txt",
        )

        assert doc.id is not None
        assert doc.filename == "hello.txt"
        assert doc.chunk_count > 0
        assert doc.status == "processed"

        # Verify record exists in database
        db_doc = await session.get(Document, doc.id)
        assert db_doc is not None
        assert db_doc.filename == "hello.txt"

    # Verify mocks were called
    mock_vector_store.add_chunks.assert_called_once()
    mock_embedder.embed_documents.assert_called_once()

    await test_engine.dispose()
