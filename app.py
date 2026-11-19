"""Streamlit interface for PawPal+ pet-care planning and RAG assistance."""

from datetime import date, time
from pathlib import Path
import os

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task
from rag import (
    MissingApiKeyError,
    MissingKnowledgeBaseError,
    ModelResponseError,
    PetCareRetriever,
    answer_question,
    call_gemini,
    load_knowledge_documents,
)


st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
)


def get_gemini_key() -> str | None:
    """Read the Gemini key from Streamlit secrets or environment variables."""
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
        if isinstance(secret_key, str) and secret_key.strip():
            return secret_key.strip()
    except Exception:
        pass
    environment_key = os.getenv("GEMINI_API_KEY")
    return environment_key.strip() if environment_key else None


def build_pet_context(owner: Owner) -> str | None:
    """Summarize only pet facts already entered by the user."""
    if not owner.pets:
        return None
    parts = []
    for pet in owner.pets:
        pending = [task.title for task in pet.get_tasks() if not task.completed]
        parts.append(
            f"{pet.name}: species={pet.species}; "
            f"pending_tasks={', '.join(pending) if pending else 'none'}"
        )
    return "\n".join(parts)


def selected_species(owner: Owner) -> str | None:
    """Return the selected species for retrieval context."""
    if not owner.pets:
        return None
    return str(owner.pets[0].species)


st.title("🐾 PawPal+")
st.caption("Pet-care planning and retrieval-grounded general guidance")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_time=60,
        preferences=[],
    )

owner = st.session_state.owner
st.session_state.setdefault("daily_plan", [])
st.session_state.setdefault("plan_explanation", "")
st.session_state.setdefault("conflict_warnings", [])
st.session_state.setdefault("completion_message", "")
st.session_state.setdefault("owner_name", owner.name)
st.session_state.setdefault("available_time", owner.available_time)
st.session_state.setdefault("owner_preferences", owner.preferences)
st.session_state.setdefault("rag_messages", [])

dashboard_tab, pets_tab, schedule_tab, ai_tab = st.tabs(
    ["Dashboard", "Pets & Tasks", "Schedule", "AI Assistant"]
)

with dashboard_tab:
    st.subheader("Dashboard")
    owner.name = st.text_input("Owner name", key="owner_name")
    owner.set_available_time(
        st.number_input(
            "Available time (minutes)",
            min_value=0,
            key="available_time",
        )
    )
    owner.update_preferences(
        st.multiselect(
            "Preferences",
            ["daily care", "walks", "feeding", "grooming", "medication", "play"],
            key="owner_preferences",
        )
    )

    pet_count = len(owner.pets)
    task_count = len(owner.get_all_tasks())
    pending_count = sum(
        1 for task in owner.get_all_tasks() if not task.completed
    )
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Pets", pet_count)
    metric_col2.metric("Pending tasks", pending_count)
    metric_col3.metric("Available minutes", owner.available_time)

    if not owner.pets:
        st.info("Start by adding a pet in the **Pets & Tasks** tab.")
    elif not task_count:
        st.info("Add a care task in the **Pets & Tasks** tab.")
    elif not st.session_state.daily_plan:
        st.info("Generate a plan in the **Schedule** tab.")
    else:
        st.success(
            f"{len(st.session_state.daily_plan)} task(s) are included in today's plan."
        )

with pets_tab:
    st.subheader("Owner and Pet Information")

    pet_name = st.text_input("Pet name", value="Mochi", key="pet_name")
    species = st.selectbox("Species", ["dog", "cat", "other"], key="pet_species")
    if st.button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), species=species))
            st.success(f"Added {pet_name.strip()} to your pets.")
            st.session_state.daily_plan = []
            st.session_state.plan_explanation = ""
            st.session_state.conflict_warnings = []
        else:
            st.warning("Enter a pet name before adding a pet.")

    if owner.pets:
        st.write("Your pets:")
        for pet in owner.pets:
            st.write(f"- {pet.name} ({pet.species})")
    else:
        st.info("Add a pet before adding care tasks.")

    st.markdown("### Tasks")
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input(
            "Task title", value="Morning walk", key="task_title"
        )
    with col2:
        duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=240,
            value=20,
            key="task_duration",
        )
    with col3:
        priority = st.selectbox(
            "Priority",
            ["low", "medium", "high"],
            index=2,
            key="task_priority",
        )

    with st.expander("Task schedule and recurrence"):
        due_date = st.date_input("Due date", value=date.today(), key="task_due_date")
        scheduled_time = st.time_input(
            "Scheduled time",
            value=time(9, 0),
            key="task_scheduled_time",
        )
        frequency = st.selectbox(
            "Frequency",
            ["once", "daily", "weekly"],
            index=1,
            key="task_frequency",
        )

    selected_pet = None
    if owner.pets:
        selected_pet = st.selectbox(
            "Task belongs to",
            options=range(len(owner.pets)),
            format_func=lambda pet_index: (
                f"{owner.pets[pet_index].name} "
                f"({owner.pets[pet_index].species})"
            ),
            key="selected_pet",
        )

    if st.button("Add task", disabled=selected_pet is None):
        if not task_title.strip():
            st.warning("Enter a task title before adding a task.")
        else:
            priority_values = {"low": 1, "medium": 2, "high": 3}
            task = Task(
                title=task_title.strip(),
                duration_minutes=int(duration),
                priority=priority_values[priority],
                frequency=frequency,
                scheduled_time=scheduled_time.strftime("%H:%M"),
                due_date=due_date,
            )
            owner.pets[selected_pet].add_task(task)
            task_conflicts = Scheduler(owner).detect_conflicts()
            if task_conflicts:
                st.info(
                    f"Added '{task.title}' to "
                    f"{owner.pets[selected_pet].name}'s tasks. "
                    "Review the scheduling conflict warning in Schedule."
                )
            else:
                st.success(
                    f"Added '{task.title}' to "
                    f"{owner.pets[selected_pet].name}'s tasks."
                )
            st.session_state.daily_plan = []
            st.session_state.plan_explanation = ""
            st.session_state.conflict_warnings = []

    all_tasks = owner.get_all_tasks()
    if st.session_state.completion_message:
        st.success(st.session_state.completion_message)
        st.session_state.completion_message = ""

    if all_tasks:
        st.write("Current tasks")
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            pet_filter_options = ["All pets"] + list(
                dict.fromkeys(pet.name for pet in owner.pets)
            )
            pet_filter = st.selectbox("Filter by pet", pet_filter_options)
        with filter_col2:
            status_filter = st.selectbox(
                "Filter by status",
                ["All", "Pending", "Completed"],
            )

        filtered_tasks = owner.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={
                "All": None,
                "Pending": False,
                "Completed": True,
            }[status_filter],
        )
        task_pet_lookup = {}
        for pet in owner.pets:
            if pet_filter != "All pets" and pet.name != pet_filter:
                continue
            for task in pet.get_tasks():
                task_pet_lookup.setdefault(id(task), pet)

        sorted_tasks = Scheduler(owner).sort_by_time(filtered_tasks)
        task_rows = [
            {
                "Pet": task_pet_lookup[id(task)].name,
                "Task": task.title,
                "Due date": task.due_date.isoformat() if task.due_date else "Not set",
                "Scheduled time": task.scheduled_time or "Not set",
                "Duration (minutes)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Status": "Completed" if task.completed else "Pending",
            }
            for task in sorted_tasks
        ]
        if task_rows:
            st.dataframe(task_rows, hide_index=True, width="stretch")
        else:
            st.info("No tasks match the selected filters.")

        pending_tasks = [task for task in sorted_tasks if not task.completed]
        if pending_tasks:
            task_index = st.selectbox(
                "Task to complete",
                options=range(len(pending_tasks)),
                format_func=lambda index: (
                    f"{task_pet_lookup[id(pending_tasks[index])].name}: "
                    f"{pending_tasks[index].title}"
                ),
                key="task_to_complete",
            )
            if st.button("Complete selected task"):
                task = pending_tasks[task_index]
                pet = task_pet_lookup[id(task)]
                next_task = pet.complete_task(task)
                if next_task is None:
                    st.session_state.completion_message = (
                        f"Marked '{task.title}' complete."
                    )
                else:
                    st.session_state.completion_message = (
                        f"Marked '{task.title}' complete. "
                        f"Next occurrence is due {next_task.due_date}."
                    )
                st.session_state.daily_plan = []
                st.session_state.plan_explanation = ""
                st.session_state.conflict_warnings = []
                st.rerun()
        else:
            st.info("No pending tasks match the selected filters.")
    else:
        st.info("No tasks yet. Add one above.")

with schedule_tab:
    st.subheader("Build Schedule")
    st.caption(
        "PawPal+ uses task priority and available time. AI responses never "
        "change this schedule automatically."
    )

    if st.button("Generate schedule"):
        scheduler = Scheduler(owner)
        st.session_state.daily_plan = scheduler.generate_plan()
        st.session_state.plan_explanation = scheduler.explain_plan()
        st.session_state.conflict_warnings = scheduler.detect_conflicts()

    conflicts = list(dict.fromkeys(Scheduler(owner).detect_conflicts()))
    st.markdown("### Scheduling Conflict Warnings")
    if conflicts:
        for warning in conflicts:
            st.warning(warning)
    elif owner.get_all_tasks():
        st.info("No scheduling conflicts found.")
    else:
        st.info("Add scheduled tasks to check for conflicts.")

    st.markdown("### Today's Schedule")
    if st.session_state.daily_plan:
        for task in st.session_state.daily_plan:
            st.write(
                f"- **{task.title}** — {task.duration_minutes} minutes "
                f"(priority {task.priority})"
            )
    else:
        st.info("Generate a schedule to see selected tasks.")

    if st.session_state.plan_explanation:
        st.markdown("### Plan Explanation")
        st.write(st.session_state.plan_explanation)

with ai_tab:
    st.subheader("PawPal+ AI Pet Care Assistant")
    st.markdown(
        "Ask a general question. PawPal+ searches local pet-care references, "
        "includes relevant passages in a Gemini prompt, and displays sources "
        "for human review."
    )

    examples = [
        "How often should I walk my dog?",
        "What are important daily care activities for cats?",
        "How can I keep my pet mentally stimulated?",
        "What are general pet grooming recommendations?",
        "What should I consider when planning a daily pet-care routine?",
    ]
    st.caption("Example questions")
    selected_example = st.selectbox(
        "Choose an example",
        [""] + examples,
    )
    if selected_example:
        st.session_state.rag_question = selected_example

    rag_question = st.text_input(
        "Pet-care question",
        key="rag_question",
        placeholder="How often should I walk my dog?",
    )

    if st.button("Ask AI", type="primary"):
        if not rag_question or not rag_question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                chunks = load_knowledge_documents(
                    Path(__file__).resolve().parent / "knowledge_base"
                )
                retriever = PetCareRetriever(chunks)
                pet_context = build_pet_context(owner)

                with st.spinner(
                    "Searching local references and generating a grounded answer..."
                ):
                    result = answer_question(
                        rag_question,
                        retriever,
                        model_call=lambda prompt: call_gemini(
                            prompt,
                            get_gemini_key(),
                        ),
                        pet_context=pet_context,
                        pet_species=selected_species(owner),
                    )

                st.session_state.rag_messages.append(
                    {
                        "question": rag_question,
                        "answer": result.answer,
                        "sources": result.sources,
                    }
                )
            except ValueError as exc:
                st.warning(str(exc))
            except MissingKnowledgeBaseError as exc:
                st.error(str(exc))
            except MissingApiKeyError as exc:
                st.info(
                    f"{exc} Add GEMINI_API_KEY to your environment or Streamlit "
                    "secrets to enable AI generation. Scheduling remains available."
                )
            except ModelResponseError as exc:
                st.error(f"{exc} Please try again.")
            except RuntimeError as exc:
                st.error(str(exc))

    for message in reversed(st.session_state.rag_messages):
        with st.chat_message("user"):
            st.write(message["question"])
        with st.chat_message("assistant"):
            st.write(message["answer"])
            st.markdown("**Retrieved sources**")
            shown = set()
            for source in message["sources"]:
                key = (source.title, source.source_url)
                if key in shown:
                    continue
                shown.add(key)
                if source.source_url:
                    st.markdown(f"- [{source.title}]({source.source_url})")
                else:
                    st.markdown(f"- {source.title}")
            with st.expander("Review retrieved passages"):
                for source in message["sources"]:
                    st.markdown(f"**{source.title}**")
                    st.write(source.text)

    st.caption(
        "General guidance only. This assistant does not diagnose conditions or "
        "replace individualized veterinary advice."
    )
