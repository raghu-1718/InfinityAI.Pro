param(
  [string]$ProjectId = "infinity-ai-5ec7c",
  [string]$Region = "us-central1",
  [switch]$IncludeExtensions,
  [switch]$PurgeArtifactRegistry,
  [switch]$PurgeSecrets,
  [switch]$NoPrompt,
  [switch]$DeployEngines,
  [switch]$DeployFunctions
)

$ErrorActionPreference = 'Stop'

function Write-Section($title) {
  Write-Host "`n==== $title ====" -ForegroundColor Cyan
}

function New-OutDirIfMissing {
  $outDir = Join-Path -Path $PSScriptRoot -ChildPath 'out'
  if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
  return $outDir
}

function Confirm-Action($message) {
  if ($NoPrompt) { return $true }
  $choice = Read-Host "$message [y/N]"
  return ($choice -match '^(?i)y')
}

Write-Section "Context"
Write-Host "Project: $ProjectId"
Write-Host "Region : $Region"

$outDir = New-OutDirIfMissing
$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$inventoryPath = Join-Path $outDir "inventory_$timestamp.json"

Write-Section "Inventorying Cloud Run services"
$runServicesJson = gcloud run services list --project $ProjectId --platform=managed --region $Region --format=json
$runServices = $null
if ($runServicesJson) { $runServices = $runServicesJson | ConvertFrom-Json } else { $runServices = @() }

Write-Host ("Found {0} Cloud Run services" -f $runServices.Count)

Write-Section "Inventorying Cloud Functions (Gen2)"
$functionsJson = gcloud functions list --project $ProjectId --regions=$Region --format=json
$functions = $null
if ($functionsJson) { $functions = $functionsJson | ConvertFrom-Json } else { $functions = @() }
Write-Host ("Found {0} Cloud Functions" -f $functions.Count)

# Build deletion lists
$engineServiceNames = @(
  'infinityai-engine-a',
  'infinityai-engine-b',
  'infinityai-engine-c',
  'infinityai-engine-c-execution',
  'infinityai-engine-d',
  'infinityai-frontend'
)

$runServicesToDelete = @()
foreach ($s in $runServices) {
  $name = $s.metadata.name
  $labels = $s.metadata.labels
  $managedBy = if ($labels) { $labels.'goog-managed-by' } else { $null }

  if ($engineServiceNames -contains $name) {
    $runServicesToDelete += $name
    continue
  }

  # Delete Cloud Functions backends (Run services managed by cloudfunctions).
  if ($managedBy -eq 'cloudfunctions') {
    if (-not $IncludeExtensions) {
      if ($name -like 'ext-*') { continue }
    }
    $runServicesToDelete += $name
  }
}
$runServicesToDelete = $runServicesToDelete | Sort-Object -Unique

$functionsToDelete = @()
foreach ($f in $functions) {
  $fname = $f.name
  if (-not $IncludeExtensions) {
    if ($fname -like 'ext-*') { continue }
  }
  $functionsToDelete += $fname
}
$functionsToDelete = $functionsToDelete | Sort-Object -Unique

# Save inventory snapshot
$inventory = [ordered]@{
  project = $ProjectId
  region = $Region
  timestamp = $timestamp
  runServices = $runServices
  functions = $functions
  deletePlan = [ordered]@{
    runServices = $runServicesToDelete
    functions = $functionsToDelete
  }
}
$inventory | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $inventoryPath
Write-Host "Inventory saved to $inventoryPath" -ForegroundColor Green

Write-Section "Delete Plan"
Write-Host "Cloud Run services to delete (count=$($runServicesToDelete.Count)):"
$runServicesToDelete | ForEach-Object { Write-Host "  - $_" }
Write-Host "Cloud Functions to delete (count=$($functionsToDelete.Count)):"
$functionsToDelete | ForEach-Object { Write-Host "  - $_" }

if (-not (Confirm-Action "Proceed with deletion?")) {
  Write-Host "Aborted by user." -ForegroundColor Yellow
  exit 1
}

Write-Section "Deleting Cloud Run services"
foreach ($name in $runServicesToDelete) {
  Write-Host "Deleting Run service: $name"
  gcloud run services delete $name --project $ProjectId --region $Region --quiet || Write-Warning "Failed to delete $name (continuing)"
}

Write-Section "Deleting Cloud Functions"
foreach ($fname in $functionsToDelete) {
  Write-Host "Deleting Function: $fname"
  gcloud functions delete $fname --project $ProjectId --region $Region --quiet || Write-Warning "Failed to delete $fname (continuing)"
}

if ($PurgeArtifactRegistry) {
  Write-Section "Purging Artifact Registry (opt-in)"
  $reposJson = gcloud artifacts repositories list --project $ProjectId --location=$Region --format=json
  $repos = @()
  if ($reposJson) { $repos = $reposJson | ConvertFrom-Json }
  foreach ($repo in $repos) {
    $rname = $repo.name.Split('/')[-1]
    Write-Host "Deleting Artifact Registry repo: $rname"
    gcloud artifacts repositories delete $rname --project $ProjectId --location=$Region --quiet || Write-Warning "Failed to delete repo $rname (continuing)"
  }
}

if ($PurgeSecrets) {
  Write-Section "Purging Secret Manager secrets (opt-in)"
  $secretsJson = gcloud secrets list --project $ProjectId --format=json
  $secrets = @()
  if ($secretsJson) { $secrets = $secretsJson | ConvertFrom-Json }
  foreach ($s in $secrets) {
    $sname = $s.name.Split('/')[-1]
    Write-Host "Deleting secret: $sname"
    gcloud secrets delete $sname --project $ProjectId --quiet || Write-Warning "Failed to delete secret $sname (continuing)"
  }
}

if ($DeployEngines) {
  Write-Section "Re-deploying engines (A, B, C-execution, D, Frontend)"
  $root = Resolve-Path (Join-Path $PSScriptRoot '..')

  Push-Location (Join-Path $root 'engines/engine-a')
  Write-Host "Deploying infinityai-engine-a..."
  gcloud run deploy infinityai-engine-a --source . --project $ProjectId --region $Region --allow-unauthenticated
  if ($LASTEXITCODE -ne 0) { throw "Deploy engine-a failed" }
  Pop-Location

  Push-Location (Join-Path $root 'engines/engine-b')
  Write-Host "Deploying infinityai-engine-b..."
  gcloud run deploy infinityai-engine-b --source . --project $ProjectId --region $Region --allow-unauthenticated `
    --set-secrets="GEMINI_API_KEY_PRIMARY=gemini-api-key-primary:latest,GEMINI_API_KEY_SECONDARY=gemini-api-key-secondary:latest"
  if ($LASTEXITCODE -ne 0) { throw "Deploy engine-b failed" }
  Pop-Location

  Push-Location (Join-Path $root 'engines/engine-c-execution')
  Write-Host "Deploying infinityai-engine-c-execution (private)..."
  gcloud run deploy infinityai-engine-c-execution --source . --project $ProjectId --region $Region --no-allow-unauthenticated
  if ($LASTEXITCODE -ne 0) { throw "Deploy engine-c-execution failed" }
  Pop-Location

  Push-Location (Join-Path $root 'engines/engine-d')
  Write-Host "Deploying infinityai-engine-d..."
  gcloud run deploy infinityai-engine-d --source . --project $ProjectId --region $Region --allow-unauthenticated
  if ($LASTEXITCODE -ne 0) { throw "Deploy engine-d failed" }
  Pop-Location

  Push-Location (Join-Path $root 'frontend')
  Write-Host "Deploying infinityai-frontend..."
  gcloud run deploy infinityai-frontend --source . --project $ProjectId --region $Region --allow-unauthenticated
  if ($LASTEXITCODE -ne 0) { throw "Deploy frontend failed" }
  Pop-Location
}

if ($DeployFunctions) {
  Write-Section "Deploying Firebase Functions (optional)"
  $root = Resolve-Path (Join-Path $PSScriptRoot '..')
  $functionsDir = Join-Path $root 'functions'
  Push-Location $functionsDir
  if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "Installing firebase-tools globally..."
    npm i -g firebase-tools | Out-Null
  }
  npm ci | Out-Null
  firebase deploy --only functions --project $ProjectId --non-interactive
  if ($LASTEXITCODE -ne 0) { throw "Firebase Functions deploy failed" }
  Pop-Location
}

Write-Section "Done"
Write-Host "Reset completed. Inventory: $inventoryPath" -ForegroundColor Green
