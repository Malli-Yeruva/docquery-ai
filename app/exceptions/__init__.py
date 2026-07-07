# Custom exceptions package
from app.exceptions.auth import AuthenticationError, InvalidAPIKeyError
from app.exceptions.document import (
    DocumentNotFoundError,
    DocumentParseError,
    UnsupportedFormatError,
)

__all__ = [
    "AuthenticationError",
    "InvalidAPIKeyError",
    "DocumentNotFoundError",
    "DocumentParseError",
    "UnsupportedFormatError",
]
