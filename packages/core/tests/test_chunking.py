"""Chunker tests: size limit, packing, overlap, bade paragraphs, aur galat config."""
import pytest

from core.ingestion.chunking.recursive import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_one_chunk():
    chunks = chunk_text("hello world", max_tokens=10, overlap_tokens=2)
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"
    assert chunks[0].token_count == 2


def test_no_chunk_exceeds_max_tokens():
    text = "\n\n".join(" ".join(f"w{i}_{j}" for j in range(37)) for i in range(20))
    chunks = chunk_text(text, max_tokens=50, overlap_tokens=5)
    assert all(c.token_count <= 50 for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_small_paragraphs_are_packed_with_overlap():
    a = " ".join(f"a{i}" for i in range(60))
    b = " ".join(f"b{i}" for i in range(60))
    chunks = chunk_text(f"{a}\n\n{b}", max_tokens=100, overlap_tokens=10)
    assert len(chunks) == 2
    assert chunks[1].text.startswith("a50 a51")
    assert chunks[1].text.endswith("b59")


def test_oversized_paragraph_is_windowed_with_overlap():
    words = [f"w{i}" for i in range(500)]
    chunks = chunk_text(" ".join(words), max_tokens=100, overlap_tokens=20)
    assert all(c.token_count <= 100 for c in chunks)
    first, second = chunks[0].text.split(), chunks[1].text.split()
    assert first[-20:] == second[:20]


@pytest.mark.parametrize("max_tokens,overlap", [(0, 0), (10, 10), (10, -1)])
def test_invalid_config_is_rejected(max_tokens, overlap):
    with pytest.raises(ValueError):
        chunk_text("some text", max_tokens=max_tokens, overlap_tokens=overlap)