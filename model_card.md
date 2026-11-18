# PawPal+ Reflection and System Card

PawPal+ is a rule-based pet-care planning application, not a deployed
machine-learning model. This card describes what the code does, where human
judgment is needed, and the author's reflections on developing and testing
the project.

## System Overview

PawPal+ is intended for pet owners who want to organize routine care tasks.
Through a Streamlit interface, a user can enter owner availability and
preferences, add pets and care tasks, track completion, and request a daily
plan. The `Scheduler` orders tasks by priority, includes positive-duration
pending tasks while they fit the available-time budget, explains its
selections, and reports some schedule conflicts.

The application does not use a trained AI model, a generative agent, or a
retriever at runtime. The scheduling decisions are deterministic rules.
Preferences are stored but do not influence the generated plan. PawPal+ is an
organizational aid, not veterinary or medical advice.

## Reflection and Responsible AI

### 1. What are the limitations or biases in your system?

PawPal+ depends on the information entered by the user. If information is
incorrect or an important task is missing, the schedule might not be accurate.
The system uses predefined scheduling rules and cannot fully understand each
pet's individual needs or handle unexpected situations. Different pets have
different routines, so the same scheduling approach might not be suitable for
everyone.

The scheduler selects tasks by priority and available time. It does not use
owner preferences or due dates to build the plan, and it warns about some
overlaps without resolving them. These limitations reflect the implemented
rules; no fairness or accuracy study has been conducted.

The available-time value is treated as one total time budget. The plan does
not assign tasks to time slots or account for travel, changing availability,
or emergencies. Conflict checks cover valid scheduled tasks on the same date;
they do not detect cross-midnight overlaps, and missing or invalid schedule
details can prevent a warning. Application data is held in Streamlit session
state rather than saved in a persistent database.

### 2. Could your AI be misused, and how would you prevent that?

Users might rely too much on a generated schedule without checking whether it
suits their pet, especially if the pet needs special care or medical
attention. PawPal+ is meant to help organize daily tasks, not replace advice
from a veterinarian. Users should review the schedule and any conflict
warnings before following it.

The application currently shows reasons for selected or skipped tasks and
displays detected conflict warnings. Its Streamlit form also constrains
available time to non-negative values, task duration to 1–240 minutes, and
priority to low, medium, or high. It requires a pet before enabling task
entry and warns when the pet name is blank. These checks do not guarantee
that a plan is realistic: conflict warnings do not change the plan, task
titles are not validated, direct Python callers can bypass the form
constraints, and the interface does not currently show a veterinary
disclaimer. A clear in-app notice and stronger input validation would be
useful future safeguards.

### 3. What surprised you while testing your AI's reliability?

What surprised me was how important it is to test small details, not just
whether the program runs. I learned that even a simple scheduling system
needs to handle situations like conflicting tasks, different priorities, and
missing information. Testing helped me understand that a program can appear
to work correctly but still need checks for unusual situations. It also
showed me why automated tests are useful for making a project more reliable.

The recorded pytest run reports **26 tests passed and 0 failed**. The tests
cover model behavior, sorting, filtering, recurrence, plan selection,
priorities and time limits, empty schedules, missing optional schedule
details, and conflict detection for overlaps and invalid or ineligible tasks.
A separate Streamlit `AppTest` startup check passed without app exceptions;
it emitted a bare-mode `ScriptRunContext` warning. The actual command output
is in [tests/test_results.txt](tests/test_results.txt). These tests verify
the behaviors they exercise, not whether a care plan is appropriate for every
pet. There is no full interactive UI test or formal human-evaluation study.

### 4. How did you collaborate with AI during this project?

I used AI assistance to help me understand the project requirements, review
my code, improve documentation, and identify useful test cases. AI also
helped me understand how to organize the system architecture and explain how
the components work together. I reviewed suggestions against the project
instead of assuming they were correct.

#### One AI suggestion I accepted

I accepted the suggestion to create a Mermaid system architecture diagram.
It helped me show how the user interface, scheduling system, and testing
components connect, making the project easier to understand and explain.

#### One AI suggestion I modified

I modified the suggestion to include more advanced AI components, such as an
AI agent or retriever, in the system architecture. PawPal+ currently uses
rule-based scheduling, so I kept the diagram focused on components that
actually exist. This kept the diagram simple and accurate.

### 5. What did you learn from this project?

This project taught me that building a useful system is not just about
writing code. It is also important to test the program, understand its
limitations, and explain how it works. I learned how AI assistance can help
with development, but I also realized that I need to review its suggestions
and make my own decisions instead of accepting everything automatically.

## Responsible AI and Human Oversight

The owner sees the selected tasks, the scheduler's explanations, and
conflict warnings, and remains responsible for deciding whether the plan is
suitable. The owner can change available time or other form inputs and
generate a new plan. Existing tasks cannot be directly edited in the UI;
users can add tasks or mark them complete.

Automated tests help catch regressions in the deterministic model and
scheduling behavior, but they do not establish that the schedule is safe or
appropriate for a particular pet. The existing reflection describes
reviewing AI-assisted code and running the demo and tests. AI-generated code,
like the scheduler's output, should be checked against requirements and
observed behavior rather than trusted automatically. No model confidence
score or AI accuracy metric is available or claimed.

## Future Improvements

- Add stronger validation for required fields and direct Python inputs.
- Support editable tasks and scheduling preferences, while explaining how
  those preferences affect the plan.
- Consider due dates and scheduled times in plan generation and add
  cross-midnight conflict handling.
- Add automated tests for more planner edge cases and interactive Streamlit
  workflows, and conduct a documented human review using a consistent rubric.
- If an AI-powered feature is added later, keep it clearly separate from the
  current rules, evaluate it on appropriate cases, and preserve human review.
