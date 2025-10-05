# Modified Automated Deployment Script for InfinityAI Engines (Using existing user credentials)
param(
    [string]$AccountId = "152687308610",
    [string]$Region = "us-east-1",
    [string]$ClusterName = "infinityai-pro-cluster",
    [switch]$SkipBuild,
    [switch]$DeployToProduction
)

$ErrorActionPreference = "Continue"

Write-Host "🚀 InfinityAI Automated Deployment Pipeline" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host "Account ID: $AccountId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Cluster: $ClusterName" -ForegroundColor Cyan

# Verify current AWS identity
Write-Host "🔍 Verifying AWS identity..." -ForegroundColor Yellow
$identity = aws sts get-caller-identity --output json | ConvertFrom-Json
Write-Host "✅ Current identity: $($identity.Arn)" -ForegroundColor Green

# Engine configuration
$engines = @(
    @{
        Name = "infinityai-engine-a"
        Port = 8000
        Cloud = "Azure"
        Description = "Azure AI Sentiment & Technical Analysis"
    },
    @{
        Name = "infinityai-engine-b" 
        Port = 8001
        Cloud = "GCP"
        Description = "Google Cloud ML Pattern Recognition & Risk Assessment"
    },
    @{
        Name = "infinityai-engine-c"
        Port = 8002
        Cloud = "AWS"
        Description = "AWS Quantitative Analysis & Backtesting"
    },
    @{
        Name = "infinityai-engine-d"
        Port = 8003
        Cloud = "AWS"
        Description = "AWS Central Orchestrator with DHAN integration"
    }
)

# Function to check if Docker images exist
function Test-DockerImages {
    Write-Host "🔍 Checking Docker images..." -ForegroundColor Yellow
    
    $missingImages = @()
    foreach ($engine in $engines) {
        try {
            $imageCheck = docker images $engine.Name --format "{{.Repository}}" 2>$null
            if (-not $imageCheck) {
                $missingImages += $engine.Name
                Write-Host "❌ Missing: $($engine.Name)" -ForegroundColor Red
            }
            else {
                Write-Host "✅ Found: $($engine.Name)" -ForegroundColor Green
            }
        }
        catch {
            $missingImages += $engine.Name
            Write-Host "❌ Missing: $($engine.Name)" -ForegroundColor Red
        }
    }
    
    return $missingImages
}

# Function to build Docker images
function Build-DockerImages {
    param([array]$ImagesToBuild)
    
    Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
    
    foreach ($imageName in $ImagesToBuild) {
        $engine = $engines | Where-Object { $_.Name -eq $imageName }
        if ($engine) {
            Write-Host "🏗️  Building $($engine.Name)..." -ForegroundColor Yellow
            
            $dockerFile = switch ($engine.Name) {
                "infinityai-engine-a" { "engine-a/Dockerfile" }
                "infinityai-engine-b" { "engine-b/Dockerfile" }
                "infinityai-engine-c" { "engine-c/Dockerfile" }
                "infinityai-engine-d" { "engine-d/Dockerfile" }
            }
            
            try {
                docker build -t $engine.Name -f $dockerFile .
                Write-Host "✅ Built: $($engine.Name)" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Failed to build: $($engine.Name)" -ForegroundColor Red
            }
        }
    }
}

# Function to create ECR repositories
function New-ECRRepositories {
    Write-Host "📦 Creating ECR repositories..." -ForegroundColor Yellow
    
    $awsEngines = $engines | Where-Object { $_.Cloud -eq "AWS" }
    
    foreach ($engine in $awsEngines) {
        try {
            # Try to describe repository first
            aws ecr describe-repositories --repository-names $engine.Name --region $Region 2>$null | Out-Null
            Write-Host "✅ Repository exists: $($engine.Name)" -ForegroundColor Green
        }
        catch {
            # Repository doesn't exist, create it
            try {
                aws ecr create-repository --repository-name $engine.Name --region $Region | Out-Null
                Write-Host "✅ Created repository: $($engine.Name)" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Failed to create repository: $($engine.Name)" -ForegroundColor Red
            }
        }
    }
}

# Function to push images to ECR
function Push-ImagesToECR {
    Write-Host "📤 Pushing images to ECR..." -ForegroundColor Yellow
    
    # Login to ECR
    try {
        Write-Host "🔑 Logging into ECR..." -ForegroundColor Yellow
        aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
        Write-Host "✅ ECR login successful" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ ECR login failed" -ForegroundColor Red
        return
    }
    
    $awsEngines = $engines | Where-Object { $_.Cloud -eq "AWS" }
    
    foreach ($engine in $awsEngines) {
        $ecrUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$($engine.Name):latest"
        
        Write-Host "🏷️  Tagging $($engine.Name)..." -ForegroundColor Yellow
        try {
            docker tag "$($engine.Name):latest" $ecrUri
            Write-Host "✅ Tagged: $ecrUri" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to tag: $($engine.Name)" -ForegroundColor Red
            continue
        }
        
        Write-Host "📤 Pushing $($engine.Name)..." -ForegroundColor Yellow
        try {
            docker push $ecrUri
            Write-Host "✅ Pushed: $ecrUri" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to push: $($engine.Name)" -ForegroundColor Red
        }
    }
}

# Function to create ECS task definitions
function New-ECSTaskDefinitions {
    Write-Host "📋 Creating ECS task definitions..." -ForegroundColor Yellow
    
    $awsEngines = $engines | Where-Object { $_.Cloud -eq "AWS" }
    
    foreach ($engine in $awsEngines) {
        $taskDefName = $engine.Name
        $imageUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$($engine.Name):latest"
        
        # Create task definition JSON
        $taskDef = @{
            family = $taskDefName
            networkMode = "awsvpc"
            requiresCompatibilities = @("FARGATE")
            cpu = "1024"
            memory = "2048"
            executionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
            containerDefinitions = @(
                @{
                    name = $engine.Name
                    image = $imageUri
                    essential = $true
                    portMappings = @(
                        @{
                            containerPort = $engine.Port
                            protocol = "tcp"
                        }
                    )
                    logConfiguration = @{
                        logDriver = "awslogs"
                        options = @{
                            "awslogs-group" = "/ecs/$taskDefName"
                            "awslogs-region" = $Region
                            "awslogs-stream-prefix" = "ecs"
                        }
                    }
                    environment = @(
                        @{
                            name = "PORT"
                            value = $engine.Port.ToString()
                        }
                    )
                    healthCheck = @{
                        command = @("CMD-SHELL", "curl -f http://localhost:$($engine.Port)/health || exit 1")
                        interval = 30
                        timeout = 5
                        retries = 3
                        startPeriod = 60
                    }
                }
            )
        }
        
        # Save task definition to file
        $taskDefFile = "$taskDefName-taskdef.json"
        $taskDef | ConvertTo-Json -Depth 10 | Out-File -FilePath $taskDefFile -Encoding UTF8
        
        # Create CloudWatch log group
        try {
            aws logs create-log-group --log-group-name "/ecs/$taskDefName" --region $Region 2>$null
            Write-Host "✅ Created log group: /ecs/$taskDefName" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️  Log group may already exist: /ecs/$taskDefName" -ForegroundColor Yellow
        }
        
        # Register task definition
        try {
            aws ecs register-task-definition --cli-input-json "file://$taskDefFile" --region $Region | Out-Null
            Write-Host "✅ Registered task definition: $taskDefName" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to register task definition: $taskDefName" -ForegroundColor Red
        }
        
        # Clean up task definition file
        Remove-Item $taskDefFile -ErrorAction SilentlyContinue
    }
}

# Function to create ECS services
function New-ECSServices {
    Write-Host "🚀 Creating ECS services..." -ForegroundColor Yellow
    
    $awsEngines = $engines | Where-Object { $_.Cloud -eq "AWS" }
    
    foreach ($engine in $awsEngines) {
        $serviceName = "$($engine.Name)-service"
        $taskDefName = $engine.Name
        
        Write-Host "🎯 Creating service: $serviceName" -ForegroundColor Yellow
        
        try {
            # Check if service already exists
            $existingService = aws ecs describe-services --cluster $ClusterName --services $serviceName --region $Region 2>$null | ConvertFrom-Json
            
            if ($existingService.services -and $existingService.services[0].status -ne "INACTIVE") {
                Write-Host "📝 Updating existing service: $serviceName" -ForegroundColor Yellow
                
                aws ecs update-service `
                    --cluster $ClusterName `
                    --service $serviceName `
                    --task-definition $taskDefName `
                    --desired-count 1 `
                    --region $Region | Out-Null
                
                Write-Host "✅ Updated service: $serviceName" -ForegroundColor Green
            }
            else {
                Write-Host "🆕 Creating new service: $serviceName" -ForegroundColor Yellow
                
                # Get default subnets and security group
                $vpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
                $subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[0:2].SubnetId" --output text --region $Region
                $securityGroup = aws ec2 describe-security-groups --filters "Name=group-name,Values=default" "Name=vpc-id,Values=$vpcId" --query "SecurityGroups[0].GroupId" --output text --region $Region
                
                aws ecs create-service `
                    --cluster $ClusterName `
                    --service-name $serviceName `
                    --task-definition $taskDefName `
                    --desired-count 1 `
                    --launch-type FARGATE `
                    --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$securityGroup],assignPublicIp=ENABLED}" `
                    --region $Region | Out-Null
                
                Write-Host "✅ Created service: $serviceName" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "❌ Failed to create/update service: $serviceName" -ForegroundColor Red
        }
    }
}

# Function to verify deployment
function Test-Deployment {
    Write-Host "🧪 Verifying deployment..." -ForegroundColor Yellow
    
    $awsEngines = $engines | Where-Object { $_.Cloud -eq "AWS" }
    
    foreach ($engine in $awsEngines) {
        $serviceName = "$($engine.Name)-service"
        
        try {
            $service = aws ecs describe-services --cluster $ClusterName --services $serviceName --region $Region --output json | ConvertFrom-Json
            
            if ($service.services -and $service.services.Count -gt 0) {
                $runningCount = $service.services[0].runningCount
                $desiredCount = $service.services[0].desiredCount
                
                if ($runningCount -eq $desiredCount -and $runningCount -gt 0) {
                    Write-Host "✅ Service healthy: $serviceName ($runningCount/$desiredCount)" -ForegroundColor Green
                }
                else {
                    Write-Host "⚠️  Service starting: $serviceName ($runningCount/$desiredCount)" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "❌ Service not found: $serviceName" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "❌ Failed to check service: $serviceName" -ForegroundColor Red
        }
    }
}

# Function to display deployment summary
function Show-DeploymentSummary {
    Write-Host ""
    Write-Host "📊 Deployment Summary" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    
    foreach ($engine in $engines) {
        Write-Host ""
        Write-Host "🔧 $($engine.Name)" -ForegroundColor Cyan
        Write-Host "   Description: $($engine.Description)" -ForegroundColor White
        Write-Host "   Port: $($engine.Port)" -ForegroundColor White
        Write-Host "   Cloud: $($engine.Cloud)" -ForegroundColor White
        
        if ($engine.Cloud -eq "AWS") {
            $ecrUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$($engine.Name):latest"
            Write-Host "   ECR Image: $ecrUri" -ForegroundColor White
            Write-Host "   ECS Service: $($engine.Name)-service" -ForegroundColor White
        }
    }
}

# Main execution
Write-Host "🔧 Starting automated deployment..." -ForegroundColor Green

# Step 1: Check and build Docker images if needed
if (-not $SkipBuild) {
    $missingImages = Test-DockerImages
    if ($missingImages.Count -gt 0) {
        Write-Host "🔨 Building missing images..." -ForegroundColor Yellow
        Build-DockerImages $missingImages
    }
    else {
        Write-Host "✅ All Docker images exist" -ForegroundColor Green
    }
}

# Step 2: AWS deployment steps
New-ECRRepositories
Push-ImagesToECR

if ($DeployToProduction) {
    New-ECSTaskDefinitions
    New-ECSServices
    
    # Wait for services to start
    Write-Host "⏱️  Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Test-Deployment
}

Show-DeploymentSummary

Write-Host "🎉 AWS deployment complete!" -ForegroundColor Green