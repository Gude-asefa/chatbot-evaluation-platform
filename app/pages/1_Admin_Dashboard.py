import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os
import hmac
from pathlib import Path
from dotenv import load_dotenv

from app.services.auth_service import verify_password

from app.services.dashboard_service import (
    get_dashboard_summary,
    get_department_progress,
    get_evaluation_records,
)


# Load administrator credentials from .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Brand colors (Bank of Abyssinia)
BRAND_YELLOW = "#F1AB15"
BRAND_BLACK = "#111111"
STATUS_COLORS = {
    "Passed": BRAND_YELLOW,
    "Failed": BRAND_BLACK,
    "Not Enough Info": "#9CA3AF",
}


# Check whether the administrator is logged in
if not st.session_state.get("admin_authenticated", False):

    _, login_col, _ = st.columns([1, 1.5, 1])

    with login_col:
        st.space("large")
        with st.container(border=True):
            st.header("Admin login", icon=":material/lock:")
            st.caption("Bank of Abyssinia · Chatbot evaluation platform")

            with st.form("admin_login_form", border=False):
                username = st.text_input(
                    "Username",
                    icon=":material/person:",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    icon=":material/key:",
                )

                login_submitted = st.form_submit_button(
                    "Log in",
                    icon=":material/login:",
                    width="stretch",
                    type="primary",
                )

            if login_submitted:

                if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
                    st.error(
                        "Administrator credentials are not configured.",
                        icon=":material/error:",
                    )

                elif (
                    hmac.compare_digest(username.strip(), ADMIN_USERNAME)
                    and verify_password(password, ADMIN_PASSWORD_HASH)
                ):
                    st.session_state["admin_authenticated"] = True
                    st.rerun()

                else:
                    st.error(
                        "Invalid username or password.",
                        icon=":material/error:",
                    )

    st.stop()


# Header with logout
with st.container(horizontal=True, vertical_alignment="center"):
    st.title(
        "Chatbot evaluation dashboard",
        icon=":material/monitoring:",
        width="stretch",
    )
    if st.button("Log out", key="admin_logout", icon=":material/logout:"):
        st.session_state["admin_authenticated"] = False
        st.rerun()

st.caption("Monitor pilot testing results across all departments.")


# 1. Retrieve dashboard data
summary = get_dashboard_summary()
department_data = get_department_progress()
progress_df = pd.DataFrame(department_data)


# 2. Overall evaluation metrics
total = summary["total"]
pass_rate = f"{summary['passed'] / total:.0%}" if total else "—"

with st.container(horizontal=True):
    st.metric("Total evaluations", total,
              icon=":material/fact_check:", border=True)
    st.metric("Pass rate", pass_rate,
              icon=":material/percent:", border=True)
    st.metric("Passed", summary["passed"],
              icon=":material/check_circle:", border=True)
    st.metric("Failed", summary["failed"],
              icon=":material/cancel:", border=True)
    st.metric("Not enough info", summary["not_enough_info"],
              icon=":material/help:", border=True)


# 3. Result distribution and department completion
chart_left, chart_right = st.columns([1, 1.6])

with chart_left:
    with st.container(border=True, height="stretch"):
        st.subheader("Result distribution", icon=":material/donut_large:")

        if total > 0:
            result_df = pd.DataFrame({
                "Status": ["Passed", "Failed", "Not Enough Info"],
                "Count": [
                    summary["passed"],
                    summary["failed"],
                    summary["not_enough_info"],
                ],
            })

            fig = px.pie(
                result_df,
                names="Status",
                values="Count",
                hole=0.55,
                color="Status",
                color_discrete_map=STATUS_COLORS,
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", y=-0.1),
            )

            st.plotly_chart(
                fig,
                alt="Donut chart of evaluation results by status",
            )

        else:
            st.caption("No evaluations have been submitted yet.")

with chart_right:
    with st.container(border=True, height="stretch"):
        st.subheader("Completion by department", icon=":material/bar_chart:")

        if not progress_df.empty:
            fig = px.bar(
                progress_df,
                x="department",
                y="progress",
                text="progress",
                range_y=[0, 105],
                labels={"department": "", "progress": "Completion (%)"},
                color_discrete_sequence=[BRAND_YELLOW],
            )
            fig.update_traces(
                texttemplate="%{text:.0f}%",
                textposition="outside",
                marker_line_color=BRAND_BLACK,
                marker_line_width=1,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))

            st.plotly_chart(
                fig,
                alt="Bar chart of testing completion percentage by department",
            )

        else:
            st.caption("No department data available.")


# 4. Department progress table
if not progress_df.empty:

    with st.container(border=True):
        st.subheader("Department progress", icon=":material/apartment:")

        department_display_df = progress_df.rename(columns={
            "department": "Department",
            "total_questions": "Total questions",
            "evaluated_questions": "Evaluated",
            "remaining_questions": "Remaining",
            "progress": "Completion",
        })

        st.dataframe(
            department_display_df,
            hide_index=True,
            column_config={
                "Completion": st.column_config.ProgressColumn(
                    "Completion",
                    min_value=0,
                    max_value=100,
                    format="%.0f%%",
                ),
            },
            alt="Testing progress by department",
        )


# 5. Detailed evaluation records
st.header("Evaluation records", icon=":material/table_view:")
st.caption("Review submitted chatbot evaluations and employee feedback.")


# Filters
with st.container(border=True):
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        selected_department_filter = st.selectbox(
            "Department",
            ["All"] + [
                item["department"] for item in department_data
            ],
            key="admin_department_filter",
        )

    with filter_col2:
        selected_section_filter = st.selectbox(
            "Section",
            ["All", "Information", "Action"],
            key="admin_section_filter",
        )

    with filter_col3:
        selected_language_filter = st.selectbox(
            "Language",
            ["All", "Amharic", "English"],
            key="admin_language_filter",
        )

    with filter_col4:
        selected_status_filter = st.selectbox(
            "Evaluation status",
            ["All", "Passed", "Failed", "Not Enough Info"],
            key="admin_status_filter",
        )


# Retrieve filtered records
records = get_evaluation_records(
    department=selected_department_filter,
    section=selected_section_filter,
    language=selected_language_filter,
    status=selected_status_filter,
)


if records:

    records_df = pd.DataFrame(records)

    st.caption(f"Found {len(records_df)} evaluation records.")

    display_df = records_df.rename(columns={
        "department": "Department",
        "section": "Section",
        "language": "Language",
        "question_id": "Question ID",
        "category": "Category",
        "question_text": "Question",
        "actual_answer": "Actual chatbot response",
        "status": "Status",
        "comments": "Employee comment",
        "submitted_at": "Submitted at",
    })

    # Display evaluation records
    st.dataframe(
        display_df.drop(columns=["id"]),
        hide_index=True,
        column_config={
            "Question": st.column_config.TextColumn(width="large"),
            "Actual chatbot response": st.column_config.TextColumn(
                width="large",
            ),
            "Submitted at": st.column_config.DatetimeColumn(
                format="YYYY-MM-DD HH:mm",
            ),
        },
        alt="Detailed evaluation records",
    )


    # 6. Excel export
    excel_buffer = BytesIO()

    # Create a separate copy for Excel
    excel_df = display_df.drop(columns=["id"]).copy()

    # Remove timezone information for Excel compatibility
    if "Submitted at" in excel_df.columns:

        excel_df["Submitted at"] = (
            pd.to_datetime(
                excel_df["Submitted at"],
                utc=True,
            )
            .dt.tz_localize(None)
        )

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:

        excel_df.to_excel(
            writer,
            index=False,
            sheet_name="Evaluations",
        )

    st.download_button(
        label="Download evaluations as Excel",
        data=excel_buffer.getvalue(),
        file_name="chatbot_evaluation_report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        icon=":material/download:",
        type="primary",
        width="stretch",
    )

else:

    st.info(
        "No evaluation records match the selected filters.",
        icon=":material/filter_alt_off:",
    )


st.space("large")
st.caption(
    "Bank of Abyssinia · Chatbot pilot testing | Administrator dashboard",
    text_alignment="center",
)
