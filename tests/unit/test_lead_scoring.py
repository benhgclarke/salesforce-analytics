"""Tests for the lead scoring engine."""

import pytest
import pandas as pd
from src.salesforce.mock_data import MockDataGenerator
from src.analytics.lead_scoring import LeadScorer


@pytest.fixture
def leads():
    gen = MockDataGenerator(seed=42)
    gen.generate_all()
    return gen.get_leads()


@pytest.fixture
def scorer():
    return LeadScorer()


class TestLeadScorer:
    def test_scores_all_leads(self, scorer, leads):
        result = scorer.score_leads(leads)
        assert len(result) == len(leads)
        assert "Lead_Score" in result.columns
        assert "Priority" in result.columns

    def test_scores_are_in_valid_range(self, scorer, leads):
        result = scorer.score_leads(leads)
        assert result["Lead_Score"].min() >= 0
        assert result["Lead_Score"].max() <= 100

    def test_priority_assignments(self, scorer, leads):
        result = scorer.score_leads(leads)
        valid_priorities = {"Low", "Medium", "High", "Critical"}
        assert set(result["Priority"].unique()).issubset(valid_priorities)

    def test_sorted_by_score_descending(self, scorer, leads):
        result = scorer.score_leads(leads)
        scores = result["Lead_Score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_get_top_leads(self, scorer, leads):
        top = scorer.get_top_leads(leads, top_n=5)
        assert len(top) == 5
        assert top.iloc[0]["Lead_Score"] >= top.iloc[-1]["Lead_Score"]

    def test_score_distribution(self, scorer, leads):
        dist = scorer.get_score_distribution(leads)
        assert "total_leads" in dist
        assert "average_score" in dist
        assert "priority_breakdown" in dist
        assert "score_ranges" in dist
        assert dist["total_leads"] == len(leads)

    def test_empty_leads(self, scorer):
        result = scorer.score_leads([])
        assert len(result) == 0

    def test_custom_weights(self, leads):
        custom_weights = {
            "company_size": 0.50,
            "engagement_score": 0.10,
            "industry_match": 0.10,
            "budget_range": 0.10,
            "response_time_days": 0.10,
            "email_opens": 0.10,
        }
        scorer = LeadScorer(weights=custom_weights)
        result = scorer.score_leads(leads)
        assert len(result) == len(leads)

    def test_high_engagement_leads_score_higher(self, scorer):
        """Leads with high engagement signals should score higher."""
        high_engagement = [{
            "Id": "001", "FirstName": "Test", "LastName": "High",
            "Company": "BigCo", "Industry": "Technology",
            "NumberOfEmployees": 5000, "AnnualRevenue": 50000000,
            "Website_Visits__c": 45, "Email_Opens__c": 25,
            "Content_Downloads__c": 8, "Days_Since_Last_Activity__c": 2,
        }]
        low_engagement = [{
            "Id": "002", "FirstName": "Test", "LastName": "Low",
            "Company": "SmallCo", "Industry": "Other",
            "NumberOfEmployees": 5, "AnnualRevenue": 50000,
            "Website_Visits__c": 0, "Email_Opens__c": 0,
            "Content_Downloads__c": 0, "Days_Since_Last_Activity__c": 55,
        }]

        high_result = scorer.score_leads(high_engagement)
        low_result = scorer.score_leads(low_engagement)
        assert high_result.iloc[0]["Lead_Score"] > low_result.iloc[0]["Lead_Score"]
