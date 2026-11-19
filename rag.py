"""Local retrieval and Gemini integration for PawPal+'s pet-care assistant."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


LOGGER = logging.getLogger("pawpal.rag")


class MissingKnowledgeBaseError(Exception):
    """Raised when no usable knowledge documents can be loaded."""


class MissingApiKeyError(Exception):
    """Raised when runtime model credentials are unavailable."""


class ModelResponseError(Exception):
    """Raised when a model call fails or returns an invalid response."""


@dataclass(frozen=True)
class DocumentChunk:
    """A retrieved passage and the source that contains it."""

    text: str
    title: str
    source_url: str
    file_name: str


@dataclass(frozen=True)
class RagResult:
    """A grounded assistant answer and its retrieved sources."""

    answer: str
    sources: list[DocumentChunk]
    retrieved_context: str
    prompt: str


def validate_question(question: str) -> str:
    """Validate and normalize a user question."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a question.")
    normalized = " ".join(question.strip().split())
    if len(normalized) < 5:
        raise ValueError("Please enter a more complete question.")
    return normalized


def load_knowledge_documents(
    knowledge_dir: str | Path,
) -> list[DocumentChunk]:
    """Load markdown documents and split them into searchable chunks."""
    directory = Path(knowledge_dir)
    if not directory.exists() or not directory.is_dir():
        LOGGER.warning("Knowledge base directory is missing")
        raise MissingKnowledgeBaseError(
            "The local pet-care knowledge base is unavailable."
        )

    chunks: list[DocumentChunk] = []
    for path in sorted(directory.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            LOGGER.warning("Could not read knowledge document", extra={"file": path.name})
            continue

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        source_match = re.search(
            r"^Source:\s*(https?://\S+)\s*$", content, re.MULTILINE
        )
        source_url = source_match.group(1).strip() if source_match else ""

        body = re.sub(r"^#.*$", "", content, count=1, flags=re.MULTILINE)
        body = re.sub(r"^Source:\s*https?://\S+\s*$", "", body, flags=re.MULTILINE)
        section_chunks = re.split(r"\n\s*\n", body.strip())
        for section in section_chunks:
            text = " ".join(line.strip() for line in section.splitlines())
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) >= 40:
                chunks.append(
                    DocumentChunk(
                        text=text,
                        title=title,
                        source_url=source_url,
                        file_name=path.name,
                    )
                )

    if not chunks:
        LOGGER.warning("Knowledge base contains no usable documents")
        raise MissingKnowledgeBaseError(
            "The local pet-care knowledge base contains no usable documents."
        )
    LOGGER.info("Loaded knowledge documents", extra={"chunk_count": len(chunks)})
    return chunks


class PetCareRetriever:
    """Retrieve relevant local passages with TF-IDF cosine similarity."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise MissingKnowledgeBaseError(
                "The local pet-care knowledge base contains no usable documents."
            )
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError as exc:
            raise RuntimeError(
                "scikit-learn is required for local knowledge retrieval."
            ) from exc

        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.chunk_matrix = self.vectorizer.fit_transform(
            [chunk.text for chunk in chunks]
        )

    def retrieve(
        self,
        question: str,
        top_k: int = 3,
        similarity_threshold: float = 0.05,
    ) -> list[DocumentChunk]:
        """Return the highest-similarity chunks above a minimum threshold."""
        from sklearn.metrics.pairwise import cosine_similarity

        question_matrix = self.vectorizer.transform([question])
        scores = cosine_similarity(question_matrix, self.chunk_matrix)[0]
        lowered_question = question.lower()
        adjusted_scores = scores.copy()
        for index, chunk in enumerate(self.chunks):
            title = chunk.title.lower()
            if "dog" in lowered_question and "dog" in title:
                adjusted_scores[index] += 0.08
            if "cat" in lowered_question and "cat" in title:
                adjusted_scores[index] += 0.08
            if (
                any(word in lowered_question for word in ("exercise", "walk", "stimulat"))
                and ("exercise" in title or "enrichment" in title)
            ):
                adjusted_scores[index] += 0.06
            if "groom" in lowered_question and "groom" in title:
                adjusted_scores[index] += 0.06
            if (
                any(word in lowered_question for word in ("daily", "routine", "planning"))
                and "daily" in title
            ):
                adjusted_scores[index] += 0.06

        ranked_indexes = adjusted_scores.argsort()[::-1][:top_k]
        results = [
            self.chunks[index]
            for index in ranked_indexes
            if adjusted_scores[index] >= similarity_threshold
        ]
        LOGGER.info(
            "Retrieval completed",
            extra={
                "top_score": round(float(adjusted_scores[ranked_indexes[0]]), 4),
                "retrieved_count": len(results),
            },
        )
        return results


def build_rag_prompt(
    question: str,
    retrieved_chunks: list[DocumentChunk],
    pet_context: str | None = None,
) -> str:
    """Build a prompt that requires the model to ground its answer in context."""
    context = "\n\n".join(
        f"[Source: {chunk.title} | {chunk.source_url}]\n{chunk.text}"
        for chunk in retrieved_chunks
    )
    pet_context_text = (
        f"\nPet and scheduling context provided by the user:\n{pet_context.strip()}\n"
        if pet_context and pet_context.strip()
        else ""
    )
    return (
        "You are a general pet-care information assistant. Answer only from the "
        "retrieved context below. Do not invent facts or personal pet details. "
        "Do not diagnose illness or prescribe treatment. If the context is "
        "insufficient for the question, say that clearly and suggest contacting "
        "a veterinarian or relevant professional. Keep the answer friendly and "
        "practical, and distinguish general guidance from individual care needs.\n"
        f"{pet_context_text}\n"
        "Retrieved context:\n"
        f"{context}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def resolve_api_key(explicit_key: str | None = None) -> str:
    """Resolve a Gemini key from an explicit value or environment."""
    api_key = explicit_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "AI generation is unavailable because no Gemini API key is configured."
        )
    return api_key


def call_gemini(prompt: str, api_key: str | None = None) -> str:
    """Call the configured Gemini model and return a validated text response."""
    key = resolve_api_key(api_key)
    try:
        from google import genai

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise ModelResponseError("The model returned an empty or invalid response.")
        return text.strip()
    except MissingApiKeyError:
        raise
    except Exception as exc:
        LOGGER.warning("Gemini API request failed", extra={"error_type": type(exc).__name__})
        raise ModelResponseError(
            "AI generation failed due to an API, connection, or model error."
        ) from exc


def answer_question(
    question: str,
    retriever: PetCareRetriever,
    model_call: Callable[[str], str] | None = None,
    pet_context: str | None = None,
) -> RagResult:
    """Run validation, retrieval, prompt construction, and model generation."""
    normalized_question = validate_question(question)
    chunks = retriever.retrieve(normalized_question)
    if not chunks:
        LOGGER.info("No relevant knowledge passages retrieved")
        raise ValueError(
            "I could not find relevant pet-care information in the knowledge base "
            "for that question. Please rephrase it or ask about dog, cat, feeding, "
            "grooming, exercise, enrichment, or daily planning."
        )

    prompt = build_rag_prompt(normalized_question, chunks, pet_context)
    if model_call is None:
        model_call = call_gemini
    try:
        answer = model_call(prompt)
    except MissingApiKeyError:
        raise
    except ModelResponseError:
        raise
    except Exception as exc:
        LOGGER.warning(
            "Unexpected model call failure",
            extra={"error_type": type(exc).__name__},
        )
        raise ModelResponseError("AI generation failed unexpectedly.") from exc

    if not isinstance(answer, str) or not answer.strip():
        raise ModelResponseError("The model returned an empty or invalid response.")
    LOGGER.info("RAG answer generated", extra={"source_count": len(chunks)})
    return RagResult(
        answer=answer.strip(),
        sources=list(dict.fromkeys(chunks)),
        retrieved_context="\n\n".join(chunk.text for chunk in chunks),
        prompt=prompt,
    )
