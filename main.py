"""
DocQuery AI — Application Entry Point
=======================================

WHY THIS FILE EXISTS:
    This is the single entry point for the entire application.
    It creates and configures the FastAPI app instance.

    Separation of concerns:
    - main.py → creates the app, registers routes and middleware
    - app/ → contains all the business logic
    - uvicorn → runs the app as a server

HOW TO RUN:
    Development:  uvicorn main:app --reload
    Production:   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    Via Makefile:  make run

WHAT HAPPENS AT STARTUP:
    1. Settings are loaded from .env / env vars
    2. Structured logging is configured
    3. Data directories are created
    4. Middleware is registered (CORS, logging, error handling)
    5. Routes are registered
    6. Startup/shutdown events run (future: init DB, load models)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends

from app.api.dependencies import require_auth
from app.api.middleware import setup_middleware
from app.api.routes import health_router, documents_router, query_router
from app.config import get_settings
from app.config.logging_config import get_logger, setup_logging
from app.db.database import init_db

# ── Initialize logging FIRST (before anything else logs) ─────────────
setup_logging()
logger = get_logger(__name__)


def create_data_directories() -> None:
    """
    Ensure runtime data directories exist.

    These are gitignored but needed at runtime for:
    - uploads/ → raw uploaded files
    - chroma_db/ → ChromaDB persistent storage
    - sqlite/ → SQLite database files
    """
    settings = get_settings()
    directories = [
        settings.uploads_dir,
        Path(settings.chroma_persist_dir),
        Path("./data/sqlite"),
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug("directory_ensured", path=str(directory))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager — runs code at startup and shutdown.

    WHY NOT @app.on_event("startup")?
        That decorator is deprecated in FastAPI. The lifespan context
        manager is the modern replacement. Code before `yield` runs
        at startup, code after `yield` runs at shutdown.
    """
    # ── STARTUP ──────────────────────────────────────────────────────
    settings = get_settings()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        debug=settings.app_debug,
        llm_model=settings.ollama_model,
    )

    # Create data directories
    create_data_directories()

    # Initialize SQLite database and pre-load embedding model
    await init_db()
    try:
        from app.core.embedder import DocumentEmbedder
        DocumentEmbedder()
    except Exception as e:
        logger.error("startup_embedding_model_load_failed", error=str(e))

    logger.info("application_started", message="Ready to accept requests")

    yield  # ← App is running and serving requests

    # ── SHUTDOWN ─────────────────────────────────────────────────────
    logger.info("application_shutting_down")

    # TODO: Phase 2 — Cleanup here:
    #   - Close database connections
    #   - Flush logs


# ── Create the FastAPI Application ───────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-ready RAG API for document Q&A. "
        "Upload documents, ask questions, get answers with citations."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc at /redoc
)

# ── Register Middleware ──────────────────────────────────────────────
setup_middleware(app)

# ── Register Routes ──────────────────────────────────────────────────
# Health routes (public — no auth required)
app.include_router(health_router)

# Add document and query routes (protected by API key authentication)
app.include_router(documents_router, prefix="/api/v1", dependencies=[Depends(require_auth)])
app.include_router(query_router, prefix="/api/v1", dependencies=[Depends(require_auth)])


# ── Direct Run Support ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
    )
