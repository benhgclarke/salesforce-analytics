"""
Salesforce Analytics Dashboard — Streamlit Cloud Edition.
Deploy to https://share.streamlit.io for a free shareable link.

Run locally:  streamlit run streamlit_app/app.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

st.set_page_config(
    page_title="Salesforce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Page imports (no rendering at import time) ---
from streamlit_app.pages.overview import show_overview
from streamlit_app.pages.lead_scoring import show_lead_scoring
from streamlit_app.pages.pipeline_health import show_pipeline_health
from streamlit_app.pages.churn_risk import show_churn_risk
from streamlit_app.pages.architecture import show_architecture

# --- Sidebar navigation ---
PAGES = {
    "Overview": show_overview,
    "Lead Scoring": show_lead_scoring,
    "Pipeline Health": show_pipeline_health,
    "Churn Risk": show_churn_risk,
    "Architecture": show_architecture,
}

selection = st.sidebar.radio("Navigation", list(PAGES.keys()))
PAGES[selection]()
