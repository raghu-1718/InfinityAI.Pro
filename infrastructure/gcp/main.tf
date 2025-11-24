# InfinityAI.Pro - Google Cloud GKE Infrastructure for Engine B (AI/ML GPU)
# Optimized for AI/ML workloads with GPU acceleration and Vertex AI integration

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-c"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "kubernetes_version" {
  description = "GKE cluster version"
  type        = string
  default     = "1.28"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudsql.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "ml.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "dns.googleapis.com",
    "servicenetworking.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = false
  disable_on_destroy         = false
}

# VPC Network
resource "google_compute_network" "infinityai" {
  name                    = "infinityai-pro-${var.environment}"
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"

  depends_on = [google_project_service.required_apis]
}

# Subnet for GKE cluster
resource "google_compute_subnetwork" "gke" {
  name          = "gke-subnet-${var.environment}"
  ip_cidr_range = "10.2.0.0/16"
  region        = var.region
  network       = google_compute_network.infinityai.id

  # Secondary IP ranges for pods and services
  secondary_ip_range {
    range_name    = "gke-pods-${var.environment}"
    ip_cidr_range = "172.16.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services-${var.environment}"
    ip_cidr_range = "172.17.0.0/16"
  }

  # Enable private Google access for nodes without external IPs
  private_ip_google_access = true

  depends_on = [google_project_service.required_apis]
}

# Subnet for Cloud SQL
resource "google_compute_subnetwork" "cloudsql" {
  name          = "cloudsql-subnet-${var.environment}"
  ip_cidr_range = "10.2.16.0/24"
  region        = var.region
  network       = google_compute_network.infinityai.id

  depends_on = [google_project_service.required_apis]
}

# Cloud NAT for egress from private nodes
resource "google_compute_router" "infinityai" {
  name    = "infinityai-router-${var.environment}"
  region  = var.region
  network = google_compute_network.infinityai.id
}

resource "google_compute_router_nat" "infinityai" {
  name                               = "infinityai-nat-${var.environment}"
  router                            = google_compute_router.infinityai.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal-${var.environment}"
  network = google_compute_network.infinityai.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "8002", "8080"] # Only allow essential ports
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.2.0.0/16", "172.16.0.0/16", "172.17.0.0/16"]
}

// Removed cross-cloud allowances: GCP-only posture

resource "google_compute_firewall" "allow_lb_health_check" {
  name    = "allow-lb-health-check-${var.environment}"
  network = google_compute_network.infinityai.name

  allow {
    protocol = "tcp"
    ports    = ["8002", "8080"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]  # Google Load Balancer ranges
  target_tags   = ["gke-node"]
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "infinityai" {
  location      = var.region
  repository_id = "infinityai-pro-${var.environment}"
  description   = "InfinityAI.Pro container images"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    project     = "infinityai-pro"
    component   = "engine-b"
  }

  depends_on = [google_project_service.required_apis]
}

# Service Account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "gke-nodes-${var.environment}"
  display_name = "GKE Nodes Service Account"
  description  = "Service account for GKE nodes"
}

# IAM bindings for GKE service account
resource "google_project_iam_member" "gke_node_service_account" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader",
    "roles/aiplatform.user",
    "roles/ml.developer",
    "roles/pubsub.editor",
    "roles/secretmanager.secretAccessor"
  ])

  role   = each.key
  member = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Service Account for Engine B workloads
resource "google_service_account" "engine_b" {
  account_id   = "engine-b-${var.environment}"
  display_name = "Engine B Service Account"
  description  = "Service account for Engine B AI/ML workloads"
}

resource "google_project_iam_member" "engine_b_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/ml.developer",
    "roles/storage.admin",
    "roles/pubsub.editor",
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter"
  ])

  role   = each.key
  member = "serviceAccount:${google_service_account.engine_b.email}"
}

# Workload Identity binding
resource "google_service_account_iam_binding" "workload_identity" {
  service_account_id = google_service_account.engine_b.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[infinityai-gcp/engine-b-sa]"
  ]
}

# GKE Cluster
resource "google_container_cluster" "infinityai" {
  name     = "infinityai-pro-${var.environment}"
  location = var.region

  # Network configuration
  network    = google_compute_network.infinityai.id
  subnetwork = google_compute_subnetwork.gke.id

  # IP allocation policy
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods-${var.environment}"
    services_secondary_range_name = "gke-services-${var.environment}"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_endpoint = false
    enable_private_nodes    = true
    master_ipv4_cidr_block  = "172.20.0.0/28"
  }

  # Master authorized networks (restrict to office/VPN CIDR only)
  master_authorized_networks_config {
    cidr_blocks = [
      {
        cidr_block   = "203.0.113.0/24" # Example: Replace with your office/VPN CIDR
        display_name = "Office VPN"
      }
    ]
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled = true
  }

  # Cluster features
  addons_config {
    http_load_balancing {
      disabled = false
    }

    horizontal_pod_autoscaling {
      disabled = false
    }

    network_policy_config {
      disabled = false
    }

    gce_persistent_disk_csi_driver_config {
      enabled = true
    }

    gcp_filestore_csi_driver_config {
      enabled = true
    }
  }

  # Cluster monitoring and logging
  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER"
    ]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER"
    ]
    
    managed_prometheus {
      enabled = true
    }
  }

  # Security configuration
  enable_shielded_nodes = true
  
  # Binary Authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Resource labels
  resource_labels = {
    environment = var.environment
    project     = "infinityai-pro"
    component   = "engine-b"
    cloud       = "gcp"
  }

  # Kubernetes version
  min_master_version = var.kubernetes_version

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  depends_on = [
    google_project_service.required_apis,
    google_compute_subnetwork.gke
  ]
}

# System node pool
resource "google_container_node_pool" "system" {
  name       = "system-pool"
  location   = var.region
  cluster    = google_container_cluster.infinityai.name
  node_count = 3

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4"
    disk_size_gb = 50
    disk_type    = "pd-ssd"

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      node-type   = "system"
      workload    = "system"
    }

    tags = ["gke-node", "system-node"]
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# GPU node pool for Engine B
resource "google_container_node_pool" "engine_b_gpu" {
  name       = "engine-b-gpu-pool"
  location   = var.region
  cluster    = google_container_cluster.infinityai.name
  node_count = 2

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  node_config {
    preemptible  = false
    machine_type = "n1-standard-4"  # Required for GPU attachment
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    # Attach NVIDIA T4 GPUs
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment   = var.environment
      node-type     = "gpu-optimized"
      workload      = "ai-ml"
      engine        = "engine-b"
      gpu-type      = "nvidia-tesla-t4"
    }

    tags = ["gke-node", "gpu-node", "engine-b"]

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# CPU node pool for Engine B (fallback)
resource "google_container_node_pool" "engine_b_cpu" {
  name       = "engine-b-cpu-pool"
  location   = var.region
  cluster    = google_container_cluster.infinityai.name
  node_count = 3

  autoscaling {
    min_node_count = 2
    max_node_count = 15
  }

  node_config {
    preemptible  = false
    machine_type = "c2-standard-8"  # CPU-optimized for ML workloads
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      node-type   = "cpu-optimized"
      workload    = "ai-ml"
      engine      = "engine-b"
    }

    tags = ["gke-node", "cpu-node", "engine-b"]

    taint {
      key    = "engine-b"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "infinityai" {
  name             = "infinityai-pro-${var.environment}"
  database_version = "POSTGRES_13"
  region           = var.region

  settings {
    tier                        = "db-custom-2-8192"
    availability_type           = "REGIONAL"
    disk_type                  = "PD_SSD"
    disk_size                  = 100
    disk_autoresize            = true
    disk_autoresize_limit      = 500

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.infinityai.id
      require_ssl     = true
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = false

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private service networking for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 24
  network       = google_compute_network.infinityai.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.infinityai.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Cloud SQL database
resource "google_sql_database" "infinityai" {
  name     = "infinityai"
  instance = google_sql_database_instance.infinityai.name
}

# Cloud SQL user
resource "google_sql_user" "infinityai" {
  name     = "infinityai_admin"
  instance = google_sql_database_instance.infinityai.name
  password = var.db_password
}

# Redis instance (Memorystore)
resource "google_redis_instance" "infinityai" {
  name           = "infinityai-pro-${var.environment}"
  tier           = "STANDARD_HA"
  memory_size_gb = 4
  region         = var.region

  authorized_network = google_compute_network.infinityai.id

  redis_version = "REDIS_6_X"

  display_name = "InfinityAI.Pro Redis Cache"

  labels = {
    environment = var.environment
    project     = "infinityai-pro"
    component   = "cache"
  }

  depends_on = [google_project_service.required_apis]
}

# Pub/Sub topics for messaging
resource "google_pubsub_topic" "market_data" {
  name = "market-data-${var.environment}"

  labels = {
    environment = var.environment
    component   = "engine-b"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "ai_predictions" {
  name = "ai-predictions-${var.environment}"

  labels = {
    environment = var.environment
    component   = "engine-b"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "model_training" {
  name = "model-training-${var.environment}"

  labels = {
    environment = var.environment
    component   = "engine-b"
  }

  depends_on = [google_project_service.required_apis]
}

# Pub/Sub subscriptions
resource "google_pubsub_subscription" "market_data" {
  name  = "market-data-subscription-${var.environment}"
  topic = google_pubsub_topic.market_data.name

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "dead_letter" {
  name = "dead-letter-${var.environment}"
}

# Cloud Storage buckets
resource "google_storage_bucket" "models" {
  name          = "infinityai-pro-models-${var.environment}-${random_suffix.bucket_suffix.result}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    component   = "ai-models"
  }
}

resource "google_storage_bucket" "training_data" {
  name          = "infinityai-pro-training-${var.environment}-${random_suffix.bucket_suffix.result}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    component   = "training-data"
  }
}

resource "random_suffix" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Secret Manager secrets
resource "google_secret_manager_secret" "database_password" {
  secret_id = "database-password-${var.environment}"

  labels = {
    environment = var.environment
  }

  replication {
    automatic = true
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_password" {
  secret      = google_secret_manager_secret.database_password.id
  secret_data = var.db_password
}

# Vertex AI model endpoints (placeholder for custom models)
resource "google_vertex_ai_endpoint" "infinityai" {
  name         = "infinityai-pro-endpoint-${var.environment}"
  display_name = "InfinityAI.Pro ML Endpoint"
  description  = "Endpoint for InfinityAI.Pro ML models"
  location     = var.region

  labels = {
    environment = var.environment
    component   = "ai-ml"
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud DNS managed zone for custom domain
resource "google_dns_managed_zone" "infinityai_gcp" {
  name     = "infinityai-gcp-${var.environment}"
  dns_name = "gcp.infinityai.pro."

  labels = {
    environment = var.environment
  }

  depends_on = [google_project_service.required_apis]
}

# Load balancer IP
resource "google_compute_global_address" "infinityai" {
  name = "infinityai-pro-ip-${var.environment}"
}

# SSL certificate
resource "google_compute_managed_ssl_certificate" "infinityai" {
  name = "infinityai-pro-ssl-${var.environment}"

  managed {
    domains = [
      "engine-b.gcp.infinityai.pro",
      "api.gcp.infinityai.pro"
    ]
  }
}

# Cloud KMS for encryption
resource "google_kms_key_ring" "infinityai" {
  name     = "infinityai-pro-${var.environment}"
  location = var.region

  depends_on = [google_project_service.required_apis]
}

resource "google_kms_crypto_key" "infinityai" {
  name     = "infinityai-pro-key"
  key_ring = google_kms_key_ring.infinityai.id

  purpose = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  labels = {
    environment = var.environment
  }
}

# Grant Engine B service account access to KMS key
resource "google_kms_crypto_key_iam_member" "engine_b_kms" {
  crypto_key_id = google_kms_crypto_key.infinityai.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.engine_b.email}"
}