param(
  [switch]$Apply = $false,
  [switch]$DestroyFirst = $false,
  [string]$ConfigPath = "multi-cloud-config.json",
  [string]$AwsRegion = "us-east-1",
  [string]$GcpProject = "",
  [string]$GcpRegion = "us-central1",
  [string]$EcsCluster = "infinityai-pro-cluster"
)

Write-Host "=== InfinityAI.Pro Clean Redeploy Orchestrator ===" -ForegroundColor Cyan
Write-Host ("Mode: {0}" -f ($Apply ? 'APPLY' : 'DRY-RUN')) -ForegroundColor Yellow

function Test-Command($Name){ $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }

if (-not (Test-Path $ConfigPath)) { Write-Host "Config not found: $ConfigPath" -ForegroundColor Red; exit 1 }
$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json

# Collect endpoints
$albDns = $cfg.clouds.aws.services.load_balancer.dns
$engineAUrl = $cfg.clouds.google_cloud.services.engine_a.endpoint
$engineBUrl = $cfg.clouds.google_cloud.services.engine_b.endpoint
$engineCUrl = $cfg.clouds.aws.services.'engine_c'.endpoint
$engineDUrl = $cfg.clouds.aws.services.'engine_d'.endpoint
## Ultra Aggressive URL derivation no longer needed here; handled by service config

Write-Host "Planned endpoints:" -ForegroundColor Green
Write-Host "  Engine A: $engineAUrl" -ForegroundColor DarkGreen
Write-Host "  Engine B: $engineBUrl" -ForegroundColor DarkGreen
Write-Host "  Engine C: $engineCUrl" -ForegroundColor DarkGreen
Write-Host "  Engine D: $engineDUrl" -ForegroundColor DarkGreen
Write-Host "  ALB DNS : $albDns" -ForegroundColor DarkGreen

# Azure removed: skipping any Azure operations

#
# GCP: Engine B and Ultra-Aggressive updates
#
if (Test-Command gcloud -and $GcpProject) {
  Write-Host "\n[B] GCP: Cloud Run" -ForegroundColor Cyan
  $gcCmds = @()
  $gcCmds += "gcloud config set project $GcpProject"
  $gcCmds += "gcloud config set run/region $GcpRegion"
  $gcCmds += "gcloud run services update infinityai-engine-b --region $GcpRegion --port 8000 --platform managed"
  if ($engineCUrl) { $gcCmds += "gcloud run services update infinityai-ultra-aggressive --region $GcpRegion --set-env-vars ENGINE_C_URL=$engineCUrl --platform managed" }
  if ($Apply) { foreach ($c in $gcCmds) { Write-Host "RUN> $c" -ForegroundColor DarkCyan; try { Invoke-Expression $c 2>$null | Out-Null } catch { } } } else { $gcCmds | ForEach-Object { Write-Host "DRY> $_" -ForegroundColor DarkGray } }
} else { Write-Host "gcloud not found or project not provided; skipping GCP" -ForegroundColor DarkGray }

#
# AWS: ECS (Engine C/D), ALB, Frontend
#
if (Test-Command aws) {
  Write-Host "\n[C] AWS: ECS + ALB + Frontend" -ForegroundColor Cyan
  $awsCmds = @()
  # ECS: force new deployment or scale down/up
  if ($DestroyFirst) {
    $awsCmds += "aws ecs update-service --cluster $EcsCluster --service infinityai-engine-c-service --desired-count 0 --region $AwsRegion"
    $awsCmds += "aws ecs update-service --cluster $EcsCluster --service infinityai-engine-d-service --desired-count 0 --region $AwsRegion"
  }
  $awsCmds += "pwsh -NoProfile -ExecutionPolicy Bypass -File 'aws-fix/fix-task-definitions.ps1'"
  $awsCmds += "aws ecs update-service --cluster $EcsCluster --service infinityai-engine-c-service --force-new-deployment --region $AwsRegion"
  $awsCmds += "aws ecs update-service --cluster $EcsCluster --service infinityai-engine-d-service --force-new-deployment --region $AwsRegion"
  $awsCmds += "pwsh -NoProfile -ExecutionPolicy Bypass -File 'scripts/fix_aws_alb_rules.ps1' -Region $AwsRegion -ConfigPath $ConfigPath"

  # Frontend (S3 + CloudFront if permissions, else S3 website)
  if ($engineDUrl) {
    $awsCmds += ("pwsh -NoProfile -ExecutionPolicy Bypass -File 'scripts/deploy_frontend_aws.ps1' -Domain 'infinityai.pro' -Region '{0}' -FrontendDir 'infinityai-pro/frontend' -ApiBaseUrl '{1}'" -f $AwsRegion, $engineDUrl)
  }
  if ($Apply) { foreach ($c in $awsCmds) { Write-Host "RUN> $c" -ForegroundColor DarkCyan; try { Invoke-Expression $c } catch { } } } else { $awsCmds | ForEach-Object { Write-Host "DRY> $_" -ForegroundColor DarkGray } }
} else { Write-Host "AWS CLI not found; skipping AWS" -ForegroundColor DarkGray }

#
# Health check at the end
#
Write-Host "\n[D] Health Check" -ForegroundColor Cyan
if ($Apply) {
  try { pwsh -NoProfile -ExecutionPolicy Bypass -File "scripts/cloud_health_check.ps1" -AwsRegion $AwsRegion -GcpRegion $GcpRegion | Out-Null } catch { }
} else {
  Write-Host "DRY> scripts/cloud_health_check.ps1 -AwsRegion $AwsRegion -GcpRegion $GcpRegion" -ForegroundColor DarkGray
}

Write-Host ("=== Redeploy orchestrator finished (mode: {0}) ===" -f ($Apply ? 'APPLY' : 'DRY-RUN')) -ForegroundColor Green
