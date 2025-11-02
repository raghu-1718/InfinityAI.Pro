param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [switch]$DoWebhookTest,
  [string]$OutputFile = "scripts/verify-results-extended.json"
)

# Normalize output path relative to this script directory if not absolute
if (-not [System.IO.Path]::IsPathRooted($OutputFile)) {
  $OutputFile = Join-Path -Path $PSScriptRoot -ChildPath (Split-Path -Path $OutputFile -Leaf)
}
try {
  $outDir = Split-Path -Path $OutputFile -Parent
  if (-not (Test-Path -Path $outDir)) { New-Item -Path $outDir -ItemType Directory -Force | Out-Null }
} catch {}

$checks = @(
  @{ name="engine-d-status"; url="$BaseUrl/engine-d/status"; method="GET" },
  @{ name="engine-d-health"; url="$BaseUrl/engine-d/health"; method="GET" },
  @{ name="engine-c-health"; url="$BaseUrl/engine-c/health"; method="GET" },
  @{ name="dhan-status-proxy"; url="$BaseUrl/engine-d/user/broker/dhan/status"; method="GET" },
  @{ name="dhan-token-proxy"; url="$BaseUrl/engine-d/user/broker/dhan/token"; method="POST"; body='{"dry_run":true}' }
)

$results = @{}

foreach ($c in $checks) {
  try {
    if ($c.method -eq "GET") {
      $r = Invoke-WebRequest -Uri $c.url -Method GET -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
      $status = $r.StatusCode
    } else {
      $r = Invoke-WebRequest -Uri $c.url -Method POST -Body $c.body -ContentType "application/json" -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
      $status = $r.StatusCode
    }
    $results[$c.name] = @{ ok = $true; status = $status; url = $c.url }
  } catch {
    $results[$c.name] = @{ ok = $false; error = $_.Exception.Message; url = $c.url }
  }
}

if ($DoWebhookTest) {
  $webhookUrl = "$BaseUrl/engine-c/webhooks/dhan/postback"
  $sample = @{
    event = "TEST_ORDER_UPDATE"
    source = "verify-backend-extended"
    timestamp = (Get-Date).ToString("o")
    payload = @{
      order_id = "TEST-0001"
      status = "validation"
      details = "This is a non-executing verification payload. No side effects expected."
    }
  } | ConvertTo-Json -Depth 10

  try {
    $r = Invoke-WebRequest -Uri $webhookUrl -Method POST -Body $sample -ContentType "application/json" -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    $results["webhook-test"] = @{ ok = $true; status = $r.StatusCode; url = $webhookUrl }
  } catch {
    $results["webhook-test"] = @{ ok = $false; error = $_.Exception.Message; url = $webhookUrl }
  }
}

$results | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $OutputFile
Write-Host "Verification complete — results written to $OutputFile"
$results | ConvertTo-Json -Depth 5
