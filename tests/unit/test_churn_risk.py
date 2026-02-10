"""Tests for the churn risk predictor."""

import pytest
from src.salesforce.mock_data import MockDataGenerator
from src.analytics.churn_risk import ChurnPredictor


@pytest.fixture
def data():
    gen = MockDataGenerator(seed=42)
    gen.generate_all()
    return {
        "accounts": gen.get_accounts(),
        "cases": gen.get_cases(),
        "opportunities": gen.get_opportunities(),
    }


@pytest.fixture
def predictor():
    return ChurnPredictor()


class TestChurnPredictor:
    def test_predict_returns_dataframe(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], data["cases"], data["opportunities"]
        )
        assert len(result) == len(data["accounts"])
        assert "Churn_Risk_Score" in result.columns
        assert "Churn_Risk_Level" in result.columns

    def test_risk_scores_in_valid_range(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], data["cases"], data["opportunities"]
        )
        assert result["Churn_Risk_Score"].min() >= 0
        assert result["Churn_Risk_Score"].max() <= 1

    def test_risk_levels_are_valid(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], data["cases"], data["opportunities"]
        )
        valid_levels = {"High", "Medium", "Low"}
        assert set(result["Churn_Risk_Level"].unique()).issubset(valid_levels)

    def test_sorted_by_risk_descending(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], data["cases"], data["opportunities"]
        )
        scores = result["Churn_Risk_Score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_risk_summary(self, predictor, data):
        summary = predictor.get_risk_summary(
            data["accounts"], data["cases"], data["opportunities"]
        )
        assert "total_accounts" in summary
        assert "average_risk_score" in summary
        assert "risk_breakdown" in summary
        assert "high_risk_accounts" in summary
        assert "total_revenue_at_risk" in summary

    def test_risk_summary_counts_match(self, predictor, data):
        summary = predictor.get_risk_summary(
            data["accounts"], data["cases"], data["opportunities"]
        )
        breakdown = summary["risk_breakdown"]
        total = sum(breakdown.values())
        assert total == summary["total_accounts"]

    def test_empty_accounts(self, predictor):
        result = predictor.predict_churn([], [], [])
        assert len(result) == 0

    def test_empty_cases_still_produces_scores(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], [], data["opportunities"]
        )
        assert len(result) == len(data["accounts"])

    def test_risk_factors_present(self, predictor, data):
        result = predictor.predict_churn(
            data["accounts"], data["cases"], data["opportunities"]
        )
        assert "Risk_Factors" in result.columns
        for factors in result["Risk_Factors"]:
            assert isinstance(factors, list)
            assert len(factors) > 0
