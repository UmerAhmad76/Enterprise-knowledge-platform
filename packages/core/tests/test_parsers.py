"""Parser tests: heading se title, line endings, strict UTF-8, aur unsupported types."""
import pytest

from core.ingestion.parsers.text import UnsupportedContentType, parse_document
from core.ingestion.types import RawDocument


def make_raw(content: bytes, content_type: str = "text/markdown", title: str = "fallback") -> RawDocument:
    return RawDocument(external_id="x.md", title=title, content=content, content_type=content_type)


def test_heading_becomes_title():
    parsed = parse_document(make_raw("# Leave Policy\n\nEmployees get 20 days.".encode()))
    assert parsed.title == "Leave Policy"


def test_falls_back_to_file_title_without_heading():
    parsed = parse_document(make_raw(b"plain body", content_type="text/plain", title="notes"))
    assert parsed.title == "notes"


def test_line_endings_and_blank_lines_are_normalised():
    parsed = parse_document(make_raw(b"line1\r\n\r\n\r\n\r\nline2"))
    assert parsed.text == "line1\n\nline2"


def test_invalid_utf8_is_rejected():
    with pytest.raises(ValueError):
        parse_document(make_raw(b"\xff\xfe\x00bad"))


def test_unsupported_content_type_is_rejected():
    with pytest.raises(UnsupportedContentType):
        parse_document(make_raw(b"%PDF", content_type="application/pdf"))