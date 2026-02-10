# Deploy Online — Shareable Dashboard Links

Two options to get a clickable link anyone can view:

---

## Option 1: Streamlit Cloud (FREE — Recommended)

Streamlit Community Cloud gives you a free shareable URL with no login required for viewers.

### Steps

1. **Push this repo to GitHub** (if not already):
   ```bash
   git add -A
   git commit -m "feat: add Streamlit Cloud dashboard"
   git remote add origin https://github.com/YOUR_USERNAME/sf-analytics.git
   git push -u origin main
   ```

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

3. **Click "New app"** and configure:
   - **Repository**: `YOUR_USERNAME/sf-analytics`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`

4. **Click Deploy**. Streamlit builds and hosts it. You get a URL like:
   ```
   https://your-app-name.streamlit.app
   ```

5. **Share the link** — anyone can click it and see the dashboard. No login needed.

### Pages (one per tab in sidebar)
- **Dashboard** — Overview with KPIs, doughnut charts, alerts
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

## Option 2: Power BI Service (Requires Microsoft 365 licence)

### Steps

1. **Open Power BI Desktop** (free download from Microsoft)

2. **Get Data → Web** and add these endpoints (start the local dashboard first):
   - `http://localhost:5001/api/leads/scores?limit=500`
   - `http://localhost:5001/api/leads/distribution`
   - `http://localhost:5001/api/pipeline/health`
   - `http://localhost:5001/api/pipeline/funnel`
   - `http://localhost:5001/api/churn/risk`
   - `http://localhost:5001/api/churn/accounts?limit=500`

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

6. For **live data from Azure Functions** (production):
   - Replace localhost URLs with your Azure Function App URLs
   - Configure scheduled refresh in Power BI Service

### Power Query M Code (Copy-Paste)
See `data/powerbi/powerbi_model.json` for ready-made M code snippets.

### CSV Import (Offline Demo)
If you don't want live endpoints, import the CSV files directly:
- `data/powerbi/lead_scores.csv`
- `data/powerbi/pipeline_funnel.csv`
- `data/powerbi/churn_accounts.csv`

---

## Quick Comparison

| Feature | Streamlit Cloud | Power BI Service |
|---------|----------------|-----------------|
| Cost | Free | Requires Pro/Premium licence |
| Setup time | 5 minutes | 30-60 minutes |
| Viewer login needed | No | Depends on sharing settings |
| Interactive filters | Yes (dropdowns) | Yes (slicers) |
| Live data refresh | On page load | Scheduled (8x/day on Pro) |
| Custom branding | Limited | Full |
| Embed in website | Yes (iframe) | Yes (embed code) |
