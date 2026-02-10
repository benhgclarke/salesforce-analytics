# 07 — Automation Layer

## Where the Automation Scripts Live

### Files
| File | Location | Purpose |
|------|----------|---------|
| `notifications.py` | `src/automation/notifications.py` | Multi-channel alert service |
| `salesforce_writeback.py` | `src/automation/salesforce_writeback.py` | Write results back to Salesforce |

### Notification Channels
| Channel | Config | Trigger |
|---------|--------|---------|
| Log (always on) | None | Every alert |
| AWS SES Email | `AWS_SES_SENDER`, `ALERT_RECIPIENTS` | When SES credentials set |
| Slack Webhook | `SLACK_WEBHOOK_URL` | When webhook URL set |

Alerts are generated for:
- Critical/High priority leads
- Low pipeline health scores
- Pipeline risk indicators
- High churn risk accounts
- Daily forecast summaries

### Salesforce Writeback
When connected to a live Salesforce org, the writeback service:
1. Updates `Lead_Score__c` and `Priority__c` custom fields on Lead records
2. Updates `Churn_Risk_Score__c` and `Churn_Risk_Level__c` on Account records
3. Creates follow-up **Task** records for Critical/High priority leads
4. Creates intervention **Task** records for High churn-risk accounts

### Alert Format
```json
{
  "type": "Lead Scoring",
  "message": "14 leads scored as Critical priority",
  "priority": "critical",
  "timestamp": "2025-01-15T06:00:00+00:00"
}
```
