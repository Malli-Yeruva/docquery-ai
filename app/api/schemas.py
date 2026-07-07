"""
Pydantic Schemas — Request/Response Models
==========================================

WHY THIS EXISTS:
    FastAPI uses Pydantic models to:
    1. Validate incoming request data (reject bad input early)
    2. Serialize outgoing responses (consistent JSON structure)
    3. Generate OpenAPI docs automatically (try /docs in browser)

    These are NOT database models (those live in app/models/).
    These define what the API accepts and returns.

NAMING CONVENTION:
    - *Request  → incoming data from the client
    - *Response → outgoing data to the client
    - *Base     → shared fields between request and response
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """Response for GET /health endpoint."""
    status: str = Field(default="healthy", examples=["healthy"])
    version: str = Field(examples=["0.1.0"])
    environment: str = Field(examples=["development"])


class ReadinessResponse(BaseModel):
    """Response for GET /ready — checks all dependencies."""
    status: str = Field(examples=["ready"])
    checks: dict[str, bool] = Field(
        examples=[{"ollama": True, "chroma": True, "sqlite": True}]
    )


# ═══════════════════════════════════════════════════════════════════════════
# Document Operations
# ═══════════════════════════════════════════════════════════════════════════

class DocumentResponse(BaseModel):
    """Response after uploading or retrieving a document."""
    id: str = Field(description="Unique document identifier")
    filename: str = Field(examples=["report.pdf"])
    file_type: str = Field(examples=["pdf"])
    file_size_bytes: int = Field(examples=[1048576])
    chunk_count: int = Field(description="Number of chunks created", examples=[12])
    created_at: datetime
    status: str = Field(default="processed", examples=["processed"])


class DocumentListResponse(BaseModel):
    """Response for GET /documents — paginated list."""
    documents: list[DocumentResponse]
    total: int = Field(description="Total number of documents")


# ═══════════════════════════════════════════════════════════════════════════
# Query (RAG)
# ═══════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    """Request body for POST /query."""
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="The question to ask about your documents",
        examples=["What are the key findings in the Q3 report?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of chunks to retrieve (overrides default)",
    )
    document_ids: list[str] | None = Field(
        default=None,
        description="Filter to specific documents (None = search all)",
    )
    similarity_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity matching score (overrides default)",
    )



class SourceChunk(BaseModel):
    """A single retrieved chunk used as context for the answer."""
    document_id: str
    document_name: str = Field(examples=["report.pdf"])
    chunk_index: int = Field(description="Position of chunk in document")
    content: str = Field(description="The actual text chunk")
    similarity_score: float = Field(
        ge=0.0, le=1.0,
        description="Cosine similarity to the query",
        examples=[0.87],
    )


class QueryResponse(BaseModel):
    """Response for POST /query — the RAG answer with sources."""
    answer: str = Field(description="Generated answer from the LLM")
    sources: list[SourceChunk] = Field(
        description="Retrieved chunks that informed the answer"
    )
    model: str = Field(
        description="LLM model used",
        examples=["gemma3:4b"],
    )
    query_time_ms: float = Field(
        description="Total processing time in milliseconds",
        examples=[1523.4],
    )


# ═══════════════════════════════════════════════════════════════════════════
# Error Response
# ═══════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    detail: str | None = Field(default=None, description="Additional detail")
