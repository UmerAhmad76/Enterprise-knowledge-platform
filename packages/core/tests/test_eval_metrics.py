"""Metrics ke formulas check karte hain. Ye numbers hath se calculate kiye gaye hain, taake formula galat na ho."""
import pytest

from core.eval.metrics import dedupe, leaked_titles, mrr, ndcg_at_k, recall_at_k


def test_recall_counts_expected_documents_in_top_k():
    assert recall_at_k(["A", "B", "C"], ["B", "D"], k=3) == pytest.approx(0.5)


def test_duplicate_chunks_of_same_document_count_once():
    assert dedupe(["A", "A", "B"]) == ["A", "B"]
    assert mrr(["A", "A", "B"], ["B"]) == pytest.approx(0.5)


def test_mrr_uses_rank_of_first_relevant_document():
    assert mrr(["X", "B"], ["B"]) == pytest.approx(0.5)
    assert mrr(["X", "Y"], ["B"]) == 0.0


def test_ndcg_matches_hand_calculation():
    # Relevant document rank 2 par: dcg = 1/log2(3), ideal = 1/log2(2) = 1
    assert ndcg_at_k(["A", "B"], ["B"], k=2) == pytest.approx(0.6309, abs=1e-4)


def test_leak_detects_forbidden_document_in_top_k_only():
    assert leaked_titles(["A", "S"], ["S"], k=2) == ["S"]
    assert leaked_titles(["A", "S"], ["S"], k=1) == []