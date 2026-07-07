"""
Document Processing Exceptions
===============================

Each exception maps to a specific failure mode in the document pipeline:
- UnsupportedFormatError → 415 Unsupported Media Type
- DocumentParseError     → 422 Unprocessable Entity
- DocumentNotFoundError  → 404 Not Found
"""


class DocumentError(Exception):
    """Base class for document-related errors."""

    def __init__(self, message: str = "Document processing error"):
        self.message = message
        super().__init__(self.message)


class UnsupportedFormatError(DocumentError):
    """Raised when an uploaded file has an unsupported format."""

    def __init__(self, filename: str, supported: list[str] | None = None):
        self.filename = filename
        self.supported = supported or [".pdf", ".txt", ".docx", ".csv", ".xlsx", ".html"]
        super().__init__(
            f"Unsupported file format: '{filename}'. "
            f"Supported: {', '.join(self.supported)}"
        )


class DocumentParseError(DocumentError):
    """Raised when a document fails to parse (corrupted, encrypted, etc.)."""

    def __init__(self, filename: str, reason: str = "Unknown error"):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to parse '{filename}': {reason}")


class DocumentNotFoundError(DocumentError):
    """Raised when a document ID doesn't exist in the database."""

    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")
