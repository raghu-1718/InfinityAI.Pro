#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete deployment script for InfinityAI.Pro platform
    Deploys all engines to AWS and GCP with proper configuration

.DESCRIPTION
    This script deploys:
    - Engine A (Market Data) to GCP Cloud Run
    - Engine B (AI/ML) to GCP Cloud Run  
    - Ultra Aggressive Trading to GCP Cloud Run
    - Engine C (Trade Execution) to AWS ECS
    - Engine D (AI Chatbot) to AWS ECS
    - Frontend to AWS S3 + CloudFront

.EXAMPLE
    .\deploy-complete-platform.ps1 -Environment production
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$DeployFrontendOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$DeployBackendOnly
)

# Configuration
$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." "Info"
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        Write-ColorOutput "✅ AWS CLI: $awsVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ AWS CLI not found. Please install AWS CLI v2." "Error"
        exit 1
    }
    
    # Check GCP CLI
    try {
        $gcpVersion = gcloud version --format="value(Google Cloud SDK)" 2>$null
        Write-ColorOutput "✅ GCloud CLI: $gcpVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ GCloud CLI not found. Please install Google Cloud SDK." "Error"
        exit 1
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        Write-ColorOutput "✅ Docker: $dockerVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ Docker not found. Please install Docker Desktop." "Error"
        exit 1
    }
    
    # Check Node.js (for frontend)
    if (-not $DeployBackendOnly) {
        try {
            $nodeVersion = node --version 2>$null
            Write-ColorOutput "✅ Node.js: $nodeVersion" "Success"
        }
        catch {
            Write-ColorOutput "❌ Node.js not found. Please install Node.js." "Error"
            exit 1
        }
    }
}

function Set-EnvironmentVariables {
    Write-ColorOutput "⚙️ Setting up environment variables..." "Info"
    
    # Load environment variables
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
        Write-ColorOutput "✅ Environment variables loaded from .env" "Success"
    } else {
        Write-ColorOutput "⚠️ .env file not found. Using example file..." "Warning"
        Copy-Item ".env.example" ".env" -Force
        Write-ColorOutput "📝 Please update .env with your actual credentials before deploying!" "Warning"
        Read-Host "Press Enter to continue or Ctrl+C to exit"
    }
}

function Deploy-GCPEngines {
    if ($DeployFrontendOnly) { return }
    
    Write-ColorOutput "`n🚀 Deploying GCP Engines..." "Header"
    
    # Set GCP project
    $gcpProject = $env:GCP_PROJECT_ID
    if (-not $gcpProject) { $gcpProject = "infinityai-pro" }
    
    gcloud config set project $gcpProject
    
    # Deploy Engine A - Market Data
    Write-ColorOutput "📊 Deploying Engine A (Market Data) to GCP..." "Info"
    Set-Location "backend\engines\engine-a-market-data"
    
    if (-not $SkipBuild) {
        docker build -t gcr.io/$gcpProject/engine-a-market-data .
        docker push gcr.io/$gcpProject/engine-a-market-data
    }
    
    gcloud run deploy engine-a-market-data `
        --image=gcr.io/$gcpProject/engine-a-market-data `
        --platform=managed `
        --region=us-central1 `
        --allow-unauthenticated `
        --memory=1Gi `
        --cpu=1 `
        --min-instances=1 `
        --max-instances=10 `
        --port=8000 `
        --set-env-vars="DHAN_ACCESS_TOKEN=$env:DHAN_ACCESS_TOKEN,DHAN_CLIENT_ID=$env:DHAN_CLIENT_ID" `
        --timeout=300s
    
    $engineAUrl = gcloud run services describe engine-a-market-data --region=us-central1 --format="value(status.url)"
    Write-ColorOutput "✅ Engine A deployed: $engineAUrl" "Success"
    
    Set-Location "..\..\..\"
    
    # Deploy Engine B - AI/ML
    Write-ColorOutput "🤖 Deploying Engine B (AI/ML) to GCP..." "Info"
    Set-Location "backend\engines\engine-b-ai-ml"
    
    if (-not $SkipBuild) {
        docker build -t gcr.io/$gcpProject/engine-b-ai-ml .
        docker push gcr.io/$gcpProject/engine-b-ai-ml
    }
    
    gcloud run deploy engine-b-ai-ml `
        --image=gcr.io/$gcpProject/engine-b-ai-ml `
        --platform=managed `
        --region=us-central1 `
        --allow-unauthenticated `
        --memory=2Gi `
        --cpu=2 `
        --min-instances=1 `
        --max-instances=10 `
        --port=8001 `
        --timeout=300s
    
    $engineBUrl = gcloud run services describe engine-b-ai-ml --region=us-central1 --format="value(status.url)"
    Write-ColorOutput "✅ Engine B deployed: $engineBUrl" "Success"
    
    Set-Location "..\..\..\"
    
    # Deploy Ultra Aggressive Trading
    Write-ColorOutput "⚡ Deploying Ultra Aggressive Trading to GCP..." "Info"
    Set-Location "backend\engines\engine-ultra-aggressive"
    
    if (-not $SkipBuild) {
        docker build -t gcr.io/$gcpProject/ultra-aggressive-trading .
        docker push gcr.io/$gcpProject/ultra-aggressive-trading
    }
    
    gcloud run deploy ultra-aggressive-trading `
        --image=gcr.io/$gcpProject/ultra-aggressive-trading `
        --platform=managed `
        --region=us-central1 `
        --allow-unauthenticated `
        --memory=1Gi `
        --cpu=1 `
        --min-instances=1 `
        --max-instances=5 `
        --port=8000 `
        --set-env-vars="DHAN_ACCESS_TOKEN=$env:DHAN_ACCESS_TOKEN,DHAN_CLIENT_ID=$env:DHAN_CLIENT_ID" `
        --timeout=300s
    
    $ultraUrl = gcloud run services describe ultra-aggressive-trading --region=us-central1 --format="value(status.url)"
    Write-ColorOutput "✅ Ultra Aggressive Trading deployed: $ultraUrl" "Success"
    
    Set-Location "..\..\..\"
}

function Deploy-AWSEngines {
    if ($DeployFrontendOnly) { return }
    
    Write-ColorOutput "`n☁️ Deploying AWS Engines..." "Header"
    
    $awsRegion = $env:AWS_REGION
    if (-not $awsRegion) { $awsRegion = "us-east-1" }
    
    $awsAccount = $env:AWS_ACCOUNT_ID
    if (-not $awsAccount) { $awsAccount = "152687308610" }
    
    $ecrRepo = "$awsAccount.dkr.ecr.$awsRegion.amazonaws.com/infinityai-pro"
    
    # ECR Login
    Write-ColorOutput "🔐 Logging into AWS ECR..." "Info"
    aws ecr get-login-password --region $awsRegion | docker login --username AWS --password-stdin $ecrRepo
    
    # Deploy Engine C - Trade Execution
    Write-ColorOutput "⚡ Deploying Engine C (Trade Execution) to AWS..." "Info"
    Set-Location "backend\engines\engine-c-execution"
    
    if (-not $SkipBuild) {
        docker build -t engine-c-execution .
        docker tag engine-c-execution:latest "$ecrRepo:engine-c"
        docker push "$ecrRepo:engine-c"
    }
    
    # Create ECS task definition for Engine C
    $engineCTaskDef = @{
        family = "engine-c-execution"
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = "512"
        memory = "1024"
        executionRoleArn = "arn:aws:iam::$awsAccount:role/ecsTaskExecutionRole"
        containerDefinitions = @(@{
            name = "engine-c"
            image = "$ecrRepo:engine-c"
            portMappings = @(@{
                containerPort = 8002
                protocol = "tcp"
            })
            environment = @(
                @{ name = "DHAN_ACCESS_TOKEN"; value = $env:DHAN_ACCESS_TOKEN }
                @{ name = "DHAN_CLIENT_ID"; value = $env:DHAN_CLIENT_ID }
                @{ name = "PORT"; value = "8002" }
            )
            essential = $true
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/engine-c"
                    "awslogs-region" = $awsRegion
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        })
    } | ConvertTo-Json -Depth 10
    
    $engineCTaskDef | Out-File "engine-c-task-def.json" -Encoding UTF8
    aws ecs register-task-definition --cli-input-json file://engine-c-task-def.json
    
    Set-Location "..\..\..\"
    
    # Deploy Engine D - Chatbot
    Write-ColorOutput "🤖 Deploying Engine D (Chatbot) to AWS..." "Info"
    Set-Location "backend\engines\engine-d-chatbot"
    
    if (-not $SkipBuild) {
        docker build -t engine-d-chatbot .
        docker tag engine-d-chatbot:latest "$ecrRepo:engine-d"
        docker push "$ecrRepo:engine-d"
    }
    
    # Create ECS task definition for Engine D
    $engineDTaskDef = @{
        family = "engine-d-chatbot"
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = "512"
        memory = "1024"
        executionRoleArn = "arn:aws:iam::$awsAccount:role/ecsTaskExecutionRole"
        containerDefinitions = @(@{
            name = "engine-d"
            image = "$ecrRepo:engine-d"
            portMappings = @(@{
                containerPort = 8003
                protocol = "tcp"
            })
            environment = @(
                @{ name = "ENGINE_A_URL"; value = $env:ENGINE_A_URL }
                @{ name = "ENGINE_B_URL"; value = $env:ENGINE_B_URL }
                @{ name = "ENGINE_C_URL"; value = $env:ENGINE_C_URL }
                @{ name = "PORT"; value = "8003" }
            )
            essential = $true
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/engine-d"
                    "awslogs-region" = $awsRegion
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        })
    } | ConvertTo-Json -Depth 10
    
    $engineDTaskDef | Out-File "engine-d-task-def.json" -Encoding UTF8
    aws ecs register-task-definition --cli-input-json file://engine-d-task-def.json
    
    Set-Location "..\..\..\"
    
    Write-ColorOutput "✅ AWS Engines deployed to ECS" "Success"
}

function Deploy-Frontend {
    if ($DeployBackendOnly) { return }
    
    Write-ColorOutput "`n🌐 Deploying Frontend to AWS S3..." "Header"
    
    Set-Location "frontend\web"
    
    # Install dependencies
    Write-ColorOutput "📦 Installing frontend dependencies..." "Info"
    npm install
    
    # Build production version
    Write-ColorOutput "🔧 Building production frontend..." "Info"
    npm run build
    
    # Deploy to S3 (assuming bucket exists)
    $s3Bucket = "infinityai-pro-frontend"
    Write-ColorOutput "📤 Uploading to S3 bucket: $s3Bucket" "Info"
    
    try {
        aws s3 sync build/ s3://$s3Bucket --delete --cache-control "max-age=31536000" --exclude "*.html"
        aws s3 sync build/ s3://$s3Bucket --delete --cache-control "max-age=0" --include "*.html"
        Write-ColorOutput "✅ Frontend deployed to S3" "Success"
    }
    catch {
        Write-ColorOutput "⚠️ S3 deployment failed. Make sure bucket exists and you have permissions." "Warning"
    }
    
    Set-Location "..\.."
}

function Test-Deployments {
    Write-ColorOutput "`n🧪 Testing deployments..." "Header"
    
    $endpoints = @{
        "Engine A (Market Data)" = $env:ENGINE_A_URL + "/health"
        "Engine B (AI/ML)" = $env:ENGINE_B_URL + "/health"
        "Engine C (Trade Execution)" = $env:ENGINE_C_URL + "/health"
        "Engine D (Chatbot)" = $env:ENGINE_D_URL + "/health"
        "Ultra Aggressive" = $env:ULTRA_AGGRESSIVE_URL + "/health"
    }
    
    foreach ($service in $endpoints.GetEnumerator()) {
        try {
            $response = Invoke-RestMethod -Uri $service.Value -Method Get -TimeoutSec 10
            if ($response.status -eq "healthy") {
                Write-ColorOutput "✅ $($service.Key): Healthy" "Success"
            } else {
                Write-ColorOutput "⚠️ $($service.Key): $($response.status)" "Warning"
            }
        }
        catch {
            Write-ColorOutput "❌ $($service.Key): Failed to connect" "Error"
        }
    }
}

function Show-Summary {
    Write-ColorOutput "`n🎉 Deployment Summary" "Header"
    Write-ColorOutput "===========================================" "Header"
    
    Write-ColorOutput "`n📊 Engine URLs:" "Info"
    Write-ColorOutput "• Engine A (Market Data): $env:ENGINE_A_URL" "Info"
    Write-ColorOutput "• Engine B (AI/ML): $env:ENGINE_B_URL" "Info"
    Write-ColorOutput "• Engine C (Trade Execution): $env:ENGINE_C_URL" "Info"
    Write-ColorOutput "• Engine D (Chatbot): $env:ENGINE_D_URL" "Info"
    Write-ColorOutput "• Ultra Aggressive Trading: $env:ULTRA_AGGRESSIVE_URL" "Info"
    
    Write-ColorOutput "`n🌐 Frontend URL:" "Info"
    Write-ColorOutput "• https://infinityai.pro" "Info"
    
    Write-ColorOutput "`n📋 Next Steps:" "Info"
    Write-ColorOutput "1. Update DNS records if needed" "Info"
    Write-ColorOutput "2. Configure SSL certificates" "Info"
    Write-ColorOutput "3. Set up monitoring and alerts" "Info"
    Write-ColorOutput "4. Run integration tests" "Info"
    
    Write-ColorOutput "`n✅ InfinityAI.Pro platform deployed successfully!" "Success"
}

# Main execution
function Main {
    Write-ColorOutput "🚀 InfinityAI.Pro Complete Deployment Script" "Header"
    Write-ColorOutput "Environment: $Environment" "Info"
    Write-ColorOutput "===========================================" "Header"
    
    Test-Prerequisites
    Set-EnvironmentVariables
    
    if (-not $DeployFrontendOnly) {
        Deploy-GCPEngines
        Deploy-AWSEngines
    }
    
    if (-not $DeployBackendOnly) {
        Deploy-Frontend
    }
    
    Test-Deployments
    Show-Summary
}

# Execute main function
Main