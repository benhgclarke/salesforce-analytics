"""Churn Risk page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Churn Risk", page_icon="⚠️", layout="wide")

from streamlit_app.app import load_all_data
data = load_all_data()
churn_summary = data["churn_summary"]
churn_df = data["churn_df"]

st.title("⚠️ Customer Churn Risk Analysis")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Accounts", churn_summary.get("total_accounts", 0))
c2.metric("High Risk", churn_summary.get("risk_breakdown", {}).get("High", 0))
c3.metric("Revenue at Risk", f"£{churn_summary.get('total_revenue_at_risk', 0):,.0f}")
c4.metric("Avg Risk Score", f"{churn_summary.get('average_risk_score', 0):.2f}")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Risk Level Distribution")
    risk_bd = churn_summary.get("risk_breakdown", {})
    risk_order = ["Low", "Medium", "High"]
    risk_colors = {"Low": "#16a34a", "Medium": "#3b82f6", "High": "#dc2626"}
    fig = px.pie(
        names=risk_order,
        values=[risk_bd.get(k, 0) for k in risk_order],
        color=risk_order, color_discrete_map=risk_colors,
        hole=0.5,
    )
    fig.update_layout(height=350, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue at Risk by Level")
    if not churn_df.empty:
        grouped = churn_df.groupby("Churn_Risk_Level")["AnnualRevenue"].agg(["sum", "mean", "count"]).reset_index()
        grouped.columns = ["Risk Level", "Total Revenue", "Avg Revenue", "Count"]
        order = ["Low", "Medium", "High"]
        grouped["Risk Level"] = pd.Categorical(grouped["Risk Level"], categories=order, ordered=True)
        grouped = grouped.sort_values("Risk Level")

        fig2 = px.bar(
            grouped, x="Risk Level", y="Total Revenue",
            color="Risk Level", color_discrete_map=risk_colors,
        )
        fig2.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False, yaxis_title="Revenue (£)")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Average Revenue by Risk Level**")
        st.dataframe(
            grouped[["Risk Level", "Avg Revenue", "Count"]].assign(**{"Avg Revenue": lambda df: df["Avg Revenue"].map("£{:,.0f}".format)}),
            use_container_width=True, hide_index=True,
        )

st.divider()
st.subheader("Accounts by Churn Risk")

level_filter = st.selectbox("Filter by Risk Level", ["All", "Low", "Medium", "High"])
display = churn_df.copy()
if level_filter != "All":
    display = display[display["Churn_Risk_Level"] == level_filter]

cols_to_show = ["Name", "Industry", "AnnualRevenue", "Type", "Churn_Risk_Score", "Churn_Risk_Level"]
available = [c for c in cols_to_show if c in display.columns]
st.dataframe(display[available].head(50), use_container_width=True, hide_index=True)
