"""
Customer Churn Risk Predictor.
Analyses account and case data to identify customers at risk of churning.
Uses a rule-based scoring model with optional ML enhancement.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from config.settings import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)


class ChurnPredictor:
    """Predicts customer churn risk based on account health signals."""

    def __init__(self):
        self.thresholds = ANALYTICS_CONFIG["churn_risk_thresholds"]

    def predict_churn(self, accounts, cases, opportunities):
        """
        Assess churn risk for each account.

        Args:
            accounts: List of account dicts.
            cases: List of case dicts.
            opportunities: List of opportunity dicts.

        Returns:
            DataFrame with churn risk scores and classifications.
        """
        df_accounts = pd.DataFrame(accounts)
        df_cases = pd.DataFrame(cases)
        df_opps = pd.DataFrame(opportunities)

        if df_accounts.empty:
            return pd.DataFrame()

        # Calculate risk factors per account
        df_accounts["_case_risk"] = self._case_risk_score(df_accounts, df_cases)
        df_accounts["_engagement_risk"] = self._engagement_risk_score(df_accounts)
        df_accounts["_revenue_risk"] = self._revenue_risk_score(df_accounts, df_opps)
        df_accounts["_satisfaction_risk"] = self._satisfaction_risk_score(
            df_accounts, df_cases
        )

        # Composite churn risk score (0.0 - 1.0)
        df_accounts["Churn_Risk_Score"] = (
            df_accounts["_case_risk"] * 0.30
            + df_accounts["_engagement_risk"] * 0.25
            + df_accounts["_revenue_risk"] * 0.25
            + df_accounts["_satisfaction_risk"] * 0.20
        ).round(3)

        # Classify risk level
        df_accounts["Churn_Risk_Level"] = df_accounts["Churn_Risk_Score"].apply(
            self._classify_risk
        )

        # Generate per-account risk factors
        df_accounts["Risk_Factors"] = df_accounts.apply(
            self._identify_risk_factors, axis=1
        )

        # Clean up internal columns
        internal_cols = [c for c in df_accounts.columns if c.startswith("_")]
        df_accounts.drop(columns=internal_cols, inplace=True)

        df_accounts.sort_values("Churn_Risk_Score", ascending=False, inplace=True)

        logger.info(
            f"Churn analysis complete. "
            f"High risk: {(df_accounts['Churn_Risk_Level'] == 'High').sum()}, "
            f"Medium: {(df_accounts['Churn_Risk_Level'] == 'Medium').sum()}"
        )
        return df_accounts

    def get_risk_summary(self, accounts, cases, opportunities):
        """Return a high-level summary of churn risk across the customer base."""
        df = self.predict_churn(accounts, cases, opportunities)
        if df.empty:
            return {"total_accounts": 0, "risk_breakdown": {}}

        return {
            "total_accounts": len(df),
            "average_risk_score": round(df["Churn_Risk_Score"].mean(), 3),
            "risk_breakdown": {
                level: int((df["Churn_Risk_Level"] == level).sum())
                for level in ["Low", "Medium", "High"]
            },
            "high_risk_accounts": df[df["Churn_Risk_Level"] == "High"][
                ["Name", "Industry", "Churn_Risk_Score"]
            ].to_dict("records"),
            "total_revenue_at_risk": float(
                df[df["Churn_Risk_Level"] == "High"]["AnnualRevenue"].sum()
            ),
        }

    def _case_risk_score(self, accounts, cases):
        """High case volume or escalations = higher risk."""
        if cases.empty:
            return pd.Series(0.0, index=accounts.index)

        case_counts = cases.groupby("AccountId").size().reset_index(name="case_count")
        escalated = (
            cases[cases["Priority"].isin(["High", "Critical"])]
            .groupby("AccountId")
            .size()
            .reset_index(name="escalated_count")
        )

        merged = accounts[["Id"]].merge(
            case_counts, left_on="Id", right_on="AccountId", how="left"
        )
        merged = merged.merge(
            escalated, left_on="Id", right_on="AccountId", how="left"
        )
        merged["case_count"] = merged["case_count"].fillna(0)
        merged["escalated_count"] = merged["escalated_count"].fillna(0)

        # Normalise: more cases + more escalations = higher risk
        case_norm = (merged["case_count"] / 10).clip(0, 1)
        esc_norm = (merged["escalated_count"] / 3).clip(0, 1)

        return (case_norm * 0.5 + esc_norm * 0.5).values

    def _engagement_risk_score(self, accounts):
        """Low engagement (no recent activity) = higher risk."""
        if "LastActivityDate" not in accounts.columns:
            return pd.Series(0.3, index=accounts.index)

        last_activity = pd.to_datetime(accounts["LastActivityDate"], errors="coerce")
        now = pd.Timestamp.now()
        days_since = (now - last_activity).dt.days.fillna(90)

        # More days since activity = higher risk
        return (days_since / 90).clip(0, 1)

    def _revenue_risk_score(self, accounts, opportunities):
        """Declining revenue / no recent wins = higher risk."""
        if opportunities.empty:
            return pd.Series(0.5, index=accounts.index)

        won = opportunities[opportunities.get("IsWon", False) == True]
        if won.empty:
            return pd.Series(0.6, index=accounts.index)

        recent_wins = (
            won.groupby("AccountId")["Amount"]
            .sum()
            .reset_index(name="won_value")
        )

        merged = accounts[["Id"]].merge(
            recent_wins, left_on="Id", right_on="AccountId", how="left"
        )
        merged["won_value"] = merged["won_value"].fillna(0)

        # No recent wins = higher risk
        has_wins = (merged["won_value"] > 0).astype(float)
        return (1 - has_wins * 0.8).values

    def _satisfaction_risk_score(self, accounts, cases):
        """Low CSAT scores = higher risk."""
        if cases.empty or "Customer_Satisfaction__c" not in cases.columns:
            return pd.Series(0.3, index=accounts.index)

        avg_csat = (
            cases.dropna(subset=["Customer_Satisfaction__c"])
            .groupby("AccountId")["Customer_Satisfaction__c"]
            .mean()
            .reset_index(name="avg_csat")
        )

        merged = accounts[["Id"]].merge(
            avg_csat, left_on="Id", right_on="AccountId", how="left"
        )
        merged["avg_csat"] = merged["avg_csat"].fillna(3.0)

        # Lower CSAT = higher risk (invert the 1-5 scale)
        return (1 - (merged["avg_csat"] - 1) / 4).clip(0, 1).values

    def _classify_risk(self, score):
        if score >= self.thresholds["high"]:
            return "High"
        elif score >= self.thresholds["medium"]:
            return "Medium"
        return "Low"

    def _identify_risk_factors(self, row):
        """List the specific risk factors for an account."""
        factors = []
        if row.get("_case_risk", 0) > 0.6:
            factors.append("High support case volume or escalations")
        if row.get("_engagement_risk", 0) > 0.6:
            factors.append("Low engagement — no recent activity")
        if row.get("_revenue_risk", 0) > 0.6:
            factors.append("No recent closed-won opportunities")
        if row.get("_satisfaction_risk", 0) > 0.6:
            factors.append("Low customer satisfaction scores")
        return factors if factors else ["No significant risk factors identified"]
