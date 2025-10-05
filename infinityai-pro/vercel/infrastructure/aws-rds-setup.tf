# InfinityAI.Pro Production AWS RDS Setup
# This creates a production PostgreSQL database in AWS RDS

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
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "infinityai_prod"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "infinityai_admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = "InfinityAI_Prod_2025_Secure"
}

# VPC for RDS
resource "aws_vpc" "infinityai_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "infinityai-prod-vpc"
    Environment = "production"
    Project     = "InfinityAI.Pro"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "infinityai_igw" {
  vpc_id = aws_vpc.infinityai_vpc.id

  tags = {
    Name = "infinityai-prod-igw"
  }
}

# Private subnets for RDS
resource "aws_subnet" "infinityai_private_1" {
  vpc_id            = aws_vpc.infinityai_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "infinityai-prod-private-1"
  }
}

resource "aws_subnet" "infinityai_private_2" {
  vpc_id            = aws_vpc.infinityai_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "infinityai-prod-private-2"
  }
}

# DB subnet group
resource "aws_db_subnet_group" "infinityai_db_subnet_group" {
  name       = "infinityai-prod-db-subnet-group"
  subnet_ids = [aws_subnet.infinityai_private_1.id, aws_subnet.infinityai_private_2.id]

  tags = {
    Name = "infinityai-prod-db-subnet-group"
  }
}

# Security group for RDS
resource "aws_security_group" "infinityai_rds_sg" {
  name_prefix = "infinityai-rds-"
  vpc_id      = aws_vpc.infinityai_vpc.id

  # PostgreSQL access from anywhere (for production access)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "infinityai-prod-rds-sg"
  }
}

# RDS PostgreSQL instance
resource "aws_db_instance" "infinityai_postgres" {
  identifier = "infinityai-prod-postgres"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type         = "gp2"
  storage_encrypted    = true
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.infinityai_rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.infinityai_db_subnet_group.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "infinityai-prod-postgres-final-snapshot"
  
  publicly_accessible = true
  
  tags = {
    Name        = "infinityai-prod-postgres"
    Environment = "production"
    Project     = "InfinityAI.Pro"
  }
}

# ElastiCache Redis for caching
resource "aws_elasticache_subnet_group" "infinityai_cache_subnet_group" {
  name       = "infinityai-prod-cache-subnet-group"
  subnet_ids = [aws_subnet.infinityai_private_1.id, aws_subnet.infinityai_private_2.id]
}

resource "aws_security_group" "infinityai_redis_sg" {
  name_prefix = "infinityai-redis-"
  vpc_id      = aws_vpc.infinityai_vpc.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "infinityai-prod-redis-sg"
  }
}

resource "aws_elasticache_replication_group" "infinityai_redis" {
  replication_group_id         = "infinityai-prod-redis"
  description                  = "InfinityAI.Pro production Redis cluster"
  
  port                    = 6379
  parameter_group_name    = "default.redis7"
  node_type              = "cache.t3.micro"
  
  num_cache_clusters = 1
  
  subnet_group_name  = aws_elasticache_subnet_group.infinityai_cache_subnet_group.name
  security_group_ids = [aws_security_group.infinityai_redis_sg.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = false
  
  tags = {
    Name        = "infinityai-prod-redis"
    Environment = "production"
    Project     = "InfinityAI.Pro"
  }
}

# Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.infinityai_postgres.endpoint
  sensitive   = false
}

output "rds_connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.infinityai_postgres.endpoint}:5432/${var.db_name}"
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_replication_group.infinityai_redis.configuration_endpoint_address != null ? aws_elasticache_replication_group.infinityai_redis.configuration_endpoint_address : aws_elasticache_replication_group.infinityai_redis.primary_endpoint_address
  sensitive   = false
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.infinityai_vpc.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = [aws_subnet.infinityai_private_1.id, aws_subnet.infinityai_private_2.id]
}