import streamlit as st

from app_lib import ui

st.set_page_config(
    page_title="DistriSense · Distribution Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.sidebar()

pages = [
    st.Page("app_pages/data_validation.py", title="Data & Validation", icon=":material/fact_check:", default=True),
    st.Page("app_pages/plan_export.py", title="Plan & Export", icon=":material/local_shipping:"),
    st.Page("app_pages/risk_baselines.py", title="Risk Dial & Baselines", icon=":material/insights:"),
]

st.navigation(pages).run()
