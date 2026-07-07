"""
Structured Logging Configuration
=================================

WHY THIS EXISTS:
    print() statements are the #1 anti-pattern in production code.
    They can't be filtered, searched, or parsed by log aggregators.

    Instead, we use structured logging (structlog) which outputs:
    - JSON format in production (machine-parseable, works with ELK/Datadog)
    - Pretty console format in development (human-readable with colors)

HOW IT WORKS:
    structlog wraps Python's standard logging module. Every log entry is a
    dict of key-value pairs, making it easy to search and filter:

    {"event": "query_processed", "user": "abc", "latency_ms": 42, "chunks": 5}

    vs. a traditional log:
    "INFO: Processed query for user abc in 42ms, found 5 chunks"

    The first is machine-parseable. The second requires regex to extract data.

USAGE:
    from app.config.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("document_ingested", filename="report.pdf", chunks=12)
"""

import logging
import sys

import structlog

from app.config.settings import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the entire application.

    Call this ONCE at application startup (in main.py).
    After this, all loggers created via get_logger() will use
    the configured format (JSON or console).
    """
    settings = get_settings()

    # ── Shared processors (run on every log entry) ───────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,     # Add context from contextvars
        structlog.stdlib.add_logger_name,             # Add logger name
        structlog.stdlib.add_log_level,               # Add level (info, error, etc.)
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 timestamps
        structlog.processors.StackInfoRenderer(),     # Stack traces when requested
        structlog.processors.UnicodeDecoder(),         # Handle unicode
    ]

    if settings.log_format == "json":
        # ── Production: JSON output ─────────────────────────────────
        # Machine-parseable, one JSON object per line
        renderer = structlog.processors.JSONRenderer()
    else:
        # ── Development: Pretty console output ──────────────────────
        # Colored, human-readable, easy to scan
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # ── Configure structlog ──────────────────────────────────────────
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── Configure Python's standard logging ──────────────────────────
    # This ensures third-party libraries (uvicorn, sqlalchemy) also
    # output in our structured format
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()     # Remove default handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structured logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("something_happened", key="value", count=42)
    """
    return structlog.get_logger(name)
