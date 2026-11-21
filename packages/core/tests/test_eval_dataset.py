"""Dataset loader tests: asli golden file parse hoti hai, aur galat entries reject hoti hain."""
from pathlib import Path

import pytest

from core.eval.dataset import DatasetError, load_cases

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN = REPO_ROOT / "eval" / "datasets" / "golden" / "retrieval_v1.jsonl"


def write(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_loads_golden_file_with_both_kinds():
    cases = load_cases(GOLDEN)
    kinds = {c.kind for c in cases}
    assert len(cases) >= 10
    assert kinds == {"quality", "acl"}


def test_rejects_unknown_kind(tmp_path):
    path = write(tmp_path, '{"id":"x","kind":"weird","question":"q","tenant":"t","user":"u"}')
    with pytest.raises(DatasetError, match="kind must be one of"):
        load_cases(path)


def test_quality_case_needs_expected_titles(tmp_path):
    path = write(tmp_path, '{"id":"x","kind":"quality","question":"q","tenant":"t","user":"u"}')
    with pytest.raises(DatasetError, match="needs expected_titles"):
        load_cases(path)


def test_acl_case_needs_forbidden_titles(tmp_path):
    path = write(tmp_path, '{"id":"x","kind":"acl","question":"q","tenant":"t","user":"u"}')
    with pytest.raises(DatasetError, match="needs forbidden_titles"):
        load_cases(path)


def test_duplicate_ids_are_rejected(tmp_path):
    line = '{"id":"x","kind":"quality","question":"q","tenant":"t","user":"u","expected_titles":["A"]}'
    path = write(tmp_path, line, line)
    with pytest.raises(DatasetError, match="duplicate id"):
        load_cases(path)