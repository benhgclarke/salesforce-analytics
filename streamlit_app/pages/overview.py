"""Overview page — KPIs, charts, and alerts."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.data_loader import load_all_data


def show_overview():
    st.title("📊 Salesforce Analytics Dashboard")
    st.caption("Cloud-Enhanced Automation & Analytics Platform")

    data = load_all_data()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leads", len(data["leads"]))
    open_opps = [o for o in data["opps"] if not o.get("IsClosed")]
    col2.metric("Open Opportunities", len(open_opps))
    pipeline_val = sum(o.get("Amount", 0) for o in open_opps)
    col3.metric("Pipeline Value", f"£{pipeline_val:,.0f}")
    health = data["pipeline"].get("health_score", {})
    col4.metric("Health Score", f"{health.get('score', 0)}/100", health.get("rating", ""))

    st.divider()

    # --- Row 1 charts ---
    left, right = st.columns(2)

    with left:
        st.subheader("Lead Score Distribution")
        ranges = data["dist"].get("score_ranges", {})
        score_order = ["0-30 (Low)", "31-60 (Medium)", "61-80 (High)", "81-100 (Critical)"]
        score_colors = {
            "0-30 (Low)": "#94a3b8",
            "31-60 (Medium)": "#3b82f6",
            "61-80 (High)": "#ea580c",
            "81-100 (Critical)": "#dc2626",
        }
        ordered_names = [k for k in score_order if k in ranges]
        ordered_vals = [ranges[k] for k in ordered_names]
        fig = px.treemap(
            names=ordered_names,
            parents=[""] * len(ordered_names),
            values=ordered_vals,
            color=ordered_names,
            color_discrete_map=score_colors,
        )
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        fig.update_traces(textinfo="label+value+percent root")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Pipeline by Stage")
        funnel_df = pd.DataFrame(data["funnel"])
        if not funnel_df.empty:
            # Colour scheme: Closed Won = dark green, Closed Lost = dark red,
            # other stages = blue gradient proportional to value
            stage_colors = {"Closed Won": "#166534", "Closed Lost": "#991b1b"}
            non_closed = [
                s for s in funnel_df["stage"].tolist()
                if s not in ("Closed Won", "Closed Lost")
            ]
            stage_vals = funnel_df.set_index("stage")["total_value"]
            max_val = max((stage_vals.get(s, 0) for s in non_closed), default=1) or 1
            light = (191, 219, 254)   # lightest blue
            dark = (30, 64, 175)      # darkest blue
            for stage in non_closed:
                pct = stage_vals.get(stage, 0) / max_val
                r = int(light[0] + (dark[0] - light[0]) * pct)
                g = int(light[1] + (dark[1] - light[1]) * pct)
                b = int(light[2] + (dark[2] - light[2]) * pct)
                stage_colors[stage] = f"#{r:02x}{g:02x}{b:02x}"

            fig2 = px.bar(
                funnel_df,
                x="total_value",
                y="stage",
                orientation="h",
                color="stage",
                color_discrete_map=stage_colors,
            )
            fig2.update_layout(
                height=350,
                margin=dict(t=20, b=20),
                yaxis_title="",
                xaxis_title="Total Value (£)",
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # --- Row 2 charts ---
    left2, right2 = st.columns(2)

    with left2:
        st.subheader("Churn Risk Breakdown")
        risk_bd = data["churn_summary"].get("risk_breakdown", {})
        risk_order = ["Low", "Medium", "High"]
        risk_colors = {"Low": "#16a34a", "Medium": "#3b82f6", "High": "#dc2626"}
        fig3 = px.pie(
            names=risk_order,
            values=[risk_bd.get(k, 0) for k in risk_order],
            color=risk_order,
            color_discrete_map=risk_colors,
            hole=0.5,
        )
        fig3.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    with right2:
        st.subheader("Pipeline Health Radar")
        bd = health.get("breakdown", {})
        categories = ["Coverage", "Distribution", "Win Rate", "Velocity"]
        values = [
            bd.get("coverage", 0),
            bd.get("distribution", 0),
            bd.get("win_rate", 0),
            bd.get("velocity", 0),
        ]
        fig4 = go.Figure()
        fig4.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(99,102,241,0.2)",
                line_color="#6366f1",
            )
        )
        fig4.update_layout(
            height=350,
            margin=dict(t=30, b=20),
            polar=dict(radialaxis=dict(visible=True, range=[0, 25])),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # --- Alerts ---
    st.divider()
    st.subheader("Recent Alerts")
    alerts = [
        {
            "type": "Lead Scoring",
            "message": f"{data['dist'].get('priority_breakdown', {}).get('Critical', 0)} leads scored as Critical priority",
            "priority": "critical",
        },
        {
            "type": "Churn Risk",
            "message": f"{data['churn_summary'].get('risk_breakdown', {}).get('High', 0)} accounts at High churn risk",
            "priority": "critical",
        },
        {
            "type": "Pipeline Health",
            "message": f"Health score: {health.get('score', 0)}/100 ({health.get('rating', '')})",
            "priority": "high" if health.get("score", 100) < 50 else "info",
        },
    ]
    for a in alerts:
        icon = "🔴" if a["priority"] == "critical" else "🟠" if a["priority"] == "high" else "🔵"
        st.markdown(f"{icon} **{a['type']}** — {a['message']}")
