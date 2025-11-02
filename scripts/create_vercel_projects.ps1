param(
  [string]$RepoSlug = "raghu-1718/InfinityAI.Pro",
  [string]$EngineCName = "infinityai-engine-c",
  [string]$EngineCRoot = "engines/engine-c-execution",
  [string]$EngineDName = "infinityai-engine-d",
  [string]$EngineDRoot = "engines/engine-d"
)

Write-Host "\n=== Create Vercel Projects (Engine C & D) ===" -ForegroundColor Cyan

$ErrorActionPreference = 'Stop'

# 1) Resolve credentials
$vercelToken = $env:VERCEL_TOKEN
$orgId = $env:VERCEL_ORG_ID
if (-not $vercelToken) {
  $vercelToken = Read-Host -AsSecureString "Enter Vercel Token (from https://vercel.com/account/tokens)" | ForEach-Object { [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($_)) }
}
if (-not $orgId) {
  $orgId = Read-Host "Enter Vercel Org/Team ID (Settings > General > Team ID)"
}

if (-not $vercelToken -or -not $orgId) {
  throw "Missing Vercel credentials. Ensure VERCEL_TOKEN and VERCEL_ORG_ID are provided."
}

$headers = @{ Authorization = "Bearer $vercelToken"; "Content-Type" = "application/json" }
$baseUrl = "https://api.vercel.com"

function New-VercelProject {
  param(
    [string]$ProjectName,
    [string]$RootDirectory
  )
  $body = @{
    name = $ProjectName
    publicSource = $false
    gitRepository = @{ type = "github"; repo = $RepoSlug; rootDirectory = $RootDirectory }
    # We delegate build to GitHub Actions or project defaults
  } | ConvertTo-Json -Depth 6

  $url = "$baseUrl/v9/projects?teamId=$orgId"
  Write-Host "\nCreating project '$ProjectName' (root: $RootDirectory)..." -ForegroundColor Yellow
  try {
    $resp = Invoke-RestMethod -Method POST -Uri $url -Headers $headers -Body $body
    return $resp
  }
  catch {
    $msg = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
    throw "Failed to create project '$ProjectName': $msg"
  }
}

$created = @()
$existing = @()

foreach ($tuple in @(@{ n=$EngineCName; r=$EngineCRoot }, @{ n=$EngineDName; r=$EngineDRoot })) {
  $projectName = $tuple.n
  $root = $tuple.r

  # Check if already exists
  $getUrl = "$baseUrl/v9/projects/$projectName?teamId=$orgId"
  try {
    $probe = Invoke-RestMethod -Method GET -Uri $getUrl -Headers $headers -ErrorAction Stop
    Write-Host "Project '$projectName' already exists (id: $($probe.id))" -ForegroundColor Green
    $existing += $probe
  }
  catch {
    # create new
    $resp = New-VercelProject -ProjectName $projectName -RootDirectory $root
    Write-Host "Created project '$projectName' (id: $($resp.id))" -ForegroundColor Green
    $created += $resp
  }
}

# Set GitHub Secrets if 'gh' is available
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
  $ids = @{}
  foreach ($p in ($existing + $created)) { $ids[$p.name] = $p.id }

  if ($ids.ContainsKey($EngineCName)) {
    $id = $ids[$EngineCName]
    Write-Host "\nSetting repo secret VERCEL_PROJECT_ID_ENGINE_C = $id" -ForegroundColor Cyan
    $id | gh secret set VERCEL_PROJECT_ID_ENGINE_C | Out-Null
  }
  if ($ids.ContainsKey($EngineDName)) {
    $id = $ids[$EngineDName]
    Write-Host "Setting repo secret VERCEL_PROJECT_ID_ENGINE_D = $id" -ForegroundColor Cyan
    $id | gh secret set VERCEL_PROJECT_ID_ENGINE_D | Out-Null
  }
}
else {
  Write-Host "\nNote: 'gh' CLI not found. Please set the following GitHub Secrets manually:" -ForegroundColor Yellow
  foreach ($p in ($existing + $created)) {
    Write-Host (" - {0} => {1}" -f $p.name, $p.id) -ForegroundColor White
  }
}

Write-Host "\nDone. Re-run the GitHub Actions deployment workflow to deploy Engine C & D on Vercel." -ForegroundColor Green
