# 06 — Web Dashboard

## Where the Dashboard Lives

### Files
| File | Location | Purpose |
|------|----------|---------|
| `app.py` | `src/dashboard/app.py` | Flask app (routes + REST API) |
| `base.html` | `src/dashboard/templates/base.html` | Base layout template |
| `index.html` | `src/dashboard/templates/index.html` | Main dashboard (overview) |
| `leads.html` | `src/dashboard/templates/leads.html` | Lead scoring detail page |
| `pipeline.html` | `src/dashboard/templates/pipeline.html` | Pipeline health page |
| `churn.html` | `src/dashboard/templates/churn.html` | Churn risk page |
| `style.css` | `src/dashboard/static/css/style.css` | Full stylesheet |
| `dashboard.js` | `src/dashboard/static/js/dashboard.js` | Shared JS + colour palette |

### Pages
1. **Dashboard** (`/`) — KPI cards, lead treemap, pipeline combo chart, churn doughnut, health radar, alerts
2. **Lead Scoring** (`/leads`) — Score bar chart, priority treemap, filterable lead table
3. **Pipeline Health** (`/pipeline`) — Horizontal funnel, radar chart, forecast doughnut, risks + recommendations
4. **Churn Risk** (`/churn`) — Risk doughnut, revenue-at-risk bar + avg revenue table, account table

### API Endpoints (consumed by Chart.js)
| Endpoint | Returns |
|----------|---------|
| `GET /api/dashboard/summary` | All KPIs + chart data |
| `GET /api/leads/scores?limit=N&priority=X` | Scored leads |
| `GET /api/leads/distribution` | Score distribution + priority breakdown |
| `GET /api/pipeline/health` | Health score, forecast, risks, recommendations |
| `GET /api/pipeline/funnel` | Stage funnel data |
| `GET /api/churn/risk` | Risk summary |
| `GET /api/churn/accounts?level=X&limit=N` | Per-account churn data |
| `GET /api/alerts` | Recent alert history |

### Chart Types Used
- **Treemap** — for 4+ category breakdowns (lead priorities, score ranges)
- **Doughnut** — for 3 or fewer categories (churn risk, forecast)
- **Bar** — revenue at risk, score distribution
- **Combo** — pipeline by stage (bar + line)
- **Radar** — pipeline health breakdown
- **Horizontal bar** — pipeline funnel

### Colour Palette
| Label | Hex | Use |
|-------|-----|-----|
| Critical | `#dc2626` | Dark red |
| High | `#ea580c` | Dark orange |
| Medium | `#3b82f6` | Light blue |
| Low | `#94a3b8` | Grey |
| Success/Low Risk | `#16a34a` | Dark green |

### Run Locally
```bash
python -m src.dashboard.app
# or
python main.py --dashboard
# Dashboard at http://localhost:5000
```
