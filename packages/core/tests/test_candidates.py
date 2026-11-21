"""Candidate tests: sirf thumbs-down, ek query ek dafa, aur unreviewed candidate golden loader mein reject ho."""
from pathlib import Path

import pytest

from core.eval.candidates import FeedbackRow, build_candidates, write_candidates
from core.eval.dataset import DatasetError, load_cases


def row(query_id: str, rating: int) -> FeedbackRow:
    return FeedbackRow(
        query_id=query_id,
        question="How many leave days?",
        tenant="acme",
        user="alice@acme.test",
        rating=rating,
        retrieved_titles=("Salary Reviews",),
    )


def test_only_thumbs_down_become_candidates_and_each_query_once():
    candidates = build_candidates([row("q1", -1), row("q1", -1), row("q2", 1)])
    assert [c["id"] for c in candidates] == ["fb-q1"]


def test_candidate_needs_review_and_has_no_expected_titles_yet():
    candidate = build_candidates([row("q1", -1)])[0]
    assert candidate["expected_titles"] == []
    assert candidate["status"] == "needs_review"
    assert candidate["retrieved_at_feedback"] == ["Salary Reviews"]


def test_unreviewed_candidate_is_rejected_by_golden_loader(tmp_path: Path):
    path = tmp_path / "candidates.jsonl"
    write_candidates(path, build_candidates([row("q1", -1)]))
    with pytest.raises(DatasetError, match="needs expected_titles"):
        load_cases(path)