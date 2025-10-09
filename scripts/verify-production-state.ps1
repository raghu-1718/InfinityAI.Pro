<#
Verifies multi-cloud production deployment state.
Requirements: aws, gcloud, curl (Invoke-RestMethod), jq (optional) available & authenticated.
#>
param(
  [string]$BaseUrl = "https://infinityai.pro",
  [string]$AwsRegion = "us-east-1",
  [string]$GcpProject = "after-yesterday-473512-k3",
  [string]$GcpRegion = "us-central1",
  [string[]]$CloudRunServices = @('infinityai-engine-a','infinityai-engine-b','infinityai-ultra-aggressive'),
  [string[]]$EcsServices = @('infinityai-engine-c-service','infinityai-engine-d-service'),
  [string]$Cluster = "infinityai-pro-cluster",
  [switch]$Json
)

function Out-Section($title){ Write-Host "`n=== $title ===" -ForegroundColor Cyan }

$results = [ordered]@{}

# Cloud Run services
Out-Section "Cloud Run"
$crState = @()
foreach($svc in $CloudRunServices){
  try {
    $desc = gcloud run services describe $svc --region $GcpRegion --project $GcpProject --format json | ConvertFrom-Json
    $rev = $desc.status.latestReadyRevisionName
    $url = $desc.status.url
    $crState += [pscustomobject]@{service=$svc; revision=$rev; url=$url}
    Write-Host "✔ $svc revision=$rev" -ForegroundColor Green
  } catch { Write-Host "✖ $svc ($_)" -ForegroundColor Red }
}
$results.CloudRun = $crState

# ECS services
Out-Section "ECS"
try {
  $ecs = aws ecs describe-services --cluster $Cluster --services ($EcsServices -join ' ') --query 'services[].{service:serviceName,taskDef:taskDefinition,desired:desiredCount,running:runningCount,status:status}' --output json | ConvertFrom-Json
  foreach($s in $ecs){
    $ok = ($s.running -eq $s.desired)
    if($ok){
      Write-Host ("✔ {0} running={1}/desired={2}" -f $s.service, $s.running, $s.desired) -ForegroundColor Green
    } else {
      Write-Host ("✖ {0} running={1}/desired={2}" -f $s.service, $s.running, $s.desired) -ForegroundColor Red
    }
  }
  $results.ECS = $ecs
} catch { Write-Host "✖ ECS describe failed: $_" -ForegroundColor Red }

# Health endpoint
Out-Section "Engine D Status"
try {
  $status = Invoke-RestMethod -Uri "$BaseUrl/engine-d/status" -Method GET -TimeoutSec 20
  $overall = $status.status
  Write-Host "Overall: $overall" -ForegroundColor Green
  $results.EngineDStatus = $status
} catch { Write-Host "✖ Status endpoint failed: $_" -ForegroundColor Red }

if($Json){ $results | ConvertTo-Json -Depth 6 } else { Write-Host "`nDone." -ForegroundColor Cyan }
