param(
  [string]$ImageTag = "latest",
  [switch]$DryRun,
  [string]$WorkflowName = "Deploy Production Stack (AWS + GCP)",
  [string]$Ref = "main"
)

<#
Dispatch the unified production deployment workflow via GitHub CLI.
Requires: gh authenticated (repo scope). Inputs must match workflow_dispatch inputs: image_tag, dry_run.
The previous version used an incorrect --field pairing that produced an empty input string.
#>

Write-Host "Locating workflow '$WorkflowName'..." -ForegroundColor Cyan
$wf = gh workflow list --limit 200 --json name,id | ConvertFrom-Json | Where-Object { $_.name -eq $WorkflowName } | Select-Object -First 1
if(-not $wf){ Write-Error "Workflow '$WorkflowName' not found"; exit 1 }

$dry = if($DryRun){ 'true' } else { 'false' }
Write-Host "Dispatching: name='$WorkflowName' id=$($wf.id) ref=$Ref image_tag=$ImageTag dry_run=$dry" -ForegroundColor Cyan

try {
  # Correct gh syntax: -f key=value (multiple)
  gh workflow run $WorkflowName -r $Ref -f image_tag=$ImageTag -f dry_run=$dry | Out-Null
} catch {
  Write-Error "Dispatch failed: $_"; exit 1
}

Start-Sleep -Seconds 5
$latest = gh run list --workflow "$WorkflowName" --limit 1 --json databaseId,status,conclusion,createdAt,url | ConvertFrom-Json | Select-Object -First 1
if(-not $latest){ Write-Warning "No run found yet (may still be queuing). Re-run: gh run list --workflow '$WorkflowName'"; exit 0 }

Write-Host "Triggered run: $($latest.url) status=$($latest.status)" -ForegroundColor Green
Write-Host "Monitor logs:" -ForegroundColor Yellow
Write-Host "  gh run watch $($latest.databaseId) --log" -ForegroundColor Yellow
Write-Host "Or follow in browser." -ForegroundColor Yellow
