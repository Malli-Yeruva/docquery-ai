"""
Document API Routes
===================

Exposes REST endpoints for uploading documents, listing metadata, and deleting records.
Requires API key authentication.
"""

from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_document_service,
    get_ingestion_service,
    require_auth,
)
from app.api.schemas import DocumentListResponse, DocumentResponse
from app.db.database import get_db_session
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload and ingest a document",
    dependencies=[Depends(require_auth)],
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentResponse:
    """
    Upload a document (PDF, TXT, DOCX, CSV, Excel, HTML) to parse and ingest it into the vector store.
    """
    file_content = await file.read()
    # Execute ingestion service pipeline
    doc = await ingestion_service.ingest_document(
        db=db,
        file_content=file_content,
        filename=file.filename or "unknown.txt",
    )
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        status=doc.status,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
    dependencies=[Depends(require_auth)],
)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """
    Retrieve a paginated list of ingested documents and their metadata.
    """
    items, total = await document_service.list_documents(db=db, skip=skip, limit=limit)
    formatted_docs = [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            status=doc.status,
        )
        for doc in items
    ]
    return DocumentListResponse(documents=formatted_docs, total=total)


@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete a document",
    dependencies=[Depends(require_auth)],
)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
    document_service: DocumentService = Depends(get_document_service),
) -> None:
    """
    Delete document metadata, raw file, and vector embeddings from vector database.
    """
    await document_service.delete_document(db=db, document_id=document_id)
