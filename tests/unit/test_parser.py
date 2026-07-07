"""
Unit Tests for DocumentParser
=============================
"""

import pytest
from unittest.mock import MagicMock, patch
from app.core.parser import DocumentParser
from app.exceptions import DocumentParseError, UnsupportedFormatError


def test_parse_txt():
    """Verify TXT parsing returns decoded text."""
    content = b"Hello, this is a plain text file."
    result = DocumentParser.parse(content, "test.txt")
    assert result == "Hello, this is a plain text file."


def test_parse_unsupported():
    """Unsupported extension raises UnsupportedFormatError."""
    with pytest.raises(UnsupportedFormatError):
        DocumentParser.parse(b"some content", "test.mp3")


def test_parse_html():
    """HTML parser filters tags and elements."""
    html_content = b"<html><head><title>Title</title></head><body><h1>Hello</h1><script>console.log('test')</script></body></html>"
    result = DocumentParser.parse(html_content, "test.html")
    assert "Hello" in result
    assert "console.log" not in result


def test_parse_csv():
    """CSV parser reads tabular values."""
    csv_content = b"name,age\nAlice,30\nBob,25"
    result = DocumentParser.parse(csv_content, "test.csv")
    assert "name: Alice, age: 30" in result or "name: Alice" in result
    assert "Bob" in result


@patch("docx.Document")
def test_parse_docx_mocked(mock_doc):
    """Test Word docx parser using mocks."""
    mock_instance = MagicMock()
    mock_paragraph = MagicMock()
    mock_paragraph.text = "Hello world paragraph"
    mock_instance.paragraphs = [mock_paragraph]
    mock_doc.return_value = mock_instance

    result = DocumentParser.parse(b"docx_binary", "test.docx")
    assert result == "Hello world paragraph"


@patch("fitz.open")
def test_parse_pdf_mocked(mock_fitz):
    """Test PDF parser using mocks."""
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "PDF Page Content"
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz.return_value = mock_doc

    result = DocumentParser.parse(b"pdf_binary", "test.pdf")
    assert result == "PDF Page Content"
