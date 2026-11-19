# PawPal+

PawPal+ is a Python and Streamlit pet-care planning application created for
CodePath AI110. It began as a Module 2 project for representing pets and care
tasks and building an explained daily schedule. It now includes local
retrieval-augmented generation (RAG) for general pet-care questions.

## Project Goals

The original PawPal+ goals were to:

- Represent owners, pets, and care tasks.
- Prioritize pending tasks and respect an available-time budget.
- Explain scheduling decisions.
- Detect overlapping scheduled intervals.
- Support recurrence, filtering, sorting, and task completion.

The final project keeps those deterministic features and adds an optional
**AI Pet Care Assistant** that searches a local knowledge base before asking a
generative model for an answer.

## What RAG Adds

Retrieval-augmented generation (RAG) first searches local reference material,
adds relevant passages to the model prompt, and asks the model to answer only
from that context. It is useful for PawPal+ because general pet-care guidance
can change over time, and source attribution makes answers more reviewable than
answers generated from model memory alone.

The implementation in `rag.py`:

1. Loads Markdown documents from `knowledge_base/`.
2. Splits each document into searchable chunks.
3. Uses TF-IDF and cosine similarity to retrieve relevant passages.
4. Adds those passages and user-provided pet/task context to a Gemini prompt.
5. Returns an answer and source URLs.
6. Communicates missing sources, missing credentials, irrelevant questions,
   and model failures without replacing the scheduler.

Retrieved context materially changes the model input: each answer prompt
contains passages, document titles, source URLs, and explicit instructions not
to diagnose or prescribe treatment. The model receives no claim that is outside
the retrieved context.

## Features

- Owner availability and preference entry.
- Multiple pets and species selection.
- Care-task creation with duration, priority, due date, scheduled time, and
  recurrence.
- Priority and available-time scheduling with written explanations.
- Same-date scheduling conflict detection.
- Pet/status filtering, sorting, completion, and recurring-task creation.
- AI assistant question validation.
- Local TF-IDF document retrieval and source attribution.
- Gemini runtime model integration with environment or Streamlit secret keys.
- Friendly handling of missing credentials and model/API errors.

## Architecture

The Streamlit interface in `app.py` updates the `Owner`, `Pet`, and `Task`
models in `pawpal_system.py`. `Scheduler` remains independent of API credentials
and produces the deterministic daily plan and conflict warnings.

The RAG workflow is separate:

```text
Pet owner -> Streamlit question -> validation -> TF-IDF retriever
-> knowledge-base chunks -> retrieved context -> Gemini prompt
-> grounded answer -> source display -> human review
```

The editable Mermaid architecture diagram is
[diagrams/system_architecture.mmd](diagrams/system_architecture.mmd).

## Installation

Python 3.11 is recommended.

```bash
cd applied-ai-system-project
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## API Configuration

The runtime model is Google Gemini. Create a Gemini API key, then set:

```bash
export GEMINI_API_KEY="your-key"
```

Streamlit can also read `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key"
```

Do not commit `.env`, `.streamlit/secrets.toml`, or an API key. A sample
environment file is [.env.example](.env.example).

If no key is configured, scheduling and all deterministic features remain
available. The AI section reports that generation is unavailable.

## Launch

Run the Streamlit application:

```bash
streamlit run app.py
```

Run the command-line demonstration:

```bash
python3 main.py
```

Run all tests:

```bash
python3 -m pytest -v
```

## Sample RAG Interactions

These examples execute the real retrieval and prompt pipeline with a mock model
call. They are included to demonstrate the integrated flow because no Gemini API
key was available in the development environment. They are **not live Gemini
responses**.

### 1. Dog walking

**Input:**

```text
How often should I walk my dog?
```

**Retrieved source:**

- [Dog Care Basics](https://www.avma.org/resources-tools/pet-owners/petcare/dog-care)

**Mocked model output produced by the test pipeline:**

```text
Walking needs vary by the individual dog. The retrieved guidance says to
provide physical activity appropriate to age, health, size, and breed, and to
ask a veterinarian for an individual plan.
```

### 2. Cat care

**Input:**

```text
What are important daily care activities for cats?
```

**Retrieved source:**

- [Cat Care Basics](https://www.avma.org/resources-tools/pet-owners/petcare/cat-care)

**Mocked model output produced by the test pipeline:**

```text
The retrieved guidance highlights fresh water, species-appropriate feeding,
regular litter-area care, enrichment, rest, and routine veterinary care.
```

### 3. Mental stimulation

**Input:**

```text
How can I keep my pet mentally stimulated?
```

**Retrieved source:**

- [Exercise and Mental Enrichment](https://www.rspcapetinsurance.org.au/pet-care/dogs-and-cats/exercise-and-mental-stimulation)

**Mocked model output produced by the test pipeline:**

```text
The retrieved guidance suggests supervised play, training games, food puzzles,
rotating toys, and climbing opportunities for cats, with activities adjusted
to age, mobility, health, and preferences.
```

The live model can change wording, but the application still supplies the same
retrieved passages and source URLs in the prompt. No live end-to-end Gemini
request is claimed in this README.

## Design Decisions and Trade-offs

- **TF-IDF:** Simple, local, reproducible, and dependency-light. It does not
  understand semantic meaning as strongly as embeddings.
- **Markdown knowledge base:** Easy to inspect and extend. Each file records a
  public source URL.
- **Topic/species boosts:** Small tie-breaking boosts help common dog, cat,
  exercise, grooming, and planning queries.
- **Similarity threshold:** Prevents clearly unrelated questions from reaching
  generation.
- **Gemini `gemini-2.5-flash`:** A supported generative runtime model. The exact
  model availability may vary by account and region.
- **No medical diagnosis:** Prompts prohibit unsupported diagnosis or
  prescriptions and advise professional help.
- **Session-only state:** Streamlit state is not persisted in a database.
- **Human review:** Sources and retrieved passages are visible for inspection.

## Testing

The automated suite covers both original scheduling behavior and RAG behavior:

- Knowledge files load successfully.
- Dog, cat, exercise, grooming, and planning queries retrieve passages.
- Blank and irrelevant questions are handled safely.
- Missing directories/files and missing API credentials are handled.
- Mocked model failures do not escape as unhandled app errors.
- Retrieved text is included in the model prompt.
- Answer results contain source references.
- Original scheduler, recurrence, filtering, and conflict tests remain intact.

The final test count and command output are saved in
[tests/test_results.txt](tests/test_results.txt).

No Gemini API key was available during validation. Therefore tests for model
integration use mocks, and no real end-to-end Gemini response is claimed.

## Known Limitations

- TF-IDF retrieval can miss paraphrases or semantically related wording.
- The knowledge base is a small curated subset of general pet-care guidance.
- The source documents are not continuously updated.
- Gemini availability depends on account configuration, rate limits, and network.
- The assistant is not a veterinarian and cannot personalize medical advice
  safely.
- Streamlit state is in-memory and not persistent.
- No formal human evaluation of answer usefulness or factual accuracy was
  performed.

## Reflection

PawPal+ demonstrates the difference between deterministic scheduling and
retrieval-grounded generation. The scheduler remains explainable and
API-independent, while RAG improves answer traceability and gives the assistant
a bounded information source. The project also shows that integration requires
source attribution, guardrails, mocks, credential handling, and regression tests
for existing behavior. Responsible deployment requires continued review of
source quality and professional advice for individual medical concerns.
