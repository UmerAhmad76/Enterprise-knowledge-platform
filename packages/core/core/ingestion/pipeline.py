"""Incremental sync: content badla to parse aur chunk; sirf ACL badli to permission update; gaye hue ko retire."""
from dataclasses import dataclass, field

from core.ingestion.change_detection import ChangeKind, classify, content_hash
from core.ingestion.chunking.recursive import chunk_text
from core.ingestion.connectors.base import Connector
from core.ingestion.parsers.text import parse_document
from core.ingestion.store import DocumentStore


@dataclass
class SyncReport:
    """Ek sync run ka summary. upserted_ids mein woh documents hain jinhe index mein dobara likhna hai."""

    new: int = 0
    changed: int = 0
    unchanged: int = 0
    acl_updated: int = 0
    deleted: int = 0
    failed: list[str] = field(default_factory=list)
    upserted_ids: list[str] = field(default_factory=list)  # new, changed, aur ACL-only changed
    deleted_ids: list[str] = field(default_factory=list)


def sync_source(
    connector: Connector,
    store: DocumentStore,
    max_tokens: int = 200,
    overlap_tokens: int = 30,
) -> SyncReport:
    report = SyncReport()
    known = store.known_hashes()
    current_ids = connector.list_document_ids()

    for external_id in current_ids:
        try:
            raw = connector.fetch(external_id)
            digest = content_hash(raw.content)
            kind = classify(known.get(external_id), digest)

            if kind is ChangeKind.UNCHANGED:
                # Content same hai, lekin permission badli ho sakti hai: ye alag check hai
                if store.refresh_acl(raw):
                    report.acl_updated += 1
                    report.upserted_ids.append(external_id)  # index ke ACL fields bhi update hon
                else:
                    report.unchanged += 1
                continue

            parsed = parse_document(raw)
            chunks = chunk_text(parsed.text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
            store.upsert_document(raw, digest, parsed.title, chunks)
        except (OSError, ValueError):
            report.failed.append(external_id)
            continue

        if kind is ChangeKind.NEW:
            report.new += 1
        else:
            report.changed += 1
        report.upserted_ids.append(external_id)

    current_set = set(current_ids)
    for external_id in known:
        if external_id not in current_set:
            store.mark_deleted(external_id)
            report.deleted += 1
            report.deleted_ids.append(external_id)

    return report