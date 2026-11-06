
import streamlit as st
import pandas as pd

from app.services.question_service import (
    get_departments,
    get_questions_by_department,
)
from app.services.evaluation_service import save_evaluations


st.set_page_config(
    page_title="Chatbot Evaluation Platform",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Bank Chatbot Pilot Testing Platform")
st.write(
    "Select your department and complete the assigned testing questions."
)
st.divider()

departments = get_departments()

selected_department = st.selectbox(
    "Select your department",
    departments,
)

if selected_department:

    questions = get_questions_by_department(selected_department)

    st.subheader(f"{selected_department} Department")

    previous_department = st.session_state.get("previous_department")

    if previous_department != selected_department:
        st.session_state["previous_department"] = selected_department

        for key in list(st.session_state.keys()):
            if key.startswith("section_open_") or key.startswith("language_open_"):
                del st.session_state[key]

    st.markdown("### Select Testing Section")

    for section in ["Information", "Action"]:

        section_questions = [
            q for q in questions
            if q.section.strip().lower() == section.lower()
        ]

        if not section_questions:
            continue

        section_key = f"section_open_{selected_department}_{section}"

        if st.button(
            f"{section} ({len(section_questions)} questions)",
            key=f"button_{selected_department}_{section}",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.get(section_key, False)
                else "secondary"
            ),
        ):
            st.session_state[section_key] = not st.session_state.get(
                section_key, False
            )

        if st.session_state.get(section_key, False):

            st.markdown(f"#### {section} Questions")

            available_languages = sorted(
                set(q.language.strip() for q in section_questions),
                key=lambda language: (
                    0 if language.lower() == "amharic"
                    else 1 if language.lower() == "english"
                    else 2
                ),
            )

            for language in available_languages:

                language_key = (
                    f"language_open_{selected_department}_{section}_{language}"
                )

                if st.button(
                    language,
                    key=f"button_{selected_department}_{section}_{language}",
                    use_container_width=True,
                    type=(
                        "primary"
                        if st.session_state.get(language_key, False)
                        else "secondary"
                    ),
                ):
                    st.session_state[language_key] = not st.session_state.get(
                        language_key, False
                    )

                if st.session_state.get(language_key, False):

                    filtered_questions = [
                        q for q in section_questions
                        if q.language.strip() == language
                    ]

                    st.write(
                        f"Total {language} questions: "
                        f"{len(filtered_questions)}"
                    )

                    # Evaluation form for this language
                    form_key = (
                        f"eval_form_{selected_department}_{section}_{language}"
                    )

                    with st.form(key=form_key):

                        # Table headings
                        headers = st.columns(
                            [1.1, 1.2, 3.2, 2.4, 1.5, 2]
                        )

                        headings = [
                            "Question ID",
                            "Category",
                            "Question",
                            "Actual Response",
                            "Status",
                            "Comment",
                        ]

                        for column, heading in zip(headers, headings):
                            column.markdown(f"**{heading}**")

                        st.divider()

                        for q in filtered_questions:

                            columns = st.columns(
                                [1.1, 1.2, 3.2, 2.4, 1.5, 2]
                            )

                            columns[0].write(q.question_id)
                            columns[1].write(q.category)
                            columns[2].write(q.question_text)

                            columns[3].text_area(
                                "Actual response",
                                key=f"answer_{q.question_id}",
                                label_visibility="collapsed",
                                placeholder="Enter chatbot response",
                                height=100,
                            )

                            if section.lower() == "information":
                                status_options = [
                                    "Select status",
                                    "Passed",
                                    "Failed",
                                    "Not Enough Info",
                                ]
                            else:
                                status_options = [
                                    "Select status",
                                    "Passed",
                                    "Failed",
                                ]

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

                        submitted = st.form_submit_button(
                            f"Submit {language} Evaluations",
                            use_container_width=True,
                            type="primary",
                        )

                    if submitted:

                        evaluation_records = []
                        validation_errors = []
                        for q in filtered_questions:

                            status = st.session_state.get(
                                f"status_{q.question_id}",
                                "Select status",
                            )

                            actual_answer = st.session_state.get(
                                f"answer_{q.question_id}",
                                "",
                            ) or ""

                            comment = st.session_state.get(
                                f"comment_{q.question_id}",
                                "",
                            ) or ""

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
                                        f"{q.question_id}: Please explain what information is missing "
                                        "or what should be improved."
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
                                "Please correct the following issues before "
                                "submitting:"
                            )
                            for error in validation_errors:
                                st.write(f"- {error}")

                        else:
                            try:
                                saved_count = save_evaluations(
                                    evaluation_records
                                )

                                st.success(
                                    f"Successfully submitted {saved_count} "
                                    f"{language} evaluations!"
                                )

                                for q in filtered_questions:
                                    for prefix in [
                                        "answer_",
                                        "status_",
                                        "comment_",
                                    ]:
                                        key = f"{prefix}{q.question_id}"
                                        if key in st.session_state:
                                            del st.session_state[key]

                            except Exception as error:
                                st.error(
                                    f"Unable to save evaluations: {error}"
                                )

            st.divider()

st.divider()

st.caption(
    "Bank Chatbot Pilot Testing | Internal Evaluation Platform"
)
