"""SQLAlchemy implementation of DocumentStore. Ek tenant aur ek source se bandha hota hai."""
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.db.models import Chunk, Document, DocumentACL, DocumentVersion
from core.ingestion.types import RawDocument, TextChunk


class SqlDocumentStore:
    """Har query tenant_id aur source_id se scoped hai, taake cross-tenant write na ho sake."""

    def __init__(self, session: Session, tenant_id: uuid.UUID, source_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.source_id = source_id

    def _find(self, external_id: str) -> Document | None:
        return self.session.execute(
            select(Document).where(
                Document.tenant_id == self.tenant_id,
                Document.source_id == self.source_id,
                Document.external_id == external_id,
            )
        ).scalar_one_or_none()

    def known_hashes(self) -> dict[str, str]:
        rows = self.session.execute(
            select(Document.external_id, Document.content_hash).where(
                Document.tenant_id == self.tenant_id,
                Document.source_id == self.source_id,
                Document.status == "active",
            )
        ).all()
        return {row.external_id: row.content_hash for row in rows}

    def upsert_document(
        self, raw: RawDocument, content_hash: str, title: str, chunks: list[TextChunk]
    ) -> None:
        doc = self._find(raw.external_id)
        if doc is None:
            doc = Document(
                tenant_id=self.tenant_id,
                source_id=self.source_id,
                external_id=raw.external_id,
                title=title,
                content_hash=content_hash,
                current_version=1,
                status="active",
            )
            self.session.add(doc)
            self.session.flush()
        else:
            doc.title = title
            doc.content_hash = content_hash
            doc.current_version += 1
            doc.status = "active"

        version_no = doc.current_version
        # Purane chunks hatao, retrieval sirf latest version dekhe
        self.session.execute(delete(Chunk).where(Chunk.document_id == doc.id))

        version = DocumentVersion(
            tenant_id=self.tenant_id,
            document_id=doc.id,
            version_no=version_no,
            content_hash=content_hash,
            storage_key=f"sources/{self.source_id}/{raw.external_id}/v{version_no}",
        )
        self.session.add(version)
        self.session.flush()

        for chunk in chunks:
            self.session.add(
                Chunk(
                    tenant_id=self.tenant_id,
                    document_id=doc.id,
                    document_version_id=version.id,
                    chunk_index=chunk.index,
                    content=chunk.text,
                    token_count=chunk.token_count,
                )
            )

        self._replace_acl(doc.id, raw)
        self.session.flush()

    def refresh_acl(self, raw: RawDocument) -> bool:
        """ACL ka current set DB se padhta hai aur source ke set se compare karta hai. Farq ho to replace karta hai."""
        doc = self._find(raw.external_id)
        if doc is None or doc.status != "active":
            return False

        current = {
            (ptype, pid)
            for ptype, pid in self.session.execute(
                select(DocumentACL.principal_type, DocumentACL.principal_id).where(
                    DocumentACL.document_id == doc.id
                )
            ).all()
        }
        if current == _desired_acl(raw):
            return False

        self._replace_acl(doc.id, raw)
        self.session.flush()
        return True

    def _replace_acl(self, document_id: uuid.UUID, raw: RawDocument) -> None:
        """Purani ACL hata kar source ki current permissions likhta hai. Source hi sach hai."""
        self.session.execute(delete(DocumentACL).where(DocumentACL.document_id == document_id))
        for ptype, pid in _desired_acl(raw):
            self.session.add(
                DocumentACL(
                    tenant_id=self.tenant_id,
                    document_id=document_id,
                    principal_type=ptype,
                    principal_id=pid,
                )
            )

    def mark_deleted(self, external_id: str) -> None:
        doc = self._find(external_id)
        if doc is None or doc.status != "active":
            return
        doc.status = "deleted"
        self.session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
        self.session.execute(delete(DocumentACL).where(DocumentACL.document_id == doc.id))
        self.session.flush()


def _desired_acl(raw: RawDocument) -> set[tuple[str, uuid.UUID]]:
    """Source ki current permissions ek set mein: ("group", id) aur ("user", id)."""
    return {("group", g) for g in raw.allowed_group_ids} | {("user", u) for u in raw.allowed_user_ids}