# 03 — Analytics Engine (Python Scripts)

## Where the Python Analytics Live

All analytics scripts are in `src/analytics/`.

### Files
| File | Location | Purpose |
|------|----------|---------|
| `lead_scoring.py` | `src/analytics/lead_scoring.py` | Weighted lead scoring model |
| `pipeline_health.py` | `src/analytics/pipeline_health.py` | Pipeline health assessment |
| `churn_risk.py` | `src/analytics/churn_risk.py` | Customer churn predictor |

### Lead Scoring Model
Scores each lead 0-100 using 6 weighted factors:
| Factor | Weight | Signal |
|--------|--------|--------|
| Company Size | 20% | NumberOfEmployees (log scale) |
| Engagement | 25% | Web visits + content downloads |
| Industry Match | 15% | Target industry list |
| Budget Range | 20% | AnnualRevenue as proxy |
| Response Time | 10% | Days since last activity |
| Email Activity | 10% | Email open count |

Priority assignment: Critical (80+), High (60-79), Medium (40-59), Low (<40)

### Pipeline Health Score (0-100)
Four factors, each worth 25 points:
- **Coverage** — ratio of open pipeline to target quota
- **Distribution** — penalises concentration in early stages
- **Win Rate** — closed-won vs total closed deals
- **Velocity** — average days opportunities sit in each stage

### Churn Risk Prediction
Four risk signals combined:
| Signal | Weight | Measures |
|--------|--------|----------|
| Case Volume | 30% | Open case count per account |
| Engagement | 25% | Days since last activity |
| Revenue | 25% | Revenue relative to median |
| Satisfaction | 20% | Average CSAT score |

Risk levels: High (>0.6), Medium (0.3-0.6), Low (<0.3)
