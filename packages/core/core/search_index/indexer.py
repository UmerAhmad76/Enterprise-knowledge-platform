"""Postgres ke chunks aur ACL ko OpenSearch mein index karta hai. SQL aur search ke beech ka bridge."""
import uuid
from typing import Any

from opensearchpy import OpenSearch
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.db.models import Chunk, Document, DocumentACL
from core.embeddings.base import Embedder


def delete_document_chunks(
    client: OpenSearch, index: str, tenant_id: uuid.UUID, document_id: uuid.UUID
) -> None:
    """Tenant aur document dono ke filter se delete karta hai, taake doosre tenant ka data kabhi na hate."""
    client.delete_by_query(
        index=index,
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"tenant_id": str(tenant_id)}},
                        {"term": {"document_id": str(document_id)}},
                    ]
                }
            }
        },
        refresh=True,
        conflicts="proceed",
    )


def index_document(
    session: Session,
    client: OpenSearch,
    embedder: Embedder,
    index: str,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
) -> int:
    """Document ke current chunks index karta hai. Pehle purane hatata hai, is liye dobara chalane se duplicate nahi banta."""
    delete_document_chunks(client, index, tenant_id, document_id)

    doc = session.execute(
        select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if doc is None or doc.status != "active":
        return 0

    chunks = session.execute(
        select(Chunk)
        .where(Chunk.document_id == doc.id, Chunk.tenant_id == tenant_id)
        .order_by(Chunk.chunk_index)
    ).scalars().all()
    if not chunks:
        return 0

    groups, users = _acl_for(session, tenant_id, doc.id)
    vectors = embedder.embed_documents([c.content for c in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        client.index(
            index=index,
            id=str(chunk.id),
            body=_chunk_body(chunk, doc, groups, users, vector),
            refresh=False,
        )
    return len(chunks)


def apply_sync_report(
    session: Session,
    client: OpenSearch,
    embedder: Embedder,
    index: str,
    tenant_id: uuid.UUID,
    source_id: uuid.UUID,
    upserted_ids: list[str],
    deleted_ids: list[str],
) -> int:
    """Sync ke baad sirf badle ya hate hue documents index karta hai. Poora source dobara nahi hota."""
    external_ids = list(set(upserted_ids) | set(deleted_ids))
    if not external_ids:
        return 0

    rows = session.execute(
        select(Document.id).where(
            Document.tenant_id == tenant_id,
            Document.source_id == source_id,
            Document.external_id.in_(external_ids),
        )
    ).scalars().all()

    total = 0
    for document_id in rows:
        total += index_document(session, client, embedder, index, tenant_id, document_id)
    return total


def _acl_for(session: Session, tenant_id: uuid.UUID, document_id: uuid.UUID) -> tuple[list[str], list[str]]:
    """Document ki allowed groups aur users ki list, string form mein (OpenSearch keyword fields ke liye)."""
    rows = session.execute(
        select(DocumentACL.principal_type, DocumentACL.principal_id).where(
            DocumentACL.document_id == document_id,
            DocumentACL.tenant_id == tenant_id,
        )
    ).all()
    groups = sorted(str(pid) for ptype, pid in rows if ptype == "group")
    users = sorted(str(pid) for ptype, pid in rows if ptype == "user")
    return groups, users


def _chunk_body(chunk: Chunk, doc: Document, groups: list[str], users: list[str], vector: list[float]) -> dict[str, Any]:
    """Ye dict exactly wahi fields rakhta hai jo chunks_v1 mapping mein hain (dynamic strict hai)."""
    return {
        "chunk_id": str(chunk.id),
        "tenant_id": str(doc.tenant_id),
        "document_id": str(doc.id),
        "source_id": str(doc.source_id),
        "title": doc.title,
        "content": chunk.content,
        "allowed_groups": groups,
        "allowed_users": users,
        "embedding": vector,
    }