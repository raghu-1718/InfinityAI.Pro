output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.infinityai.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.infinityai.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.infinityai.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository"
  value       = google_artifact_registry_repository.infinityai.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.infinityai.repository_id}"
}

output "cloudsql_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.infinityai.name
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.infinityai.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL private IP"
  value       = google_sql_database_instance.infinityai.private_ip_address
}

output "redis_instance_name" {
  description = "Redis instance name"
  value       = google_redis_instance.infinityai.name
}

output "redis_host" {
  description = "Redis host"
  value       = google_redis_instance.infinityai.host
}

output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.infinityai.port
}

output "redis_auth_string" {
  description = "Redis auth string"
  value       = google_redis_instance.infinityai.auth_string
  sensitive   = true
}

output "storage_bucket_models" {
  description = "Cloud Storage bucket for models"
  value       = google_storage_bucket.models.name
}

output "storage_bucket_training_data" {
  description = "Cloud Storage bucket for training data"
  value       = google_storage_bucket.training_data.name
}

output "pubsub_topic_market_data" {
  description = "Pub/Sub topic for market data"
  value       = google_pubsub_topic.market_data.name
}

output "pubsub_topic_ai_predictions" {
  description = "Pub/Sub topic for AI predictions"
  value       = google_pubsub_topic.ai_predictions.name
}

output "vertex_ai_endpoint" {
  description = "Vertex AI endpoint"
  value       = google_vertex_ai_endpoint.infinityai.name
}

output "service_account_engine_b" {
  description = "Engine B service account email"
  value       = google_service_account.engine_b.email
}

output "kms_crypto_key" {
  description = "KMS crypto key"
  value       = google_kms_crypto_key.infinityai.id
}

output "dns_zone_name_servers" {
  description = "DNS zone name servers"
  value       = google_dns_managed_zone.infinityai_gcp.name_servers
}

output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = google_compute_global_address.infinityai.address
}

output "ssl_certificate_name" {
  description = "SSL certificate name"
  value       = google_compute_managed_ssl_certificate.infinityai.name
}

# Kubernetes connection info
output "kubernetes_cluster_host" {
  description = "GKE cluster host"
  value       = google_container_cluster.infinityai.endpoint
  sensitive   = true
}

output "kubernetes_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = base64decode(google_container_cluster.infinityai.master_auth.0.cluster_ca_certificate)
  sensitive   = true
}

# Engine B specific outputs
output "engine_b_endpoints" {
  description = "Engine B endpoints"
  value = {
    api_endpoint     = "https://${google_compute_global_address.infinityai.address}/engine-b"
    health_endpoint  = "https://${google_compute_global_address.infinityai.address}/engine-b/health"
    metrics_endpoint = "https://${google_compute_global_address.infinityai.address}/engine-b/metrics"
    models_endpoint  = "https://${google_compute_global_address.infinityai.address}/engine-b/api/v1/models"
  }
}

# Cross-cloud communication endpoints
output "cross_cloud_endpoints" {
  description = "Cross-cloud communication endpoints"
  value = {
    pubsub_endpoint  = "pubsub.googleapis.com"
    storage_endpoint = "storage.googleapis.com"
    vertex_endpoint  = "aiplatform.googleapis.com"
    cluster_endpoint = google_container_cluster.infinityai.endpoint
  }
}

# GPU node pool info
output "gpu_node_pool_info" {
  description = "GPU node pool information"
  value = {
    name         = google_container_node_pool.engine_b_gpu.name
    machine_type = "n1-standard-4"
    gpu_type     = "nvidia-tesla-t4"
    gpu_count    = 1
    min_nodes    = google_container_node_pool.engine_b_gpu.autoscaling[0].min_node_count
    max_nodes    = google_container_node_pool.engine_b_gpu.autoscaling[0].max_node_count
  }
}

# Network configuration
output "vpc_network" {
  description = "VPC network information"
  value = {
    network_id        = google_compute_network.infinityai.id
    network_self_link = google_compute_network.infinityai.self_link
    subnet_id         = google_compute_subnetwork.gke.id
    subnet_cidr       = google_compute_subnetwork.gke.ip_cidr_range
    pods_cidr         = "172.16.0.0/16"
    services_cidr     = "172.17.0.0/16"
  }
}

# AI/ML specific outputs
output "ai_ml_resources" {
  description = "AI/ML specific resources"
  value = {
    vertex_ai_endpoint     = google_vertex_ai_endpoint.infinityai.name
    models_bucket         = google_storage_bucket.models.name
    training_data_bucket  = google_storage_bucket.training_data.name
    pubsub_market_data    = google_pubsub_topic.market_data.name
    pubsub_predictions    = google_pubsub_topic.ai_predictions.name
    gpu_node_pool         = google_container_node_pool.engine_b_gpu.name
    service_account       = google_service_account.engine_b.email
  }
}