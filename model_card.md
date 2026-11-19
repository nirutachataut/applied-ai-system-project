# PawPal+ Model and Responsible-AI Card

PawPal+ combines a deterministic pet-care scheduler with an optional
retrieval-augmented generative assistant. The runtime AI is used only for
general guidance; it does not make scheduler decisions or replace the
user's judgment.

## Intended Use

PawPal+ is intended for pet owners who want to organize routine care tasks and
ask general questions about dog care, cat care, exercise, feeding and hydration,
grooming, and daily planning. The assistant should explain general guidance,
show supporting public sources, and encourage professional review where
appropriate.

The model must answer from retrieved passages and must not present unsupported
medical diagnoses or treatment instructions. Scheduling remains a rules-based
feature independent of the API.

## Limitations and Biases

- TF-IDF can miss paraphrases or favor keyword overlap over meaning.
- The knowledge base is a small curated set and may not cover uncommon, regional,
  breed-specific, age-specific, or medical situations.
- Public guidance is general and cannot represent every individual animal.
- Generated wording can oversimplify or combine sources incorrectly.
- No persistent memory or longitudinal health record is used.
- The system has limited pet context and should not infer details not supplied
  by the owner.
- Source availability or model behavior may vary outside this environment.

## Reliability and Evaluation

Automated tests cover document loading, relevant retrieval, dog/cat queries,
empty and irrelevant questions, missing knowledge files, missing credentials,
mocked API failures, prompt context, source references, and original scheduling
behavior. Real Gemini calls require a valid key and network access. No live key
was available during validation, so model behavior was tested with mocks and
retrieval was tested locally.

The UI shows retrieved passages and URLs for human review. It also reports
uncertainty or API errors. These safeguards reduce unsupported output but do
not guarantee medical accuracy.

## Potential Misuse and Safeguards

A user could misuse the assistant as a veterinary diagnostic tool or follow
general guidance without considering an individual pet's needs. PawPal+ mitigates
this by:

- Restricting model answers to retrieved context.
- Prohibiting diagnosis and prescribed treatment in the prompt.
- Showing source URLs and the retrieved passages.
- Displaying uncertainty when retrieval finds no relevant passage.
- Keeping deterministic scheduling separate from AI output.
- Requiring human review and professional care for individual concerns.

API keys are read from environment variables or Streamlit secrets, never
hardcoded in source. Logs record event and error types, not API keys or raw
questions.

## What Was Surprising During Testing

Testing showed that keyword overlap alone can retrieve a generic or wrong
species passage. Small title/topic boosts and a relevance threshold improved
dog, cat, grooming, and exercise retrieval. It was also surprising how often
integration failures came from missing credentials or malformed UI state rather
than model logic. Mocked tests were therefore useful for verifying prompt
construction and error handling.

## How AI Tools Assisted Development

GitHub Copilot and Google Gemini were development assistants. Copilot can assist
with code, tests, and documentation, while Gemini can help explore design ideas.
Neither tool is the runtime RAG model. The runtime model is a separately
configured Google Gemini API call after local retrieval.

All AI-assisted code and wording should be reviewed and tested. API calls,
retrieval thresholds, dependencies, and model behavior must be verified against
the repository rather than assumed to be correct.

## Draft for Personal Review

> The following draft is marked for the author to personalize after reviewing
> the actual development process and testing experience.

### One AI Suggestion I Accepted

I accepted using TF-IDF with local Markdown files instead of a paid vector
database or external indexing service. This made the RAG implementation easy to
run, inspect, and test while preserving source attribution.

### Why I Accepted It

The smaller implementation matched a college project, kept knowledge and code
reproducible, and allowed a genuine retrieval step without unnecessary
infrastructure. It also supported clear tests for retrieval relevance and
missing documents.

### One AI Suggestion I Rejected or Modified

I modified an initial architecture proposal that placed Gemini retrieval or
generation in front of the scheduler and could make scheduling depend on an API.
I kept the original deterministic scheduler independent and added RAG as a
separate optional UI feature.

### Why I Modified It

Scheduling behavior should remain available when credentials or the network
fail. Separating the workflows also preserves existing test behavior and makes
human review of AI guidance explicit.
