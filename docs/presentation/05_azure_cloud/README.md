# 05 — Azure Cloud Implementation

## Where the Azure Code Lives

### Files
| File | Location | Purpose |
|------|----------|---------|
| `function_app.py` | `src/azure_functions/function_app.py` | Azure Functions app (HTTP + timer triggers) |
| `blob_utils.py` | `src/azure_functions/blob_utils.py` | Azure Blob Storage utilities |
| `host.json` | `src/azure_functions/host.json` | Azure Functions host configuration |
| `main.bicep` | `infrastructure/azure/main.bicep` | Bicep IaC for all Azure resources |

### Azure Architecture
```
Timer Trigger (daily 06:00 UTC)  ──┐
                                    ├──> Azure Functions ──> Blob Storage
HTTP Triggers (/analyse, etc.)   ──┘                       ├── analytics/lead_scoring/...
                                                            ├── analytics/pipeline_health/...
     ┌── Power BI (connected via HTTP endpoints)           └── analytics/churn_prediction/...
     │
HTTP Endpoints:
  GET /api/analyse          Full analysis
  GET /api/leads/scores     Lead scores (Power BI source)
  GET /api/pipeline/health  Pipeline health (Power BI source)
  GET /api/churn/risk       Churn risk (Power BI source)
```

### Power BI Integration
The HTTP endpoints are designed as direct Power BI Web data sources:
- JSON format, pre-aggregated for Power BI consumption
- CORS-enabled for cross-origin requests
- Can be scheduled to refresh in Power BI Service

### Bicep Resources Provisioned
- Storage Account + Blob container
- Application Insights (monitoring)
- App Service Plan (Linux, Python)
- Function App (Python 3.11 runtime)
- Web App for dashboard (gunicorn-served Flask)

### Deploy
```bash
# Deploy infrastructure
az deployment group create \
  --resource-group sf-analytics-rg \
  --template-file infrastructure/azure/main.bicep \
  --parameters environment=dev

# Deploy Function App
cd src/azure_functions
func azure functionapp publish <app-name>
```
