"""POST /feedback: user apne hi sawal par thumbs up/down de sakta hai. Doosre user ya tenant ka sawal 404 deta hai."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_principals
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from core.acl.principals import Principals
from core.common.errors import NotFoundError
from core.feedback.service import record_feedback

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def give_feedback(
    request: Request,
    body: FeedbackRequest,
    principals: Principals = Depends(get_principals),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    # "comment" key bheji gayi thi ya nahi, ye batata hai ke purana comment overwrite karna hai ya nahi
    raw_body = await request.json()
    comment_kwargs = {"comment": body.comment} if "comment" in raw_body else {}

    try:
        row = record_feedback(
            db, principals.tenant_id, principals.user_id, body.query_id, body.rating, **comment_kwargs
        )
    except NotFoundError as exc:
        # Ye wahi message hai jo galat tenant ya user ko milta hai, existence ka pata na chale
        raise HTTPException(status_code=404, detail="query not found") from exc
    return FeedbackResponse(query_id=body.query_id, rating=row.rating)