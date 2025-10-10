# InfinityAI.Pro - Azure AKS Infrastructure for Engine A (Data Ingestion)
# Optimized for financial data processing and global edge deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Data sources
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "infinityai" {
  name     = "rg-infinityai-pro-${var.environment}"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
    Component   = "Engine-A-DataIngestion"
    ManagedBy   = "Terraform"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "infinityai" {
  name                = "vnet-infinityai-pro-${var.environment}"
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "snet-aks-${var.environment}"
  resource_group_name  = azurerm_resource_group.infinityai.name
  virtual_network_name = azurerm_virtual_network.infinityai.name
  address_prefixes     = ["10.1.1.0/24"]
}

# Subnet for Application Gateway
resource "azurerm_subnet" "appgateway" {
  name                 = "snet-appgateway-${var.environment}"
  resource_group_name  = azurerm_resource_group.infinityai.name
  virtual_network_name = azurerm_virtual_network.infinityai.name
  address_prefixes     = ["10.1.2.0/24"]
}

# Network Security Group
resource "azurerm_network_security_group" "infinityai" {
  name                = "nsg-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Container Registry
resource "azurerm_container_registry" "infinityai" {
  name                = "acrinfinityaipro${var.environment}"
  resource_group_name = azurerm_resource_group.infinityai.name
  location            = azurerm_resource_group.infinityai.location
  sku                 = "Premium"  # Premium for geo-replication and advanced security
  admin_enabled       = false

  # Enable geo-replication for global deployment
  georeplications {
    location = "East US"
    tags = {
      Environment = var.environment
      Replica     = "eastus"
    }
  }

  georeplications {
    location = "West Europe"
    tags = {
      Environment = var.environment
      Replica     = "westeurope"
    }
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "infinityai" {
  name                = "law-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Application Insights
resource "azurerm_application_insights" "infinityai" {
  name                = "appi-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name
  workspace_id        = azurerm_log_analytics_workspace.infinityai.id
  application_type    = "web"

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "infinityai" {
  name                   = "psql-infinityai-pro-${var.environment}"
  resource_group_name    = azurerm_resource_group.infinityai.name
  location               = azurerm_resource_group.infinityai.location
  version                = "13"
  delegated_subnet_id    = azurerm_subnet.database.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgresql.id
  administrator_login    = var.db_username
  administrator_password = var.db_password
  zone                   = "1"
  storage_mb             = 32768
  sku_name               = "GP_Standard_D2s_v3"

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgresql]

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Database subnet
resource "azurerm_subnet" "database" {
  name                 = "snet-database-${var.environment}"
  resource_group_name  = azurerm_resource_group.infinityai.name
  virtual_network_name = azurerm_virtual_network.infinityai.name
  address_prefixes     = ["10.1.3.0/24"]

  delegation {
    name = "fs"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# Private DNS Zone for PostgreSQL
resource "azurerm_private_dns_zone" "postgresql" {
  name                = "infinityai-pro-${var.environment}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.infinityai.name

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Private DNS Zone Virtual Network Link
resource "azurerm_private_dns_zone_virtual_network_link" "postgresql" {
  name                  = "vnetlink-postgresql-${var.environment}"
  private_dns_zone_name = azurerm_private_dns_zone.postgresql.name
  virtual_network_id    = azurerm_virtual_network.infinityai.id
  resource_group_name   = azurerm_resource_group.infinityai.name

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "infinityai" {
  name                          = "redis-infinityai-pro-${var.environment}"
  location                      = azurerm_resource_group.infinityai.location
  resource_group_name           = azurerm_resource_group.infinityai.name
  capacity                      = 1
  family                        = "P"
  sku_name                      = "Premium"
  enable_non_ssl_port           = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = false
  subnet_id                     = azurerm_subnet.redis.id

  redis_configuration {
    enable_authentication = true
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Redis subnet
resource "azurerm_subnet" "redis" {
  name                 = "snet-redis-${var.environment}"
  resource_group_name  = azurerm_resource_group.infinityai.name
  virtual_network_name = azurerm_virtual_network.infinityai.name
  address_prefixes     = ["10.1.4.0/24"]
}

# Service Principal for AKS
resource "azuread_application" "aks" {
  display_name = "aks-infinityai-pro-${var.environment}"
}

resource "azuread_service_principal" "aks" {
  application_id = azuread_application.aks.application_id
}

resource "azuread_service_principal_password" "aks" {
  service_principal_id = azuread_service_principal.aks.object_id
}

# Role assignments
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope                = azurerm_virtual_network.infinityai.id
  role_definition_name = "Network Contributor"
  principal_id         = azuread_service_principal.aks.object_id
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.infinityai.id
  role_definition_name = "AcrPull"
  principal_id         = azuread_service_principal.aks.object_id
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "infinityai" {
  name                = "aks-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name
  dns_prefix          = "infinityai-pro-${var.environment}"
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "system"
    node_count          = var.system_node_count
    vm_size             = "Standard_DS2_v2"
    vnet_subnet_id      = azurerm_subnet.aks.id
    zones               = ["1", "2", "3"]
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 10

    upgrade_settings {
      max_surge = "33%"
    }
  }

  # Managed Identity
  identity {
    type = "SystemAssigned"
  }

  # Network Profile
  network_profile {
    network_plugin      = "azure"
    network_policy      = "azure"
    load_balancer_sku   = "standard"
    outbound_type       = "loadBalancer"
  }

  # Monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.infinityai.id
  }

  # Azure AD Integration
  azure_active_directory_role_based_access_control {
    managed            = true
    azure_rbac_enabled = true
  }

  # Security
  role_based_access_control_enabled = true

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
    Component   = "Engine-A"
  }
}

# Additional Node Pool for Engine A workloads
resource "azurerm_kubernetes_cluster_node_pool" "engine_a" {
  name                  = "enginea"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.infinityai.id
  vm_size               = "Standard_F8s_v2"  # Compute optimized for data processing
  node_count            = var.engine_a_node_count
  vnet_subnet_id        = azurerm_subnet.aks.id
  zones                 = ["1", "2", "3"]
  enable_auto_scaling   = true
  min_count             = 2
  max_count             = 20

  node_labels = {
    "workload-type"    = "data-ingestion"
    "engine"           = "engine-a"
    "node-type"        = "compute-optimized"
  }

  node_taints = [
    "engine-a=true:NoSchedule"
  ]

  upgrade_settings {
    max_surge = "33%"
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
    Component   = "Engine-A"
    NodePool    = "EngineA"
  }
}

# Key Vault for secrets
resource "azurerm_key_vault" "infinityai" {
  name                        = "kv-infinityai-pro-${var.environment}"
  location                    = azurerm_resource_group.infinityai.location
  resource_group_name         = azurerm_resource_group.infinityai.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "premium"

  # Network ACLs
  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
    virtual_network_subnet_ids = [
      azurerm_subnet.aks.id
    ]
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Key Vault access policy for AKS
resource "azurerm_key_vault_access_policy" "aks" {
  key_vault_id = azurerm_key_vault.infinityai.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_kubernetes_cluster.infinityai.identity[0].principal_id

  secret_permissions = [
    "Get", "List"
  ]

  certificate_permissions = [
    "Get", "List"
  ]
}

# Application Gateway for Ingress
resource "azurerm_public_ip" "appgateway" {
  name                = "pip-appgateway-infinityai-pro-${var.environment}"
  resource_group_name = azurerm_resource_group.infinityai.name
  location            = azurerm_resource_group.infinityai.location
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = ["1", "2", "3"]

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

resource "azurerm_application_gateway" "infinityai" {
  name                = "agw-infinityai-pro-${var.environment}"
  resource_group_name = azurerm_resource_group.infinityai.name
  location            = azurerm_resource_group.infinityai.location

  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 2
  }

  waf_configuration {
    enabled          = true
    firewall_mode    = "Prevention"
    rule_set_type    = "OWASP"
    rule_set_version = "3.2"
  }

  gateway_ip_configuration {
    name      = "appGatewayIpConfig"
    subnet_id = azurerm_subnet.appgateway.id
  }

  frontend_port {
    name = "httpsPort"
    port = 443
  }

  frontend_port {
    name = "httpPort"
    port = 80
  }

  frontend_ip_configuration {
    name                 = "appGwPublicFrontendIp"
    public_ip_address_id = azurerm_public_ip.appgateway.id
  }

  backend_address_pool {
    name = "engine-a-backend"
  }

  backend_http_settings {
    name                  = "engine-a-http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
  }

  http_listener {
    name                           = "engine-a-listener"
    frontend_ip_configuration_name = "appGwPublicFrontendIp"
    frontend_port_name             = "httpsPort"
    protocol                       = "Https"
    ssl_certificate_name           = "infinityai-ssl"
  }

  request_routing_rule {
    name                       = "engine-a-routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "engine-a-listener"
    backend_address_pool_name  = "engine-a-backend"
    backend_http_settings_name = "engine-a-http-settings"
    priority                   = 100
  }

  # SSL certificate (would be uploaded separately)
  ssl_certificate {
    name     = "infinityai-ssl"
    data     = filebase64("${path.module}/certificates/wildcard.pfx")
    password = var.ssl_certificate_password
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Event Grid Topic for cross-cloud communication
resource "azurerm_eventgrid_topic" "infinityai" {
  name                = "egt-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Storage Account for data lake
resource "azurerm_storage_account" "infinityai" {
  name                     = "sainfinityaipro${var.environment}"
  resource_group_name      = azurerm_resource_group.infinityai.name
  location                 = azurerm_resource_group.infinityai.location
  account_tier             = "Standard"
  account_replication_type = "ZRS"  # Zone redundant storage
  is_hns_enabled           = true   # Enable hierarchical namespace for Data Lake Gen2

  blob_properties {
    versioning_enabled       = true
    last_access_time_enabled = true
    
    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Data Lake containers
resource "azurerm_storage_data_lake_gen2_filesystem" "raw_data" {
  name               = "raw-market-data"
  storage_account_id = azurerm_storage_account.infinityai.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "processed_data" {
  name               = "processed-market-data"
  storage_account_id = azurerm_storage_account.infinityai.id
}

# Azure Service Bus for message queuing (alternative to Kafka)
resource "azurerm_servicebus_namespace" "infinityai" {
  name                = "sb-infinityai-pro-${var.environment}"
  location            = azurerm_resource_group.infinityai.location
  resource_group_name = azurerm_resource_group.infinityai.name
  sku                 = "Premium"
  capacity            = 1

  tags = {
    Environment = var.environment
    Project     = "InfinityAI.Pro"
  }
}

# Service Bus Queue for market data
resource "azurerm_servicebus_queue" "market_data" {
  name         = "market-data-queue"
  namespace_id = azurerm_servicebus_namespace.infinityai.id

  enable_partitioning = true
  max_size_in_megabytes = 5120
}

# Service Bus Topic for news data
resource "azurerm_servicebus_topic" "news_data" {
  name         = "news-data-topic"
  namespace_id = azurerm_servicebus_namespace.infinityai.id

  enable_partitioning = true
  max_size_in_megabytes = 5120
}