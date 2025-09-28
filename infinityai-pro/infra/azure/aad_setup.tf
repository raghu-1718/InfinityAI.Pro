# Azure Active Directory Setup Terraform Configuration
# Creates Azure AD application and service principal for InfinityAI.Pro

terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
  }
}

variable "environment" {
  description = "Environment name"
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  default     = "infinityai-pro"
}

# Azure AD Application
resource "azuread_application" "infinityai" {
  display_name = "${var.project_name}-app-${var.environment}"

  web {
    homepage_url  = "https://infinityai.pro"
    redirect_uris = [
      "https://infinityai.pro/auth/callback",
      "https://api.infinityai.pro/auth/callback"
    ]

    implicit_grant {
      access_token_issuance_enabled = true
      id_token_issuance_enabled     = true
    }
  }

  api {
    requested_access_token_version = 2
  }

  required_resource_access {
    # Microsoft Graph API permissions
    resource_app_id = "00000003-0000-0000-c000-000000000000"

    resource_access {
      id   = "e1fe6dd8-ba31-4d61-89e7-88639da4683d" # User.Read
      type = "Scope"
    }

    resource_access {
      id   = "b4e74841-8e56-480b-be8b-910348b18b4c" # User.ReadWrite
      type = "Scope"
    }
  }

  tags = ["InfinityAI", var.environment]
}

# Azure AD Application Password (Client Secret)
resource "azuread_application_password" "infinityai" {
  application_object_id = azuread_application.infinityai.object_id
  display_name          = "${var.project_name}-secret-${var.environment}"
  end_date_relative     = "8760h" # 1 year
}

# Service Principal
resource "azuread_service_principal" "infinityai" {
  application_id = azuread_application.infinityai.application_id
}

# Optional: Azure AD Group for users
resource "azuread_group" "infinityai_users" {
  display_name     = "${var.project_name}-users-${var.environment}"
  description      = "InfinityAI.Pro application users"
  security_enabled = true

  members = [] # Add user object IDs here
}

# Outputs
output "application_id" {
  value = azuread_application.infinityai.application_id
}

output "client_secret" {
  value     = azuread_application_password.infinityai.value
  sensitive = true
}

output "tenant_id" {
  value = data.azuread_client_config.current.tenant_id
}

output "service_principal_object_id" {
  value = azuread_service_principal.infinityai.object_id
}

output "user_group_id" {
  value = azuread_group.infinityai_users.object_id
}

# Data source for current client config
data "azuread_client_config" "current" {}