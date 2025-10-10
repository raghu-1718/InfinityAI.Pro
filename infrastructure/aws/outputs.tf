# Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = module.eks.cluster_oidc_issuer_url
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

output "cluster_primary_security_group_id" {
  description = "Cluster security group that was created by Amazon EKS for the cluster"
  value       = module.eks.cluster_primary_security_group_id
}

# ECR Repository URLs
output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value = {
    for k, v in aws_ecr_repository.engine_repositories : k => v.repository_url
  }
}

# Database outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.infinityai_postgres.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.infinityai_postgres.port
}

output "db_instance_address" {
  description = "RDS instance hostname"
  value       = aws_db_instance.infinityai_postgres.address
  sensitive   = true
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.infinityai_postgres.arn
}

output "db_instance_availability_zone" {
  description = "RDS instance availability zone"
  value       = aws_db_instance.infinityai_postgres.availability_zone
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.infinityai_postgres.id
}

# Redis outputs
output "redis_cluster_address" {
  description = "Address of the replication group configuration endpoint"
  value       = aws_elasticache_replication_group.infinityai_redis.configuration_endpoint_address
}

output "redis_cluster_port" {
  description = "Port number on which the configuration endpoint will accept connections"
  value       = aws_elasticache_replication_group.infinityai_redis.port
}

# Load balancer outputs
output "load_balancer_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.infinityai_alb.dns_name
}

output "load_balancer_zone_id" {
  description = "The canonical hosted zone ID of the load balancer"
  value       = aws_lb.infinityai_alb.zone_id
}

# S3 bucket
output "s3_bucket_id" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.infinityai_data.id
}

output "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.infinityai_data.arn
}

output "s3_bucket_domain_name" {
  description = "The bucket domain name"
  value       = aws_s3_bucket.infinityai_data.bucket_domain_name
}

# VPC outputs
output "vpc_id" {
  description = "ID of the VPC where to create security group"
  value       = module.vpc.vpc_id
}

output "vpc_arn" {
  description = "The ARN of the VPC"
  value       = module.vpc.vpc_arn
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "nat_public_ips" {
  description = "List of public Elastic IPs created for AWS NAT Gateway"
  value       = module.vpc.nat_public_ips
}

# Configuration for kubectl
output "configure_kubectl" {
  description = "Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig"
  value       = "aws eks --region ${var.aws_region} update-kubeconfig --name ${module.eks.cluster_name}"
}

# Database connection string (without password)
output "database_url_template" {
  description = "Database connection URL template (replace PASSWORD with actual password)"
  value       = "postgresql://infinityai:PASSWORD@${aws_db_instance.infinityai_postgres.endpoint}/infinityai"
}

# Redis connection string
output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_replication_group.infinityai_redis.configuration_endpoint_address}:${aws_elasticache_replication_group.infinityai_redis.port}"
}