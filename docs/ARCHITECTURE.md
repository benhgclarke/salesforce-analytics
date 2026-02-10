# Architecture: Cloud-Enhanced Salesforce Analytics Platform

## Overview

This platform extracts data from Salesforce, processes it through cloud-based analytics engines on **both AWS and Azure**, and delivers actionable insights through a web dashboard. It demonstrates competency across both major cloud providers.

## System Architecture

```
┌──────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Salesforce      │     │   Analytics Engine   │     │   Dashboard      │
│   (REST API)      │────>│   (Python)           │────>│   (Flask + JS)   │
│                   │     │   - Lead Scoring      │     │   - Charts       │
│   Objects:        │     │   - Pipeline Health   │     │   - Tables       │
│   - Leads         │     │   - Churn Prediction  │     │   - KPIs         │
│   - Opportunities │     └──────────┬────────────┘     └──────────────────┘
│   - Accounts      │               │
│   - Cases         │     ┌─────────┴─────────┐
└──────────────────┘     │                     │
                   ┌─────┴──────┐     ┌───────┴───────┐
                   │   AWS       │     │   Azure        │
                   │             │     │                │
                   │  Lambda     │     │  Functions     │
                   │  S3         │     │  Blob Storage  │
                   │  EventBridge│     │  App Service   │
                   │  API Gateway│     │  App Insights  │
                   └─────────────┘     └────────────────┘
```

## Component Breakdown

### 1. Data Integration Layer (`src/salesforce/`)

| Component | Purpose |
|-----------|---------|
| `client.py` | Unified Salesforce API client supporting live and mock modes |
| `mock_data.py` | Generates realistic test data for Leads, Opportunities, Accounts, Cases |

**Design Decision:** The `SalesforceClient` uses a strategy pattern — mock mode for development, live mode (via `simple-salesforce`) for production. A single interface serves both.

### 2. Analytics Engine (`src/analytics/`)

| Component | Purpose |
|-----------|---------|
| `lead_scoring.py` | Weighted composite scoring (0-100) based on firmographic + behavioural signals |
| `pipeline_health.py` | Multi-factor pipeline assessment: coverage, velocity, win rate, stage distribution |
| `churn_risk.py` | Customer churn prediction based on case volume, engagement, revenue, and CSAT |

**Lead Scoring Model:**
- Company size (20%) — logarithmic scale based on employee count
- Engagement score (25%) — web visits + content downloads
- Industry match (15%) — target industries score higher
- Budget range (20%) — annual revenue as proxy
- Response time (10%) — days since last activity
- Email activity (10%) — email open count

**Pipeline Health Score (0-100):**
- Coverage ratio (25pts) — open pipeline vs quota
- Stage distribution (25pts) — penalises early-stage concentration
- Win rate (25pts) — closed-won / total closed
- Velocity (25pts) — average days in current stage

### 3. AWS Implementation (`src/aws_functions/`)

| Component | Purpose |
|-----------|---------|
| `lambda_handler.py` | AWS Lambda function — triggered by EventBridge or API Gateway |
| `s3_utils.py` | S3 data store with timestamped partitioning and lifecycle management |

**AWS Architecture:**
- **Lambda** processes Salesforce data on schedule (daily via EventBridge) or on-demand (API Gateway)
- **S3** stores analytics results with date-based partitioning (`analytics/{type}/year=/month=/day=`)
- **API Gateway** (HTTP API) exposes the Lambda as a REST endpoint
- Results are stored with AES256 server-side encryption

### 4. Azure Implementation (`src/azure_functions/`)

| Component | Purpose |
|-----------|---------|
| `function_app.py` | Azure Functions app — HTTP triggers + timer trigger |
| `blob_utils.py` | Azure Blob Storage data store with container management |

**Azure Architecture:**
- **Azure Functions** with HTTP triggers (for on-demand analysis and Power BI integration) and timer trigger (daily 06:00 UTC)
- **Blob Storage** stores results with the same partitioning scheme as S3
- **App Service** hosts the Flask dashboard
- **Application Insights** provides monitoring and telemetry

**Power BI Integration:** The HTTP endpoints (`/leads/scores`, `/pipeline/health`, `/churn/risk`) are designed to serve as Power BI data sources directly.

### 5. Automation Layer (`src/automation/`)

| Component | Purpose |
|-----------|---------|
| `notifications.py` | Multi-channel alerting: log, AWS SES email, Slack webhook |
| `salesforce_writeback.py` | Writes analytics results back to Salesforce (scores, tasks, risk flags) |

**Writeback Actions:**
- Updates `Lead_Score__c` and `Priority__c` custom fields on Lead records
- Updates `Churn_Risk_Score__c` and `Churn_Risk_Level__c` on Account records
- Creates follow-up Task records for high-priority leads
- Creates intervention Task records for high churn-risk accounts

### 6. Web Dashboard (`src/dashboard/`)

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask application with page routes and API endpoints |
| `templates/` | Jinja2 HTML templates with Chart.js visualisations |
| `static/` | CSS styles and shared JavaScript utilities |

**Dashboard Pages:**
- **Overview** — KPI cards, lead distribution, pipeline funnel, churn donut, health radar
- **Lead Scoring** — Score distribution, priority breakdown, filterable lead table
- **Pipeline Health** — Horizontal funnel, radar chart, forecast doughnut, risks and recommendations
- **Churn Risk** — Risk distribution, revenue-at-risk bar chart, filterable account table

### 7. Infrastructure as Code

| File | Provider | Resources |
|------|----------|-----------|
| `infrastructure/aws/main.tf` | AWS (Terraform) | S3, Lambda, IAM, EventBridge, API Gateway |
| `infrastructure/azure/main.bicep` | Azure (Bicep) | Storage, Function App, App Service, App Insights |

## Data Flow

```
1. EXTRACT   Salesforce REST API → SalesforceClient
2. TRANSFORM Analytics Engine → Lead Scores, Pipeline Health, Churn Risk
3. LOAD      Results → S3 (AWS) / Blob Storage (Azure)
4. PRESENT   Dashboard API → Chart.js Visualisations
5. ACT       Writeback → Salesforce (updated fields, new tasks)
6. ALERT     Notifications → Log / Email / Slack
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment (uses mock data by default)
cp .env.example .env

# Run the dashboard
python -m src.dashboard.app

# Run analytics from CLI
python main.py --action full_analysis

# Run tests
pytest tests/ -v
```

## Deployment

### AWS
```bash
# Package Lambda
cd /project-root
zip -r lambda_package.zip src/ config/ requirements.txt

# Deploy with Terraform
cd infrastructure/aws
terraform init
terraform plan
terraform apply
```

### Azure
```bash
# Deploy Function App
cd src/azure_functions
func azure functionapp publish <app-name>

# Deploy infrastructure with Bicep
az deployment group create \
  --resource-group sf-analytics-rg \
  --template-file infrastructure/azure/main.bicep \
  --parameters environment=dev
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Salesforce | simple-salesforce, REST API v59.0 |
| Analytics | pandas, numpy, scikit-learn |
| AWS | Lambda, S3, EventBridge, API Gateway, SES |
| Azure | Functions, Blob Storage, App Service, Application Insights |
| Dashboard | Flask, Chart.js, Jinja2 |
| IaC | Terraform (AWS), Bicep (Azure) |
| Testing | pytest, moto (AWS mocking) |
| Version Control | Git |
