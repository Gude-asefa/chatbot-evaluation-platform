
import streamlit as st

# Configure the application
st.set_page_config(
    page_title="Bank Chatbot Evaluation Platform",
    page_icon=":material/smart_toy:",
    layout="wide",
)

# Define the employee page
employee_page = st.Page(
    "main.py",
    title="Employee Evaluation",
    default=True,
)

# Define the admin page
admin_page = st.Page(
    "app/pages/1_Admin_Dashboard.py",
    title="Admin Dashboard",
    url_path="admin",
)

# Configure navigation
navigation = st.navigation(
    [employee_page, admin_page],
    position="hidden",
)

# Run the selected page
navigation.run()
