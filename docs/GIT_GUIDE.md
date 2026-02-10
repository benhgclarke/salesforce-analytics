# Git Version Control

## Repository Structure

```
.
├── config/                  # Configuration and settings
│   ├── settings.py          # Central config (env vars with defaults)
│   └── __init__.py
├── data/                    # Exported analytics data (JSON)
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System architecture reference
│   ├── WORKFLOW.md          # Data pipeline workflow
│   ├── GIT_GUIDE.md         # This file
│   └── presentation/        # Numbered folders for screenshare
│       ├── 01_overview/
│       ├── 02_salesforce_data/
│       ├── 03_analytics_engine/
│       ├── 04_aws_cloud/
│       ├── 05_azure_cloud/
│       ├── 06_dashboard/
│       ├── 07_automation/
│       ├── 08_infrastructure/
│       ├── 09_powerbi/
│       └── 10_testing_ci/
├── infrastructure/          # Infrastructure as Code
│   ├── aws/main.tf          # Terraform (AWS)
│   └── azure/main.bicep     # Bicep (Azure)
├── src/                     # Source code
│   ├── salesforce/          # Salesforce data layer
│   │   ├── client.py
│   │   └── mock_data.py
│   ├── analytics/           # Analytics engines
│   │   ├── lead_scoring.py
│   │   ├── pipeline_health.py
│   │   └── churn_risk.py
│   ├── aws_functions/       # AWS Lambda handlers
│   │   ├── lambda_handler.py
│   │   └── s3_utils.py
│   ├── azure_functions/     # Azure Functions app
│   │   ├── function_app.py
│   │   ├── blob_utils.py
│   │   └── host.json
│   ├── automation/          # Notifications + writeback
│   │   ├── notifications.py
│   │   └── salesforce_writeback.py
│   └── dashboard/           # Flask web dashboard
│       ├── app.py
│       ├── templates/
│       └── static/
├── tests/                   # Test suite
│   ├── unit/
│   └── integration/
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── .gitignore               # Git ignore rules
```

## Key Branches
- `main` — production-ready code, all tests passing

## Commit History
View with:
```bash
git log --oneline --graph
```

## Common Commands
```bash
# Status
git status

# View changes
git diff

# Stage and commit
git add -A
git commit -m "feat: add churn risk analytics engine"

# View branch history
git log --oneline -20
```
