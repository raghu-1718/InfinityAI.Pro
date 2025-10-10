output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.infinityai.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.infinityai.name
}

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = azurerm_kubernetes_cluster.infinityai.id
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = azurerm_kubernetes_cluster.infinityai.fqdn
}

output "aks_node_resource_group" {
  description = "Node resource group of the AKS cluster"
  value       = azurerm_kubernetes_cluster.infinityai.node_resource_group
}

output "container_registry_name" {
  description = "Name of the container registry"
  value       = azurerm_container_registry.infinityai.name
}

output "container_registry_login_server" {
  description = "Login server of the container registry"
  value       = azurerm_container_registry.infinityai.login_server
}

output "application_gateway_public_ip" {
  description = "Public IP of the Application Gateway"
  value       = azurerm_public_ip.appgateway.ip_address
}

output "postgresql_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.infinityai.fqdn
}

output "redis_hostname" {
  description = "Hostname of Redis cache"
  value       = azurerm_redis_cache.infinityai.hostname
}

output "redis_primary_access_key" {
  description = "Primary access key of Redis cache"
  value       = azurerm_redis_cache.infinityai.primary_access_key
  sensitive   = true
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.infinityai.name
}

output "storage_account_primary_endpoint" {
  description = "Primary endpoint of the storage account"
  value       = azurerm_storage_account.infinityai.primary_dfs_endpoint
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.infinityai.vault_uri
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.infinityai.workspace_id
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key of Application Insights"
  value       = azurerm_application_insights.infinityai.instrumentation_key
  sensitive   = true
}

output "service_bus_namespace_name" {
  description = "Name of the Service Bus namespace"
  value       = azurerm_servicebus_namespace.infinityai.name
}

output "eventgrid_topic_endpoint" {
  description = "Endpoint of the Event Grid topic"
  value       = azurerm_eventgrid_topic.infinityai.endpoint
}

output "virtual_network_id" {
  description = "ID of the virtual network"
  value       = azurerm_virtual_network.infinityai.id
}

# Kubernetes configuration
output "kube_config" {
  description = "Kubernetes configuration"
  value       = azurerm_kubernetes_cluster.infinityai.kube_config_raw
  sensitive   = true
}

output "client_certificate" {
  description = "Client certificate"
  value       = azurerm_kubernetes_cluster.infinityai.kube_config.0.client_certificate
  sensitive   = true
}

output "client_key" {
  description = "Client key"
  value       = azurerm_kubernetes_cluster.infinityai.kube_config.0.client_key
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate"
  value       = azurerm_kubernetes_cluster.infinityai.kube_config.0.cluster_ca_certificate
  sensitive   = true
}

output "cluster_endpoint" {
  description = "Kubernetes cluster endpoint"
  value       = azurerm_kubernetes_cluster.infinityai.kube_config.0.host
}

# Engine A specific outputs
output "engine_a_endpoints" {
  description = "Engine A endpoints"
  value = {
    api_endpoint    = "https://${azurerm_public_ip.appgateway.ip_address}/engine-a"
    health_endpoint = "https://${azurerm_public_ip.appgateway.ip_address}/engine-a/health"
    metrics_endpoint = "https://${azurerm_public_ip.appgateway.ip_address}/engine-a/metrics"
  }
}

# Cross-cloud communication endpoints
output "cross_cloud_endpoints" {
  description = "Cross-cloud communication endpoints"
  value = {
    eventgrid_endpoint = azurerm_eventgrid_topic.infinityai.endpoint
    servicebus_endpoint = "${azurerm_servicebus_namespace.infinityai.name}.servicebus.windows.net"
    storage_endpoint = azurerm_storage_account.infinityai.primary_dfs_endpoint
  }
}