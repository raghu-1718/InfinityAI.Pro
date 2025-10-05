# Update ECS Task Definitions with correct port mappings
$region = "us-east-1"
$cluster = "infinityai-pro-cluster"

Write-Host "Updating Engine C task definition..." -ForegroundColor Cyan

# Create new task definition for Engine C with port 8000
$taskDefC = @"
{
  "family": "infinityai-engine-c",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::152687308610:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "infinityai-engine-c",
      "image": "152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:infinityai-engine-c",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "PORT",
          "value": "8000"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
"@

$taskDefC | Out-File -FilePath "engine-c-task.json" -Encoding UTF8

Write-Host "Updating Engine D task definition..." -ForegroundColor Cyan

# Create new task definition for Engine D with port 8004  
$taskDefD = @"
{
  "family": "infinityai-engine-d",
  "networkMode": "awsvpc", 
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::152687308610:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "infinityai-engine-d",
      "image": "152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:infinityai-engine-d",
      "portMappings": [
        {
          "containerPort": 8004,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "PORT",
          "value": "8004"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8004/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
"@

$taskDefD | Out-File -FilePath "engine-d-task.json" -Encoding UTF8

# Register new task definitions
aws ecs register-task-definition --cli-input-json file://engine-c-task.json --region $region
aws ecs register-task-definition --cli-input-json file://engine-d-task.json --region $region

# Update services to use new task definitions
aws ecs update-service --cluster $cluster --service infinityai-engine-c-service --task-definition infinityai-engine-c --region $region
aws ecs update-service --cluster $cluster --service infinityai-engine-d-service --task-definition infinityai-engine-d --region $region

Write-Host "Task definitions updated successfully!" -ForegroundColor Green