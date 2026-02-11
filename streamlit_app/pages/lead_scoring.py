"""Lead Scoring page."""

import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_app.data_loader import load_all_data


def show_lead_scoring():
    data = load_all_data()
    dist = data["dist"]
    scored = data["scored"]

    st.title("🎯 Lead Scoring & Prioritisation")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", dist.get("total_leads", 0))
    c2.metric("Critical Priority", dist.get("priority_breakdown", {}).get("Critical", 0))
    c3.metric("High Priority", dist.get("priority_breakdown", {}).get("High", 0))
    c4.metric("Average Score", dist.get("average_score", 0))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Score Distribution")
        ranges = dist.get("score_ranges", {})
        colors = ["#94a3b8", "#3b82f6", "#ea580c", "#dc2626"]
        fig = px.bar(
            x=list(ranges.keys()),
            y=list(ranges.values()),
            color=list(ranges.keys()),
            color_discrete_sequence=colors,
        )
        fig.update_layout(
            height=350, margin=dict(t=20, b=20),
            showlegend=False, xaxis_title="Score Range", yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Priority Breakdown")
        bd = dist.get("priority_breakdown", {})
        priority_order = ["Low", "Medium", "High", "Critical"]
        priority_colors = {
            "Low": "#94a3b8", "Medium": "#3b82f6",
            "High": "#ea580c", "Critical": "#dc2626",
        }
        ordered_names = [k for k in priority_order if bd.get(k, 0) > 0]
        ordered_vals = [bd[k] for k in ordered_names]
        fig2 = px.treemap(
            names=ordered_names,
            parents=[""] * len(ordered_names),
            values=ordered_vals,
            color=ordered_names,
            color_discrete_map=priority_colors,
        )
        fig2.update_layout(height=350, margin=dict(t=20, b=20))
        fig2.update_traces(textinfo="label+value+percent root")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Top Scored Leads")

    priority_filter = st.selectbox("Filter by Priority", ["All", "Low", "Medium", "High", "Critical"])
    display_df = scored.copy()
    if priority_filter != "All":
        display_df = display_df[display_df["Priority"] == priority_filter]

    cols_to_show = ["FirstName", "LastName", "Company", "Industry", "LeadSource", "Lead_Score", "Priority", "Status"]
    available = [c for c in cols_to_show if c in display_df.columns]
    rename_map = {"FirstName": "First_Name", "LastName": "Last_Name", "LeadSource": "Lead_Source"}
    st.dataframe(
        display_df[available].head(50).rename(columns=rename_map),
        use_container_width=True, hide_index=True,
    )
