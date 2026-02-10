# 01 — Project Overview

## Cloud-Enhanced Salesforce Automation & Analytics

A full-stack data platform that extracts Salesforce CRM data, processes it through
analytics engines on **both AWS and Azure**, and delivers insights via an interactive
web dashboard.

### What It Does
- Pulls Leads, Opportunities, Accounts, and Cases from Salesforce (or mock data)
- Scores leads 0-100 using a weighted composite model
- Assesses pipeline health across coverage, velocity, distribution, and win rate
- Predicts customer churn risk from case volume, engagement, revenue, and CSAT
- Stores results in AWS S3 and Azure Blob Storage
- Visualises everything in a live Flask + Chart.js dashboard
- Writes scores and tasks back to Salesforce

### Key Files
| File | Description |
|------|-------------|
| `main.py` | CLI entry point — run analytics, start dashboard, export data |
| `config/settings.py` | Central configuration (env vars with defaults) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

### Quick Start
```bash
pip install -r requirements.txt
python main.py --dashboard        # Launch dashboard at localhost:5000
python main.py --action full_analysis  # Run full analytics pipeline
```
