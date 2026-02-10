"""
Power BI Data Model Generator.

Generates a Power BI-compatible data model configuration and exports
analytics data as structured JSON/CSV files that Power BI can import.

Usage:
    python -m src.powerbi.powerbi_generator

This creates:
    - data/powerbi/lead_scores.csv
    - data/powerbi/lead_distribution.json
    - data/powerbi/pipeline_health.json
    - data/powerbi/pipeline_funnel.csv
    - data/powerbi/churn_risk.json
    - data/powerbi/churn_accounts.csv
    - data/powerbi/powerbi_model.json  (data model definition)
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor


def generate_powerbi_exports():
    """Generate all Power BI data exports."""
    output_dir = os.path.join(os.path.dirname(__file__), "../../data/powerbi")
    os.makedirs(output_dir, exist_ok=True)

    print("Initialising data sources...")
    sf = SalesforceClient()
    leads = sf.get_leads()
    opps = sf.get_opportunities()
    accounts = sf.get_accounts()
    cases = sf.get_cases()

    scorer = LeadScorer()
    analyser = PipelineAnalyser()
    predictor = ChurnPredictor()

    # 1. Lead Scores (CSV for Power BI table)
    print("Generating lead scores...")
    scored_leads = scorer.score_leads(leads)
    scored_leads.to_csv(os.path.join(output_dir, "lead_scores.csv"), index=False)

    # 2. Lead Distribution (JSON)
    dist = scorer.get_score_distribution(leads)
    with open(os.path.join(output_dir, "lead_distribution.json"), "w") as f:
        json.dump(dist, f, indent=2, default=str)

    # 3. Pipeline Health (JSON)
    print("Generating pipeline health...")
    pipeline = analyser.analyse_pipeline(opps)
    with open(os.path.join(output_dir, "pipeline_health.json"), "w") as f:
        json.dump(pipeline, f, indent=2, default=str)

    # 4. Pipeline Funnel (CSV)
    funnel = analyser.get_stage_funnel(opps)
    import csv
    with open(os.path.join(output_dir, "pipeline_funnel.csv"), "w", newline="") as f:
        if funnel:
            writer = csv.DictWriter(f, fieldnames=funnel[0].keys())
            writer.writeheader()
            writer.writerows(funnel)

    # 5. Churn Risk Summary (JSON)
    print("Generating churn predictions...")
    churn = predictor.get_risk_summary(accounts, cases, opps)
    with open(os.path.join(output_dir, "churn_risk.json"), "w") as f:
        json.dump(churn, f, indent=2, default=str)

    # 6. Churn Accounts (CSV)
    churn_df = predictor.predict_churn(accounts, cases, opps)
    churn_df.to_csv(os.path.join(output_dir, "churn_accounts.csv"), index=False)

    # 7. Power BI Data Model Definition
    print("Generating Power BI data model...")
    model = generate_powerbi_model(output_dir)
    with open(os.path.join(output_dir, "powerbi_model.json"), "w") as f:
        json.dump(model, f, indent=2)

    print(f"\nPower BI exports saved to: {output_dir}/")
    print("Files generated:")
    for f in sorted(os.listdir(output_dir)):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"  {f:<30} {size:>8,} bytes")

    return output_dir


def generate_powerbi_model(output_dir):
    """Generate a Power BI data model definition."""
    base_url_render = "https://salesforce-analytics-api.onrender.com/api"
    base_url_azure = "https://<your-function-app>.azurewebsites.net/api"
    base_url_local = "http://localhost:5001/api"

    model = {
        "name": "Salesforce Analytics",
        "description": "Cloud-Enhanced Salesforce Automation & Analytics data model",
        "version": "1.0",
        "data_sources": {
            "render_api": {
                "description": "Render.com hosted API (free tier — public URL)",
                "base_url": base_url_render,
                "endpoints": {
                    "dashboard_summary": {"url": f"{base_url_render}/dashboard/summary", "method": "GET"},
                    "lead_scores": {"url": f"{base_url_render}/leads/scores?limit=500", "method": "GET"},
                    "lead_distribution": {"url": f"{base_url_render}/leads/distribution", "method": "GET"},
                    "pipeline_health": {"url": f"{base_url_render}/pipeline/health", "method": "GET"},
                    "pipeline_funnel": {"url": f"{base_url_render}/pipeline/funnel", "method": "GET"},
                    "churn_risk": {"url": f"{base_url_render}/churn/risk", "method": "GET"},
                    "churn_accounts": {"url": f"{base_url_render}/churn/accounts?limit=500", "method": "GET"},
                },
            },
            "azure_functions": {
                "description": "Azure Functions HTTP endpoints (production)",
                "base_url": base_url_azure,
                "endpoints": {
                    "lead_scores": {"url": f"{base_url_azure}/leads/scores", "method": "GET"},
                    "pipeline_health": {"url": f"{base_url_azure}/pipeline/health", "method": "GET"},
                    "churn_risk": {"url": f"{base_url_azure}/churn/risk", "method": "GET"},
                    "full_analysis": {"url": f"{base_url_azure}/analyse", "method": "GET"},
                },
            },
            "local_dashboard": {
                "description": "Local Flask dashboard API (development)",
                "base_url": base_url_local,
                "endpoints": {
                    "dashboard_summary": {"url": f"{base_url_local}/dashboard/summary", "method": "GET"},
                    "lead_scores": {"url": f"{base_url_local}/leads/scores?limit=500", "method": "GET"},
                    "lead_distribution": {"url": f"{base_url_local}/leads/distribution", "method": "GET"},
                    "pipeline_health": {"url": f"{base_url_local}/pipeline/health", "method": "GET"},
                    "pipeline_funnel": {"url": f"{base_url_local}/pipeline/funnel", "method": "GET"},
                    "churn_risk": {"url": f"{base_url_local}/churn/risk", "method": "GET"},
                    "churn_accounts": {"url": f"{base_url_local}/churn/accounts?limit=500", "method": "GET"},
                },
            },
            "aws_s3": {
                "description": "AWS S3 historical data (via Amazon S3 connector)",
                "bucket": "sf-analytics-dev",
                "paths": {
                    "lead_scoring": "analytics/lead_scoring/",
                    "pipeline_health": "analytics/pipeline_health/",
                    "churn_prediction": "analytics/churn_prediction/",
                },
            },
            "csv_files": {
                "description": "Local CSV exports (for offline / demo use)",
                "files": {
                    "lead_scores": os.path.abspath(os.path.join(output_dir, "lead_scores.csv")),
                    "pipeline_funnel": os.path.abspath(os.path.join(output_dir, "pipeline_funnel.csv")),
                    "churn_accounts": os.path.abspath(os.path.join(output_dir, "churn_accounts.csv")),
                },
            },
        },
        "tables": [
            {
                "name": "LeadScores",
                "source": "lead_scores",
                "columns": [
                    {"name": "FirstName", "type": "text"},
                    {"name": "LastName", "type": "text"},
                    {"name": "Company", "type": "text"},
                    {"name": "Industry", "type": "text"},
                    {"name": "Status", "type": "text"},
                    {"name": "LeadSource", "type": "text"},
                    {"name": "Lead_Score", "type": "decimal"},
                    {"name": "Priority", "type": "text"},
                    {"name": "NumberOfEmployees", "type": "integer"},
                    {"name": "AnnualRevenue", "type": "decimal"},
                ],
                "measures": [
                    {"name": "Avg Lead Score", "formula": "AVERAGE(LeadScores[Lead_Score])"},
                    {"name": "Critical Count", "formula": "COUNTROWS(FILTER(LeadScores, LeadScores[Priority]=\"Critical\"))"},
                    {"name": "High Count", "formula": "COUNTROWS(FILTER(LeadScores, LeadScores[Priority]=\"High\"))"},
                ],
            },
            {
                "name": "PipelineFunnel",
                "source": "pipeline_funnel",
                "columns": [
                    {"name": "stage", "type": "text"},
                    {"name": "count", "type": "integer"},
                    {"name": "total_value", "type": "decimal"},
                    {"name": "avg_value", "type": "decimal"},
                    {"name": "avg_probability", "type": "decimal"},
                ],
                "measures": [
                    {"name": "Total Pipeline", "formula": "SUM(PipelineFunnel[total_value])"},
                    {"name": "Avg Deal Size", "formula": "AVERAGE(PipelineFunnel[avg_value])"},
                ],
            },
            {
                "name": "ChurnAccounts",
                "source": "churn_accounts",
                "columns": [
                    {"name": "Name", "type": "text"},
                    {"name": "Industry", "type": "text"},
                    {"name": "AnnualRevenue", "type": "decimal"},
                    {"name": "Type", "type": "text"},
                    {"name": "Churn_Risk_Score", "type": "decimal"},
                    {"name": "Churn_Risk_Level", "type": "text"},
                ],
                "measures": [
                    {"name": "Revenue at Risk", "formula": "SUMX(FILTER(ChurnAccounts, ChurnAccounts[Churn_Risk_Level]=\"High\"), ChurnAccounts[AnnualRevenue])"},
                    {"name": "High Risk Count", "formula": "COUNTROWS(FILTER(ChurnAccounts, ChurnAccounts[Churn_Risk_Level]=\"High\"))"},
                    {"name": "Avg Risk Score", "formula": "AVERAGE(ChurnAccounts[Churn_Risk_Score])"},
                ],
            },
        ],
        "relationships": [
            {
                "description": "Lead industry to churn account industry",
                "from_table": "LeadScores",
                "from_column": "Industry",
                "to_table": "ChurnAccounts",
                "to_column": "Industry",
                "type": "many-to-many",
            }
        ],
        "power_query_m": {
            "description": "Power Query M code snippets — replace BASE_URL with your Render URL",
            "note": "Replace https://salesforce-analytics-api.onrender.com with your actual Render URL after deployment",
            "lead_scores": f'let Source = Json.Document(Web.Contents("{base_url_render}/leads/scores?limit=500")), AsTable = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error), Expanded = Table.ExpandRecordColumn(AsTable, "Column1", {{"FirstName","LastName","Company","Industry","Lead_Score","Priority","Status"}}) in Expanded',
            "pipeline_health": f'let Source = Json.Document(Web.Contents("{base_url_render}/pipeline/health")), HealthScore = Source[health_score], Forecast = Source[forecast] in HealthScore',
            "churn_accounts": f'let Source = Json.Document(Web.Contents("{base_url_render}/churn/accounts?limit=500")), AsTable = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error), Expanded = Table.ExpandRecordColumn(AsTable, "Column1", {{"Name","Industry","AnnualRevenue","Type","Churn_Risk_Score","Churn_Risk_Level"}}) in Expanded',
            "pipeline_funnel": f'let Source = Json.Document(Web.Contents("{base_url_render}/pipeline/funnel")), AsTable = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error), Expanded = Table.ExpandRecordColumn(AsTable, "Column1", {{"stage","count","total_value","avg_value","avg_probability"}}) in Expanded',
        },
    }

    return model


if __name__ == "__main__":
    generate_powerbi_exports()
