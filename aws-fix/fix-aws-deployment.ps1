# AWS ECS and Load Balancer Fix Script
# Run this script to restore Engine C and D functionality

# Set AWS region
$region = "us-east-1"
$clusterName = "infinityai-pro-cluster"

Write-Host "🔧 Starting AWS ECS and Load Balancer Fix..." -ForegroundColor Yellow

# 1. Check ECS cluster status
Write-Host "1. Checking ECS cluster status..." -ForegroundColor Cyan
aws ecs describe-clusters --clusters $clusterName --region $region

# 2. Register updated task definitions
Write-Host "2. Registering Engine C task definition..." -ForegroundColor Cyan
aws ecs register-task-definition --cli-input-json file://ecs-task-definition-engine-c.json --region $region

Write-Host "3. Registering Engine D task definition..." -ForegroundColor Cyan
aws ecs register-task-definition --cli-input-json file://ecs-task-definition-engine-d.json --region $region

# 4. Update ECS services
Write-Host "4. Updating Engine C service..." -ForegroundColor Cyan
aws ecs update-service --cluster $clusterName --service engine-c-service --task-definition engine-c-task --desired-count 1 --region $region

Write-Host "5. Updating Engine D service..." -ForegroundColor Cyan
aws ecs update-service --cluster $clusterName --service engine-d-service --task-definition engine-d-task --desired-count 1 --region $region

# 5. Check load balancer target groups
Write-Host "6. Checking load balancer target groups..." -ForegroundColor Cyan
aws elbv2 describe-target-groups --region $region

# 6. Wait for services to stabilize
Write-Host "7. Waiting for services to stabilize..." -ForegroundColor Cyan
aws ecs wait services-stable --cluster $clusterName --services engine-c-service engine-d-service --region $region

# 7. Verify service status
Write-Host "8. Verifying service status..." -ForegroundColor Cyan
aws ecs describe-services --cluster $clusterName --services engine-c-service engine-d-service --region $region

Write-Host "✅ AWS deployment fix completed!" -ForegroundColor Green
Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Test endpoints
curl -s -o $null -w "Engine C: %{http_code}`n" http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8002/health
curl -s -o $null -w "Engine D: %{http_code}`n" http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8000/health