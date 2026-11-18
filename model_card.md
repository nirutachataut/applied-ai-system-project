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

The application does not use a trained AI model, a generative agent, a
retriever, or a Gemini API at runtime. The scheduling decisions are
deterministic rules. GitHub Copilot and Google Gemini were used during
development only; neither is integrated into the application. Preferences
are stored but do not influence the generated plan. PawPal+ is an
organizational aid, not veterinary or medical advice.

## Reflection and Responsible AI

### 1. What are the limitations or biases in your system?

PawPal+ depends on accurate information from the user. If information is
incorrect or an important task is missing, the schedule might not be
accurate. It uses predefined scheduling rules and may not account for every
pet's individual needs, emergencies, or unexpected changes in daily routines.
Different pets have different routines, so the same scheduling approach might
not be suitable for everyone.

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

Users might rely too heavily on generated schedules without checking whether
they meet their pets' needs. Users should review schedules and any conflict
warnings before following them. PawPal+ helps organize daily tasks and does
not replace professional veterinary advice.

The application currently shows reasons for selected or skipped tasks and
displays detected conflict warnings. Its Streamlit form constrains available
time to non-negative values, task duration to 1–240 minutes, and priority to
low, medium, or high. It requires a pet before enabling task entry and
rejects blank task titles. These checks do not guarantee that a plan is
realistic: conflict warnings do not change the plan, direct Python callers
can bypass form constraints, and the interface does not currently show a
veterinary disclaimer. A clear in-app notice and stronger validation for
direct inputs would be useful future safeguards.

### 3. What surprised you while testing your AI's reliability?

What surprised me during testing was how important it is to check small details instead of only checking whether the application runs. I learned that scheduling conflicts, priorities, and missing information all need to be handled carefully.

The recorded pytest run reports **27 tests passed and 0 failed**. The tests
cover model behavior, sorting, filtering, recurrence, plan selection,
priorities and time limits, empty schedules, missing optional schedule
details, conflict detection for overlaps and invalid or ineligible tasks,
and rejection of a blank task title in the Streamlit interface. A separate
Streamlit `AppTest` startup check passed without app exceptions; it emitted
a bare-mode `ScriptRunContext` warning. The actual command output is in
[tests/test_results.txt](tests/test_results.txt). These tests verify the
behaviors they exercise, not whether a care plan is appropriate for every
pet. There is no full interactive UI test or formal human-evaluation study.

### 4. How did you collaborate with AI during this project?

During this project, I used GitHub Copilot and Google Gemini to help me develop PawPal+. Copilot helped me write and review code, debug problems, improve testing, and organize my project. I also used Gemini to understand concepts better, explore ideas, and get additional suggestions.

#### One AI suggestion I accepted

One AI suggestion I accepted was creating a Mermaid system architecture diagram. It helped me understand how the different parts of my project connect and made the system easier to explain.

#### One AI suggestion I modified

One suggestion I modified was including advanced AI components that were not actually part of my application. Instead, I kept the diagram focused on the scheduling system and existing features so it accurately represents my project.

This project taught me that AI tools can be very helpful during development, but I still need to review their suggestions and make decisions myself.

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
