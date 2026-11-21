"""Dev helper: source sync karta hai, OpenSearch index aur chunks_active alias banata hai, embedding_versions row likhta hai, phir active documents index karta hai."""
import os
import sys
import uuid

from dotenv import load_dotenv
from sqlalchemy import select

from core.db.models import Document, EmbeddingVersion, Tenant
from core.db.session import make_engine, make_session_factory
from core.embeddings.fake import FakeEmbedder
from core.ingestion.service import run_source_sync
from core.search_index.client import make_opensearch_client
from core.search_index.index_manager import (
    build_index_name,
    create_versioned_index,
    switch_active_alias,
)
from core.search_index.indexer import index_document


def _ensure_embedding_version_row(session, embedder, index_name: str) -> None:
    """Postgres mein embedding_versions ka record rakhta hai, taake schema aur asal index ek doosre se match karein."""
    existing = session.execute(
        select(EmbeddingVersion).where(
            EmbeddingVersion.model_name == embedder.model_name,
            EmbeddingVersion.model_version == embedder.model_version,
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            EmbeddingVersion(
                model_name=embedder.model_name,
                model_version=embedder.model_version,
                dimension=embedder.dimension,
                status="active",
                index_name=index_name,
            )
        )
    elif existing.status != "active":
        existing.status = "active"
        existing.index_name = index_name


def main(tenant_slug: str, source_id: str) -> None:
    load_dotenv()
    embedder = FakeEmbedder(dimension=int(os.environ.get("EMBEDDING_DIMENSION", "64")))
    client = make_opensearch_client(os.environ["OPENSEARCH_URL"])

    index = build_index_name(embedder.model_name, embedder.model_version)
    create_versioned_index(client, index, embedder.dimension)
    switch_active_alias(client, index)

    session_factory = make_session_factory(make_engine(os.environ["DATABASE_URL"]))
    with session_factory() as db:
        tenant = db.execute(select(Tenant).where(Tenant.slug == tenant_slug)).scalar_one()
        src_id = uuid.UUID(source_id)

        _ensure_embedding_version_row(db, embedder, index)

        report = run_source_sync(db, tenant.id, src_id)
        doc_ids = db.execute(
            select(Document.id).where(
                Document.tenant_id == tenant.id,
                Document.source_id == src_id,
                Document.status == "active",
            )
        ).scalars().all()
        indexed = sum(index_document(db, client, embedder, index, tenant.id, d) for d in doc_ids)
        db.commit()

    print(f"index={index}")
    print(f"sync: new={report.new} changed={report.changed} unchanged={report.unchanged} "
          f"acl_updated={report.acl_updated} failed={report.failed}")
    print(f"chunks indexed={indexed}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python scripts/index_source.py <tenant_slug> <source_id>")
    main(sys.argv[1], sys.argv[2])