"""Shared data loader for all Streamlit pages."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor


@st.cache_data(ttl=300)
def load_all_data():
    sf = SalesforceClient()
    leads = sf.get_leads()
    opps = sf.get_opportunities()
    accounts = sf.get_accounts()
    cases = sf.get_cases()

    scorer = LeadScorer()
    analyser = PipelineAnalyser()
    predictor = ChurnPredictor()

    scored = scorer.score_leads(leads)
    dist = scorer.get_score_distribution(leads)
    pipeline = analyser.analyse_pipeline(opps)
    funnel = analyser.get_stage_funnel(opps)
    churn_summary = predictor.get_risk_summary(accounts, cases, opps)
    churn_df = predictor.predict_churn(accounts, cases, opps)

    return {
        "leads": leads,
        "opps": opps,
        "accounts": accounts,
        "cases": cases,
        "scored": scored,
        "dist": dist,
        "pipeline": pipeline,
        "funnel": funnel,
        "churn_summary": churn_summary,
        "churn_df": churn_df,
    }
