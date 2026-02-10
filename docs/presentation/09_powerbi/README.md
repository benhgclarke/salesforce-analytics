# 09 — Power BI Integration

## How Power BI Connects

This project provides **two approaches** for Power BI integration:

### Approach 1: Azure Functions HTTP Endpoints (Recommended)
The Azure Functions app exposes REST endpoints designed as Power BI Web data sources:

| Power BI Data Source | Endpoint URL | Data |
|---------------------|-------------|------|
| Lead Scores | `https://<function-app>.azurewebsites.net/api/leads/scores` | Scored leads with priorities |
| Pipeline Health | `https://<function-app>.azurewebsites.net/api/pipeline/health` | Health score, forecast, risks |
| Churn Risk | `https://<function-app>.azurewebsites.net/api/churn/risk` | Risk summary + revenue at risk |
| Full Analysis | `https://<function-app>.azurewebsites.net/api/analyse` | Complete analytics output |

### Approach 2: Local Dashboard API (Development)
When running locally, the Flask dashboard API serves identical data:

| Power BI Data Source | Endpoint URL |
|---------------------|-------------|
| Dashboard Summary | `http://localhost:5000/api/dashboard/summary` |
| Lead Scores | `http://localhost:5000/api/leads/scores?limit=500` |
| Lead Distribution | `http://localhost:5000/api/leads/distribution` |
| Pipeline Health | `http://localhost:5000/api/pipeline/health` |
| Pipeline Funnel | `http://localhost:5000/api/pipeline/funnel` |
| Churn Risk | `http://localhost:5000/api/churn/risk` |
| Churn Accounts | `http://localhost:5000/api/churn/accounts?limit=500` |

### Approach 3: AWS S3 (Historical Data)
Power BI can connect to S3 via the Amazon S3 connector:
- Bucket: `sf-analytics-{env}`
- Path: `analytics/{type}/year=/month=/day=/results.json`

## Setup in Power BI Desktop

### Step 1: Add Web Data Source
1. Open Power BI Desktop
2. **Get Data** > **Web**
3. Enter endpoint URL (e.g., `http://localhost:5000/api/leads/scores?limit=500`)
4. Power BI will detect JSON format automatically
5. Use **Transform Data** to expand JSON records into columns

### Step 2: Add Multiple Tables
Repeat for each endpoint — creates separate tables in the data model:
- `LeadScores` from `/api/leads/scores`
- `LeadDistribution` from `/api/leads/distribution`
- `PipelineHealth` from `/api/pipeline/health`
- `PipelineFunnel` from `/api/pipeline/funnel`
- `ChurnRisk` from `/api/churn/risk`
- `ChurnAccounts` from `/api/churn/accounts`

### Step 3: Configure Refresh
- **Power BI Service**: Set scheduled refresh to match EventBridge/Timer trigger
- **Power BI Desktop**: Manual refresh or use Power BI Gateway for local sources

## Files
| File | Purpose |
|------|---------|
| `powerbi_generator.py` | Python script to generate Power BI data model JSON |
| `powerbi_template.json` | Pre-built data model template for import |
| `README.md` | This guide |
