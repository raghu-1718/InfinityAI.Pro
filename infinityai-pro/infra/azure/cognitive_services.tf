# Azure Cognitive Services Terraform Configuration
# Creates Azure AI services for InfinityAI.Pro

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  description = "Environment name"
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  default     = "infinityai-pro"
}

variable "location" {
  description = "Azure region"
  default     = "East US"
}

# Resource Group (assumes it exists from blob_storage.tf)
data "azurerm_resource_group" "infinityai" {
  name = "${var.project_name}-rg-${var.environment}"
}

# Azure OpenAI Service
resource "azurerm_cognitive_account" "openai" {
  name                = "${var.project_name}-openai-${var.environment}"
  location            = data.azurerm_resource_group.infinityai.location
  resource_group_name = data.azurerm_resource_group.infinityai.name
  kind                = "OpenAI"

  sku_name = "S0"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Azure OpenAI Model Deployment (GPT-4)
resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "0613"
  }

  scale {
    type = "Standard"
  }
}

# Azure Speech Service
resource "azurerm_cognitive_account" "speech" {
  name                = "${var.project_name}-speech-${var.environment}"
  location            = data.azurerm_resource_group.infinityai.location
  resource_group_name = data.azurerm_resource_group.infinityai.name
  kind                = "SpeechServices"

  sku_name = "S0"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Azure Vision Service
resource "azurerm_cognitive_account" "vision" {
  name                = "${var.project_name}-vision-${var.environment}"
  location            = data.azurerm_resource_group.infinityai.location
  resource_group_name = data.azurerm_resource_group.infinityai.name
  kind                = "ComputerVision"

  sku_name = "S1"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Azure Form Recognizer (for document analysis)
resource "azurerm_cognitive_account" "form_recognizer" {
  name                = "${var.project_name}-form-${var.environment}"
  location            = data.azurerm_resource_group.infinityai.location
  resource_group_name = data.azurerm_resource_group.infinityai.name
  kind                = "FormRecognizer"

  sku_name = "S0"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Azure Application Insights for monitoring
resource "azurerm_application_insights" "infinityai" {
  name                = "${var.project_name}-appinsights-${var.environment}"
  location            = data.azurerm_resource_group.infinityai.location
  resource_group_name = data.azurerm_resource_group.infinityai.name
  application_type    = "web"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Outputs
output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "openai_key" {
  value     = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}

output "speech_endpoint" {
  value = azurerm_cognitive_account.speech.endpoint
}

output "speech_key" {
  value     = azurerm_cognitive_account.speech.primary_access_key
  sensitive = true
}

output "vision_endpoint" {
  value = azurerm_cognitive_account.vision.endpoint
}

output "vision_key" {
  value     = azurerm_cognitive_account.vision.primary_access_key
  sensitive = true
}

output "app_insights_instrumentation_key" {
  value = azurerm_application_insights.infinityai.instrumentation_key
}

output "app_insights_connection_string" {
  value = azurerm_application_insights.infinityai.connection_string
}