"""
Database Session Management
==========================

Provides the SQLAlchemy database engine, session factory, base model class,
and FastAPI dependency for accessing database sessions asynchronously.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create async database engine
# We use SQLite with the aiosqlite driver
engine = create_async_engine(
    settings.sqlite_url,
    echo=settings.app_debug,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base class for models
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an asynchronous database session.
    Automatically closes the session after the request finishes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("database_session_error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize SQLite database tables defined by SQLAlchemy models.
    Should be run once at application startup.
    """
    logger.info("database_init_started")
    try:
        async with engine.begin() as conn:
            # We import all models here so that they are registered on the Base metadata
            from app.models.document import Document  # noqa: F401
            from app.models.query_log import QueryLog  # noqa: F401

            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_init_completed")
    except Exception as e:
        logger.critical("database_init_failed", error=str(e))
        raise
