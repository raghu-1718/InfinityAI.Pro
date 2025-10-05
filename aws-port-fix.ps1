# AWS ECS Port Fix Script
# This script fixes the port mismatch issue for InfinityAI engines in AWS ECS

Write-Host "🔧 AWS ECS Port Fix Script" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Issue: Engine C is running on port 8003 but ALB expects port 8000
# Solution: Update task definition to use port 8003

$CLUSTER_NAME = "infinityai-pro-cluster"
$ENGINE_C_SERVICE = "infinityai-engine-c-service"
$ENGINE_D_SERVICE = "infinityai-engine-d-service"
$REGION = "us-east-1"

Write-Host "🔍 Current issue: Engine C running on port 8003, but configured for 8000" -ForegroundColor Yellow

# First, let's get the current task definition
Write-Host "`n📋 Getting current task definition for Engine C..." -ForegroundColor Green
$taskDef = aws ecs describe-task-definition --task-definition infinityai-engine-c:5 --region $REGION | ConvertFrom-Json

if ($taskDef) {
    Write-Host "✅ Current task definition found" -ForegroundColor Green
    
    # Update port mapping from 8000 to 8003
    $taskDef.taskDefinition.containerDefinitions[0].portMappings[0].containerPort = 8003
    $taskDef.taskDefinition.containerDefinitions[0].portMappings[0].hostPort = 8003
    
    # Update environment variable
    foreach ($env in $taskDef.taskDefinition.containerDefinitions[0].environment) {
        if ($env.name -eq "PORT") {
            $env.value = "8003"
        }
    }
    
    # Update health check command to use port 8003
    $taskDef.taskDefinition.containerDefinitions[0].healthCheck.command[1] = "curl -f http://localhost:8003/health || exit 1"
    
    Write-Host "🔄 Updated container port mapping: 8000 → 8003" -ForegroundColor Yellow
    Write-Host "🔄 Updated PORT environment variable: 8000 → 8003" -ForegroundColor Yellow
    Write-Host "🔄 Updated health check endpoint: 8000 → 8003" -ForegroundColor Yellow
} else {
    Write-Host "❌ Failed to get task definition" -ForegroundColor Red
    exit 1
}

# Now check the target group to update port
Write-Host "`n🎯 Checking target group configuration..." -ForegroundColor Green
$targetGroup = aws elbv2 describe-target-groups --target-group-arns "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683" --region $REGION | ConvertFrom-Json

if ($targetGroup) {
    $currentPort = $targetGroup.TargetGroups[0].Port
    Write-Host "📊 Current target group port: $currentPort" -ForegroundColor Cyan
    
    if ($currentPort -ne 8003) {
        Write-Host "⚠️  Target group needs to be updated to port 8003" -ForegroundColor Yellow
        Write-Host "💡 Manual action required: Update target group port via AWS Console or CLI" -ForegroundColor Magenta
    }
}

Write-Host "`n🚀 Options to fix this issue:" -ForegroundColor Green
Write-Host "1. Update Engine C application to run on port 8000 (requires code change)" -ForegroundColor White
Write-Host "2. Update AWS infrastructure to expect port 8003 (target group + ALB)" -ForegroundColor White
Write-Host "3. Recreate task definition with correct port mapping" -ForegroundColor White

Write-Host "`n📝 Recommended immediate fix:" -ForegroundColor Yellow
Write-Host "aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683 --port 8003 --region us-east-1" -ForegroundColor Cyan

Write-Host "`n✨ Engine D is correctly configured (port 8000) and should work once Engine C is fixed!" -ForegroundColor Green

Write-Host "`n🔧 Running the target group fix now..." -ForegroundColor Magenta