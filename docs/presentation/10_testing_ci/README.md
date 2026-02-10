# 10 — Testing & Quality

## Where the Tests Live

### Files
| File | Location | Scope |
|------|----------|-------|
| `test_mock_data.py` | `tests/unit/test_mock_data.py` | Mock data generator |
| `test_lead_scoring.py` | `tests/unit/test_lead_scoring.py` | Lead scoring engine |
| `test_pipeline_health.py` | `tests/unit/test_pipeline_health.py` | Pipeline health analyser |
| `test_churn_risk.py` | `tests/unit/test_churn_risk.py` | Churn predictor |
| `test_salesforce_client.py` | `tests/unit/test_salesforce_client.py` | Salesforce client |
| `test_end_to_end.py` | `tests/integration/test_end_to_end.py` | Full pipeline integration |

### Test Coverage
- **53 tests**, all passing
- Unit tests cover: data generation, scoring algorithms, edge cases, filtering
- Integration test covers: full Salesforce → Analytics → Notification pipeline

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Test Structure
```
tests/
  unit/
    test_mock_data.py         # Data shape, type validation, seeded consistency
    test_lead_scoring.py      # Score ranges, priority mapping, edge cases
    test_pipeline_health.py   # Health scoring, forecasting, funnel metrics
    test_churn_risk.py        # Risk calculation, level assignment, summaries
    test_salesforce_client.py # Client interface, mock SOQL, data retrieval
  integration/
    test_end_to_end.py        # Full pipeline: extract → analyse → alert → writeback
```
