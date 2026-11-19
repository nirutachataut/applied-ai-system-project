from pathlib import Path

import pytest

from rag import (
    MissingApiKeyError,
    MissingKnowledgeBaseError,
    ModelResponseError,
    PetCareRetriever,
    answer_question,
    build_rag_prompt,
    load_knowledge_documents,
    resolve_api_key,
)


KNOWLEDGE_DIR = Path(__file__).parents[1] / "knowledge_base"


@pytest.fixture
def retriever():
    return PetCareRetriever(load_knowledge_documents(KNOWLEDGE_DIR))


def test_knowledge_documents_load_successfully():
    chunks = load_knowledge_documents(KNOWLEDGE_DIR)
    assert chunks
    assert all(chunk.title for chunk in chunks)
    assert all(chunk.source_url.startswith("https://") for chunk in chunks)


@pytest.mark.parametrize(
    ("question", "expected_title"),
    [
        ("How often should I walk my dog?", "Dog Care Basics"),
        ("What are important daily care activities for a cat?", "Cat Care Basics"),
    ],
)
def test_retrieval_returns_species_relevant_passages(
    retriever, question, expected_title
):
    results = retriever.retrieve(question)
    assert results
    assert expected_title in {chunk.title for chunk in results}


def test_retrieval_handles_exercise_and_grooming_questions(retriever):
    exercise = retriever.retrieve("How can I keep my pet mentally stimulated?")
    grooming = retriever.retrieve("What are general pet grooming recommendations?")
    assert exercise
    assert grooming
    assert any("Exercise" in chunk.title for chunk in exercise)
    assert any("Grooming" in chunk.title for chunk in grooming)


def test_empty_question_is_rejected(retriever):
    with pytest.raises(ValueError, match="Please enter"):
        answer_question("   ", retriever, model_call=lambda prompt: "unused")


def test_irrelevant_question_is_handled_safely(retriever):
    with pytest.raises(ValueError, match="could not find relevant"):
        answer_question(
            "What is the capital of France?",
            retriever,
            model_call=lambda prompt: "unsupported answer",
        )


def test_missing_knowledge_directory_is_handled_gracefully(tmp_path):
    with pytest.raises(MissingKnowledgeBaseError):
        load_knowledge_documents(tmp_path / "missing")


def test_missing_knowledge_documents_are_handled_gracefully(tmp_path):
    (tmp_path / "notes.txt").write_text("not markdown", encoding="utf-8")
    with pytest.raises(MissingKnowledgeBaseError):
        load_knowledge_documents(tmp_path)


def test_missing_api_credentials_produce_understandable_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="Gemini API key"):
        resolve_api_key()


def test_api_failure_does_not_crash_answer_pipeline(retriever):
    def failed_model(prompt):
        raise ModelResponseError("AI generation failed due to an API error.")

    with pytest.raises(ModelResponseError, match="API error"):
        answer_question(
            "How often should I walk my dog?",
            retriever,
            model_call=failed_model,
        )


def test_retrieved_passages_are_passed_to_model_prompt(retriever):
    captured = {}

    def mock_model(prompt):
        captured["prompt"] = prompt
        return "A grounded general-care response."

    result = answer_question(
        "How often should I walk my dog?",
        retriever,
        model_call=mock_model,
        pet_context="Buddy: species=dog; pending_tasks=Walk Buddy",
    )

    assert "Retrieved context:" in captured["prompt"]
    assert "Buddy: species=dog" in captured["prompt"]
    assert any(chunk.text in captured["prompt"] for chunk in result.sources)
    assert result.prompt == captured["prompt"]


def test_sources_are_returned_with_generated_answer(retriever):
    result = answer_question(
        "What are some general pet grooming recommendations?",
        retriever,
        model_call=lambda prompt: "Brush safely and consult a professional.",
    )

    assert result.answer
    assert result.sources
    assert all(source.title for source in result.sources)
    assert all(source.source_url for source in result.sources)


def test_build_prompt_includes_context_and_uncertainty_guardrail(retriever):
    chunks = retriever.retrieve("How should I plan a daily pet-care routine?")
    prompt = build_rag_prompt(
        "How should I plan a daily pet-care routine?",
        chunks,
        "Mochi: species=cat; pending_tasks=Feed Mochi",
    )
    assert "Daily Pet-Care Planning" in prompt
    assert "Mochi: species=cat" in prompt
    assert "Do not diagnose illness" in prompt
