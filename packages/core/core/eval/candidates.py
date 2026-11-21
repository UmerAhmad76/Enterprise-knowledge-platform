"""Feedback se golden candidates banata hai. Candidates golden mein seedhe nahi jaate, pehle human review hota hai."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FeedbackRow:
    """Ek thumbs-down wale sawal ka snapshot: sawal, user, aur jo documents us waqt mile the."""

    query_id: str
    question: str
    tenant: str
    user: str
    rating: int
    retrieved_titles: tuple[str, ...]


def build_candidates(rows: list[FeedbackRow]) -> list[dict[str, Any]]:
    """Sirf thumbs-down lete hain, aur har query ek hi dafa. expected_titles khaali rehte hain, jo reviewer bharega."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if row.rating != -1 or row.query_id in seen:
            continue
        seen.add(row.query_id)
        candidates.append(
            {
                "id": f"fb-{row.query_id}",
                "kind": "quality",
                "question": row.question,
                "tenant": row.tenant,
                "user": row.user,
                "expected_titles": [],
                "forbidden_titles": [],
                "retrieved_at_feedback": list(row.retrieved_titles),
                "status": "needs_review",
            }
        )
    return candidates


def write_candidates(path: Path, candidates: list[dict[str, Any]]) -> None:
    """JSONL likhta hai. Golden loader ise tab tak reject karega jab tak expected_titles na bhare jayein."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(c, ensure_ascii=False) for c in candidates]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")