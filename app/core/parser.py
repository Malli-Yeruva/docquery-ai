"""
Document Parsing Module
=======================

Extracts raw text content from uploaded files depending on their file extension.
Supported formats: PDF, DOCX, CSV, Excel (XLSX), HTML, and TXT.
"""

from io import BytesIO
from pathlib import Path
import docx
import fitz  # PyMuPDF
import pandas as pd
from bs4 import BeautifulSoup

from app.config.logging_config import get_logger
from app.exceptions import DocumentParseError, UnsupportedFormatError

logger = get_logger(__name__)


class DocumentParser:
    """
    Parses different document formats into raw string content.
    """

    @staticmethod
    def parse(file_content: bytes, filename: str) -> str:
        """
        Detect file extension and route to the corresponding parser method.

        Args:
            file_content: Raw bytes of the uploaded file.
            filename: Name of the uploaded file.

        Returns:
            Extracted text string.

        Raises:
            UnsupportedFormatError: If the format is not supported.
            DocumentParseError: If parsing fails due to corruption, encryption, etc.
        """
        ext = Path(filename).suffix.lower()
        logger.info("parsing_started", filename=filename, size_bytes=len(file_content), extension=ext)

        try:
            if ext == ".pdf":
                return DocumentParser._parse_pdf(file_content, filename)
            elif ext == ".docx":
                return DocumentParser._parse_docx(file_content, filename)
            elif ext in (".csv", ".xlsx", ".xls"):
                return DocumentParser._parse_tabular(file_content, filename, ext)
            elif ext in (".html", ".htm"):
                return DocumentParser._parse_html(file_content, filename)
            elif ext == ".txt":
                return DocumentParser._parse_txt(file_content, filename)
            else:
                raise UnsupportedFormatError(filename)
        except (UnsupportedFormatError, DocumentParseError):
            raise
        except Exception as e:
            logger.error("parsing_failed", filename=filename, error=str(e))
            raise DocumentParseError(filename, reason=str(e)) from e

    @staticmethod
    def _parse_pdf(file_content: bytes, filename: str) -> str:
        """Parse PDF document using PyMuPDF (fitz)."""
        try:
            doc = fitz.open(stream=BytesIO(file_content), filetype="pdf")
            text_parts = []
            for i, page in enumerate(doc):
                text_parts.append(page.get_text())
            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("pdf_parse_error", filename=filename, error=str(e))
            raise DocumentParseError(filename, reason=f"Invalid or corrupted PDF: {e}") from e

    @staticmethod
    def _parse_docx(file_content: bytes, filename: str) -> str:
        """Parse Word document using python-docx."""
        try:
            doc = docx.Document(BytesIO(file_content))
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.error("docx_parse_error", filename=filename, error=str(e))
            raise DocumentParseError(filename, reason=f"Invalid Word document: {e}") from e

    @staticmethod
    def _parse_tabular(file_content: bytes, filename: str, ext: str) -> str:
        """Parse CSV or Excel spreadsheet using pandas."""
        try:
            if ext == ".csv":
                df = pd.read_csv(BytesIO(file_content))
            else:
                df = pd.read_excel(BytesIO(file_content))

            # Convert spreadsheet to structural Markdown-like text representation
            # to help the LLM understand table row-column relationships
            records = df.to_dict(orient="records")
            text_lines = []
            for r in records:
                row_str = ", ".join([f"{k}: {v}" for k, v in r.items() if pd.notna(v)])
                text_lines.append(row_str)
            return "\n".join(text_lines)
        except Exception as e:
            logger.error("tabular_parse_error", filename=filename, error=str(e))
            raise DocumentParseError(filename, reason=f"Invalid tabular file: {e}") from e

    @staticmethod
    def _parse_html(file_content: bytes, filename: str) -> str:
        """Parse HTML page filtering script/style headers using BeautifulSoup."""
        try:
            soup = BeautifulSoup(file_content, "lxml")
            # Kill script and style elements
            for script in soup(["script", "style", "meta", "noscript", "header", "footer"]):
                script.decompose()
            # Get text and resolve whitespace
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return "\n".join(chunk for chunk in chunks if chunk)
        except Exception as e:
            logger.error("html_parse_error", filename=filename, error=str(e))
            raise DocumentParseError(filename, reason=f"Invalid HTML document: {e}") from e

    @staticmethod
    def _parse_txt(file_content: bytes, filename: str) -> str:
        """Parse raw text document."""
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 if utf-8 fails
                return file_content.decode("latin-1")
            except Exception as e:
                logger.error("txt_decode_error", filename=filename, error=str(e))
                raise DocumentParseError(filename, reason=f"Failed to decode text: {e}") from e
