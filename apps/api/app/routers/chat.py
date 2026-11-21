"""POST /chat: sawal se retrieval, generation, aur audit row. Har step ACL ke andar hota hai."""
import time
import uuid

from core.acl.principals import Principals
from core.db.models import ChatQuery
from core.generation.answer import SourceChunk, generate_answer
from core.retrieval.pipeline import retrieve
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_principals
from app.schemas.chat import ChatRequest, ChatResponse, CitationOut
from app.services import ChatServices, get_chat_services

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    principals: Principals = Depends(get_principals),
    services: ChatServices = Depends(get_chat_services),
    db: Session = Depends(get_db),
) -> ChatResponse:
    started = time.perf_counter()
    query_id = uuid.uuid4()

    try:
        chunks = retrieve(
            body.question,
            principals,
            services.embedder,
            services.search,
            top_k=body.top_k,
            reranker=services.reranker,
        )
    except Exception as exc:  # OpenSearch down, embedder error, etc. ACL se pehle hi rukta hai, leak ka risk nahi
        raise HTTPException(status_code=503, detail="Search is temporarily unavailable") from exc

    sources = [
        SourceChunk(chunk_id=c.chunk_id, document_id=c.document_id, title=c.title, text=c.text)
        for c in chunks
    ]

    try:
        result = generate_answer(body.question, sources, services.llm)
    except Exception as exc:  # LLM provider down, rate limited, network error, etc.
        _save_audit(db, query_id, principals, body.question, answer=None, chunks=chunks, started=started)
        raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable") from exc

    _save_audit(db, query_id, principals, body.question, answer=result.text, chunks=chunks, started=started)

    return ChatResponse(
        query_id=query_id,
        answer=result.text,
        citations=[
            CitationOut(number=c.number, document_id=c.document_id, chunk_id=c.chunk_id, title=c.title)
            for c in result.citations
        ],
        invalid_citation_numbers=result.invalid_citation_numbers,
        prompt_version=result.prompt_version,
        model_name=result.model_name,
    )


def _save_audit(
    db: Session,
    query_id: uuid.UUID,
    principals: Principals,
    question: str,
    answer: str | None,
    chunks: list,
    started: float,
) -> None:
    """Chat ka audit row, success ya LLM failure dono mein. Failure par answer None hota hai, chunk IDs phir bhi save hoti hain."""
    db.add(
        ChatQuery(
            id=query_id,
            tenant_id=principals.tenant_id,
            user_id=principals.user_id,
            question=question,
            answer=answer,
            retrieved_chunk_ids=[c.chunk_id for c in chunks],
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    )
    db.commit()