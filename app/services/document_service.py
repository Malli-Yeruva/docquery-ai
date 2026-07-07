"""
Document Service Module
=======================

Implements the business logic layer for document management, including metadata CRUD,
retrieval of uploaded lists, and cascading removal from SQLite, filesystem, and ChromaDB.
"""

from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.db.vector_store import VectorStore
from app.exceptions import DocumentNotFoundError
from app.models.document import Document

logger = get_logger(__name__)


class DocumentService:
    """
    Handles CRUD operations on documents, linking SQLite, filesystem, and vector storage.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """
        Initialize the service with a VectorStore instance.
        """
        self.vector_store = vector_store

    async def get_document(self, db: AsyncSession, document_id: str) -> Document:
        """
        Get document metadata by ID.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            logger.warning("document_not_found", document_id=document_id)
            raise DocumentNotFoundError(document_id)

        return document

    async def list_documents(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[list[Document], int]:
        """
        Get paginated list of document metadata entries along with total count.
        """
        # Count total
        count_stmt = select(func.count()).select_from(Document)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Query items
        query_stmt = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        items_result = await db.execute(query_stmt)
        items = list(items_result.scalars().all())

        logger.info("list_documents_retrieved", count=len(items), total=total)
        return items, total

    async def delete_document(self, db: AsyncSession, document_id: str) -> None:
        """
        Cascade delete a document from SQLite, filesystem storage, and vector index.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        # 1. Fetch document metadata or raise 404
        document = await self.get_document(db, document_id)

        logger.info("document_deletion_started", document_id=document_id, filename=document.filename)

        # 2. Delete vectors from ChromaDB
        try:
            self.vector_store.delete_document(document_id)
            logger.debug("document_vectors_deleted", document_id=document_id)
        except Exception as e:
            logger.error("chromadb_deletion_error", document_id=document_id, error=str(e))
            # Continue deletion sequence even if vector store fails

        # 3. Delete raw file from local storage if it exists
        # We store files in data/uploads using document_id as prefix or name
        from app.config import get_settings
        settings = get_settings()
        file_path = Path(settings.uploads_dir) / f"{document_id}_{document.filename}"
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug("document_raw_file_deleted", path=str(file_path))
        except Exception as e:
            logger.error("raw_file_deletion_error", path=str(file_path), error=str(e))

        # 4. Delete DB metadata record
        try:
            await db.delete(document)
            await db.commit()
            logger.info("document_metadata_deleted", document_id=document_id)
        except Exception as e:
            await db.rollback()
            logger.error("database_deletion_error", document_id=document_id, error=str(e))
            raise
