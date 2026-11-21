"""Thumbs-down feedback ko candidates JSONL mein export karta hai. Output eval/datasets/candidates/ mein jata hai, golden mein nahi."""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

from core.db.models import Chunk, ChatQuery, Document, Feedback, Tenant, User
from core.db.session import make_engine, make_session_factory
from core.eval.candidates import FeedbackRow, build_candidates, write_candidates

OUT = Path("eval/datasets/candidates/feedback_candidates.jsonl")


def main() -> None:
    load_dotenv()
    session_factory = make_session_factory(make_engine(os.environ["DATABASE_URL"]))
    rows: list[FeedbackRow] = []

    with session_factory() as db:
        found = db.execute(
            select(ChatQuery, Tenant, User)
            .join(Feedback, Feedback.query_id == ChatQuery.id)
            .join(Tenant, Tenant.id == ChatQuery.tenant_id)
            .join(User, User.id == ChatQuery.user_id)
            .where(Feedback.rating == -1)
        ).all()

        for query, tenant, user in found:
            chunk_ids = [uuid.UUID(c) for c in query.retrieved_chunk_ids]
            titles: list[str] = []
            if chunk_ids:
                titles = list(
                    db.execute(
                        select(Document.title)
                        .join(Chunk, Chunk.document_id == Document.id)
                        .where(Chunk.id.in_(chunk_ids))
                    ).scalars().all()
                )
            rows.append(
                FeedbackRow(
                    query_id=str(query.id),
                    question=query.question,
                    tenant=tenant.slug,
                    user=user.email,
                    rating=-1,
                    retrieved_titles=tuple(dict.fromkeys(titles)),
                )
            )

    candidates = build_candidates(rows)
    write_candidates(OUT, candidates)
    print(f"candidates={len(candidates)} -> {OUT}")
    print("Har candidate ka expected_titles bharo, status hata do, phir golden file mein copy karo.")


if __name__ == "__main__":
    main()