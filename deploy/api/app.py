"""
Salesforce Analytics — Deployable REST API.

A lightweight Flask app that serves analytics data via JSON and CSV endpoints.
Designed for deployment on Render.com (free tier) so that Power BI, Streamlit,
or any other client can pull live data from a public URL.

Endpoints:
    GET /                        → API index with all available routes
    GET /api/dashboard/summary   → Full KPI summary
    GET /api/leads/scores        → Scored leads (JSON)
    GET /api/leads/distribution  → Score distribution
    GET /api/pipeline/health     → Pipeline analysis
    GET /api/pipeline/funnel     → Stage funnel
    GET /api/churn/risk          → Churn risk summary
    GET /api/churn/accounts      → Per-account churn data
    GET /api/alerts              → Recent alerts
    GET /model                   → Power BI data model definition
    GET /csv/<filename>          → Download a CSV export
    GET /csvjson/<filename>      → CSV content as JSON array

Run locally:
    pip install -r requirements.txt
    python app.py                   # http://localhost:5001
"""

import json
import math
import os
import sys

# Allow imports from the project root when running inside the repo
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.automation.notifications import NotificationService

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Data directory — pre-generated CSV/JSON exports live here
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "powerbi")


# ---------------------------------------------------------------------------
# Utility: safe JSON serialisation (NaN / Infinity → null)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Initialise analytics services (mock data by default)
# ---------------------------------------------------------------------------
sf = SalesforceClient()
scorer = LeadScorer()
analyser = PipelineAnalyser()
predictor = ChurnPredictor()
notifier = NotificationService()


def _generate_startup_alerts():
    """Pre-populate alert history so /api/alerts returns useful data."""
    try:
        leads = sf.get_leads()
        opps = sf.get_opportunities()
        accounts = sf.get_accounts()
        cases = sf.get_cases()

        dist = scorer.get_score_distribution(leads)
        critical = dist.get("priority_breakdown", {}).get("Critical", 0)
        high = dist.get("priority_breakdown", {}).get("High", 0)
        if critical > 0:
            notifier.send_alert({
                "type": "Lead Scoring",
                "message": f"{critical} leads scored as Critical priority.",
                "priority": "critical",
            })
        if high > 0:
            notifier.send_alert({
                "type": "Lead Scoring",
                "message": f"{high} leads scored as High priority.",
                "priority": "high",
            })

        pipeline = analyser.analyse_pipeline(opps)
        health = pipeline.get("health_score", {})
        score = health.get("score", 0)
        if score < 50:
            notifier.send_alert({
                "type": "Pipeline Health",
                "message": f"Health score {score}/100 ({health.get('rating', 'N/A')}).",
                "priority": "high",
            })

        for risk in pipeline.get("risk_indicators", [])[:3]:
            notifier.send_alert({
                "type": f"Pipeline Risk: {risk.get('type', '')}",
                "message": risk.get("message", ""),
                "priority": risk.get("severity", "medium").lower(),
            })

        churn = predictor.get_risk_summary(accounts, cases, opps)
        high_risk = churn.get("risk_breakdown", {}).get("High", 0)
        rev = churn.get("total_revenue_at_risk", 0)
        if high_risk > 0:
            notifier.send_alert({
                "type": "Churn Risk",
                "message": f"{high_risk} accounts at High churn risk ({rev:,.0f} revenue at risk).",
                "priority": "critical",
            })

        forecast = pipeline.get("forecast", {})
        notifier.send_alert({
            "type": "Daily Forecast",
            "message": f"Weighted: {forecast.get('total_weighted', 0):,.0f} | Commit: {forecast.get('commit', 0):,.0f}",
            "priority": "info",
        })
    except Exception as e:
        print(f"Alert generation failed: {e}")


_generate_startup_alerts()


# ---------------------------------------------------------------------------
# API Index
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """API index listing all available endpoints."""
    return safe_jsonify({
        "name": "Salesforce Analytics API",
        "version": "1.0",
        "endpoints": {
            "/api/dashboard/summary": "Full KPI summary",
            "/api/leads/scores?priority=X&limit=N": "Scored leads (JSON)",
            "/api/leads/distribution": "Score distribution + priority breakdown",
            "/api/pipeline/health": "Full pipeline analysis",
            "/api/pipeline/funnel": "Stage funnel data",
            "/api/churn/risk": "Churn risk summary",
            "/api/churn/accounts?level=X&limit=N": "Per-account churn data",
            "/api/alerts": "Recent alert history",
            "/model": "Power BI data model definition (JSON)",
            "/csv/<filename>": "Download CSV export (e.g. /csv/lead_scores.csv)",
            "/csvjson/<filename>": "CSV content as JSON array",
        },
    })


# ---------------------------------------------------------------------------
# Analytics API endpoints (same as main dashboard)
# ---------------------------------------------------------------------------
@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    leads = sf.get_leads()
    opps = sf.get_opportunities()
    accounts = sf.get_accounts()
    cases = sf.get_cases()

    lead_dist = scorer.get_score_distribution(leads)
    pipeline = analyser.analyse_pipeline(opps)
    churn = predictor.get_risk_summary(accounts, cases, opps)

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
    leads = sf.get_leads()
    scored = scorer.score_leads(leads)
    priority = request.args.get("priority")
    if priority:
        scored = scored[scored["Priority"] == priority]
    top_n = int(request.args.get("limit", 50))
    return safe_jsonify(scored.head(top_n).to_dict("records"))


@app.route("/api/leads/distribution")
def api_lead_distribution():
    leads = sf.get_leads()
    return safe_jsonify(scorer.get_score_distribution(leads))


@app.route("/api/pipeline/health")
def api_pipeline_health():
    opps = sf.get_opportunities()
    return safe_jsonify(analyser.analyse_pipeline(opps))


@app.route("/api/pipeline/funnel")
def api_pipeline_funnel():
    opps = sf.get_opportunities()
    return safe_jsonify(analyser.get_stage_funnel(opps))


@app.route("/api/churn/risk")
def api_churn_risk():
    accounts = sf.get_accounts()
    cases = sf.get_cases()
    opps = sf.get_opportunities()
    return safe_jsonify(predictor.get_risk_summary(accounts, cases, opps))


@app.route("/api/churn/accounts")
def api_churn_accounts():
    accounts = sf.get_accounts()
    cases = sf.get_cases()
    opps = sf.get_opportunities()
    df = predictor.predict_churn(accounts, cases, opps)
    level = request.args.get("level")
    if level:
        df = df[df["Churn_Risk_Level"] == level]
    top_n = int(request.args.get("limit", 50))
    return safe_jsonify(df.head(top_n).to_dict("records"))


@app.route("/api/alerts")
def api_alerts():
    return safe_jsonify(notifier.get_alert_history())


# ---------------------------------------------------------------------------
# Power BI model + CSV/JSON file serving
# ---------------------------------------------------------------------------
@app.route("/model")
def get_model():
    """Serve the Power BI data model definition."""
    model_file = os.path.join(DATA_DIR, "powerbi_model.json")
    if os.path.exists(model_file):
        with open(model_file) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Model file not found — run powerbi_generator first"}), 404


@app.route("/csv/<filename>")
def get_csv(filename):
    """Download a CSV export file."""
    if not filename.endswith(".csv"):
        return jsonify({"error": "Only .csv files can be served"}), 400
    csv_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(csv_path):
        return send_file(csv_path, mimetype="text/csv", as_attachment=True)
    return jsonify({"error": f"File '{filename}' not found"}), 404


@app.route("/csvjson/<filename>")
def get_csv_json(filename):
    """Return CSV content as a JSON array of records."""
    if not filename.endswith(".csv"):
        return jsonify({"error": "Only .csv files can be served"}), 400
    csv_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        return safe_jsonify(df.to_dict("records"))
    return jsonify({"error": f"File '{filename}' not found"}), 404


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
