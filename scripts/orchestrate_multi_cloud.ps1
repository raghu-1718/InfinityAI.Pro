# Orchestrate InfinityAI.Pro multi-cloud verification and light fixes
param(
  [string]$AwsRegion = "us-east-1",
  [string]$GcpRegion = "us-central1",
  [string]$GcpProject = ""
)

Write-Host "=== InfinityAI.Pro Multi-Cloud Orchestrator ===" -ForegroundColor Cyan

function Test-Command($Name){ $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }

# Azure steps removed (environment is AWS + GCP only)

# 2) GCP: ensure engine-b uses the correct port (8000)
if (Test-Command gcloud -and $GcpProject) {
  try {
    gcloud config set project $GcpProject 2>$null | Out-Null
    gcloud config set run/region $GcpRegion 2>$null | Out-Null
  Write-Host "GCP: updating Cloud Run service infinityai-engine-b to port 8000" -ForegroundColor Yellow
  gcloud run services update infinityai-engine-b --region $GcpRegion --port 8000 --platform managed | Out-Null
  } catch { Write-Host "GCP step skipped: $($_.Exception.Message)" -ForegroundColor DarkGray }
} else { Write-Host "GCloud not found or project not provided; skipping GCP step" -ForegroundColor DarkGray }

# 3) Consolidated health check (AWS/GCP/K8s)
$healthArgs = @("-AwsRegion", $AwsRegion, "-GcpRegion", $GcpRegion)
Write-Host "Running consolidated health check..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File "scripts\cloud_health_check.ps1" @healthArgs

# 4) Wire frontend with engine endpoints
Write-Host "Wiring frontend environment with engine endpoints..." -ForegroundColor Cyan

$engineAUrl = $null
$engineBUrl = $null
$engineCUrl = $null
$engineDUrl = $null
$ultraUrl  = $null

# Engine A now on GCP, not Azure

try {
  if (Test-Command gcloud -and $GcpProject) {
    gcloud config set project $GcpProject 2>$null | Out-Null
    $engineBUrl = gcloud run services describe infinityai-engine-b --platform managed --region $GcpRegion --format='value(status.url)' 2>$null
    $ultraUrl   = gcloud run services describe infinityai-ultra-aggressive --platform managed --region $GcpRegion --format='value(status.url)' 2>$null
  }
} catch {}

try {
  # Prefer multi-cloud-config.json for AWS endpoints
  $cfgPath = Join-Path (Get-Location) 'multi-cloud-config.json'
  if (Test-Path $cfgPath) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    $awsServices = $cfg.clouds.aws.services
    if ($awsServices.'engine_c'.endpoint) { $engineCUrl = $awsServices.'engine_c'.endpoint }
    if ($awsServices.'engine_d'.endpoint) { $engineDUrl = $awsServices.'engine_d'.endpoint }
  }
} catch {}

# Azure frontend wiring removed; frontend is on AWS S3/CloudFront

Write-Host "=== Orchestration complete. See cloud_health_report.json for results. ===" -ForegroundColor Green
