"""
Pipeline Health Analyser.
Evaluates the sales pipeline across stages, velocity, conversion rates,
and forecast accuracy. Produces actionable insights for sales managers.
"""

import logging
from datetime import datetime

import pandas as pd
import numpy as np

from config.settings import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)


class PipelineAnalyser:
    """Analyses Salesforce opportunity data to assess pipeline health."""

    def __init__(self):
        self.stages = ANALYTICS_CONFIG["pipeline_health_stages"]

    def analyse_pipeline(self, opportunities):
        """
        Full pipeline health analysis.

        Returns:
            dict with stage_summary, velocity, forecast, and health_score.
        """
        df = pd.DataFrame(opportunities)
        if df.empty:
            return self._empty_result()

        df["Amount"] = pd.to_numeric(df.get("Amount", 0), errors="coerce").fillna(0)
        df["Probability"] = pd.to_numeric(
            df.get("Probability", 0), errors="coerce"
        ).fillna(0)

        return {
            "stage_summary": self._stage_summary(df),
            "velocity_metrics": self._velocity_metrics(df),
            "forecast": self._forecast(df),
            "health_score": self._calculate_health_score(df),
            "risk_indicators": self._identify_risks(df),
            "recommendations": self._generate_recommendations(df),
        }

    def get_stage_funnel(self, opportunities):
        """Return data formatted for a funnel chart."""
        df = pd.DataFrame(opportunities)
        if df.empty:
            return []

        funnel = []
        for stage in self.stages:
            stage_df = df[df["StageName"] == stage]
            funnel.append({
                "stage": stage,
                "count": len(stage_df),
                "total_value": float(stage_df["Amount"].sum()),
                "avg_value": float(stage_df["Amount"].mean()) if len(stage_df) > 0 else 0,
            })
        return funnel

    def _stage_summary(self, df):
        """Breakdown by pipeline stage."""
        summary = []
        for stage in self.stages:
            stage_df = df[df["StageName"] == stage]
            summary.append({
                "stage": stage,
                "count": len(stage_df),
                "total_value": float(stage_df["Amount"].sum()),
                "avg_value": float(stage_df["Amount"].mean()) if len(stage_df) > 0 else 0,
                "weighted_value": float(
                    (stage_df["Amount"] * stage_df["Probability"] / 100).sum()
                ),
            })
        return summary

    def _velocity_metrics(self, df):
        """Measure how fast deals move through the pipeline."""
        days_in_stage = df.get("Days_In_Stage__c", pd.Series(dtype=float)).fillna(0)

        open_df = df[df.get("IsClosed", False) == False]
        closed_won = df[df.get("IsWon", False) == True]

        return {
            "avg_days_in_current_stage": float(days_in_stage.mean()),
            "median_days_in_stage": float(days_in_stage.median()),
            "open_deals": len(open_df),
            "open_pipeline_value": float(open_df["Amount"].sum()),
            "closed_won_count": len(closed_won),
            "closed_won_value": float(closed_won["Amount"].sum()),
            "avg_deal_size": float(closed_won["Amount"].mean())
            if len(closed_won) > 0 else 0,
        }

    def _forecast(self, df):
        """Generate a weighted pipeline forecast."""
        open_df = df[df.get("IsClosed", False) == False].copy()
        if open_df.empty:
            return {"best_case": 0, "commit": 0, "pipeline": 0, "total_weighted": 0}

        forecast_col = open_df.get("ForecastCategory", pd.Series("Pipeline", index=open_df.index))
        return {
            "best_case": float(
                open_df.loc[forecast_col == "Best Case", "Amount"].sum()
            ),
            "commit": float(
                open_df.loc[forecast_col == "Commit", "Amount"].sum()
            ),
            "pipeline": float(
                open_df.loc[forecast_col == "Pipeline", "Amount"].sum()
            ),
            "total_weighted": float(
                (open_df["Amount"] * open_df["Probability"] / 100).sum()
            ),
        }

    def _calculate_health_score(self, df):
        """
        Composite pipeline health score (0-100).
        Based on: coverage ratio, stage distribution, velocity, win rate.
        """
        scores = []

        # 1. Pipeline coverage (open pipeline vs quota assumption)
        open_value = df[df.get("IsClosed", False) == False]["Amount"].sum()
        # Assume a quarterly quota of 500k for scoring purposes
        coverage = min(open_value / 500000, 1.0)
        scores.append(coverage * 25)

        # 2. Stage distribution (penalise if too concentrated in early stages)
        stage_counts = df["StageName"].value_counts(normalize=True)
        late_stages = {"Proposal", "Negotiation", "Closed Won"}
        late_ratio = sum(
            stage_counts.get(s, 0) for s in late_stages
        )
        scores.append(late_ratio * 25)

        # 3. Win rate
        closed = df[df.get("IsClosed", False) == True]
        if len(closed) > 0:
            win_rate = len(closed[closed.get("IsWon", False) == True]) / len(closed)
        else:
            win_rate = 0.5
        scores.append(win_rate * 25)

        # 4. Velocity (lower avg days in stage = healthier)
        avg_days = df.get("Days_In_Stage__c", pd.Series(30)).fillna(30).mean()
        velocity_score = max(0, 1 - avg_days / 60)
        scores.append(velocity_score * 25)

        total = round(sum(scores), 1)
        return {
            "score": total,
            "rating": "Excellent" if total >= 75 else
                      "Good" if total >= 55 else
                      "Fair" if total >= 35 else "Poor",
            "breakdown": {
                "coverage": round(scores[0], 1),
                "distribution": round(scores[1], 1),
                "win_rate": round(scores[2], 1),
                "velocity": round(scores[3], 1),
            },
        }

    def _identify_risks(self, df):
        """Identify pipeline risk indicators."""
        risks = []
        open_df = df[df.get("IsClosed", False) == False]

        # Stalled deals
        stalled = open_df[
            open_df.get("Days_In_Stage__c", pd.Series(0)).fillna(0) > 30
        ]
        if len(stalled) > 0:
            risks.append({
                "type": "Stalled Deals",
                "severity": "High",
                "count": len(stalled),
                "value": float(stalled["Amount"].sum()),
                "message": f"{len(stalled)} deals stalled (>30 days in current stage), "
                           f"worth £{stalled['Amount'].sum():,.0f}",
            })

        # Concentration risk (single deal > 40% of pipeline)
        if len(open_df) > 0 and open_df["Amount"].sum() > 0:
            max_deal_pct = open_df["Amount"].max() / open_df["Amount"].sum()
            if max_deal_pct > 0.4:
                risks.append({
                    "type": "Concentration Risk",
                    "severity": "Medium",
                    "message": f"Largest deal represents {max_deal_pct:.0%} of pipeline",
                })

        # Low early-stage pipeline (future pipeline health)
        early = open_df[open_df["StageName"].isin(["Prospecting", "Qualification"])]
        if len(early) < 5:
            risks.append({
                "type": "Thin Top of Funnel",
                "severity": "Medium",
                "count": len(early),
                "message": f"Only {len(early)} deals in early stages — future pipeline at risk",
            })

        return risks

    def _generate_recommendations(self, df):
        """Generate actionable recommendations based on pipeline data."""
        recommendations = []
        risks = self._identify_risks(df)

        for risk in risks:
            if risk["type"] == "Stalled Deals":
                recommendations.append(
                    f"Review {risk['count']} stalled deals — consider re-engagement "
                    f"campaigns or pipeline clean-up."
                )
            elif risk["type"] == "Concentration Risk":
                recommendations.append(
                    "Diversify pipeline — high dependency on a single large deal "
                    "increases forecast risk."
                )
            elif risk["type"] == "Thin Top of Funnel":
                recommendations.append(
                    "Increase prospecting activity — the early-stage pipeline is thin "
                    "and will impact future quarters."
                )

        health = self._calculate_health_score(df)
        if health["breakdown"]["win_rate"] < 10:
            recommendations.append(
                "Win rate is below target — review qualification criteria and "
                "sales process effectiveness."
            )

        return recommendations

    def _empty_result(self):
        return {
            "stage_summary": [],
            "velocity_metrics": {},
            "forecast": {},
            "health_score": {"score": 0, "rating": "No Data", "breakdown": {}},
            "risk_indicators": [],
            "recommendations": ["No opportunity data available for analysis."],
        }
