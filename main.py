"""
Main entry point for Salesforce Cloud Analytics Platform.
Run analytics from the command line or start the dashboard.

Usage:
    python main.py                          # Run full analysis
    python main.py --action lead_scoring    # Score leads only
    python main.py --action pipeline_health # Analyse pipeline only
    python main.py --action churn_prediction # Predict churn only
    python main.py --dashboard              # Start web dashboard
    python main.py --export                 # Export mock data to JSON
"""

import argparse
import json
import logging
import sys

from src.salesforce.client import SalesforceClient
from src.analytics.lead_scoring import LeadScorer
from src.analytics.pipeline_health import PipelineAnalyser
from src.analytics.churn_risk import ChurnPredictor
from src.automation.notifications import NotificationService
from src.automation.salesforce_writeback import SalesforceWriteback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_analysis(action="full_analysis"):
    """Run the analytics pipeline."""
    logger.info(f"Starting analysis: {action}")
    sf = SalesforceClient()
    results = {}

    if action in ("full_analysis", "lead_scoring"):
        logger.info("--- Lead Scoring ---")
        leads = sf.get_leads()
        scorer = LeadScorer()
        scored = scorer.score_leads(leads)
        dist = scorer.get_score_distribution(leads)

        results["lead_scoring"] = {
            "leads_scored": len(scored),
            "distribution": dist,
            "top_10": scored.head(10).to_dict("records"),
        }

        print(f"\nLead Scoring Results:")
        print(f"  Total scored: {dist['total_leads']}")
        print(f"  Average score: {dist['average_score']}")
        print(f"  Priority breakdown: {dist['priority_breakdown']}")
        print(f"  Top lead: {scored.iloc[0]['FirstName']} {scored.iloc[0]['LastName']} "
              f"({scored.iloc[0]['Company']}) — Score: {scored.iloc[0]['Lead_Score']}")

    if action in ("full_analysis", "pipeline_health"):
        logger.info("--- Pipeline Health ---")
        opps = sf.get_opportunities()
        analyser = PipelineAnalyser()
        pipeline = analyser.analyse_pipeline(opps)

        results["pipeline_health"] = pipeline

        health = pipeline["health_score"]
        print(f"\nPipeline Health:")
        print(f"  Health score: {health['score']}/100 ({health['rating']})")
        print(f"  Breakdown: {health['breakdown']}")
        vm = pipeline["velocity_metrics"]
        print(f"  Open deals: {vm['open_deals']}")
        print(f"  Open pipeline value: £{vm['open_pipeline_value']:,.0f}")
        print(f"  Risks: {len(pipeline['risk_indicators'])}")
        for rec in pipeline["recommendations"]:
            print(f"  -> {rec}")

    if action in ("full_analysis", "churn_prediction"):
        logger.info("--- Churn Prediction ---")
        accounts = sf.get_accounts()
        cases = sf.get_cases()
        opps = sf.get_opportunities()
        predictor = ChurnPredictor()
        churn = predictor.get_risk_summary(accounts, cases, opps)

        results["churn_prediction"] = churn

        print(f"\nChurn Risk:")
        print(f"  Total accounts: {churn['total_accounts']}")
        print(f"  Risk breakdown: {churn['risk_breakdown']}")
        print(f"  Revenue at risk: £{churn['total_revenue_at_risk']:,.0f}")
        if churn["high_risk_accounts"]:
            print(f"  High risk accounts:")
            for acc in churn["high_risk_accounts"][:5]:
                print(f"    - {acc['Name']} ({acc['Industry']}) — "
                      f"Score: {acc['Churn_Risk_Score']}")

    # Send summary notification
    notifier = NotificationService()
    notifier.send_daily_summary(results)

    print(f"\nAnalysis complete. Results generated for: {list(results.keys())}")
    return results


def export_data():
    """Export mock data to JSON files."""
    sf = SalesforceClient()
    counts = sf.export_to_json()
    print(f"Exported mock data: {counts}")


def start_dashboard():
    """Start the Flask web dashboard."""
    from src.dashboard.app import app
    from config.settings import DASHBOARD_CONFIG

    print(f"\nStarting dashboard at http://localhost:{DASHBOARD_CONFIG['port']}")
    app.run(
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
        debug=DASHBOARD_CONFIG["debug"],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Salesforce Cloud Analytics Platform"
    )
    parser.add_argument(
        "--action",
        choices=["full_analysis", "lead_scoring", "pipeline_health", "churn_prediction"],
        default="full_analysis",
        help="Which analysis to run (default: full_analysis)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Start the web dashboard instead of running analysis",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export mock data to JSON files",
    )

    args = parser.parse_args()

    if args.dashboard:
        start_dashboard()
    elif args.export:
        export_data()
    else:
        run_analysis(args.action)


if __name__ == "__main__":
    main()
