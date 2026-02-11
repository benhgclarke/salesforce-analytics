"""Pipeline Health page."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.data_loader import load_all_data


def show_pipeline_health():
    data = load_all_data()
    pipeline = data["pipeline"]
    funnel = data["funnel"]
    health = pipeline.get("health_score", {})
    forecast = pipeline.get("forecast", {})

    st.title("📈 Pipeline Health Analysis")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Health Score", f"{health.get('score', 0)}/100", health.get("rating", ""))
    vm = pipeline.get("velocity_metrics", {})
    c2.metric("Open Pipeline", f"£{vm.get('open_pipeline_value', 0):,.0f}")
    c3.metric("Weighted Forecast", f"£{forecast.get('total_weighted', 0):,.0f}")
    won = vm.get("closed_won_count", 0)
    lost = sum(s["count"] for s in pipeline.get("stage_summary", []) if s.get("stage") == "Closed Lost")
    wr = f"{won / (won + lost) * 100:.0f}%" if (won + lost) > 0 else "N/A"
    c4.metric("Win Rate", wr)

    st.divider()

    # Pipeline Funnel
    st.subheader("Pipeline Funnel")
    funnel_df = pd.DataFrame(funnel)
    if not funnel_df.empty:
        # Colour scheme: Closed Won = dark green, Closed Lost = dark red,
        # other stages = purple gradient (lighter for smaller x-axis values)
        stage_colors = {}
        non_closed = [
            s for s in funnel_df["stage"].tolist()
            if s not in ("Closed Won", "Closed Lost")
        ]
        stage_vals = funnel_df.set_index("stage")["total_value"]
        non_closed_sorted = sorted(non_closed, key=lambda s: stage_vals.get(s, 0))
        purple_shades = ["#e9d5ff", "#d8b4fe", "#c084fc", "#a855f7",
                         "#9333ea", "#7e22ce", "#6b21a8", "#581c87"]
        for i, stage in enumerate(non_closed_sorted):
            shade_idx = int(i / max(len(non_closed_sorted) - 1, 1) * (len(purple_shades) - 1))
            stage_colors[stage] = purple_shades[shade_idx]
        stage_colors["Closed Won"] = "#166534"
        stage_colors["Closed Lost"] = "#991b1b"

        fig = px.bar(
            funnel_df, x="total_value", y="stage", orientation="h",
            color="stage",
            color_discrete_map=stage_colors,
        )
        fig.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False, xaxis_title="Total Value (£)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Health Score Radar")
        bd = health.get("breakdown", {})
        categories = ["Coverage", "Distribution", "Win Rate", "Velocity"]
        values = [bd.get("coverage", 0), bd.get("distribution", 0), bd.get("win_rate", 0), bd.get("velocity", 0)]
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatterpolar(
                r=values + [values[0]], theta=categories + [categories[0]],
                fill="toself", fillcolor="rgba(99,102,241,0.2)", line_color="#6366f1",
            )
        )
        fig2.update_layout(height=350, margin=dict(t=30, b=20), polar=dict(radialaxis=dict(visible=True, range=[0, 25])))
        st.plotly_chart(fig2, use_container_width=True)

    with right:
        st.subheader("Forecast Categories")
        fc_colors = {"Commit": "#16a34a", "Best Case": "#3b82f6", "Pipeline": "#94a3b8"}
        fig3 = px.pie(
            names=["Commit", "Best Case", "Pipeline"],
            values=[forecast.get("commit", 0), forecast.get("best_case", 0), forecast.get("pipeline", 0)],
            color=["Commit", "Best Case", "Pipeline"],
            color_discrete_map=fc_colors,
            hole=0.5,
        )
        fig3.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    left2, right2 = st.columns(2)

    with left2:
        st.subheader("Risk Indicators")
        risks = pipeline.get("risk_indicators", [])
        if risks:
            for r in risks:
                icon = "🔴" if r.get("severity") == "High" else "🟡"
                st.markdown(f"{icon} **{r.get('type', '')}** — {r.get('message', '')}")
        else:
            st.success("No significant risks identified")

    with right2:
        st.subheader("Recommendations")
        recs = pipeline.get("recommendations", [])
        if recs:
            for r in recs:
                st.markdown(f"• {r}")
        else:
            st.info("No recommendations at this time")
