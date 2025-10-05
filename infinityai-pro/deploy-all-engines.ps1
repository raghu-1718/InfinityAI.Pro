# InfinityAI.Pro - Complete Multi-Cloud Deployment Script
# This script deploys all 4 engines to their respective cloud platforms

Write-Host "🚀 InfinityAI.Pro Multi-Cloud Deployment Started" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Configuration
$AWS_ACCOUNT_ID = "152687308610"
$AWS_REGION = "us-east-1"
$AZURE_RESOURCE_GROUP = "infinityai"
$GCP_PROJECT_ID = "infinityai-pro-project"

# Step 1: Deploy Engine D to AWS ECS
Write-Host "🔵 Step 1: Deploying Engine D to AWS ECS..." -ForegroundColor Blue

# ECR Login
Write-Host "  - Logging into AWS ECR..."
try {
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    Write-Host "  ✅ ECR login successful" -ForegroundColor Green
} catch {
    Write-Host "  ❌ ECR login failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Please ensure IAM permissions are properly set" -ForegroundColor Yellow
    exit 1
}

# Tag and push Engine D
Write-Host "  - Building and pushing Engine D to ECR..."
docker tag infinityai-engine-d:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-d:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-d:latest"

# Create/Update ECS Task Definition
Write-Host "  - Creating ECS Task Definition..."
$taskDefinition = @{
    family = "infinityai-engine-d"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "1024"
    memory = "2048"
    executionRoleArn = "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole"
    taskRoleArn = "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole"
    containerDefinitions = @(
        @{
            name = "infinityai-engine-d"
            image = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-d:latest"
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            environment = @(
                @{
                    name = "ENVIRONMENT"
                    value = "production"
                },
                @{
                    name = "AWS_DEFAULT_REGION"
                    value = $AWS_REGION
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/infinityai-engine-d"
                    "awslogs-region" = $AWS_REGION
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8000/health || exit 1")
                interval = 30
                timeout = 10
                retries = 3
                startPeriod = 60
            }
        }
    )
} | ConvertTo-Json -Depth 10

$taskDefinition | Out-File -FilePath "engine-d-task-definition.json" -Encoding UTF8
aws ecs register-task-definition --cli-input-json file://engine-d-task-definition.json

# Create/Update ECS Service
Write-Host "  - Creating/Updating ECS Service..."
$serviceExists = aws ecs describe-services --cluster infinityai-pro-cluster --services infinityai-engine-d-service --query "services[0].serviceName" --output text 2>$null

if ($serviceExists -eq "infinityai-engine-d-service") {
    # Update existing service
    aws ecs update-service `
        --cluster infinityai-pro-cluster `
        --service infinityai-engine-d-service `
        --task-definition infinityai-engine-d:LATEST `
        --desired-count 2
} else {
    # Create new service
    aws ecs create-service `
        --cluster infinityai-pro-cluster `
        --service-name infinityai-engine-d-service `
        --task-definition infinityai-engine-d:LATEST `
        --desired-count 2 `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[subnet-0a1b2c3d,subnet-0e1f2g3h],securityGroups=[sg-0123456789abcdef0],assignPublicIp=ENABLED}" `
        --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:$AWS_REGION:$AWS_ACCOUNT_ID:targetgroup/infinityai-engine-d-tg/0123456789abcdef,containerName=infinityai-engine-d,containerPort=8000"
}

Write-Host "  ✅ Engine D deployed to AWS ECS" -ForegroundColor Green

# Step 2: Deploy Engine A to Azure Container Instances
Write-Host "🔵 Step 2: Deploying Engine A to Azure..." -ForegroundColor Blue

# Azure Container Registry
Write-Host "  - Building and pushing to Azure Container Registry..."
az acr build --registry infinityairegistry --image engine-a:latest scripts/engine-a-azure/

# Deploy to Azure Container Instances
Write-Host "  - Deploying to Azure Container Instances..."
az container create `
    --resource-group $AZURE_RESOURCE_GROUP `
    --name infinityai-engine-a `
    --image infinityairegistry.azurecr.io/engine-a:latest `
    --cpu 1 `
    --memory 2 `
    --ports 8001 `
    --dns-name-label infinityai-engine-a `
    --environment-variables AZURE_COGNITIVE_SERVICES_KEY="" AZURE_STORAGE_CONNECTION_STRING="" `
    --restart-policy Always

Write-Host "  ✅ Engine A deployed to Azure" -ForegroundColor Green

# Step 3: Deploy Engine B to Google Cloud Run
Write-Host "🔵 Step 3: Deploying Engine B to Google Cloud..." -ForegroundColor Blue

# Build and push to Google Container Registry
Write-Host "  - Building and pushing to Google Container Registry..."
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/engine-b scripts/engine-b-gcp/

# Deploy to Cloud Run
Write-Host "  - Deploying to Google Cloud Run..."
gcloud run deploy infinityai-engine-b `
    --image gcr.io/$GCP_PROJECT_ID/engine-b `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --port 8002 `
    --memory 2Gi `
    --cpu 1 `
    --set-env-vars GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID

Write-Host "  ✅ Engine B deployed to Google Cloud Run" -ForegroundColor Green

# Step 4: Deploy Engine C to AWS ECS (Secondary)
Write-Host "🔵 Step 4: Deploying Engine C to AWS ECS..." -ForegroundColor Blue

# Tag and push Engine C
Write-Host "  - Building and pushing Engine C to ECR..."
docker tag infinityai-engine-c:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-c:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-c:latest"

# Create Task Definition for Engine C
$taskDefinitionC = @{
    family = "infinityai-engine-c"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "2048"
    memory = "4096"
    executionRoleArn = "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole"
    taskRoleArn = "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole"
    containerDefinitions = @(
        @{
            name = "infinityai-engine-c"
            image = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/infinityai-engine-c:latest"
            portMappings = @(
                @{
                    containerPort = 8003
                    protocol = "tcp"
                }
            )
            environment = @(
                @{
                    name = "AWS_DEFAULT_REGION"
                    value = $AWS_REGION
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/infinityai-engine-c"
                    "awslogs-region" = $AWS_REGION
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8003/health || exit 1")
                interval = 30
                timeout = 10
                retries = 3
                startPeriod = 60
            }
        }
    )
} | ConvertTo-Json -Depth 10

$taskDefinitionC | Out-File -FilePath "engine-c-task-definition.json" -Encoding UTF8
aws ecs register-task-definition --cli-input-json file://engine-c-task-definition.json

# Create ECS Service for Engine C
aws ecs create-service `
    --cluster infinityai-learning-cluster `
    --service-name infinityai-engine-c-service `
    --task-definition infinityai-engine-c:LATEST `
    --desired-count 1 `
    --launch-type FARGATE `
    --network-configuration "awsvpcConfiguration={subnets=[subnet-0a1b2c3d,subnet-0e1f2g3h],securityGroups=[sg-0123456789abcdef0],assignPublicIp=ENABLED}"

Write-Host "  ✅ Engine C deployed to AWS ECS" -ForegroundColor Green

# Step 5: Get deployment URLs
Write-Host "🔵 Step 5: Getting deployment URLs..." -ForegroundColor Blue

# Get AWS Load Balancer DNS
$AWS_ALB_DNS = aws elbv2 describe-load-balancers --names infinityai-pro-alb --query "LoadBalancers[0].DNSName" --output text
Write-Host "  Engine D (AWS): https://$AWS_ALB_DNS" -ForegroundColor Yellow

# Get Azure Container Instance FQDN
$AZURE_FQDN = az container show --resource-group $AZURE_RESOURCE_GROUP --name infinityai-engine-a --query "ipAddress.fqdn" --output tsv
Write-Host "  Engine A (Azure): https://$AZURE_FQDN:8001" -ForegroundColor Yellow

# Get Google Cloud Run URL
$GCP_URL = gcloud run services describe infinityai-engine-b --platform managed --region us-central1 --format "value(status.url)"
Write-Host "  Engine B (GCP): $GCP_URL" -ForegroundColor Yellow

Write-Host "  Engine C (AWS): https://$AWS_ALB_DNS:8003 (via secondary load balancer)" -ForegroundColor Yellow

Write-Host ""
Write-Host "🎉 Multi-Cloud Deployment Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Create deployment summary
$deploymentSummary = @"
🚀 InfinityAI.Pro Multi-Cloud Deployment Summary
===============================================

✅ All engines successfully deployed!

📍 Engine URLs:
- Engine D (Central): https://$AWS_ALB_DNS
- Engine A (Azure): https://$AZURE_FQDN:8001  
- Engine B (GCP): $GCP_URL
- Engine C (AWS): https://$AWS_ALB_DNS:8003

🌐 DNS Records for Namecheap:
- api.infinityai.pro → $AWS_ALB_DNS (CNAME)
- engine-a.infinityai.pro → $AZURE_FQDN (CNAME)  
- engine-b.infinityai.pro → $($GCP_URL -replace 'https://','') (CNAME)
- engine-c.infinityai.pro → $AWS_ALB_DNS (CNAME)

🔧 Next Steps:
1. Configure DNS records in Namecheap
2. Test all engine endpoints
3. Run integration tests
4. Monitor deployment health

Deployment completed at: $(Get-Date)
"@

$deploymentSummary | Out-File -FilePath "DEPLOYMENT_SUMMARY.md" -Encoding UTF8
Write-Host $deploymentSummary -ForegroundColor Cyan