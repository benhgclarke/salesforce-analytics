# 04 — AWS Cloud Implementation

## Where the AWS Code Lives

### Files
| File | Location | Purpose |
|------|----------|---------|
| `lambda_handler.py` | `src/aws_functions/lambda_handler.py` | AWS Lambda function handler |
| `s3_utils.py` | `src/aws_functions/s3_utils.py` | S3 data store utilities |
| `main.tf` | `infrastructure/aws/main.tf` | Terraform IaC for all AWS resources |

### AWS Architecture
```
EventBridge (daily cron)  ──┐
                            ├──> Lambda ──> S3 (analytics results)
API Gateway (HTTP API)    ──┘              ├── analytics/lead_scoring/year=/month=/day=
                                           ├── analytics/pipeline_health/...
                                           └── analytics/churn_prediction/...
```

### Lambda Handler
- Supports actions: `full_analysis`, `lead_scoring`, `pipeline_health`, `churn_prediction`
- Triggered by EventBridge (scheduled daily) or API Gateway (on-demand HTTP)
- Results stored in S3 with date-partitioned keys and AES256 encryption

### S3 Storage Pattern
```
s3://sf-analytics-{env}/
  analytics/
    lead_scoring/year=2025/month=01/day=15/results.json
    pipeline_health/year=2025/month=01/day=15/results.json
    churn_prediction/year=2025/month=01/day=15/results.json
```

### Terraform Resources Provisioned
- S3 bucket with versioning, encryption, lifecycle rules (90-day archival)
- IAM role and policy for Lambda execution
- Lambda function (Python 3.11, 512MB, 5min timeout)
- CloudWatch log group (14-day retention)
- EventBridge rule (daily 06:00 UTC)
- API Gateway HTTP API with Lambda integration

### Deploy
```bash
cd infrastructure/aws
terraform init
terraform plan -var="environment=dev"
terraform apply -var="environment=dev"
```
