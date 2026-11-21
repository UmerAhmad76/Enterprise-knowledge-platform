"""RRF tests: consensus items upar aayein, order deterministic ho, aur top_n ka limit lage."""
from core.retrieval.fusion import rrf_fuse


def test_item_in_both_lists_ranks_above_single_list_items():
    fused = rrf_fuse([["a", "b", "c"], ["c", "a", "d"]])
    ids = [item for item, _ in fused]
    assert ids[0] in {"a", "c"}
    assert ids.index("d") > ids.index("a")


def test_scores_follow_reciprocal_rank_formula():
    fused = dict(rrf_fuse([["a"], ["a"]], k=60))
    assert abs(fused["a"] - 2 / 61) < 1e-9


def test_ties_are_broken_by_id_for_determinism():
    fused = rrf_fuse([["x"], ["y"]])
    assert [item for item, _ in fused] == ["x", "y"]


def test_top_n_limits_output():
    fused = rrf_fuse([[str(i) for i in range(100)]], top_n=5)
    assert len(fused) == 5