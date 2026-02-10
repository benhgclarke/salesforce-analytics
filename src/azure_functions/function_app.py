"""
Azure Functions app for Salesforce data processing.

Provides HTTP-triggered and timer-triggered functions for:
- Lead scoring and prioritisation
- Pipeline health analysis
- Churn risk prediction
- Automated Salesforce writeback

Deployment: Azure Functions Core Tools or Terraform.
"""

import json
import logging
import os
from datetime import datetime

import azure.functions as func

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.azure_functions.blob_utils import AzureBlobStore
from src.automation.notifications import NotificationService

app = func.FunctionApp()
logger = logging.getLogger(__name__)


# --- HTTP-Triggered Functions (API Gateway equivalent) ---

@app.route(route="analyse", methods=["POST", "GET"], auth_level=func.AuthLevel.FUNCTION)
def analyse_salesforce(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function to run Salesforce analytics on demand.

    Query params or JSON body:
        action: 'full_analysis' | 'lead_scoring' | 'pipeline_health' | 'churn_prediction'
    """
    action = req.params.get("action")
    if not action:
        try:
            body = req.get_json()
            action = body.get("action", "full_analysis")
        except ValueError:
            action = "full_analysis"

    logger.info(f"Azure Function triggered: analyse_salesforce, action={action}")

    try:
        sf_client = SalesforceClient()
        results = {}

        if action in ("full_analysis", "lead_scoring"):
            results["lead_scoring"] = _score_leads(sf_client)

        if action in ("full_analysis", "pipeline_health"):
            results["pipeline_health"] = _analyse_pipeline(sf_client)

        if action in ("full_analysis", "churn_prediction"):
            results["churn_prediction"] = _predict_churn(sf_client)

        # Store in Azure Blob Storage
        blob_store = AzureBlobStore()
        blob_url = blob_store.store_analytics(results, action)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "action": action,
                "blob_url": blob_url,
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }, default=str),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Function failed: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="leads/scores", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_lead_scores(req: func.HttpRequest) -> func.HttpResponse:
    """Return current lead scores — useful for Power BI data source."""
    try:
        sf_client = SalesforceClient()
        leads = sf_client.get_leads()
        scorer = LeadScorer()
        scored = scorer.score_leads(leads)

        top_n = int(req.params.get("top", 50))
        result = scored.head(top_n).to_dict("records")

        return func.HttpResponse(
            json.dumps(result, default=str),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="pipeline/health", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_pipeline_health(req: func.HttpRequest) -> func.HttpResponse:
    """Return pipeline health metrics — useful for Power BI data source."""
    try:
        sf_client = SalesforceClient()
        opportunities = sf_client.get_opportunities()
        analyser = PipelineAnalyser()
        result = analyser.analyse_pipeline(opportunities)

        return func.HttpResponse(
            json.dumps(result, default=str),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="churn/risk", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_churn_risk(req: func.HttpRequest) -> func.HttpResponse:
    """Return churn risk assessment — useful for Power BI data source."""
    try:
        sf_client = SalesforceClient()
        accounts = sf_client.get_accounts()
        cases = sf_client.get_cases()
        opportunities = sf_client.get_opportunities()

        predictor = ChurnPredictor()
        result = predictor.get_risk_summary(accounts, cases, opportunities)

        return func.HttpResponse(
            json.dumps(result, default=str),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# --- Timer-Triggered Function (scheduled analytics) ---

@app.timer_trigger(
    schedule="0 0 6 * * *",  # Every day at 06:00 UTC
    arg_name="timer",
    run_on_startup=False,
)
def scheduled_analysis(timer: func.TimerRequest) -> None:
    """
    Runs full Salesforce analytics daily.
    Stores results in Blob Storage and sends notification alerts.
    """
    logger.info("Scheduled analysis triggered")

    if timer.past_due:
        logger.warning("Timer is past due — running immediately")

    try:
        sf_client = SalesforceClient()

        results = {
            "lead_scoring": _score_leads(sf_client),
            "pipeline_health": _analyse_pipeline(sf_client),
            "churn_prediction": _predict_churn(sf_client),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store results
        blob_store = AzureBlobStore()
        blob_store.store_analytics(results, "daily_full_analysis")

        # Send notifications
        _send_scheduled_notifications(results)

        logger.info("Scheduled analysis completed successfully")

    except Exception as e:
        logger.error(f"Scheduled analysis failed: {e}", exc_info=True)


# --- Shared helper functions ---

def _score_leads(sf_client):
    leads = sf_client.get_leads()
    scorer = LeadScorer()
    scored_df = scorer.score_leads(leads)
    distribution = scorer.get_score_distribution(leads)

    for _, lead in scored_df.head(10).iterrows():
        sf_client.update_record("Lead", lead["Id"], {
            "Lead_Score__c": lead["Lead_Score"],
            "Priority__c": str(lead["Priority"]),
        })

    return {
        "leads_scored": len(scored_df),
        "distribution": distribution,
        "top_leads": scored_df.head(10).to_dict("records"),
    }


def _analyse_pipeline(sf_client):
    opportunities = sf_client.get_opportunities()
    analyser = PipelineAnalyser()
    return analyser.analyse_pipeline(opportunities)


def _predict_churn(sf_client):
    accounts = sf_client.get_accounts()
    cases = sf_client.get_cases()
    opportunities = sf_client.get_opportunities()
    predictor = ChurnPredictor()
    return predictor.get_risk_summary(accounts, cases, opportunities)


def _send_scheduled_notifications(results):
    notifier = NotificationService()
    churn_data = results.get("churn_prediction", {})
    high_risk = churn_data.get("risk_breakdown", {}).get("High", 0)

    if high_risk > 0:
        notifier.send_alert({
            "type": "daily_churn_alert",
            "message": f"Daily report: {high_risk} accounts at high churn risk",
            "priority": "critical",
        })

    pipeline_data = results.get("pipeline_health", {})
    health = pipeline_data.get("health_score", {})
    if health.get("score", 100) < 40:
        notifier.send_alert({
            "type": "pipeline_health_alert",
            "message": f"Pipeline health is {health.get('rating', 'Poor')} "
                       f"(score: {health.get('score', 0)})",
            "priority": "high",
        })
