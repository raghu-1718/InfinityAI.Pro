#!/usr/bin/env pwsh
# Deploy Ultra Aggressive Trader to AWS ECS
param(
  [string]$Region = "us-east-1",
  [string]$Cluster = "infinityai-pro-cluster",
  [string]$ECRRepo = "152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend"
)

Write-Host "🚀 Deploying Ultra Aggressive Trader to AWS ECS..." -ForegroundColor Green

try { docker version | Out-Null } catch { Write-Host "❌ Docker not running" -ForegroundColor Red; exit 1 }

Write-Host "🔐 Logging into AWS ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRepo.Split('/')[0]

# Build image
Set-Location "$(Split-Path $PSScriptRoot)\.."

docker build -f Dockerfile.ultra-aggressive -t ultra-aggressive:latest .
docker tag ultra-aggressive:latest "$ECRRepo:ultra-aggressive"
docker push "$ECRRepo:ultra-aggressive"

Set-Location $PSScriptRoot

# Task definition
$Task = @{
  family = "ultra-aggressive"
  networkMode = "awsvpc"
  requiresCompatibilities = @("FARGATE")
  cpu = "512"
  memory = "1024"
  executionRoleArn = "arn:aws:iam::152687308610:role/ecsTaskExecutionRole"
  containerDefinitions = @(
    @{ name = "ultra-aggressive"; image = "$ECRRepo:ultra-aggressive";
       portMappings = @(@{ containerPort = 8080; protocol = "tcp"});
       environment = @(
          @{ name="ULTRA_AGGRESSIVE_MODE"; value="true" }
       );
       logConfiguration = @{ logDriver = "awslogs"; options = @{ "awslogs-group"="/ecs/ultra-aggressive"; "awslogs-region"=$Region; "awslogs-stream-prefix"="ecs" } }
    }
  )
} | ConvertTo-Json -Depth 10

$Task | Out-File -FilePath ultra-taskdef.json -Encoding UTF8
aws ecs register-task-definition --cli-input-json file://ultra-taskdef.json --region $Region | Out-Null

# Create or update service
$svcName = "ultra-aggressive-service"
$exists = aws ecs describe-services --cluster $Cluster --services $svcName --region $Region --query "services[0].serviceName" --output text

if ($exists -eq $svcName) {
  Write-Host "♻️ Updating existing service $svcName" -ForegroundColor Yellow
  aws ecs update-service --cluster $Cluster --service $svcName --task-definition ultra-aggressive --desired-count 1 --region $Region | Out-Null
} else {
  Write-Host "🆕 Creating service $svcName" -ForegroundColor Yellow
  $VpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
  $Subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" --query "Subnets[0:2].SubnetId" --output text --region $Region
  $List = $Subnets -split "`t"
  aws ecs create-service --cluster $Cluster --service-name $svcName --task-definition ultra-aggressive --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$($List[0]),$($List[1])],assignPublicIp=ENABLED}" --region $Region | Out-Null
}

Write-Host "✅ Ultra Aggressive deployed/updated." -ForegroundColor Green
