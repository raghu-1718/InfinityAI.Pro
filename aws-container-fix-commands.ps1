# AWS ECS Container Image Fix Commands
# Critical Issue: Both Engine C and D are running nginx:alpine instead of actual applications
# This script will update the task definitions with correct container images

Write-Host "=== AWS ECS Container Image Fix Commands ===" -ForegroundColor Cyan
Write-Host "CRITICAL: Both engines are running nginx:alpine instead of actual applications" -ForegroundColor Red
Write-Host ""

# Step 1: Download current task definitions
Write-Host "Step 1: Download current task definitions" -ForegroundColor Yellow
Write-Host "aws ecs describe-task-definition --task-definition infinityai-engine-c-task --query 'taskDefinition' > engine-c-task-def.json"
Write-Host "aws ecs describe-task-definition --task-definition infinityai-engine-d-task --query 'taskDefinition' > engine-d-task-def.json"
Write-Host ""

# Step 2: Review current container configurations
Write-Host "Step 2: Current problematic configurations:" -ForegroundColor Yellow
Write-Host "Engine C Task ARN: arn:aws:ecs:us-east-1:152687308610:task/infinityai-pro-cluster/519d0dd6a97f45dfbe1c790fc7423d68"
Write-Host "Engine C Private IP: 172.31.28.133"
Write-Host "Engine C Current Image: nginx:alpine (WRONG - should be trading application)"
Write-Host "Engine C Port Mismatch: Target group port 8000, app should run on 8003"
Write-Host ""
Write-Host "Engine D Task ARN: arn:aws:ecs:us-east-1:152687308610:task/infinityai-pro-cluster/9fb1ee31c3744254971f1d7220374b44"
Write-Host "Engine D Private IP: 172.31.69.72"
Write-Host "Engine D Current Image: nginx:alpine (WRONG - should be AI chatbot application)"
Write-Host "Engine D Port: 8004 (correct)"
Write-Host ""

# Step 3: Create corrected task definitions
Write-Host "Step 3: Create corrected task definitions" -ForegroundColor Yellow
Write-Host "You need to modify the downloaded JSON files with correct container images:"
Write-Host ""
Write-Host "For Engine C (Trade Execution):" -ForegroundColor Green
Write-Host "- Replace 'nginx:alpine' with your actual trading application image"
Write-Host "- Ensure container port mapping is 8003:8003"
Write-Host "- Add environment variables for trading functionality"
Write-Host "- Example image: 'your-registry/infinityai-engine-c:latest'"
Write-Host ""
Write-Host "For Engine D (AI Chatbot):" -ForegroundColor Green
Write-Host "- Replace 'nginx:alpine' with your actual AI chatbot application image"
Write-Host "- Ensure container port mapping is 8004:8004"
Write-Host "- Add environment variables for AI functionality"
Write-Host "- Example image: 'your-registry/infinityai-engine-d:latest'"
Write-Host ""

# Step 4: Register new task definitions
Write-Host "Step 4: Register updated task definitions" -ForegroundColor Yellow
Write-Host "aws ecs register-task-definition --cli-input-json file://engine-c-task-def-fixed.json"
Write-Host "aws ecs register-task-definition --cli-input-json file://engine-d-task-def-fixed.json"
Write-Host ""

# Step 5: Update services to use new task definitions
Write-Host "Step 5: Update services with new task definitions" -ForegroundColor Yellow
Write-Host "aws ecs update-service --cluster infinityai-pro-cluster --service infinityai-engine-c-service --task-definition infinityai-engine-c-task:NEW_REVISION"
Write-Host "aws ecs update-service --cluster infinityai-pro-cluster --service infinityai-engine-d-service --task-definition infinityai-engine-d-task:NEW_REVISION"
Write-Host ""

# Step 6: Fix target group port for Engine C
Write-Host "Step 6: Fix target group port mismatch for Engine C" -ForegroundColor Yellow
Write-Host "# Current: Target group expects port 8000, but app should run on 8003"
Write-Host "aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683 --port 8003"
Write-Host ""

# Step 7: Wait for deployment and verify
Write-Host "Step 7: Wait for deployment and verify" -ForegroundColor Yellow
Write-Host "aws ecs wait services-stable --cluster infinityai-pro-cluster --services infinityai-engine-c-service infinityai-engine-d-service"
Write-Host ""
Write-Host "# Verify new tasks are running with correct images:"
Write-Host "aws ecs describe-tasks --cluster infinityai-pro-cluster --tasks \$(aws ecs list-tasks --cluster infinityai-pro-cluster --service-name infinityai-engine-c-service --query 'taskArns[0]' --output text)"
Write-Host "aws ecs describe-tasks --cluster infinityai-pro-cluster --tasks \$(aws ecs list-tasks --cluster infinityai-pro-cluster --service-name infinityai-engine-d-service --query 'taskArns[0]' --output text)"
Write-Host ""

# Step 8: After containers are fixed, apply load balancer routing
Write-Host "Step 8: After containers are fixed, apply load balancer routing (run aws-fix-commands.ps1)" -ForegroundColor Yellow
Write-Host "Note: You must run the IAM permission fixes and load balancer routing configuration"
Write-Host "from aws-fix-commands.ps1 after the containers are properly deployed."
Write-Host ""

Write-Host "=== CRITICAL CONTAINER IMAGES NEEDED ===" -ForegroundColor Red
Write-Host "Before running these commands, you MUST have the following container images ready:"
Write-Host ""
Write-Host "Engine C (Trade Execution):" -ForegroundColor Yellow
Write-Host "- Function: trade_execution"
Write-Host "- Required endpoints: /health, /trade"
Write-Host "- Port: 8003"
Write-Host "- Image: your-registry/infinityai-engine-c:latest"
Write-Host ""
Write-Host "Engine D (AI Chatbot):" -ForegroundColor Yellow
Write-Host "- Function: ai_chatbot_assistant"
Write-Host "- Required endpoints: /health, /chat"
Write-Host "- Port: 8004"
Write-Host "- Image: your-registry/infinityai-engine-d:latest"
Write-Host ""
Write-Host "If you don't have these images, you need to:"
Write-Host "1. Build your trading and AI applications"
Write-Host "2. Push them to ECR or another registry"
Write-Host "3. Update the task definition JSON files with correct image URIs"
Write-Host ""
Write-Host "=== END OF CONTAINER FIX SCRIPT ===" -ForegroundColor Cyan