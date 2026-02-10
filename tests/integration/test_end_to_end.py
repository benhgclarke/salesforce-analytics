"""
Integration tests — end-to-end analytics pipeline.
Tests the full flow: data extraction -> analytics -> results.
"""

import pytest
from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.automation.notifications import NotificationService


@pytest.fixture
def sf_client():
    return SalesforceClient(use_mock=True)


class TestEndToEndPipeline:
    def test_full_lead_scoring_pipeline(self, sf_client):
        """Test: extract leads -> score -> get distribution."""
        leads = sf_client.get_leads()
        assert len(leads) > 0

        scorer = LeadScorer()
        scored = scorer.score_leads(leads)
        assert len(scored) == len(leads)
        assert scored["Lead_Score"].max() <= 100

        dist = scorer.get_score_distribution(leads)
        assert dist["total_leads"] == len(leads)

    def test_full_pipeline_analysis(self, sf_client):
        """Test: extract opportunities -> analyse pipeline -> get health."""
        opps = sf_client.get_opportunities()
        assert len(opps) > 0

        analyser = PipelineAnalyser()
        result = analyser.analyse_pipeline(opps)
        assert result["health_score"]["score"] >= 0

    def test_full_churn_prediction(self, sf_client):
        """Test: extract all data -> predict churn -> get summary."""
        accounts = sf_client.get_accounts()
        cases = sf_client.get_cases()
        opps = sf_client.get_opportunities()

        predictor = ChurnPredictor()
        summary = predictor.get_risk_summary(accounts, cases, opps)
        assert summary["total_accounts"] == len(accounts)
        assert sum(summary["risk_breakdown"].values()) == len(accounts)

    def test_full_analytics_and_notification(self, sf_client):
        """Test: run all analytics and generate notification summary."""
        leads = sf_client.get_leads()
        opps = sf_client.get_opportunities()
        accounts = sf_client.get_accounts()
        cases = sf_client.get_cases()

        scorer = LeadScorer()
        lead_dist = scorer.get_score_distribution(leads)

        analyser = PipelineAnalyser()
        pipeline = analyser.analyse_pipeline(opps)

        predictor = ChurnPredictor()
        churn = predictor.get_risk_summary(accounts, cases, opps)

        # Generate notification summary
        notifier = NotificationService()
        results = {
            "lead_scoring": {"leads_scored": lead_dist["total_leads"], "distribution": lead_dist},
            "pipeline_health": pipeline,
            "churn_prediction": churn,
        }
        summary = notifier.send_daily_summary(results)
        assert "Lead Scoring" in summary
        assert "Pipeline Health" in summary
        assert "Churn Risk" in summary

    def test_writeback_integration(self, sf_client):
        """Test: score leads -> write scores back to Salesforce."""
        from src.automation.salesforce_writeback import SalesforceWriteback

        leads = sf_client.get_leads()
        scorer = LeadScorer()
        scored = scorer.score_leads(leads)

        writeback = SalesforceWriteback(sf_client=sf_client)
        result = writeback.update_lead_scores(scored.head(5))
        assert result["updated"] == 5
        assert result["errors"] == 0
