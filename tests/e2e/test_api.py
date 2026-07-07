"""
E2E API Integration Tests
=========================
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from app.api.dependencies import get_document_service, get_query_service
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_health_and_readiness():
    """Verify health and ready routes respond without auth headers."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Test /health
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # Test /ready (with placeholder dependencies mocked or active)
        resp = await ac.get("/ready")
        assert resp.status_code in (200, 503)  # Dependent on Ollama being online


@pytest.mark.asyncio
async def test_auth_middleware_blocks():
    """Verify routing blocks calls without the correct X-API-Key."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Request should fail with 401 Unauthorized
        resp = await ac.get("/api/v1/documents")
        assert resp.status_code == 401
        assert "authentication_error" in resp.json()["error"]


@pytest.mark.asyncio
async def test_get_documents_authorized():
    """Verify listing documents with valid API key header."""
    mock_doc_service = MagicMock()
    mock_doc_service.list_documents = AsyncMock(return_value=([], 0))

    # Override service dependency
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        headers = {"X-API-Key": "your-secret-api-key-change-me"}
        resp = await ac.get("/api/v1/documents", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == {"documents": [], "total": 0}

    # Clean up overrides
    app.dependency_overrides.clear()
