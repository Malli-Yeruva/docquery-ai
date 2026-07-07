"""
Document Ingestion Service Module
=================================

Orchestrates the RAG ingestion pipeline: saves raw files, extracts text using DocumentParser,
chunks text using TextChunker, generates vector embeddings using DocumentEmbedder,
inserts embeddings into ChromaDB, and logs metadata in SQLite.
"""

from pathlib import Path
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.config.logging_config import get_logger
from app.core.parser import DocumentParser
from app.core.chunker import TextChunker
from app.core.embedder import DocumentEmbedder
from app.db.vector_store import VectorStore
from app.models.document import Document

logger = get_logger(__name__)
settings = get_settings()


class IngestionService:
    """
    Coordinates ingestion tasks across parsing, chunking, embeddings, and database services.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: DocumentEmbedder,
        chunker: TextChunker,
    ) -> None:
        """
        Inject dependencies for the ingestion pipeline.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.chunker = chunker

    async def ingest_document(
        self,
        db: AsyncSession,
        file_content: bytes,
        filename: str,
    ) -> Document:
        """
        Execute end-to-end ingestion sequence for a single document.

        Args:
            db: Asynchronous SQLite DB session.
            file_content: Uploaded file byte array.
            filename: Original name of the uploaded document.

        Returns:
            The created Document model instance.
        """
        document_id = str(uuid.uuid4())
        logger.info("ingestion_flow_started", document_id=document_id, filename=filename)

        # 1. Save raw file copy to settings.uploads_dir
        # We prepend the unique document_id to filename to prevent name collisions
        saved_filename = f"{document_id}_{filename}"
        file_path = Path(settings.uploads_dir) / saved_filename
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.debug("raw_file_saved", path=str(file_path))
        except Exception as e:
            logger.error("raw_file_save_failed", filename=filename, error=str(e))
            # Continue ingestion even if raw file save fails (in-memory processing works)

        try:
            # 2. Parse text content from file
            parsed_text = DocumentParser.parse(file_content, filename)
            if not parsed_text.strip():
                logger.warning("empty_document_extracted", filename=filename)
                # Keep running, chunker will return empty list and we log chunk_count = 0

            # 3. Segment extracted text into overlapping chunks
            chunks = self.chunker.split_text(parsed_text)
            chunk_count = len(chunks)
            logger.info("document_parsing_and_chunking_completed", chunks=chunk_count)

            # 4. Generate vector embeddings for text chunks
            embeddings = []
            if chunk_count > 0:
                embeddings = self.embedder.embed_documents(chunks)

            # 5. Insert chunks and embeddings into ChromaDB Vector Store
            if chunk_count > 0:
                self.vector_store.add_chunks(
                    document_id=document_id,
                    document_name=filename,
                    chunks=chunks,
                    embeddings=embeddings,
                )
                logger.debug("chromadb_ingestion_completed", document_id=document_id)

            # 6. Save document metadata in SQLite
            doc_metadata = Document(
                id=document_id,
                filename=filename,
                file_type=Path(filename).suffix.lstrip(".").lower() or "unknown",
                file_size_bytes=len(file_content),
                chunk_count=chunk_count,
                status="processed",
            )
            db.add(doc_metadata)
            await db.commit()
            await db.refresh(doc_metadata)

            logger.info(
                "ingestion_flow_completed",
                document_id=document_id,
                filename=filename,
                chunks=chunk_count,
            )
            return doc_metadata

        except Exception as e:
            await db.rollback()
            logger.error("ingestion_flow_failed", document_id=document_id, error=str(e))
            # Clean up raw file if it was saved
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass
            # Clean up any partial vectors uploaded
            try:
                self.vector_store.delete_document(document_id)
            except Exception:
                pass
            raise
