# Azure Blob Storage Terraform Configuration
# Creates Azure Blob Storage for InfinityAI.Pro

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

# Resource Group
resource "azurerm_resource_group" "infinityai" {
  name     = "${var.project_name}-rg-${var.environment}"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Storage Account
resource "azurerm_storage_account" "infinityai" {
  name                     = "${var.project_name}storage${var.environment}"
  resource_group_name      = azurerm_resource_group.infinityai.name
  location                 = azurerm_resource_group.infinityai.location
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant storage

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Storage Container for AI models
resource "azurerm_storage_container" "ai_models" {
  name                  = "ai-models"
  storage_account_name  = azurerm_storage_account.infinityai.name
  container_access_type = "private"
}

# Storage Container for logs
resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_name  = azurerm_storage_account.infinityai.name
  container_access_type = "private"
}

# Storage Container for backups
resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.infinityai.name
  container_access_type = "private"
}

# Lifecycle management policy
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.infinityai.id

  rule {
    name    = "delete_old_logs"
    enabled = true
    filters {
      prefix_match = ["logs/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 30
      }
    }
  }

  rule {
    name    = "delete_old_backups"
    enabled = true
    filters {
      prefix_match = ["backups/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 90
      }
    }
  }
}

# Outputs
output "storage_account_name" {
  value = azurerm_storage_account.infinityai.name
}

output "storage_account_key" {
  value     = azurerm_storage_account.infinityai.primary_access_key
  sensitive = true
}

output "ai_models_container_url" {
  value = "https://${azurerm_storage_account.infinityai.name}.blob.core.windows.net/ai-models"
}

output "resource_group_name" {
  value = azurerm_resource_group.infinityai.name
}