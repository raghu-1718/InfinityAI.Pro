# AWS CloudWatch Monitoring Terraform Configuration
# Sets up monitoring and logging for InfinityAI.Pro

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  default     = "infinityai-pro"
}

variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  default     = ""
}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "infinityai_logs" {
  name              = "/aws/infinityai/${var.project_name}/${var.environment}"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group for AI service logs
resource "aws_cloudwatch_log_group" "ai_service_logs" {
  name              = "/aws/infinityai/${var.project_name}/ai/${var.environment}"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Service     = "ai"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "infinityai_dashboard" {
  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", "${var.project_name}-api-${var.environment}"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Gateway Requests"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", "${var.project_name}-api-${var.environment}"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Gateway Latency"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6

        properties = {
          query = "SOURCE '${aws_cloudwatch_log_group.infinityai_logs.name}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region = var.aws_region
          title  = "Application Logs"
        }
      }
    ]
  })
}

# SNS Topic for alarms
resource "aws_sns_topic" "infinityai_alarms" {
  name = "${var.project_name}-alarms-${var.environment}"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.infinityai_alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# CloudWatch Alarms

# API Gateway 5xx errors
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.project_name}-api-5xx-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "API Gateway 5xx errors > 5 in 10 minutes"
  alarm_actions       = [aws_sns_topic.infinityai_alarms.arn]

  dimensions = {
    ApiName = "${var.project_name}-api-${var.environment}"
  }
}

# API Gateway latency
resource "aws_cloudwatch_metric_alarm" "api_high_latency" {
  alarm_name          = "${var.project_name}-api-high-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000"
  alarm_description   = "API Gateway latency > 5 seconds"
  alarm_actions       = [aws_sns_topic.infinityai_alarms.arn]

  dimensions = {
    ApiName = "${var.project_name}-api-${var.environment}"
  }
}

# Custom metric filter for AI service errors
resource "aws_cloudwatch_log_metric_filter" "ai_service_errors" {
  name           = "${var.project_name}-ai-errors-${var.environment}"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.ai_service_logs.name

  metric_transformation {
    name      = "AIErrorCount"
    namespace = "InfinityAI/AI"
    value     = "1"
  }
}

# Alarm for AI service errors
resource "aws_cloudwatch_metric_alarm" "ai_service_errors" {
  alarm_name          = "${var.project_name}-ai-service-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AIErrorCount"
  namespace           = "InfinityAI/AI"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "AI service errors > 10 in 5 minutes"
  alarm_actions       = [aws_sns_topic.infinityai_alarms.arn]
}

# Outputs
output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.infinityai_logs.name
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.infinityai_dashboard.dashboard_name}"
}

output "sns_topic_arn" {
  value = aws_sns_topic.infinityai_alarms.arn
}