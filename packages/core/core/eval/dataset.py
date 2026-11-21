"""JSONL golden dataset loader. Har line ek case hai, aur adhoori ya galat entry run hone se pehle hi pakdi jaati hai."""
import json
from dataclasses import dataclass
from pathlib import Path

VALID_KINDS = {"quality", "acl"}
REQUIRED_FIELDS = ("id", "kind", "question", "tenant", "user")


class DatasetError(ValueError):
    """Dataset ki file ya kisi line mein galti. Message mein file aur line number hota hai."""


@dataclass(frozen=True)
class EvalCase:
    """Ek test case. quality cases ke liye expected_titles, acl cases ke liye forbidden_titles lazmi hai."""

    id: str
    kind: str
    question: str
    tenant: str
    user: str
    expected_titles: tuple[str, ...] = ()
    forbidden_titles: tuple[str, ...] = ()


def load_cases(path: Path) -> list[EvalCase]:
    """File padhta hai, khaali lines aur # comments skip karta hai, aur duplicate IDs reject karta hai."""
    cases: list[EvalCase] = []
    seen: set[str] = set()
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{path}:{line_no}"
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{where}: invalid JSON ({exc.msg})") from exc

        case = _to_case(row, where)
        if case.id in seen:
            raise DatasetError(f"{where}: duplicate id {case.id}")
        seen.add(case.id)
        cases.append(case)

    if not cases:
        raise DatasetError(f"{path}: no cases found")
    return cases


def _to_case(row: dict, where: str) -> EvalCase:
    missing = [name for name in REQUIRED_FIELDS if not row.get(name)]
    if missing:
        raise DatasetError(f"{where}: missing fields {missing}")
    if row["kind"] not in VALID_KINDS:
        raise DatasetError(f"{where}: kind must be one of {sorted(VALID_KINDS)}")

    expected = tuple(row.get("expected_titles", []))
    forbidden = tuple(row.get("forbidden_titles", []))
    if row["kind"] == "quality" and not expected:
        raise DatasetError(f"{where}: quality case needs expected_titles")
    if row["kind"] == "acl" and not forbidden:
        raise DatasetError(f"{where}: acl case needs forbidden_titles")

    return EvalCase(
        id=row["id"],
        kind=row["kind"],
        question=row["question"],
        tenant=row["tenant"],
        user=row["user"],
        expected_titles=expected,
        forbidden_titles=forbidden,
    )