"""Request aur response shapes for /chat. Response mein query_id bhi hai, taake frontend feedback bhej sake."""
import uuid

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Sawal aur kitne chunks chahiye. Empty ya sirf spaces wala sawal reject hota hai."""

    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=8, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class CitationOut(BaseModel):
    """Ek source jo jawab mein use hua. Frontend isi se citation chip banata hai."""

    number: int
    document_id: str
    chunk_id: str
    title: str


class ChatResponse(BaseModel):
    """Jawab, uske citations, aur query_id jo feedback ke liye use hoga."""

    query_id: uuid.UUID
    answer: str
    citations: list[CitationOut]
    invalid_citation_numbers: list[int]
    prompt_version: str
    model_name: str