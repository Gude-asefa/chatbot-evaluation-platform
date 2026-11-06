import streamlit as st

from app.components.device_id import get_device_id
from app.database.connection import engine
from app.database.models import Base
from app.services.question_service import (
    get_departments,
    get_questions_by_department,
)
from app.services.evaluation_service import (
    AlreadySubmittedError,
    get_submitted_sections,
    save_evaluations,
)


st.set_page_config(
    page_title="Chatbot Evaluation Platform",
    page_icon=":material/smart_toy:",
    layout="wide",
)

SECTION_ICONS = {
    "Information": ":material/info:",
    "Action": ":material/bolt:",
}

TABLE_COLUMNS = [1.1, 1.2, 3.2, 2.4, 1.5, 2]
TABLE_HEADINGS = [
    "Question ID",
    "Category",
    "Question",
    "Actual response",
    "Status",
    "Comment",
]


@st.cache_resource
def ensure_database_tables():
    """Create any missing tables (e.g. submissions). Existing ones are untouched."""
    Base.metadata.create_all(bind=engine)


@st.cache_resource(ttl=300, show_spinner=False)
def load_departments():
    """Departments change rarely; cache for 5 minutes (read-only)."""
    return get_departments()


@st.cache_resource(ttl=300, max_entries=50, show_spinner=False)
def load_department_questions(department):
    """Question bank per department; cache for 5 minutes (read-only)."""
    return get_questions_by_department(department)


def language_sort_key(language):
    lowered = language.lower()
    return 0 if lowered == "amharic" else 1 if lowered == "english" else 2


def describe_remaining(remaining):
    return ", ".join(f"{sec} ({lang})" for sec, lang in remaining)


ensure_database_tables()


# Header
st.title("Chatbot pilot testing", icon=":material/smart_toy:")
st.caption(
    "Bank of Abyssinia · Internal evaluation platform — select your "
    "department and complete the assigned testing questions."
)

device_id = get_device_id()

if not device_id:
    st.caption(":material/hourglass_top: Preparing your testing session…")
    st.stop()


# Step 1: department
with st.container(border=True):
    selected_department = st.selectbox(
        "Select your department",
        load_departments(),
        index=None,
        placeholder="Choose your department",
    )

if not selected_department:
    st.info(
        "Select your department to continue.",
        icon=":material/arrow_upward:",
    )
    st.stop()


questions = load_department_questions(selected_department)

sections = {
    section: [
        q for q in questions
        if q.section.strip().lower() == section.lower()
    ]
    for section in ["Information", "Action"]
}
sections = {name: qs for name, qs in sections.items() if qs}

if not sections:
    st.warning(
        "No questions are assigned to this department yet.",
        icon=":material/warning:",
    )
    st.stop()

languages_by_section = {
    name: sorted(
        set(q.language.strip() for q in qs),
        key=language_sort_key,
    )
    for name, qs in sections.items()
}

submitted = get_submitted_sections(device_id, selected_department)

all_combinations = [
    (name, lang)
    for name, langs in languages_by_section.items()
    for lang in langs
]
remaining = [combo for combo in all_combinations if combo not in submitted]


st.header(f"{selected_department} department", icon=":material/apartment:")

done_count = len(all_combinations) - len(remaining)
st.progress(
    done_count / len(all_combinations),
    text=f"{done_count} of {len(all_combinations)} section/language sets submitted",
)

if not remaining:
    st.success(
        "You have submitted every section for this department. Thank you!",
        icon=":material/celebration:",
    )


# Step 2: section
def section_label(name):
    done = all((name, lang) in submitted for lang in languages_by_section[name])
    mark = " :material/check_circle:" if done else ""
    return f"{SECTION_ICONS[name]} {name} ({len(sections[name])} questions){mark}"


with st.container(border=True):
    st.subheader("Select testing section", icon=":material/tune:")

    section = st.segmented_control(
        "Testing section",
        options=list(sections.keys()),
        format_func=section_label,
        key=f"section_{selected_department}",
        label_visibility="collapsed",
        width="stretch",
    )

    if not section:
        st.caption("Choose Information or Action to continue.")
        st.stop()

    section_questions = sections[section]

    # Step 3: language
    st.subheader(f"{section} questions", icon=SECTION_ICONS[section])

    def language_label(lang):
        if (section, lang) in submitted:
            return f":material/check_circle: {lang} — submitted"
        return f":material/translate: {lang}"

    language = st.segmented_control(
        "Language",
        options=languages_by_section[section],
        format_func=language_label,
        key=f"language_{selected_department}_{section}",
        label_visibility="collapsed",
        width="stretch",
    )

    if not language:
        st.caption("Choose Amharic or English to load the questions.")
        st.stop()


filtered_questions = [
    q for q in section_questions
    if q.language.strip() == language
]

already_submitted_message = (
    f"You have already submitted an evaluation for **{section} — "
    f"{language}** from this device."
)


# Already submitted from this device: don't show the form again
if (section, language) in submitted:
    st.warning(
        already_submitted_message
        + (
            f"\n\nPlease continue with the remaining sets: "
            f"{describe_remaining(remaining)}."
            if remaining else
            "\n\nAll sets for this department are complete."
        ),
        title="Already submitted",
        icon=":material/task_alt:",
    )
    st.stop()


# Step 4: evaluation form (table format)
st.subheader(
    f"{section} · {language} ({len(filtered_questions)} questions)",
    icon=":material/checklist:",
)
st.caption(
    "An actual response is required for Failed and Not Enough Info; "
    "a comment is required for Not Enough Info. Each section/language "
    "can be submitted once per device."
)

if section.lower() == "information":
    status_options = ["Select status", "Passed", "Failed", "Not Enough Info"]
else:
    status_options = ["Select status", "Passed", "Failed"]

form_key = f"eval_form_{selected_department}_{section}_{language}"

with st.form(key=form_key):

    headers = st.columns(TABLE_COLUMNS)
    for column, heading in zip(headers, TABLE_HEADINGS):
        column.markdown(f"**{heading}**")

    st.divider()

    for q in filtered_questions:

        columns = st.columns(TABLE_COLUMNS)

        columns[0].markdown(f"**{q.question_id}**")
        columns[1].caption(q.category)
        columns[2].write(q.question_text)

        columns[3].text_area(
            "Actual response",
            key=f"answer_{q.question_id}",
            label_visibility="collapsed",
            placeholder="Enter chatbot response",
            height=100,
        )

        columns[4].selectbox(
            "Status",
            options=status_options,
            key=f"status_{q.question_id}",
            label_visibility="collapsed",
        )

        columns[5].text_area(
            "Comment",
            key=f"comment_{q.question_id}",
            label_visibility="collapsed",
            placeholder="If Not Enough Info, what should be improved?",
            height=100,
        )

        st.divider()

    form_submitted = st.form_submit_button(
        f"Submit {section} — {language} evaluations",
        icon=":material/send:",
        width="stretch",
        type="primary",
    )


if form_submitted:

    evaluation_records = []
    validation_errors = []

    for q in filtered_questions:

        status = st.session_state.get(f"status_{q.question_id}", "Select status")
        actual_answer = st.session_state.get(f"answer_{q.question_id}", "") or ""
        comment = st.session_state.get(f"comment_{q.question_id}", "") or ""

        if status == "Select status":
            validation_errors.append(
                f"{q.question_id}: Please select a status."
            )
            continue

        if status in ["Failed", "Not Enough Info"]:
            if not actual_answer.strip():
                validation_errors.append(
                    f"{q.question_id}: Actual chatbot response is required."
                )
                continue

        if status == "Not Enough Info":
            if not comment.strip():
                validation_errors.append(
                    f"{q.question_id}: Please explain what information is "
                    "missing or what should be improved."
                )
                continue

        evaluation_records.append({
            "question_id": q.id,
            "actual_answer": actual_answer.strip() or None,
            "status": status,
            "comments": comment.strip() or None,
        })

    if validation_errors:
        st.error(
            "\n".join(f"- {error}" for error in validation_errors),
            title="Please correct the following issues before submitting",
            icon=":material/error:",
        )

    else:
        remaining_after = [
            combo for combo in remaining if combo != (section, language)
        ]

        try:
            saved_count = save_evaluations(
                evaluation_records,
                device_id=device_id,
                department=selected_department,
                section=section,
                language=language,
            )

            st.success(
                f"Successfully submitted {saved_count} {section} — "
                f"{language} evaluations."
                + (
                    f"\n\nNext, please complete: "
                    f"{describe_remaining(remaining_after)}."
                    if remaining_after else
                    "\n\nYou have completed every set for this department."
                ),
                icon=":material/task_alt:",
            )
            st.toast("Evaluations saved", icon=":material/check_circle:")

            for q in filtered_questions:
                for prefix in ["answer_", "status_", "comment_"]:
                    key = f"{prefix}{q.question_id}"
                    if key in st.session_state:
                        del st.session_state[key]

        except AlreadySubmittedError:
            st.warning(
                already_submitted_message
                + (
                    f"\n\nPlease continue with the remaining sets: "
                    f"{describe_remaining(remaining_after)}."
                    if remaining_after else ""
                ),
                title="Already submitted",
                icon=":material/task_alt:",
            )

        except Exception as error:
            st.error(
                f"Unable to save evaluations: {error}",
                icon=":material/error:",
            )


st.space("large")
st.caption(
    "Bank of Abyssinia · Chatbot pilot testing | Internal evaluation platform",
    text_alignment="center",
)
