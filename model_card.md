# PawPal+ Model and Responsible-AI Card

PawPal+ is a Streamlit pet-care planning application with a local
retrieval-augmented Gemini assistant. Its scheduler is deterministic and
independent of API credentials. The AI assistant is a general-information
feature, not a medical system.

## Intended Use

PawPal+ helps a pet owner track pets and care tasks, generate a time-bounded
daily plan, identify schedule overlaps, and ask general questions about dog
care, cat care, feeding, hydration, exercise, grooming, daily routines, and
preventive care.

The assistant retrieves local reference passages before model generation.
Generated answers should be limited to retrieved context and shown with source
links. Human review remains required.

## Limitations and Biases

- TF-IDF may miss semantically similar wording or rank keyword matches poorly.
- The knowledge base contains a small curated set of general references.
- Public guidance cannot represent every breed, age, health state, region, or
  individual animal.
- Retrieved passages are not continuously verified or updated.
- Species boosts improve common dog/cat queries but do not replace individualized
  retrieval or veterinary judgment.
- Gemini can still phrase information incompletely or combine passages incorrectly.
- The application does not persist health records and should not infer facts
  that the user did not provide.
- A live Gemini request succeeded with `gemini-flash-lite-latest` after
  model discovery and 404/503/504 testing. Live 404 responses with earlier
  model choices were identified as model/API availability issues.

## Reliability and Evaluation

The pytest suite tests original scheduler behavior, document loading, dog/cat
retrieval, exercise and grooming retrieval, blank and irrelevant questions,
missing files, missing credentials, mocked API failures, source attribution,
and injection of retrieved context into prompts.

A labeled 10-case dataset measures document Hit@3. Actual local evaluation
result: **9 of 10 cases, or 90% Hit@3**. This is an automatically measured
retrieval metric, not a human assessment of answer accuracy or medical
appropriateness.

Testing also revealed that generic species wording can rank the wrong document
if TF-IDF weighting is not balanced by topic boosts. The retriever now combines
cosine similarity with modest species and topic boosts.

## Potential Misuse and Safeguards

The assistant could be misused as a diagnosis tool, dosing guide, or emergency
substitute. It could also receive a schedule-changing request. The implementation
reduces these risks by:

- Requiring relevant retrieved context before generation.
- Telling the model not to diagnose, prescribe, dose, or invent personal details.
- Returning uncertainty for irrelevant or unsupported questions.
- Displaying expandable retrieved passages and source URLs.
- Keeping scheduling deterministic and independent of AI output.
- Never modifying tasks automatically based on an AI response.
- Prompting users to consult a qualified professional for individual concerns.
- Keeping API keys in environment variables or Streamlit secrets.
- Logging event types and error classes without raw user questions or credentials.

## What Was Surprising During Testing

The evaluation showed that plausible keyword matches can be misleading. A
generic cat question may initially retrieve daily-planning or dog text unless
species and topic signals are balanced. It was also clear that robust integration
depends more than model calls: missing files, missing credentials, malformed
responses, and user-interface state need explicit tests.

## How AI Assisted Development

GitHub Copilot provided development assistance for code organization, tests,
debugging, and documentation. Gemini was explored as a development tool, but
Copilot and Gemini development suggestions are separate from the runtime
application.

The PawPal+ runtime uses the Google Gemini SDK only after local retrieval.
Runtime calls are grounded in retrieved context and configured through
`GEMINI_API_KEY` or Streamlit secrets. A live connection and generated responses
were observed successfully with `gemini-flash-lite-latest`; the key itself was
never printed or logged.

## Draft for Author Review

> This marked draft should be personalized after the author reviews the actual
> implementation and testing work.

### One AI Suggestion Accepted

One accepted suggestion was to use TF-IDF and local Markdown documents instead
of a paid vector database or external retrieval service. This kept RAG
reproducible and understandable for a college application.

### Why It Was Accepted

The approach directly satisfies the retrieval workflow, stores inspectable
sources, avoids extra infrastructure, and supports mocked tests and
reproducible Hit@3 evaluation.

### One AI Suggestion Rejected or Modified

One suggestion was to let the assistant directly change care tasks or daily
plans. That behavior was rejected. AI suggestions remain separate from the
deterministic scheduler and require explicit future approval before any task
would be added.

### Why It Was Modified

Automatic schedule changes could silently override priorities, availability,
veterinary instructions, or user intent. Keeping the scheduler final authority
preserves existing behavior and maintains human oversight.
