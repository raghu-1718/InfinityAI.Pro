# Update ECS Task Definitions with correct port mappings
$region = "us-east-1"
$cluster = "infinityai-pro-cluster"

# Read endpoints from multi-cloud-config.json
$cfgPath = Join-Path (Split-Path -Parent $PSCommandPath) "..\multi-cloud-config.json" | Resolve-Path -ErrorAction SilentlyContinue
$engineAUrl = $null; $engineBUrl = $null; $engineCUrl = $null; $engineDUrl = $null
if ($cfgPath) {
  try {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    # Engine A now runs on GCP Cloud Run (Azure removed)
    $engineAUrl = $cfg.clouds.google_cloud.services.engine_a.endpoint
    $engineBUrl = $cfg.clouds.google_cloud.services.engine_b.endpoint
    $engineCUrl = $cfg.clouds.aws.services.'engine_c'.endpoint
    $engineDUrl = $cfg.clouds.aws.services.'engine_d'.endpoint
  } catch { }
}
Write-Host "Resolved endpoints:" -ForegroundColor Yellow
Write-Host ("  A: {0}" -f ($engineAUrl ?? '-')) -ForegroundColor DarkYellow
Write-Host ("  B: {0}" -f ($engineBUrl ?? '-')) -ForegroundColor DarkYellow
Write-Host ("  C: {0}" -f ($engineCUrl ?? '-')) -ForegroundColor DarkYellow
Write-Host ("  D: {0}" -f ($engineDUrl ?? '-')) -ForegroundColor DarkYellow

Write-Host "Updating Engine C task definition..." -ForegroundColor Cyan

# Build Engine C task definition object with env vars
$envC = @(
  @{ name = 'PORT'; value = '8000' }
)
if ($engineAUrl) { $envC += @{ name = 'ENGINE_A_URL'; value = $engineAUrl } }
if ($engineBUrl) { $envC += @{ name = 'ENGINE_B_URL'; value = $engineBUrl } }
if ($engineDUrl) { $envC += @{ name = 'ENGINE_D_URL'; value = $engineDUrl } }

$taskDefCObj = [ordered]@{
  family = 'infinityai-engine-c'
  networkMode = 'awsvpc'
  requiresCompatibilities = @('FARGATE')
  cpu = '512'
  memory = '1024'
  executionRoleArn = 'arn:aws:iam::152687308610:role/ecsTaskExecutionRole'
  containerDefinitions = @(
    [ordered]@{
      name = 'infinityai-engine-c'
      image = '152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:infinityai-engine-c'
      portMappings = @(@{ containerPort = 8000; protocol = 'tcp' })
      essential = $true
      environment = $envC
      healthCheck = @{ command = @('CMD-SHELL','curl -f http://localhost:8000/health || exit 1'); interval = 30; timeout = 5; retries = 3 }
    }
  )
}

($taskDefCObj | ConvertTo-Json -Depth 10) | Out-File -FilePath 'engine-c-task.json' -Encoding UTF8

Write-Host "Updating Engine D task definition..." -ForegroundColor Cyan

# Build Engine D task definition object with env vars
$envD = @(
  @{ name = 'PORT'; value = '8004' }
)
if ($engineAUrl) { $envD += @{ name = 'ENGINE_A_URL'; value = $engineAUrl } }
if ($engineBUrl) { $envD += @{ name = 'ENGINE_B_URL'; value = $engineBUrl } }
if ($engineCUrl) { $envD += @{ name = 'ENGINE_C_URL'; value = $engineCUrl } }

$taskDefDObj = [ordered]@{
  family = 'infinityai-engine-d'
  networkMode = 'awsvpc'
  requiresCompatibilities = @('FARGATE')
  cpu = '512'
  memory = '1024'
  executionRoleArn = 'arn:aws:iam::152687308610:role/ecsTaskExecutionRole'
  containerDefinitions = @(
    [ordered]@{
      name = 'infinityai-engine-d'
      image = '152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:infinityai-engine-d'
      portMappings = @(@{ containerPort = 8004; protocol = 'tcp' })
      essential = $true
      environment = $envD
      healthCheck = @{ command = @('CMD-SHELL','curl -f http://localhost:8004/health || exit 1'); interval = 30; timeout = 5; retries = 3 }
    }
  )
}

($taskDefDObj | ConvertTo-Json -Depth 10) | Out-File -FilePath 'engine-d-task.json' -Encoding UTF8

# Register new task definitions
aws ecs register-task-definition --cli-input-json file://engine-c-task.json --region $region
aws ecs register-task-definition --cli-input-json file://engine-d-task.json --region $region

# Update services to use new task definitions
aws ecs update-service --cluster $cluster --service infinityai-engine-c-service --task-definition infinityai-engine-c --region $region
aws ecs update-service --cluster $cluster --service infinityai-engine-d-service --task-definition infinityai-engine-d --region $region

Write-Host "Task definitions updated successfully!" -ForegroundColor Green