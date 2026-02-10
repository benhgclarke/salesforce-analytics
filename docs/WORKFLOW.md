# Workflow & Data Pipeline

## End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAILY AUTOMATED PIPELINE                          │
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  EXTRACT     │    │  TRANSFORM   │    │    LOAD      │    │  PRESENT  │ │
│  │             │    │              │    │              │    │           │ │
│  │  Salesforce  │──>│  Analytics   │──>│  Cloud Store │──>│ Dashboard │ │
│  │  REST API    │    │  Engine      │    │  (S3/Blob)   │    │ (Flask)   │ │
│  └─────────────┘    └──────┬───────┘    └──────────────┘    └───────────┘ │
│                            │                                               │
│                     ┌──────┴───────┐                                       │
│                     │   ACT        │                                       │
│                     │              │                                       │
│                     │ ┌──────────┐ │                                       │
│                     │ │Writeback │ │   Scores + Tasks back to Salesforce   │
│                     │ └──────────┘ │                                       │
│                     │ ┌──────────┐ │                                       │
│                     │ │ Alerts   │ │   Email / Slack / Logs                │
│                     │ └──────────┘ │                                       │
│                     └──────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Workflow

### 1. Data Extraction
**Trigger:** EventBridge (AWS) or Timer Trigger (Azure) fires at 06:00 UTC daily

```
Salesforce CRM
  ├── GET /services/data/v59.0/query?q=SELECT ... FROM Lead
  ├── GET /services/data/v59.0/query?q=SELECT ... FROM Opportunity
  ├── GET /services/data/v59.0/query?q=SELECT ... FROM Account
  └── GET /services/data/v59.0/query?q=SELECT ... FROM Case
```

### 2. Analytics Processing
Three engines run in sequence:

```
Lead Scoring
  Input:  100 Lead records
  Model:  6-factor weighted composite (0-100)
  Output: Lead_Score, Priority (Critical/High/Medium/Low)

Pipeline Health
  Input:  80 Opportunity records
  Model:  4-factor assessment (Coverage, Distribution, Win Rate, Velocity)
  Output: Health Score (0-100), Forecast, Risk Indicators, Recommendations

Churn Prediction
  Input:  25 Accounts + 60 Cases + Opportunities
  Model:  4-signal risk score (Case Volume, Engagement, Revenue, CSAT)
  Output: Churn_Risk_Score (0-1), Churn_Risk_Level (High/Medium/Low)
```

### 3. Cloud Storage
Results stored in both AWS and Azure:

```
AWS S3:                                    Azure Blob:
  analytics/                                 analytics/
    lead_scoring/                              lead_scoring/
      year=2025/month=01/day=15/                year=2025/month=01/day=15/
        results.json                              results.json
    pipeline_health/...                        pipeline_health/...
    churn_prediction/...                       churn_prediction/...
```

### 4. Dashboard Presentation
Flask app serves 4 pages via REST API:

```
Browser ──> Flask Routes (HTML pages)
              │
              └──> API Endpoints (JSON data)
                     │
                     ├── /api/dashboard/summary
                     ├── /api/leads/scores
                     ├── /api/leads/distribution
                     ├── /api/pipeline/health
                     ├── /api/pipeline/funnel
                     ├── /api/churn/risk
                     ├── /api/churn/accounts
                     └── /api/alerts
```

### 5. Automated Actions
After analytics complete:

```
Writeback to Salesforce:
  ├── UPDATE Lead SET Lead_Score__c=85, Priority__c='Critical'
  ├── UPDATE Account SET Churn_Risk_Score__c=0.78, Churn_Risk_Level__c='High'
  ├── INSERT Task (follow-up for Critical leads)
  └── INSERT Task (intervention for High-risk accounts)

Notifications:
  ├── Log channel (always on)
  ├── AWS SES email (when configured)
  └── Slack webhook (when configured)
```

## Dual-Cloud Architecture

```
                    ┌─────────────────┐
                    │   Salesforce     │
                    │   (Data Source)  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                              │
     ┌────────┴────────┐          ┌─────────┴────────┐
     │      AWS         │          │      Azure        │
     │                  │          │                   │
     │  EventBridge     │          │  Timer Trigger    │
     │       │          │          │       │           │
     │  Lambda Function │          │  Azure Functions  │
     │       │          │          │       │           │
     │  S3 Storage      │          │  Blob Storage     │
     │       │          │          │       │           │
     │  API Gateway     │          │  HTTP Triggers ───┤──> Power BI
     │       │          │          │       │           │
     │  SES (email)     │          │  App Service      │
     │                  │          │  (Dashboard)      │
     │  CloudWatch      │          │                   │
     │  (logs)          │          │  App Insights     │
     │                  │          │  (monitoring)     │
     └─────────────────┘          └───────────────────┘
```

## Git Workflow

```
main
  └── feature/analytics-engine
  └── feature/aws-lambda
  └── feature/azure-functions
  └── feature/dashboard
  └── feature/infrastructure
```

All code on `main` branch. Feature branches used for significant changes.
Commits follow conventional commit format.
