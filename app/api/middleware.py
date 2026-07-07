"""
Middleware — Cross-Cutting Concerns
=====================================

WHY THIS EXISTS:
    Middleware runs on EVERY request, before and after the route handler.
    It's perfect for cross-cutting concerns that apply globally:

    1. CORS — allow frontend (different origin) to call the API
    2. Request logging — log every request with timing
    3. Error handling — catch exceptions and return clean JSON errors
    4. API Key check — authenticate before reaching any route

    Without middleware, you'd duplicate this logic in every route.

HOW IT WORKS:
    Request → CORS → Logging → Error Handler → Auth → Route Handler
                                                          ↓
    Response ← CORS ← Logging ← Error Handler ← ← ← Response
"""

import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.logging_config import get_logger
from app.exceptions import (
    AuthenticationError,
    DocumentNotFoundError,
    DocumentParseError,
    UnsupportedFormatError,
)

logger = get_logger(__name__)

# Routes that don't require API key authentication
PUBLIC_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


def setup_middleware(app: FastAPI) -> None:
    """
    Register all middleware on the FastAPI application.

    Called once during app startup in main.py.
    Order matters! Middleware executes top-to-bottom on request,
    bottom-to-top on response.
    """

    # ── CORS Middleware ──────────────────────────────────────────────
    # Allows the Streamlit frontend (different port) to call our API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ───────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        """Log every request with method, path, status, and duration."""
        start_time = time.perf_counter()

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=request.client.host if request.client else "unknown",
        )

        # Add timing header (useful for debugging)
        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))

        return response

    # ── Exception Handler Middleware ─────────────────────────────────
    # Maps our custom exceptions to proper HTTP responses

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        """401 Unauthorized — invalid or missing API key."""
        return JSONResponse(
            status_code=401,
            content={
                "error": "authentication_error",
                "message": exc.message,
            },
        )

    @app.exception_handler(DocumentNotFoundError)
    async def not_found_handler(request: Request, exc: DocumentNotFoundError):
        """404 Not Found — document doesn't exist."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "message": exc.message,
            },
        )

    @app.exception_handler(UnsupportedFormatError)
    async def unsupported_format_handler(
        request: Request, exc: UnsupportedFormatError
    ):
        """415 Unsupported Media Type — file format not supported."""
        return JSONResponse(
            status_code=415,
            content={
                "error": "unsupported_format",
                "message": exc.message,
            },
        )

    @app.exception_handler(DocumentParseError)
    async def parse_error_handler(request: Request, exc: DocumentParseError):
        """422 Unprocessable Entity — file couldn't be parsed."""
        return JSONResponse(
            status_code=422,
            content={
                "error": "parse_error",
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        """500 Internal Server Error — unexpected errors."""
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            },
        )
