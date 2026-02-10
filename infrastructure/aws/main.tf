# ============================================================
# AWS Infrastructure for Salesforce Analytics Platform
# Terraform configuration for Lambda, S3, EventBridge, API Gateway
# ============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "sf-analytics-terraform-state"
    key    = "salesforce-analytics/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SalesforceAnalytics"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# --- Variables ---

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

# --- S3 Bucket for Analytics Data ---

resource "aws_s3_bucket" "analytics_data" {
  bucket = "sf-analytics-data-${var.environment}"
}

resource "aws_s3_bucket_versioning" "analytics_data" {
  bucket = aws_s3_bucket.analytics_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "analytics_data" {
  bucket = aws_s3_bucket.analytics_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "analytics_data" {
  bucket = aws_s3_bucket.analytics_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "analytics_data" {
  bucket = aws_s3_bucket.analytics_data.id

  rule {
    id     = "archive-old-results"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# --- IAM Role for Lambda ---

resource "aws_iam_role" "lambda_role" {
  name = "sf-analytics-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "sf-analytics-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.analytics_data.arn,
          "${aws_s3_bucket.analytics_data.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
        ]
        Resource = "*"
      }
    ]
  })
}

# --- Lambda Function ---

resource "aws_lambda_function" "sf_analytics" {
  function_name = "sf-data-processor-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.aws_functions.lambda_handler.handler"
  runtime       = "python3.11"
  memory_size   = var.lambda_memory
  timeout       = var.lambda_timeout

  filename         = "${path.module}/../../lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../lambda_package.zip")

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.analytics_data.id
      USE_MOCK_DATA  = "true"
      ENVIRONMENT    = var.environment
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.sf_analytics.function_name}"
  retention_in_days = 30
}

# --- EventBridge (Scheduled Trigger) ---

resource "aws_cloudwatch_event_rule" "daily_analysis" {
  name                = "sf-analytics-daily-${var.environment}"
  description         = "Trigger Salesforce analytics daily at 06:00 UTC"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule = aws_cloudwatch_event_rule.daily_analysis.name
  arn  = aws_lambda_function.sf_analytics.arn

  input = jsonencode({
    action = "full_analysis"
  })
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sf_analytics.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_analysis.arn
}

# --- API Gateway (HTTP API) ---

resource "aws_apigatewayv2_api" "analytics_api" {
  name          = "sf-analytics-api-${var.environment}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.analytics_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.analytics_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.sf_analytics.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "analyse" {
  api_id    = aws_apigatewayv2_api.analytics_api.id
  route_key = "POST /analyse"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sf_analytics.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.analytics_api.execution_arn}/*/*"
}

# --- Outputs ---

output "s3_bucket_name" {
  value = aws_s3_bucket.analytics_data.id
}

output "lambda_function_name" {
  value = aws_lambda_function.sf_analytics.function_name
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.analytics_api.api_endpoint
}
