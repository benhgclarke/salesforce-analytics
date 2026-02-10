# 08 — Infrastructure as Code

## Where the IaC Files Live

### Files
| File | Location | Provider | Language |
|------|----------|----------|----------|
| `main.tf` | `infrastructure/aws/main.tf` | AWS | Terraform (HCL) |
| `main.bicep` | `infrastructure/azure/main.bicep` | Azure | Bicep |

### AWS Resources (Terraform)
| Resource | Purpose |
|----------|---------|
| S3 Bucket | Analytics result storage (versioning, encryption, lifecycle) |
| IAM Role + Policy | Lambda execution permissions (S3, CloudWatch, SES) |
| Lambda Function | Runs analytics on schedule or on-demand |
| CloudWatch Log Group | Lambda log retention (14 days) |
| EventBridge Rule | Daily CRON schedule (06:00 UTC) |
| API Gateway HTTP API | REST endpoint for on-demand analytics |

### Azure Resources (Bicep)
| Resource | Purpose |
|----------|---------|
| Storage Account + Container | Analytics result storage |
| Application Insights | Monitoring and telemetry |
| App Service Plan | Linux hosting plan for Python workloads |
| Function App | Runs analytics (HTTP + timer triggers) |
| Web App | Hosts Flask dashboard (gunicorn) |

### Deployment Commands
```bash
# AWS
cd infrastructure/aws
terraform init && terraform apply -var="environment=dev"

# Azure
az deployment group create \
  --resource-group sf-analytics-rg \
  --template-file infrastructure/azure/main.bicep \
  --parameters environment=dev
```
