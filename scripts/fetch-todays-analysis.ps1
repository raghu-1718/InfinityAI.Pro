
param(
  [Parameter(Mandatory = $true)][string]$BaseUrl,
  [string]$Symbol = 'NIFTY',
  [string]$OutputFile = 'scripts/todays-analysis.json'
)

$ErrorActionPreference = 'Stop'

function Get-Json($url) {
  try {
    $r = Invoke-WebRequest -Uri $url -Method GET -Headers @{ 'Accept' = 'application/json' } -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    try {
      $data = $r.Content | ConvertFrom-Json
    } catch {
      $data = @{ raw = ($r.Content | Out-String).Trim() }
    }
    return @{ ok=$true; status=$r.StatusCode; url=$url; data=$data }
  } catch {
    return @{ ok=$false; url=$url; error=$_.Exception.Message }
  }
}

$results = @{}

# Engine D proxied endpoints first
$results.chart = Get-Json "${BaseUrl}/engine-d/chart/${Symbol}?timeframe=1D"
$results.overview = Get-Json "${BaseUrl}/engine-d/market/overview"
$results.insights = Get-Json "${BaseUrl}/engine-d/insights"

# Fallback to Engine A/B direct if needed (best effort)
if (-not $results.chart.ok) { $results.chart_fallback = Get-Json "https://infinityai-engine-a-429140669077.us-central1.run.app/chart/${Symbol}?timeframe=1D" }
if (-not $results.overview.ok) { $results.overview_fallback = Get-Json "https://infinityai-engine-a-429140669077.us-central1.run.app/market/overview" }
if (-not $results.insights.ok) { $results.insights_fallback = Get-Json "https://infinityai-engine-b-429140669077.us-central1.run.app/insights" }

# Save
if (-not [System.IO.Path]::IsPathRooted($OutputFile)) { $OutputFile = Join-Path -Path $PSScriptRoot -ChildPath (Split-Path -Path $OutputFile -Leaf) }
try { $outDir = Split-Path -Path $OutputFile -Parent; if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null } } catch {}

$results | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $OutputFile
Write-Host "Wrote analysis to $OutputFile"
