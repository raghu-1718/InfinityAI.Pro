#!/usr/bin/env pwsh
# Deploy InfinityAI Engines to AWS ECS
# Deploys Engine C and Engine D after IAM fix

param(
    [string]$Region = "us-east-1",
    [string]$Cluster = "infinityai-pro-cluster",
    [string]$ECRRepo = "152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend"
)

Write-Host "🚀 Deploying InfinityAI Engines to AWS ECS..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Login to ECR
Write-Host "🔐 Logging into AWS ECR..." -ForegroundColor Cyan
try {
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRepo.Split('/')[0]
    Write-Host "✅ ECR login successful" -ForegroundColor Green
}
catch {
    Write-Host "❌ ECR login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Build and push Engine C
Write-Host "`n🔧 Building and pushing Engine C (Trade Execution)..." -ForegroundColor Cyan
try {
    Set-Location "infinityai-pro\backend\engines\engine-c"
    
    docker build -t engine-c:latest .
    docker tag engine-c:latest "$ECRRepo:engine-c"
    docker push "$ECRRepo:engine-c"
    
    Write-Host "✅ Engine C image pushed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Engine C build/push failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Build and push Engine D  
Write-Host "`n🤖 Building and pushing Engine D (AI Chatbot)..." -ForegroundColor Cyan
try {
    Set-Location "..\engine-d"
    
    docker build -t engine-d:latest .
    docker tag engine-d:latest "$ECRRepo:engine-d"
    docker push "$ECRRepo:engine-d"
    
    Write-Host "✅ Engine D image pushed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Engine D build/push failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Return to root directory
Set-Location "..\..\..\.."

# Create task definitions
Write-Host "`n📋 Creating ECS task definitions..." -ForegroundColor Cyan

# Engine C task definition
$EngineC_TaskDef = @{
    family = "engine-c"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "512"
    memory = "1024"
    executionRoleArn = "arn:aws:iam::152687308610:role/ecsTaskExecutionRole"
    containerDefinitions = @(
        @{
            name = "engine-c"
            image = "$ECRRepo:engine-c"
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            essential = $true
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/engine-c"
                    "awslogs-region" = $Region
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

# Engine D task definition
$EngineD_TaskDef = @{
    family = "engine-d"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "512"
    memory = "1024"
    executionRoleArn = "arn:aws:iam::152687308610:role/ecsTaskExecutionRole"
    containerDefinitions = @(
        @{
            name = "engine-d"
            image = "$ECRRepo:engine-d"
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            essential = $true
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/engine-d"
                    "awslogs-region" = $Region
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

# Save task definitions
$EngineC_TaskDef | Out-File -FilePath "engine-c-taskdef.json" -Encoding UTF8
$EngineD_TaskDef | Out-File -FilePath "engine-d-taskdef.json" -Encoding UTF8

# Register task definitions
try {
    Write-Host "📝 Registering Engine C task definition..." -ForegroundColor Cyan
    aws ecs register-task-definition --cli-input-json "file://engine-c-taskdef.json" --region $Region
    
    Write-Host "📝 Registering Engine D task definition..." -ForegroundColor Cyan
    aws ecs register-task-definition --cli-input-json "file://engine-d-taskdef.json" --region $Region
    
    Write-Host "✅ Task definitions registered" -ForegroundColor Green
}
catch {
    Write-Host "❌ Task definition registration failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Create services
Write-Host "`n🎯 Creating ECS services..." -ForegroundColor Cyan

try {
    # Get VPC and subnet info
    $VpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
    $SubnetIds = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" --query "Subnets[0:2].SubnetId" --output text --region $Region
    $SubnetList = $SubnetIds -split "`t"
    
    Write-Host "🌐 Using VPC: $VpcId" -ForegroundColor Yellow
    Write-Host "🌐 Using Subnets: $($SubnetList -join ', ')" -ForegroundColor Yellow
    
    # Create Engine C service
    Write-Host "🔧 Creating Engine C service..." -ForegroundColor Cyan
    aws ecs create-service `
        --cluster $Cluster `
        --service-name "engine-c-service" `
        --task-definition "engine-c" `
        --desired-count 1 `
        --launch-type "FARGATE" `
        --network-configuration "awsvpcConfiguration={subnets=[$($SubnetList[0]),$($SubnetList[1])],assignPublicIp=ENABLED}" `
        --region $Region
    
    # Create Engine D service
    Write-Host "🤖 Creating Engine D service..." -ForegroundColor Cyan
    aws ecs create-service `
        --cluster $Cluster `
        --service-name "engine-d-service" `
        --task-definition "engine-d" `
        --desired-count 1 `
        --launch-type "FARGATE" `
        --network-configuration "awsvpcConfiguration={subnets=[$($SubnetList[0]),$($SubnetList[1])],assignPublicIp=ENABLED}" `
        --region $Region
    
    Write-Host "✅ ECS services created successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Service creation failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Check service status
Write-Host "`n📊 Checking service status..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

try {
    $Services = aws ecs describe-services --cluster $Cluster --services "engine-c-service" "engine-d-service" --region $Region | ConvertFrom-Json
    
    foreach ($Service in $Services.services) {
        $ServiceName = $Service.serviceName
        $Status = $Service.status
        $RunningCount = $Service.runningCount
        $DesiredCount = $Service.desiredCount
        
        Write-Host "🎯 $ServiceName`: Status=$Status, Running=$RunningCount/$DesiredCount" -ForegroundColor $(if ($Status -eq "ACTIVE") { "Green" } else { "Yellow" })
    }
}
catch {
    Write-Host "⚠️ Could not retrieve service status" -ForegroundColor Yellow
}

# Cleanup temp files
Remove-Item "engine-c-taskdef.json" -ErrorAction SilentlyContinue
Remove-Item "engine-d-taskdef.json" -ErrorAction SilentlyContinue

Write-Host "`n🎉 Deployment completed!" -ForegroundColor Green
Write-Host "`n🔗 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Wait 2-3 minutes for services to start" -ForegroundColor White
Write-Host "2. Check AWS ECS Console for service status" -ForegroundColor White
Write-Host "3. Configure load balancer target groups" -ForegroundColor White
Write-Host "4. Test engine endpoints" -ForegroundColor White