"""Feedback service: sirf sawal ka owner vote de sakta hai. Dobara vote dene par rating update hoti hai, naya row nahi banta."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.common.errors import NotFoundError
from core.db.models import ChatQuery, Feedback

_UNSET = object()  # comment ko "nahi diya gaya" aur "khaali string diya gaya" mein farq karne ke liye


def record_feedback(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    query_id: uuid.UUID,
    rating: int,
    comment: str | None = _UNSET,  # type: ignore[assignment]
) -> Feedback:
    """Query isi tenant aur isi user ki honi chahiye. Doosre case mein 'not found' jaisa hi error."""
    if rating not in (-1, 1):
        raise ValueError("rating must be -1 or 1")

    query = db.execute(
        select(ChatQuery).where(
            ChatQuery.id == query_id,
            ChatQuery.tenant_id == tenant_id,
            ChatQuery.user_id == user_id,
        )
    ).scalar_one_or_none()
    if query is None:
        raise NotFoundError("query not found")

    row = db.execute(
        select(Feedback).where(Feedback.query_id == query_id, Feedback.user_id == user_id)
    ).scalar_one_or_none()
    if row is None:
        row = Feedback(
            tenant_id=tenant_id,
            query_id=query_id,
            user_id=user_id,
            rating=rating,
            comment=None if comment is _UNSET else comment,
        )
        db.add(row)
    else:
        row.rating = rating
        # Comment sirf tab badalta hai jab caller ne naya comment diya ho.
        # Bina comment ke dobara vote (jaise 👎 se 👍) purana comment nahi mitata.
        if comment is not _UNSET:
            row.comment = comment

    db.commit()
    return row