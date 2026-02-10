"""
Lead Scoring Engine.
Assigns a composite score (0-100) to each lead based on firmographic,
behavioural, and engagement signals. Used by both AWS and Azure functions.
"""

import logging
from datetime import datetime

import pandas as pd
import numpy as np

from config.settings import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores and prioritises Salesforce leads based on weighted criteria."""

    def __init__(self, weights=None):
        self.weights = weights or ANALYTICS_CONFIG["lead_score_weights"]

    def score_leads(self, leads):
        """
        Score a list of lead records and return a DataFrame with scores.

        Args:
            leads: List of lead dicts from SalesforceClient.

        Returns:
            DataFrame with original fields plus Lead_Score and Priority.
        """
        df = pd.DataFrame(leads)
        if df.empty:
            return df

        # Calculate individual scoring components (each normalised 0-1)
        df["_company_size_score"] = self._score_company_size(df)
        df["_engagement_score"] = self._score_engagement(df)
        df["_industry_score"] = self._score_industry(df)
        df["_budget_score"] = self._score_budget(df)
        df["_response_time_score"] = self._score_response_time(df)
        df["_email_score"] = self._score_email_activity(df)

        # Compute weighted composite score
        df["Lead_Score"] = (
            df["_company_size_score"] * self.weights["company_size"]
            + df["_engagement_score"] * self.weights["engagement_score"]
            + df["_industry_score"] * self.weights["industry_match"]
            + df["_budget_score"] * self.weights["budget_range"]
            + df["_response_time_score"] * self.weights["response_time_days"]
            + df["_email_score"] * self.weights["email_opens"]
        ) * 100

        df["Lead_Score"] = df["Lead_Score"].clip(0, 100).round(1)

        # Assign priority tiers
        df["Priority"] = pd.cut(
            df["Lead_Score"],
            bins=[-1, 30, 60, 80, 101],
            labels=["Low", "Medium", "High", "Critical"],
        )

        # Clean up internal scoring columns
        internal_cols = [c for c in df.columns if c.startswith("_")]
        df.drop(columns=internal_cols, inplace=True)

        df.sort_values("Lead_Score", ascending=False, inplace=True)
        logger.info(f"Scored {len(df)} leads. "
                    f"Critical: {(df['Priority'] == 'Critical').sum()}, "
                    f"High: {(df['Priority'] == 'High').sum()}")
        return df

    def get_top_leads(self, leads, top_n=10):
        """Return the top N highest-scored leads."""
        scored = self.score_leads(leads)
        return scored.head(top_n)

    def get_score_distribution(self, leads):
        """Return score distribution summary."""
        scored = self.score_leads(leads)
        return {
            "total_leads": len(scored),
            "average_score": round(scored["Lead_Score"].mean(), 1),
            "median_score": round(scored["Lead_Score"].median(), 1),
            "priority_breakdown": scored["Priority"].value_counts().to_dict(),
            "score_ranges": {
                "0-30 (Low)": int((scored["Lead_Score"] <= 30).sum()),
                "31-60 (Medium)": int(
                    ((scored["Lead_Score"] > 30) & (scored["Lead_Score"] <= 60)).sum()
                ),
                "61-80 (High)": int(
                    ((scored["Lead_Score"] > 60) & (scored["Lead_Score"] <= 80)).sum()
                ),
                "81-100 (Critical)": int((scored["Lead_Score"] > 80).sum()),
            },
        }

    # --- Individual scoring functions (normalised 0-1) ---

    def _score_company_size(self, df):
        """Larger companies score higher (logarithmic scale)."""
        employees = df.get("NumberOfEmployees", pd.Series(dtype=float)).fillna(1)
        return np.log1p(employees) / np.log1p(10000)

    def _score_engagement(self, df):
        """Composite engagement based on web visits and content downloads."""
        visits = df.get("Website_Visits__c", pd.Series(0)).fillna(0)
        downloads = df.get("Content_Downloads__c", pd.Series(0)).fillna(0)
        engagement = (visits / 50 * 0.6) + (downloads / 10 * 0.4)
        return engagement.clip(0, 1)

    def _score_industry(self, df):
        """Target industries score higher."""
        target_industries = {"Technology", "Finance", "Healthcare", "Consulting"}
        return df.get("Industry", pd.Series("")).apply(
            lambda x: 1.0 if x in target_industries else 0.4
        )

    def _score_budget(self, df):
        """Higher annual revenue = higher score (logarithmic)."""
        revenue = df.get("AnnualRevenue", pd.Series(dtype=float)).fillna(0)
        return (np.log1p(revenue) / np.log1p(100000000)).clip(0, 1)

    def _score_response_time(self, df):
        """Leads with recent activity score higher."""
        days = df.get("Days_Since_Last_Activity__c", pd.Series(30)).fillna(30)
        return (1 - days / 60).clip(0, 1)

    def _score_email_activity(self, df):
        """More email opens = more engaged."""
        opens = df.get("Email_Opens__c", pd.Series(0)).fillna(0)
        return (opens / 30).clip(0, 1)
