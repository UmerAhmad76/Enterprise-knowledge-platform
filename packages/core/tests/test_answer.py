"""Answer flow tests: ACL-filtered chunks hi prompt mein jayein, khaali chunks par LLM call na ho, aur citations sahi hon."""
from core.generation.answer import NO_SOURCES_TEXT, SourceChunk, generate_answer
from core.llm.fake import FakeLLM
from core.llm.prompts import DEFAULT_PROMPT_VERSION


def make_chunks() -> list[SourceChunk]:
    return [
        SourceChunk(chunk_id="c1", document_id="d1", title="Leave Policy", text="Employees get 20 days."),
        SourceChunk(chunk_id="c2", document_id="d2", title="Salary", text="Reviews happen in March."),
    ]


def test_prompt_contains_only_the_given_chunks():
    llm = FakeLLM(reply="Employees get 20 days [1].")
    generate_answer("how many leave days?", make_chunks(), llm)

    user_msg = llm.calls[0]["user"]
    assert "Employees get 20 days." in user_msg
    assert "Reviews happen in March." in user_msg
    assert "[1] Leave Policy" in user_msg


def test_citations_resolve_to_the_right_chunk():
    llm = FakeLLM(reply="Employees get 20 days [1].")
    answer = generate_answer("leave?", make_chunks(), llm)

    assert [c.chunk_id for c in answer.citations] == ["c1"]
    assert answer.invalid_citation_numbers == []


def test_invalid_citation_is_reported_not_silently_kept():
    llm = FakeLLM(reply="Something [7].")
    answer = generate_answer("q", make_chunks(), llm)
    assert answer.citations == []
    assert answer.invalid_citation_numbers == [7]


def test_no_chunks_means_no_llm_call():
    llm = FakeLLM()
    answer = generate_answer("q", [], llm)
    assert answer.text == NO_SOURCES_TEXT
    assert llm.calls == []


def test_answer_records_prompt_version_and_model():
    answer = generate_answer("q", make_chunks(), FakeLLM())
    assert answer.prompt_version == DEFAULT_PROMPT_VERSION
    assert answer.model_name == "fake-llm"