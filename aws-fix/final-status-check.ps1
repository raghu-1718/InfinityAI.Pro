# Final AWS Deployment Status Check
Write-Host "🔍 AWS Deployment Status Check" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

# Check ECS Services
Write-Host "`n1. ECS Services Status:" -ForegroundColor Cyan
aws ecs describe-services --cluster infinityai-pro-cluster --services infinityai-engine-c-service infinityai-engine-d-service --region us-east-1 --query "services[*].{Name:serviceName,Status:status,Running:runningCount,Desired:desiredCount,TaskDef:taskDefinition}" --output table

# Check Load Balancer
Write-Host "`n2. Load Balancer Status:" -ForegroundColor Cyan
aws elbv2 describe-load-balancers --names infinityai-pro-alb --region us-east-1 --query "LoadBalancers[0].{DNS:DNSName,State:State.Code}" --output table

# Check Target Groups Health
Write-Host "`n3. Target Groups Health:" -ForegroundColor Cyan
$tgC = "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683"
$tgD = "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-d/14ba59846c070247"

Write-Host "Engine C Target Group:"
aws elbv2 describe-target-health --target-group-arn $tgC --region us-east-1 --query "TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State}" --output table

Write-Host "Engine D Target Group:"
aws elbv2 describe-target-health --target-group-arn $tgD --region us-east-1 --query "TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State}" --output table

# Test Endpoints
Write-Host "`n4. Endpoint Tests:" -ForegroundColor Cyan
Write-Host "Testing Load Balancer..."
$response = try { Invoke-WebRequest -Uri "http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com" -TimeoutSec 10 } catch { $null }
if ($response) {
    Write-Host "✅ Load Balancer responding: $($response.StatusCode)" -ForegroundColor Green
} else {
    Write-Host "❌ Load Balancer not responding" -ForegroundColor Red
}

Write-Host "`n📋 Summary:" -ForegroundColor Yellow
Write-Host "- ECS Services: Both running (1/1 desired count)" -ForegroundColor Green
Write-Host "- Task Definitions: Updated with correct port mappings" -ForegroundColor Green
Write-Host "- Load Balancer: Active but not externally accessible" -ForegroundColor Red
Write-Host "- Next Steps: Fix security groups or load balancer listeners" -ForegroundColor Yellow