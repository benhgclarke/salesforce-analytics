# Deploy Online — Shareable Dashboard Links

Three options to get a clickable link anyone can view:

---

## Option 1: Streamlit Cloud (FREE — Recommended for Dashboard)

Streamlit Community Cloud gives you a free shareable URL with no login required for viewers.

### Steps

1. **Push this repo to GitHub** (if not already):
   ```bash
   git add -A
   git commit -m "feat: add Streamlit Cloud dashboard"
   git push -u origin main
   ```

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

3. **Click "New app"** and configure:
   - **Repository**: `benhgclarke/salesforce-analytics`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`

4. **Click Deploy**. Streamlit builds and hosts it. You get a URL like:
   ```
   https://your-app-name.streamlit.app
   ```

5. **Share the link** — anyone can click it and see the dashboard. No login needed.

### Pages (one per tab in sidebar)
- **Overview** — KPIs, treemap charts, alerts
- **Lead Scoring** — Score distribution, priority breakdown, lead table
- **Pipeline Health** — Funnel, radar, forecast, risks & recommendations
- **Churn Risk** — Risk distribution, revenue at risk, account table
- **Architecture** — System diagram, file locations, tech stack

### Test Locally First
```bash
streamlit run streamlit_app/app.py
```
Opens at http://localhost:8501

---

## Option 2: Render.com API (FREE — For Power BI / Live Data)

Deploy the Flask REST API to Render.com so Power BI (or any client) can fetch
live analytics data from a public URL. No credit card required.

### One-Click Deploy

1. Go to [render.com/deploy](https://render.com/deploy) and sign in with GitHub.

2. Click **New → Web Service** and connect your repo:
   - **Repository**: `benhgclarke/salesforce-analytics`
   - **Branch**: `main`
   - **Build command**: `pip install -r deploy/api/requirements.txt`
   - **Start command**: `gunicorn deploy.api.app:app --bind 0.0.0.0:$PORT --timeout 120`
   - **Plan**: Free

3. Add environment variable:
   - `USE_MOCK_DATA` = `true`

4. Click **Create Web Service**. Render builds and deploys. You get a URL like:
   ```
   https://salesforce-analytics-api.onrender.com
   ```

5. Test the API by visiting:
   ```
   https://salesforce-analytics-api.onrender.com/
   ```
   This shows all available endpoints.

### Or use the Blueprint

The repo includes a `render.yaml` blueprint — Render can auto-detect it:
```bash
# Just push to GitHub and connect the repo on Render
# render.yaml handles all the config
```

### Available Endpoints (after deployment)

| Endpoint | Returns |
|----------|---------|
| `GET /` | API index with all routes |
| `GET /api/dashboard/summary` | Full KPI summary |
| `GET /api/leads/scores?limit=N&priority=X` | Scored leads (JSON) |
| `GET /api/leads/distribution` | Score distribution + priority breakdown |
| `GET /api/pipeline/health` | Full pipeline analysis |
| `GET /api/pipeline/funnel` | Stage funnel data |
| `GET /api/churn/risk` | Churn risk summary |
| `GET /api/churn/accounts?level=X&limit=N` | Per-account churn data |
| `GET /api/alerts` | Recent alert history |
| `GET /model` | Power BI data model definition |
| `GET /csv/<filename>` | Download CSV export |
| `GET /csvjson/<filename>` | CSV content as JSON |

### Test Locally First
```bash
pip install -r deploy/api/requirements.txt
python deploy/api/app.py
```
Opens at http://localhost:5001

---

## Option 3: Power BI Service (Requires Microsoft 365 licence)

### Steps

1. **Open Power BI Desktop** (free download from Microsoft)

2. **Get Data → Web** and add these endpoints (use your Render URL or localhost):
   - `https://YOUR-APP.onrender.com/api/leads/scores?limit=500`
   - `https://YOUR-APP.onrender.com/api/leads/distribution`
   - `https://YOUR-APP.onrender.com/api/pipeline/health`
   - `https://YOUR-APP.onrender.com/api/pipeline/funnel`
   - `https://YOUR-APP.onrender.com/api/churn/risk`
   - `https://YOUR-APP.onrender.com/api/churn/accounts?limit=500`

3. **Transform Data** to expand JSON records into columns.

4. **Create report pages** (one per section):
   - Page 1: Overview — KPI cards + summary charts
   - Page 2: Lead Scoring — bar + doughnut charts
   - Page 3: Pipeline Health — funnel + radar
   - Page 4: Churn Risk — doughnut + revenue bar

5. **Publish to Power BI Service**:
   - File → Publish → Publish to Power BI
   - Select your workspace
   - Get shareable link from the workspace

6. **Configure scheduled refresh** pointing at your Render URL.

### Power Query M Code (Copy-Paste)
See `data/powerbi/powerbi_model.json` for ready-made M code snippets.
After deploying to Render, the M code will point to your live URL.

### CSV Import (Offline Demo)
If you don't want live endpoints, import the CSV files directly:
- `data/powerbi/lead_scores.csv`
- `data/powerbi/pipeline_funnel.csv`
- `data/powerbi/churn_accounts.csv`

---

## Quick Comparison

| Feature | Streamlit Cloud | Render API | Power BI Service |
|---------|----------------|------------|-----------------|
| Cost | Free | Free | Requires Pro/Premium licence |
| Setup time | 5 minutes | 5 minutes | 30-60 minutes |
| What it serves | Visual dashboard | JSON/CSV API | Report + visuals |
| Viewer login needed | No | No (public API) | Depends on sharing |
| Interactive filters | Yes (dropdowns) | Yes (query params) | Yes (slicers) |
| Live data refresh | On page load | On API call | Scheduled (8x/day on Pro) |
| Embed in website | Yes (iframe) | Yes (fetch API) | Yes (embed code) |

---

## Deployment Files

| File | Purpose |
|------|---------|
| `deploy/api/app.py` | Self-contained Flask API for deployment |
| `deploy/api/requirements.txt` | Minimal Python dependencies |
| `Procfile` | Gunicorn start command (Render/Heroku) |
| `render.yaml` | Render.com blueprint (auto-config) |
| `runtime.txt` | Python version for deployment |
| `data/powerbi/powerbi_model.json` | Power BI data model + M code |
