# 02 — Salesforce Data Layer

## Where the Data Lives

### Files
| File | Location | Purpose |
|------|----------|---------|
| `client.py` | `src/salesforce/client.py` | Unified API client (mock + live Salesforce) |
| `mock_data.py` | `src/salesforce/mock_data.py` | Generates realistic CRM test data |

### How It Works
The `SalesforceClient` class uses a **strategy pattern**:
- **Mock mode** (default): Generates data in-memory via `MockSalesforceData`
- **Live mode**: Connects to a real Salesforce org via `simple-salesforce`

Toggle via the `USE_MOCK_DATA` environment variable in `.env`.

### Salesforce Objects Used
| Object | Key Fields | Records Generated |
|--------|-----------|-------------------|
| Lead | Name, Company, Industry, Status, engagement metrics | 100 |
| Opportunity | Name, StageName, Amount, Probability, CloseDate | 80 |
| Account | Name, Industry, AnnualRevenue, Type | 25 |
| Case | Subject, Priority, Status, CSAT_Score__c | 60 |

### Mock Data Profiles
- **Leads**: Hot (15%), Warm (25%), Cold (30%), Dead (30%) — varying engagement
- **Accounts**: Disengaged (25%), At-Risk (25%), Healthy (50%)
- **Cases**: 60% concentrated on at-risk accounts with low CSAT

### To Connect Real Salesforce
Set these environment variables:
```
USE_MOCK_DATA=false
SF_USERNAME=your_username
SF_PASSWORD=your_password
SF_SECURITY_TOKEN=your_token
```
