"""Runner tests: fake search se gate ke teenon result check karte hain: pass, ACL leak fail, aur low recall fail."""
import uuid

from core.acl.principals import Principals
from core.embeddings.fake import FakeEmbedder
from core.eval.dataset import EvalCase
from core.eval.runner import Thresholds, run_eval


def hit(title: str) -> dict:
    return {"_source": {"chunk_id": f"c-{title}", "document_id": f"d-{title}", "title": title, "content": "x"}}


def corpus_search(answers: dict[str, list[str]]):
    """Question text ke hisaab se documents return karta hai. kNN call khaali deta hai."""

    def search(body: dict) -> list[dict]:
        if "multi_match" not in str(body["query"]):
            return []
        question = body["query"]["bool"]["must"][0]["multi_match"]["query"]
        return [hit(t) for t in answers.get(question, [])]

    return search


def resolve(_case: EvalCase) -> Principals:
    return Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())


def cases_with_acl() -> list[EvalCase]:
    return [
        EvalCase(id="q1", kind="quality", question="leave?", tenant="t", user="u",
                 expected_titles=("Leave Policy",)),
        EvalCase(id="q2", kind="quality", question="salary?", tenant="t", user="u",
                 expected_titles=("Salary Reviews",)),
        EvalCase(id="a1", kind="acl", question="secret?", tenant="t", user="u",
                 forbidden_titles=("Salary Reviews",)),
    ]


def test_gate_passes_with_good_retrieval_and_no_leaks():
    search = corpus_search({"leave?": ["Leave Policy"], "salary?": ["Salary Reviews"], "secret?": []})
    report = run_eval(cases_with_acl(), resolve, FakeEmbedder(), search, k=3)

    assert report.passed is True
    assert report.mean_recall == 1.0
    assert report.total_leaks == 0


def test_gate_fails_when_forbidden_document_is_returned():
    search = corpus_search({"leave?": ["Leave Policy"], "salary?": ["Salary Reviews"], "secret?": ["Salary Reviews"]})
    report = run_eval(cases_with_acl(), resolve, FakeEmbedder(), search, k=3)

    assert report.passed is False
    assert report.total_leaks == 1
    assert any("ACL leaks" in f for f in report.failures)


def test_gate_fails_on_low_recall():
    search = corpus_search({"leave?": ["Onboarding Guide"], "salary?": ["Salary Reviews"], "secret?": []})
    report = run_eval(cases_with_acl(), resolve, FakeEmbedder(), search, k=3,
                      thresholds=Thresholds(min_recall=0.8, min_mrr=0.0, max_leaks=0))

    assert report.passed is False
    assert any("recall" in f for f in report.failures)