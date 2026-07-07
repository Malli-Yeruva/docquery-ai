"""
Configuration Management — The Single Source of Truth
=====================================================

WHY THIS EXISTS:
    In production, you NEVER hardcode values like database URLs, API keys, or
    model names. Instead, you externalize them as environment variables.

    This module uses Pydantic Settings to:
    1. Load values from .env file (development)
    2. Override with real env vars (production/Docker)
    3. Validate types at startup (catch misconfig early)
    4. Provide sensible defaults (works out of the box)

HOW IT WORKS:
    Pydantic Settings reads env vars matching the field names.
    Example: `OLLAMA_MODEL=gemma3:4b` → settings.ollama_model = "gemma3:4b"

    We use @lru_cache so the settings object is created ONCE and reused.
    This is a common pattern called the "Singleton via caching" pattern.

USAGE:
    from app.config import get_settings

    settings = get_settings()
    print(settings.ollama_model)  # "gemma3:4b"
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Each field maps to an env var of the same name (case-insensitive).
    Example: `app_name` ← reads from `APP_NAME` env var.
    """

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "DocQuery AI"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── API Authentication ───────────────────────────────────────────────
    # In production, this MUST be set via env var, not the default
    api_key: str = "your-secret-api-key-change-me"

    # ── Ollama (LLM) ────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: int = 120  # seconds

    # ── Embedding Model ─────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ── ChromaDB (Vector Store) ──────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "documents"

    # ── SQLite (Metadata DB) ─────────────────────────────────────────────
    sqlite_url: str = "sqlite+aiosqlite:///./data/sqlite/docquery.db"

    # ── Document Processing ──────────────────────────────────────────────
    chunk_size: int = 1000       # characters per chunk
    chunk_overlap: int = 200     # overlap between adjacent chunks
    max_file_size_mb: int = 50   # max upload size in MB

    # ── Retrieval ────────────────────────────────────────────────────────
    top_k: int = 5                     # chunks to retrieve
    similarity_threshold: float = 0.0  # minimum cosine similarity

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # ── Computed Properties ──────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB limit to bytes for file validation."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def data_dir(self) -> Path:
        """Base data directory."""
        return Path("./data")

    @property
    def uploads_dir(self) -> Path:
        """Directory for uploaded files."""
        return self.data_dir / "uploads"

    # ── Pydantic Settings Config ─────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,       # APP_NAME = app_name
        extra="ignore",            # Don't error on unknown env vars
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Using @lru_cache ensures we create the Settings object only ONCE,
    even if get_settings() is called from 50 different places.
    This avoids re-reading the .env file on every call.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
