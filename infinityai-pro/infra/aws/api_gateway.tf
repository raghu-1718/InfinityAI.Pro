# AWS API Gateway Terraform Configuration
# Creates API Gateway for InfinityAI.Pro backend

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

# API Gateway REST API
resource "aws_api_gateway_rest_api" "infinityai_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "InfinityAI.Pro Trading API Gateway"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway Resource - AI endpoints
resource "aws_api_gateway_resource" "ai" {
  rest_api_id = aws_api_gateway_rest_api.infinityai_api.id
  parent_id   = aws_api_gateway_rest_api.infinityai_api.root_resource_id
  path_part   = "ai"
}

# AI sub-resources
resource "aws_api_gateway_resource" "llm" {
  rest_api_id = aws_api_gateway_rest_api.infinityai_api.id
  parent_id   = aws_api_gateway_resource.ai.id
  path_part   = "llm"
}

resource "aws_api_gateway_resource" "vision" {
  rest_api_id = aws_api_gateway_rest_api.infinityai_api.id
  parent_id   = aws_api_gateway_resource.ai.id
  path_part   = "vision"
}

resource "aws_api_gateway_resource" "speech" {
  rest_api_id = aws_api_gateway_rest_api.infinityai_api.id
  parent_id   = aws_api_gateway_resource.ai.id
  path_part   = "speech"
}

# Lambda functions (placeholder - integrate with actual backend)
resource "aws_lambda_function" "ai_router" {
  function_name = "${var.project_name}-ai-router-${var.environment}"
  runtime       = "python3.9"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_role.arn

  # Placeholder code - replace with actual AI router logic
  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

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

# CloudWatch Logs policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# API Gateway Lambda integration
resource "aws_api_gateway_integration" "llm_integration" {
  rest_api_id             = aws_api_gateway_rest_api.infinityai_api.id
  resource_id             = aws_api_gateway_resource.llm.id
  http_method             = aws_api_gateway_method.llm_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_router.invoke_arn
}

# API Gateway Methods
resource "aws_api_gateway_method" "llm_method" {
  rest_api_id   = aws_api_gateway_rest_api.infinityai_api.id
  resource_id   = aws_api_gateway_resource.llm.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
    aws_api_gateway_integration.llm_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.infinityai_api.id
  stage_name  = var.environment
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_router.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.infinityai_api.execution_arn}/*/*"
}

# Outputs
output "api_gateway_url" {
  value = aws_api_gateway_deployment.api_deployment.invoke_url
}

output "api_gateway_id" {
  value = aws_api_gateway_rest_api.infinityai_api.id
}