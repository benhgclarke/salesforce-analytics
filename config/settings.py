"""
Configuration settings for the Salesforce Cloud Analytics project.
Loads from environment variables with sensible defaults for development.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# Salesforce Configuration
SALESFORCE_CONFIG = {
    "username": os.getenv("SF_USERNAME", ""),
    "password": os.getenv("SF_PASSWORD", ""),
    "security_token": os.getenv("SF_SECURITY_TOKEN", ""),
    "domain": os.getenv("SF_DOMAIN", "login"),  # 'login' for prod, 'test' for sandbox
    "api_version": os.getenv("SF_API_VERSION", "59.0"),
}

# AWS Configuration
AWS_CONFIG = {
    "region": os.getenv("AWS_REGION", "eu-west-1"),
    "s3_bucket": os.getenv("S3_BUCKET", "salesforce-analytics-data"),
    "lambda_function_name": os.getenv("LAMBDA_FUNCTION", "sf-data-processor"),
}

# Azure Configuration
AZURE_CONFIG = {
    "storage_connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
    "storage_container": os.getenv("AZURE_CONTAINER", "salesforce-data"),
    "function_app_name": os.getenv("AZURE_FUNCTION_APP", "sf-analytics-func"),
}

# Analytics Configuration
ANALYTICS_CONFIG = {
    "lead_score_weights": {
        "company_size": 0.20,
        "engagement_score": 0.25,
        "industry_match": 0.15,
        "budget_range": 0.20,
        "response_time_days": 0.10,
        "email_opens": 0.10,
    },
    "churn_risk_thresholds": {
        "high": 0.7,
        "medium": 0.4,
        "low": 0.0,
    },
    "pipeline_health_stages": [
        "Prospecting",
        "Qualification",
        "Needs Analysis",
        "Proposal",
        "Negotiation",
        "Closed Won",
        "Closed Lost",
    ],
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    "host": os.getenv("DASHBOARD_HOST", "0.0.0.0"),
    "port": int(os.getenv("DASHBOARD_PORT", "5001")),
    "debug": os.getenv("DASHBOARD_DEBUG", "true").lower() == "true",
}

# Use mock data instead of live Salesforce connection
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
