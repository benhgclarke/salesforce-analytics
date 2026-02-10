"""Tests for the pipeline health analyser."""

import pytest
from src.salesforce.mock_data import MockDataGenerator
from src.analytics.pipeline_health import PipelineAnalyser


@pytest.fixture
def opportunities():
    gen = MockDataGenerator(seed=42)
    gen.generate_all()
    return gen.get_opportunities()


@pytest.fixture
def analyser():
    return PipelineAnalyser()


class TestPipelineAnalyser:
    def test_analyse_returns_all_sections(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        assert "stage_summary" in result
        assert "velocity_metrics" in result
        assert "forecast" in result
        assert "health_score" in result
        assert "risk_indicators" in result
        assert "recommendations" in result

    def test_stage_summary_covers_all_stages(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        stages = [s["stage"] for s in result["stage_summary"]]
        expected = [
            "Prospecting", "Qualification", "Needs Analysis",
            "Proposal", "Negotiation", "Closed Won", "Closed Lost",
        ]
        assert stages == expected

    def test_health_score_in_valid_range(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        score = result["health_score"]["score"]
        assert 0 <= score <= 100

    def test_health_score_has_rating(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        valid_ratings = {"Excellent", "Good", "Fair", "Poor"}
        assert result["health_score"]["rating"] in valid_ratings

    def test_health_score_breakdown(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        breakdown = result["health_score"]["breakdown"]
        assert "coverage" in breakdown
        assert "distribution" in breakdown
        assert "win_rate" in breakdown
        assert "velocity" in breakdown

    def test_forecast_categories(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        forecast = result["forecast"]
        assert "best_case" in forecast
        assert "commit" in forecast
        assert "pipeline" in forecast
        assert "total_weighted" in forecast

    def test_velocity_metrics(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        vm = result["velocity_metrics"]
        assert "open_deals" in vm
        assert "open_pipeline_value" in vm
        assert "avg_deal_size" in vm

    def test_funnel_data(self, analyser, opportunities):
        funnel = analyser.get_stage_funnel(opportunities)
        assert len(funnel) == 7
        assert all("stage" in f for f in funnel)
        assert all("count" in f for f in funnel)
        assert all("total_value" in f for f in funnel)

    def test_empty_opportunities(self, analyser):
        result = analyser.analyse_pipeline([])
        assert result["health_score"]["rating"] == "No Data"

    def test_recommendations_are_strings(self, analyser, opportunities):
        result = analyser.analyse_pipeline(opportunities)
        for rec in result["recommendations"]:
            assert isinstance(rec, str)
