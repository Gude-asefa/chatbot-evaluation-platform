
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

# Check whether the administrator is logged in
if not st.session_state.get("admin_authenticated", False):

    st.title("🔐 Admin Login")
    st.write("Please enter your administrator credentials.")

    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        login_submitted = st.form_submit_button(
            "Login",
            use_container_width=True,
            type="primary",
        )

    if login_submitted:

        if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
            st.error("Administrator credentials are not configured.")

        elif (
            hmac.compare_digest(username.strip(), ADMIN_USERNAME)
            and verify_password(password, ADMIN_PASSWORD_HASH)
        ):
            st.session_state["admin_authenticated"] = True
            st.rerun()

        else:
            st.error("Invalid username or password.")

    st.stop()


# Logout button
if st.button("Logout", key="admin_logout"):
    st.session_state["admin_authenticated"] = False
    st.rerun()


st.title("📊 Chatbot Evaluation - Admin Dashboard")

st.write(
    "Monitor pilot testing results across all seven departments."
)

st.divider()


# 1. Retrieve dashboard data
summary = get_dashboard_summary()
department_data = get_department_progress()


# 2. Overall evaluation metrics
st.subheader("Overall Evaluation Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Evaluations", summary["total"])
col2.metric("Passed", summary["passed"])
col3.metric("Failed", summary["failed"])
col4.metric("Not Enough Info", summary["not_enough_info"])


# 3. Evaluation result distribution
st.divider()
st.subheader("Evaluation Result Distribution")

if summary["total"] > 0:

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
        title="Distribution of Evaluation Results",
        hole=0.4,
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No evaluations have been submitted yet.")


# 4. Department progress
st.divider()
st.subheader("Department Testing Progress")

progress_df = pd.DataFrame(department_data)

if not progress_df.empty:

    department_display_df = progress_df.rename(columns={
        "department": "Department",
        "total_questions": "Total Questions",
        "evaluated_questions": "Evaluated Questions",
        "remaining_questions": "Remaining Questions",
        "progress": "Completion (%)",
    })

    st.dataframe(
        department_display_df,
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        department_display_df,
        x="Department",
        y="Completion (%)",
        title="Testing Completion by Department",
        text="Completion (%)",
        range_y=[0, 100],
    )

    st.plotly_chart(fig, use_container_width=True)


# 5. Detailed evaluation records
st.divider()
st.subheader("Detailed Evaluation Records")

st.write(
    "Review submitted chatbot evaluations and employee feedback."
)


# Filters
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
        "Evaluation Status",
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

    st.write(
        f"Found {len(records_df)} evaluation records."
    )

    display_df = records_df.rename(columns={
        "department": "Department",
        "section": "Section",
        "language": "Language",
        "question_id": "Question ID",
        "category": "Category",
        "question_text": "Question",
        "actual_answer": "Actual Chatbot Response",
        "status": "Status",
        "comments": "Employee Comment",
        "submitted_at": "Submitted At",
    })

    # Display evaluation records
    st.dataframe(
        display_df.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
    )


    # 6. Excel export
    excel_buffer = BytesIO()

    # Create a separate copy for Excel
    excel_df = display_df.drop(columns=["id"]).copy()

    # Remove timezone information for Excel compatibility
    if "Submitted At" in excel_df.columns:

        excel_df["Submitted At"] = (
            pd.to_datetime(
                excel_df["Submitted At"],
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
        label="Download Evaluations as Excel",
        data=excel_buffer.getvalue(),
        file_name="chatbot_evaluation_report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

else:

    st.info(
        "No evaluation records match the selected filters."
    )


st.divider()

st.caption(
    "Bank Chatbot Pilot Testing | Administrator Dashboard"
)
