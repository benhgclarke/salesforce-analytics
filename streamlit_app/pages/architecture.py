"""Architecture & Project Structure page."""

import streamlit as st


def show_architecture():
    st.title("🏗️ Architecture & Project Structure")

    st.subheader("System Architecture")
    st.code("""
                         ┌──────────────────────────────────────────────────────────────┐
                         │                    CLOUD EXECUTION LAYER                      │
                         │                                                              │
                         │   ┌─── AWS ──────────────┐   ┌─── Azure ────────────────┐   │
                         │   │ EventBridge (cron)    │   │ Timer Trigger (cron)     │   │
                         │   │        │              │   │        │                 │   │
                         │   │        ▼              │   │        ▼                 │   │
  ┌──────────────────┐   │   │ Lambda Function ──────┤   │ Azure Function ──────────┤   │
  │   Salesforce      │   │   │   ┌──────────────┐   │   │   ┌──────────────────┐   │   │
  │   (REST API)      │───┼──►│   │  Analytics   │   │   │   │  Analytics       │   │   │
  │                   │   │   │   │  Engine      │   │   │   │  Engine          │   │   │
  │   Objects:        │   │   │   │ • Lead Score │   │   │   │ • Lead Score     │   │   │
  │   - Leads         │   │   │   │ • Pipeline   │   │   │   │ • Pipeline       │   │   │
  │   - Opportunities │   │   │   │ • Churn Risk │   │   │   │ • Churn Risk     │   │   │
  │   - Accounts      │   │   │   └──────┬───────┘   │   │   └──────┬───────────┘   │   │
  │   - Cases         │   │   │          │           │   │          │               │   │
  └──────────────────┘   │   │          ▼           │   │          ▼               │   │
          ▲              │   │   S3 Bucket           │   │   Blob Storage           │   │
          │              │   │   (results + CSV)     │   │   (results + CSV)        │   │
          │              │   │          │           │   │          │               │   │
          │              │   │   API Gateway         │   │   App Service            │   │
          │              │   │          │           │   │          │               │   │
          │              │   └──────────┼───────────┘   └──────────┼───────────────┘   │
          │              │              │                           │                   │
          │              └──────────────┼───────────────────────────┼───────────────────┘
          │                             │                           │
          │                             ▼                           ▼
          │              ┌──────────────────────────────────────────────────────────────┐
          │              │                    PRESENTATION LAYER                         │
          │              │                                                              │
          │              │   Flask + Chart.js    Streamlit Cloud    Power BI             │
          │              │   (local dashboard)   (hosted dashboard) (enterprise BI)     │
          │              └──────────────────────────────────────────────────────────────┘
          │
  ┌───────┴──────────┐
  │   Automation      │
  │   - Writeback     │
  │   - Notifications │
  │   - SES / Slack   │
  └──────────────────┘
""", language="text")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("📂 Where Files Live")
        st.markdown("""
| Component | Location |
|-----------|----------|
| Salesforce client | `src/salesforce/client.py` |
| Mock data generator | `src/salesforce/mock_data.py` |
| Lead scoring engine | `src/analytics/lead_scoring.py` |
| Pipeline health | `src/analytics/pipeline_health.py` |
| Churn predictor | `src/analytics/churn_risk.py` |
| AWS Lambda handler | `src/aws_functions/lambda_handler.py` |
| AWS S3 utilities | `src/aws_functions/s3_utils.py` |
| Azure Functions app | `src/azure_functions/function_app.py` |
| Azure Blob utilities | `src/azure_functions/blob_utils.py` |
| Flask dashboard | `src/dashboard/app.py` |
| Notifications | `src/automation/notifications.py` |
| SF Writeback | `src/automation/salesforce_writeback.py` |
| Terraform (AWS) | `infrastructure/aws/main.tf` |
| Bicep (Azure) | `infrastructure/azure/main.bicep` |
        """)

    with right:
        st.subheader("🔧 Technology Stack")
        st.markdown("""
| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Salesforce | simple-salesforce, REST API v59.0 |
| Analytics | pandas, numpy |
| AWS | Lambda, S3, EventBridge, API Gateway, SES |
| Azure | Functions, Blob Storage, App Service, App Insights |
| Dashboard | Flask + Chart.js (local), Streamlit (cloud) |
| IaC | Terraform (AWS), Bicep (Azure) |
| Testing | pytest (53 tests, all passing) |
| Visualisation | Plotly, Chart.js |
        """)

    st.divider()
    st.subheader("Data Flow")
    st.code("""
1. TRIGGER    EventBridge (AWS) / Timer Trigger (Azure)  →  Scheduled invocation
2. EXTRACT    Lambda / Azure Function  →  Salesforce REST API  →  Leads, Opps, Accounts, Cases
3. TRANSFORM  Analytics Engine (inside function)  →  Lead Scores, Pipeline Health, Churn Risk
4. STORE      Results  →  S3 Bucket (AWS) / Blob Storage (Azure)  →  JSON + CSV exports
5. SERVE      API Gateway (AWS) / App Service (Azure)  →  REST endpoints for consumers
6. PRESENT    Flask + Chart.js / Streamlit Cloud / Power BI  →  Dashboards & reports
7. ACT        Writeback  →  Salesforce (updated fields, new tasks)
8. ALERT      Notifications  →  SES (AWS) / Log / Slack
""", language="text")

    st.divider()
    st.subheader("Analytics Models")

    tab1, tab2, tab3 = st.tabs(["Lead Scoring", "Pipeline Health", "Churn Prediction"])

    with tab1:
        st.markdown("""
        **Weighted Composite Score (0-100)**

        | Factor | Weight | Signal |
        |--------|--------|--------|
        | Company Size | 20% | Employee count (log scale) |
        | Engagement | 25% | Web visits + content downloads |
        | Industry Match | 15% | Target industry list |
        | Budget Range | 20% | Annual revenue as proxy |
        | Response Time | 10% | Days since last activity |
        | Email Activity | 10% | Email open count |

        **Priority**: Critical (80+), High (60-79), Medium (40-59), Low (<40)
        """)

    with tab2:
        st.markdown("""
        **Four-Factor Assessment (each 25 points)**

        - **Coverage** — Open pipeline vs target quota ratio
        - **Distribution** — Penalises early-stage concentration
        - **Win Rate** — Closed-won vs total closed deals
        - **Velocity** — Average days in current stage
        """)

    with tab3:
        st.markdown("""
        **Four Risk Signals Combined**

        | Signal | Weight | Measures |
        |--------|--------|----------|
        | Case Volume | 30% | Open cases per account |
        | Engagement | 25% | Days since last activity |
        | Revenue | 25% | Revenue relative to median |
        | Satisfaction | 20% | Average CSAT score |

        **Risk Level**: High (>0.6), Medium (0.3-0.6), Low (<0.3)
        """)
