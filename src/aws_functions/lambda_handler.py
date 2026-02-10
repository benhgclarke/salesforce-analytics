"""
AWS Lambda handler for Salesforce data processing.

Triggered on a schedule (EventBridge) or via API Gateway.
Extracts Salesforce data, runs analytics, stores results in S3,
and optionally writes back to Salesforce.

Deployment: Package with dependencies and deploy via SAM or Terraform.
"""

import json
import logging
import os
from datetime import datetime

import boto3

# These imports work when deployed as a Lambda layer or packaged together
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.automation.notifications import NotificationService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
S3_BUCKET = os.environ.get("S3_BUCKET", "salesforce-analytics-data")


def handler(event, context):
    """
    Main Lambda entry point.

    Supports multiple operation modes via the 'action' field in the event:
    - 'full_analysis': Run all analytics and store results
    - 'lead_scoring': Score leads only
    - 'pipeline_health': Analyse pipeline only
    - 'churn_prediction': Predict churn only
    """
    action = event.get("action", "full_analysis")
    logger.info(f"Lambda invoked with action: {action}")

    try:
        sf_client = SalesforceClient()
        results = {}

        if action in ("full_analysis", "lead_scoring"):
            results["lead_scoring"] = _run_lead_scoring(sf_client)

        if action in ("full_analysis", "pipeline_health"):
            results["pipeline_health"] = _run_pipeline_analysis(sf_client)

        if action in ("full_analysis", "churn_prediction"):
            results["churn_prediction"] = _run_churn_prediction(sf_client)

        # Store results in S3
        timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H%M%S")
        s3_key = f"analytics/{action}/{timestamp}/results.json"
        _store_results_s3(results, s3_key)

        # Trigger notifications for critical findings
        _send_notifications(results)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Successfully completed {action}",
                "s3_location": f"s3://{S3_BUCKET}/{s3_key}",
                "summary": _build_summary(results),
            }, default=str),
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def _run_lead_scoring(sf_client):
    """Extract leads and run scoring."""
    logger.info("Running lead scoring...")
    leads = sf_client.get_leads()
    scorer = LeadScorer()
    scored_df = scorer.score_leads(leads)
    distribution = scorer.get_score_distribution(leads)

    # Write scores back to Salesforce
    top_leads = scored_df.head(10)
    for _, lead in top_leads.iterrows():
        sf_client.update_record("Lead", lead["Id"], {
            "Lead_Score__c": lead["Lead_Score"],
            "Priority__c": str(lead["Priority"]),
        })

    return {
        "leads_scored": len(scored_df),
        "distribution": distribution,
        "top_leads": scored_df.head(10).to_dict("records"),
    }


def _run_pipeline_analysis(sf_client):
    """Extract opportunities and analyse pipeline."""
    logger.info("Running pipeline analysis...")
    opportunities = sf_client.get_opportunities()
    analyser = PipelineAnalyser()
    analysis = analyser.analyse_pipeline(opportunities)
    return analysis


def _run_churn_prediction(sf_client):
    """Run churn risk analysis across accounts."""
    logger.info("Running churn prediction...")
    accounts = sf_client.get_accounts()
    cases = sf_client.get_cases()
    opportunities = sf_client.get_opportunities()

    predictor = ChurnPredictor()
    summary = predictor.get_risk_summary(accounts, cases, opportunities)
    return summary


def _store_results_s3(results, key):
    """Store analytics results in S3."""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(results, indent=2, default=str),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        logger.info(f"Results stored: s3://{S3_BUCKET}/{key}")
    except Exception as e:
        logger.error(f"Failed to store results in S3: {e}")
        raise


def _send_notifications(results):
    """Send notifications for critical findings."""
    notifier = NotificationService()
    alerts = []

    # Check for critical lead scores
    lead_data = results.get("lead_scoring", {})
    dist = lead_data.get("distribution", {})
    critical_count = dist.get("priority_breakdown", {}).get("Critical", 0)
    if critical_count > 0:
        alerts.append({
            "type": "lead_alert",
            "message": f"{critical_count} critical-priority leads identified",
            "priority": "high",
        })

    # Check for pipeline risks
    pipeline_data = results.get("pipeline_health", {})
    risks = pipeline_data.get("risk_indicators", [])
    for risk in risks:
        if risk.get("severity") == "High":
            alerts.append({
                "type": "pipeline_risk",
                "message": risk.get("message", "Pipeline risk detected"),
                "priority": "high",
            })

    # Check for high churn risk
    churn_data = results.get("churn_prediction", {})
    high_risk = churn_data.get("risk_breakdown", {}).get("High", 0)
    if high_risk > 0:
        alerts.append({
            "type": "churn_alert",
            "message": f"{high_risk} accounts at high churn risk",
            "priority": "critical",
        })

    for alert in alerts:
        notifier.send_alert(alert)

    return alerts


def _build_summary(results):
    """Build a concise summary of all analytics results."""
    summary = {}

    if "lead_scoring" in results:
        summary["leads"] = {
            "total_scored": results["lead_scoring"].get("leads_scored", 0),
            "avg_score": results["lead_scoring"]
            .get("distribution", {})
            .get("average_score", 0),
        }

    if "pipeline_health" in results:
        health = results["pipeline_health"].get("health_score", {})
        summary["pipeline"] = {
            "health_score": health.get("score", 0),
            "rating": health.get("rating", "Unknown"),
        }

    if "churn_prediction" in results:
        summary["churn"] = {
            "high_risk_accounts": results["churn_prediction"]
            .get("risk_breakdown", {})
            .get("High", 0),
            "revenue_at_risk": results["churn_prediction"]
            .get("total_revenue_at_risk", 0),
        }

    return summary


# Allow local testing
if __name__ == "__main__":
    test_event = {"action": "full_analysis"}
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
