# PawPal+ Reflection and System Card

PawPal+ is a rule-based pet-care planning application, not a deployed
machine-learning model. This card describes what the code does, where human
judgment is needed, and which personal reflections still need the author's
confirmation.

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

## Limitations and Potential Biases

- The priority-first, greedy scheduler does not search for the best overall
  combination of tasks. A long high-priority task can leave too little time
  for multiple lower-priority tasks that might together be more useful.
- Plan generation does not filter tasks by due date or assign them to
  scheduled time slots. Due dates and times are used for task display and
  conflict checking, not for selecting the generated plan.
- Conflict checking warns about overlapping pending tasks with valid times
  and the same date, but it does not resolve or remove the conflict.
  Cross-midnight overlaps are not detected.
- The result depends on accurate durations, priorities, and task details.
  The app cannot infer that an owner has entered an unrealistic duration or
  forgotten an important task.
- Pet care needs differ by age, health, species, and individual circumstances.
  The scheduler does not model those differences. It treats tasks according
  to their entered priority and duration; owner preferences are not used.
- The available-time field assumes a single usable time budget. Emergencies,
  changing availability, travel time, and other unexpected events are not
  represented.
- Task data is kept in Streamlit session state rather than a persistent
  database. The application has not been validated for medical or veterinary
  decisions.
- Missing or invalid date/time information is ignored by conflict detection,
  so a warning may not be produced for incomplete task data.

These are limitations of the implemented logic, not measured fairness or
accuracy findings.

## Potential Misuse and Prevention

A user could treat the generated plan as complete or authoritative, follow an
unrealistic schedule without checking it, or mistake organization support for
professional pet-care guidance. A conflict warning does not fix a schedule:
both tasks may still appear in the generated plan. The app does not currently
display a veterinary disclaimer in its interface.

**Protections currently implemented**

- The Streamlit form constrains available time to non-negative values,
  duration to 1–240 minutes, and priority to low, medium, or high. It asks for
  a pet before enabling task entry and warns when the pet name is blank.
- The scheduler displays reasons for selected or skipped tasks.
- The app displays conflict warnings so the owner can inspect overlaps; it
  does not silently reschedule tasks.
- Users can review the output, change owner settings or task form values,
  add tasks, and generate the plan again.

These checks do not prove that a duration or plan is realistic. The form does
not validate every field (for example, task titles can be blank), and direct
Python callers can construct values outside the UI constraints.

**Additional safeguards proposed for future work**

- Add a clear in-app notice that PawPal+ is not veterinary advice and that
  owners should confirm care requirements with a qualified professional.
- Validate required task details and provide clear feedback for malformed or
  incomplete data, including direct API use.
- Make unresolved conflicts and assumptions more prominent, and let users
  edit or reschedule existing tasks rather than only adding tasks or
  completing them.
- Ask the owner to confirm a generated plan before treating it as final.

## Reliability Testing Reflection

The saved pytest run reports **26 tests passed and 0 failed**. Tests exercise
model operations, sorting, filtering, daily and weekly recurrence, plan
selection under a time budget, completed and non-positive-duration tasks,
empty schedules, missing optional schedule details, and conflict detection
for overlaps, back-to-back tasks, different dates, and invalid or incomplete
conflict inputs. The recorded output is in
[tests/test_results.txt](tests/test_results.txt). A separate Streamlit
`AppTest` startup check also passed without app exceptions; it emitted a
bare-mode `ScriptRunContext` warning.

During test development, an initial assertion expected a priority label in
the explanation for an invalid-duration task. The observed implementation
omits that label for this case, so the assertion was corrected and the final
suite passed. This was a mismatch in the test expectation, not an application
failure. Testing also confirms that conflict warnings are produced for
tested same-date overlaps, but the scheduler does not resolve them.

**What surprised me — personal reflection needed:** The repository records
the test behavior above, but it does not document what personally surprised
the author. [Complete this sentence in your own words: “While testing
reliability, I was surprised that …”] Do not treat the initial assertion
mismatch as a personal reaction unless that reflects your experience.

Passing tests demonstrate those tested software behaviors only. They do not
show that every care plan is appropriate, and no formal human-evaluation
study, interactive UI test suite, or cross-midnight conflict test has been
recorded.

## Collaboration With AI

The existing [project reflection](reflection.md) reports using AI assistance
to draft the UML and class skeletons, implement methods, review code, suggest
tests, connect the backend to Streamlit, and help with documentation. It also
describes checking suggestions against the source code and tests. The
repository does not preserve the exact prompts or a complete conversation
log, so the decisions below are summarized from that reflection rather than
quoted as verbatim AI messages.

### AI Suggestion I Accepted

The reflection documents an AI-assisted comparison between direct pairwise
conflict checks and grouping/sorting tasks. The design decision recorded
there is to keep the simpler pairwise comparison: it is readable, fits the
small schedules in this project, and the reflection says it was checked with
overlap, back-to-back, different-date, and invalid-input tests.

**Author confirmation:** [Confirm that this describes a suggestion you
accepted. The exact AI wording is not recorded; revise this section if your
recollection differs.]

### AI Suggestion I Rejected or Modified

The reflection records not accepting a suggestion to add functionality while
still building the class skeletons; that work was deferred until the later
implementation phase to follow the assignment steps. This is documented as a
delay, not a permanent rejection.

**Author confirmation:** [Confirm that this accurately describes the
suggestion and your decision. The exact prompt and wording are not recorded.]

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
