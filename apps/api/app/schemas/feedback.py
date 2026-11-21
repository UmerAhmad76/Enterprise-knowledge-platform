"""Feedback request aur response shapes. Rating sirf -1 ya 1 ho sakti hai, is liye 0 ya 5 jaise values 422 denge."""
import uuid
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """Kis sawal par vote hai, aur kya vote hai. Comment optional hai."""

    query_id: uuid.UUID
    rating: Literal[-1, 1]
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    """Vote ki confirmation: query ID aur final rating."""

    query_id: uuid.UUID
    rating: int