"""
API Key Authentication
======================

WHY THIS EXISTS:
    Every production API needs authentication. We use the simplest
    production-ready approach: API key via HTTP header.

HOW IT WORKS:
    1. Client sends: `X-API-Key: <their-key>` header with every request
    2. We compare it against the key in our settings (from env var)
    3. Match → request proceeds. Mismatch → 401 Unauthorized.

    This is implemented as a FastAPI "dependency" — a function that runs
    BEFORE your route handler. If it raises, the route never executes.

WHY NOT OAuth/JWT:
    For a single-service app, API keys are perfectly fine.
    JWT/OAuth adds complexity that's only justified for multi-service
    architectures with user management.

SECURITY NOTES:
    - The API key is compared using `secrets.compare_digest()` which
      prevents timing attacks (constant-time comparison).
    - In production, set a strong key via the API_KEY env var.
    - Health check endpoints are excluded from auth (see middleware.py).
"""

import secrets

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.exceptions import InvalidAPIKeyError

# Define where to look for the API key in the request
# This creates the "X-API-Key" header requirement in OpenAPI docs
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,  # We handle the error ourselves for better messages
)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """
    Verify the API key from the request header.

    This is used as a FastAPI dependency:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])

    Args:
        api_key: The API key extracted from X-API-Key header.

    Returns:
        The validated API key string.

    Raises:
        InvalidAPIKeyError: If the key is missing or doesn't match.
    """
    settings = get_settings()

    if api_key is None:
        raise InvalidAPIKeyError("Missing X-API-Key header")

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key):
        raise InvalidAPIKeyError("Invalid API key")

    return api_key
