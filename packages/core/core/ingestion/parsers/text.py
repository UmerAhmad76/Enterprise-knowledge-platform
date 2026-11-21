"""Raw bytes ko saaf plain text mein badalta hai. Markdown ka pehla heading title ban jata hai."""
import re

from core.ingestion.types import ParsedDocument, RawDocument

SUPPORTED_TYPES = {"text/markdown", "text/plain"}
_HEADING = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_EXTRA_BLANK_LINES = re.compile(r"\n{3,}")


class UnsupportedContentType(ValueError):
    """Is content type ke liye parser nahi hai."""


def parse_document(raw: RawDocument) -> ParsedDocument:
    """Strict decode karta hai (galat bytes par error, silent corruption nahi), line endings normalise karta hai."""
    if raw.content_type not in SUPPORTED_TYPES:
        raise UnsupportedContentType(raw.content_type)
    # utf-8-sig BOM handle karta hai, invalid bytes par UnicodeDecodeError (jo ValueError hai) aata hai
    text = raw.content.decode("utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _EXTRA_BLANK_LINES.sub("\n\n", text).strip()
    heading = _HEADING.search(text)
    title = heading.group(1).strip() if heading else raw.title
    return ParsedDocument(title=title, text=text)

