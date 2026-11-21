"""Eval runner: har case ko asli retrieve() se chalata hai, metrics nikalta hai, aur gate lagata hai."""
from collections.abc import Callable
from dataclasses import dataclass, field

from core.acl.principals import Principals
from core.embeddings.base import Embedder
from core.eval.dataset import EvalCase
from core.eval.metrics import dedupe, leaked_titles, mrr, ndcg_at_k, recall_at_k
from core.retrieval.pipeline import SearchFn, retrieve


@dataclass(frozen=True)
class Thresholds:
    """Build pass karne ki minimum shart. Ye numbers data dekh kar tune honge, pehle se fix nahi hain."""

    min_recall: float = 0.8
    min_mrr: float = 0.6
    max_leaks: int = 0


@dataclass(frozen=True)
class CaseResult:
    """Ek case ka result. Quality metrics acl cases ke liye None hote hain."""

    id: str
    kind: str
    retrieved_titles: tuple[str, ...]
    recall: float | None
    mrr: float | None
    ndcg: float | None
    leaked_titles: tuple[str, ...]


@dataclass
class EvalReport:
    """Poore run ka summary. JSON mein save hota hai aur CI gate isi ka passed flag dekhta hai."""

    k: int
    cases: list[CaseResult]
    mean_recall: float
    mean_mrr: float
    mean_ndcg: float
    total_leaks: int
    passed: bool
    failures: list[str] = field(default_factory=list)


def run_eval(
    cases: list[EvalCase],
    resolve: Callable[[EvalCase], Principals],
    embedder: Embedder,
    search: SearchFn,
    k: int = 5,
    thresholds: Thresholds = Thresholds(),
) -> EvalReport:
    results: list[CaseResult] = []

    for case in cases:
        principals = resolve(case)
        chunks = retrieve(case.question, principals, embedder, search, top_k=k)
        titles = [c.title for c in chunks]
        is_quality = case.kind == "quality"

        results.append(
            CaseResult(
                id=case.id,
                kind=case.kind,
                retrieved_titles=tuple(dedupe(titles)[:k]),
                recall=recall_at_k(titles, case.expected_titles, k) if is_quality else None,
                mrr=mrr(titles, case.expected_titles) if is_quality else None,
                ndcg=ndcg_at_k(titles, case.expected_titles, k) if is_quality else None,
                leaked_titles=tuple(leaked_titles(titles, case.forbidden_titles, k)),
            )
        )

    quality = [r for r in results if r.kind == "quality"]
    mean_recall = _mean([r.recall for r in quality])
    mean_mrr = _mean([r.mrr for r in quality])
    mean_ndcg = _mean([r.ndcg for r in quality])
    total_leaks = sum(len(r.leaked_titles) for r in results)

    failures: list[str] = []
    if mean_recall < thresholds.min_recall:
        failures.append(f"mean recall@{k} {mean_recall:.3f} < min {thresholds.min_recall}")
    if mean_mrr < thresholds.min_mrr:
        failures.append(f"mean MRR {mean_mrr:.3f} < min {thresholds.min_mrr}")
    if total_leaks > thresholds.max_leaks:
        failures.append(f"ACL leaks: {total_leaks} forbidden document(s) returned")

    return EvalReport(
        k=k,
        cases=results,
        mean_recall=mean_recall,
        mean_mrr=mean_mrr,
        mean_ndcg=mean_ndcg,
        total_leaks=total_leaks,
        passed=not failures,
        failures=failures,
    )


def _mean(values: list[float | None]) -> float:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else 0.0