"""
Authentication Exceptions
=========================

WHY CUSTOM EXCEPTIONS:
    Instead of raising generic `ValueError` or returning error dicts,
    we define specific exception classes. This gives us:

    1. Type safety — catch specific errors, not everything
    2. Clean API layer — map each exception to an HTTP status code
    3. Readable code — `raise InvalidAPIKeyError()` is self-documenting
"""


class AuthenticationError(Exception):
    """Base class for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class InvalidAPIKeyError(AuthenticationError):
    """Raised when an API key is missing or invalid."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)
