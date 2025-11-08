<#
Bulk set GitHub secrets using gh CLI. Existing secrets are skipped unless -Force is supplied.
Requires: Authenticated gh CLI.
#>
param(
  [switch]$Force,
  [string]$Repo = 'raghu-1718/InfinityAI.Pro',
  [string]$JsonFile,
  [hashtable]$Map,
  [switch]$DryRun
)

$required = @(
  'GCP_PROJECT_ID','GCP_REGION','GCP_WORKLOAD_IDENTITY_PROVIDER','GCP_SERVICE_ACCOUNT',
  'ADMIN_DASHBOARD_API_KEY'
)

$existing = @()
if(-not $DryRun){
  try { $existing = gh secret list --repo $Repo --limit 200 | ForEach-Object { ($_ -split '\s+')[0] } } catch { Write-Host "[WARN] Unable to list existing secrets (gh missing?)" -ForegroundColor Yellow }
}

$inputMap = @{}
if($Map){ $Map.GetEnumerator() | ForEach-Object { $inputMap[$_.Key] = $_.Value } }
if($JsonFile -and (Test-Path $JsonFile)){
  try {
    $jsonData = Get-Content $JsonFile -Raw | ConvertFrom-Json
    $jsonData.PSObject.Properties | ForEach-Object { $inputMap[$_.Name] = $_.Value }
  } catch { Write-Host "[WARN] Could not parse JSON file $JsonFile" -ForegroundColor Yellow }
}

foreach($name in $required){
  if(-not $Force -and $existing -contains $name){ Write-Host "[SKIP] $name already set" -ForegroundColor Yellow; continue }
  $value = $null
  if($inputMap.ContainsKey($name)){ $value = [string]$inputMap[$name] }
  if(-not $value){ $value = Read-Host "Enter value for $name" }
  if([string]::IsNullOrWhiteSpace($value)){ Write-Host "[WARN] Empty value for $name. Skipping." -ForegroundColor Red; continue }
  if($DryRun){ Write-Host "[DRYRUN] Would set $name" -ForegroundColor DarkCyan; continue }
  try {
    $value | gh secret set $name --repo $Repo 1>$null
    Write-Host "[SET] $name" -ForegroundColor Cyan
  } catch {
    Write-Host ('[ERR] Failed to set ' + $name + ': ' + $_.Exception.Message) -ForegroundColor Red
  }
}

Write-Host "[DONE] Secret population routine complete (DryRun=$DryRun)"
