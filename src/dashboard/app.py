"""
Flask web dashboard for Salesforce Analytics.
Provides a visual interface for lead scoring, pipeline health,
and churn risk analytics. Serves as a local dashboard and can be
deployed to Azure App Service or AWS Amplify.
"""

import json
import logging
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.automation.notifications import NotificationService
from config.settings import DASHBOARD_CONFIG

app = Flask(__name__)
CORS(app)


def safe_jsonify(data):
    """Serialize data to JSON, converting NaN/Infinity to null."""
    def clean(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj

    cleaned = clean(data)
    return Response(
        json.dumps(cleaned, default=str),
        mimetype="application/json",
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialise shared services
sf_client = SalesforceClient()
lead_scorer = LeadScorer()
pipeline_analyser = PipelineAnalyser()
churn_predictor = ChurnPredictor()
notifier = NotificationService()


def _generate_startup_alerts():
    """Run analytics on startup so the alerts section has data."""
    try:
        leads = sf_client.get_leads()
        opps = sf_client.get_opportunities()
        accounts = sf_client.get_accounts()
        cases = sf_client.get_cases()

        # Lead scoring alerts
        dist = lead_scorer.get_score_distribution(leads)
        critical = dist.get("priority_breakdown", {}).get("Critical", 0)
        high = dist.get("priority_breakdown", {}).get("High", 0)
        if critical > 0:
            notifier.send_alert({
                "type": "Lead Scoring",
                "message": f"{critical} leads scored as Critical priority — immediate follow-up recommended.",
                "priority": "critical",
            })
        if high > 0:
            notifier.send_alert({
                "type": "Lead Scoring",
                "message": f"{high} leads scored as High priority — schedule outreach within 24 hours.",
                "priority": "high",
            })

        # Pipeline health alerts
        pipeline = pipeline_analyser.analyse_pipeline(opps)
        health = pipeline.get("health_score", {})
        score = health.get("score", 0)
        if score < 50:
            notifier.send_alert({
                "type": "Pipeline Health",
                "message": f"Pipeline health score is {score}/100 ({health.get('rating', 'N/A')}). Review risk indicators.",
                "priority": "high",
            })

        risks = pipeline.get("risk_indicators", [])
        for risk in risks[:3]:
            notifier.send_alert({
                "type": f"Pipeline Risk: {risk.get('type', 'Unknown')}",
                "message": risk.get("message", ""),
                "priority": risk.get("severity", "medium").lower(),
            })

        # Churn risk alerts
        churn = churn_predictor.get_risk_summary(accounts, cases, opps)
        high_risk = churn.get("risk_breakdown", {}).get("High", 0)
        rev_at_risk = churn.get("total_revenue_at_risk", 0)
        if high_risk > 0:
            notifier.send_alert({
                "type": "Churn Risk",
                "message": f"{high_risk} accounts at High churn risk with £{rev_at_risk:,.0f} revenue at risk.",
                "priority": "critical",
            })

        # Forecast summary
        forecast = pipeline.get("forecast", {})
        notifier.send_alert({
            "type": "Daily Forecast",
            "message": f"Weighted forecast: £{forecast.get('total_weighted', 0):,.0f} | Commit: £{forecast.get('commit', 0):,.0f} | Best Case: £{forecast.get('best_case', 0):,.0f}",
            "priority": "info",
        })

        logger.info(f"Generated {len(notifier.get_alert_history())} startup alerts")
    except Exception as e:
        logger.error(f"Failed to generate startup alerts: {e}")


_generate_startup_alerts()


# --- Page Routes ---

@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/leads")
def leads_page():
    """Lead scoring detail page."""
    return render_template("leads.html")


@app.route("/pipeline")
def pipeline_page():
    """Pipeline health detail page."""
    return render_template("pipeline.html")


@app.route("/churn")
def churn_page():
    """Churn risk detail page."""
    return render_template("churn.html")


# --- API Routes (consumed by Chart.js frontend) ---

@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    """Return high-level metrics for the main dashboard."""
    leads = sf_client.get_leads()
    opps = sf_client.get_opportunities()
    accounts = sf_client.get_accounts()
    cases = sf_client.get_cases()

    lead_dist = lead_scorer.get_score_distribution(leads)
    pipeline = pipeline_analyser.analyse_pipeline(opps)
    churn = churn_predictor.get_risk_summary(accounts, cases, opps)

    return safe_jsonify({
        "lead_summary": lead_dist,
        "pipeline_health": pipeline.get("health_score", {}),
        "pipeline_forecast": pipeline.get("forecast", {}),
        "churn_summary": {
            "total_accounts": churn.get("total_accounts", 0),
            "risk_breakdown": churn.get("risk_breakdown", {}),
            "revenue_at_risk": churn.get("total_revenue_at_risk", 0),
        },
        "kpis": {
            "total_leads": len(leads),
            "open_opportunities": len([o for o in opps if not o.get("IsClosed")]),
            "total_pipeline_value": sum(
                o.get("Amount", 0) for o in opps if not o.get("IsClosed")
            ),
            "open_cases": len([c for c in cases if not c.get("IsClosed")]),
        },
    })


@app.route("/api/leads/scores")
def api_lead_scores():
    """Return scored leads with optional filtering."""
    leads = sf_client.get_leads()
    scored = lead_scorer.score_leads(leads)

    priority = request.args.get("priority")
    if priority:
        scored = scored[scored["Priority"] == priority]

    top_n = int(request.args.get("limit", 50))
    return safe_jsonify(scored.head(top_n).to_dict("records"))


@app.route("/api/leads/distribution")
def api_lead_distribution():
    """Return lead score distribution data for charts."""
    leads = sf_client.get_leads()
    return safe_jsonify(lead_scorer.get_score_distribution(leads))


@app.route("/api/pipeline/health")
def api_pipeline_health():
    """Return full pipeline health analysis."""
    opps = sf_client.get_opportunities()
    return safe_jsonify(pipeline_analyser.analyse_pipeline(opps))


@app.route("/api/pipeline/funnel")
def api_pipeline_funnel():
    """Return pipeline funnel data for chart."""
    opps = sf_client.get_opportunities()
    return safe_jsonify(pipeline_analyser.get_stage_funnel(opps))


@app.route("/api/churn/risk")
def api_churn_risk():
    """Return churn risk analysis."""
    accounts = sf_client.get_accounts()
    cases = sf_client.get_cases()
    opps = sf_client.get_opportunities()
    return safe_jsonify(churn_predictor.get_risk_summary(accounts, cases, opps))


@app.route("/api/churn/accounts")
def api_churn_accounts():
    """Return per-account churn risk details."""
    accounts = sf_client.get_accounts()
    cases = sf_client.get_cases()
    opps = sf_client.get_opportunities()

    df = churn_predictor.predict_churn(accounts, cases, opps)
    level = request.args.get("level")
    if level:
        df = df[df["Churn_Risk_Level"] == level]

    top_n = int(request.args.get("limit", 50))
    return safe_jsonify(df.head(top_n).to_dict("records"))


@app.route("/api/alerts")
def api_alerts():
    """Return recent alert history."""
    return safe_jsonify(notifier.get_alert_history())


if __name__ == "__main__":
    app.run(
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
        debug=DASHBOARD_CONFIG["debug"],
    )
