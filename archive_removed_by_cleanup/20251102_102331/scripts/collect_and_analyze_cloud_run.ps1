# Collect current Cloud Run services and analyze duplicates/overlaps
# Requires: gcloud CLI authenticated and active project set

param(
  [string]$ProjectId = "infinity-ai-5ec7c",
  [string]$Region = "us-central1",
  [string]$OutputJson = "reports/cloud_run_services.json"
)

Write-Host "Collecting Cloud Run services for $ProjectId ($Region) ..."
$ErrorActionPreference = "Stop"

# Ensure reports directory exists
$reportsDir = Split-Path -Parent $OutputJson
if (-not (Test-Path $reportsDir)) {
  New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
}

# Export services list
& gcloud run services list --platform managed --region $Region --project $ProjectId --format json | Out-File -Encoding utf8 $OutputJson

Write-Host "Analyzing duplicates and overlaps ..."
# Prefer repo Python for portability
$pythonCmd = "python"
try {
  & $pythonCmd --version | Out-Null
} catch {
  Write-Host "Python not found in PATH. Please run analysis manually: python scripts/analyze_cloud_run_duplicates.py $OutputJson"
  exit 1
}

& $pythonCmd scripts/analyze_cloud_run_duplicates.py $OutputJson

Write-Host "Done. See reports/cloud_run_duplicates_report.json and .md"