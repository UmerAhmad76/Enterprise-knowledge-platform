"""Citation tests: numbers sahi nikalte hain, duplicates hatte hain, aur invalid numbers pakde jate hain."""
from core.generation.citations import Citation, extract_citation_numbers, resolve_citations


def make_map(*numbers: int) -> dict[int, Citation]:
    return {
        n: Citation(number=n, chunk_id=f"c{n}", document_id=f"d{n}", title=f"T{n}")
        for n in numbers
    }


def test_extracts_numbers_in_order_without_duplicates():
    assert extract_citation_numbers("A [2] and B [1], again [2].") == [2, 1]


def test_no_citations_gives_empty_list():
    assert extract_citation_numbers("No sources used.") == []


def test_valid_citations_are_resolved_to_chunks():
    used, invalid = resolve_citations("Yes [1] and [3].", make_map(1, 2, 3))
    assert [c.chunk_id for c in used] == ["c1", "c3"]
    assert invalid == []


def test_hallucinated_citation_number_is_reported_as_invalid():
    used, invalid = resolve_citations("Claim [1] and fake [9].", make_map(1))
    assert [c.chunk_id for c in used] == ["c1"]
    assert invalid == [9]