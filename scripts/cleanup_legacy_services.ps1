#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup Legacy Cloud Run Services
.DESCRIPTION
    Deletes duplicate Cloud Run services that have been migrated to Firebase Functions
.NOTES
    Run after Firebase Functions deployment is verified
#>

$PROJECT = "after-yesterday-473512-k3"
$REGION = "us-central1"

# Legacy services to delete (now handled by Firebase Functions)
$LEGACY_SERVICES = @(
    "analyzeimagewithroboticser",
    "analyzeportfolio",
    "getaisignals",
    "getbatchaisignals",
    "getdhanoverview",
    "getenginebstatus",
    "getgeminianalysis",
    "getvertexaianalysis",
    "infinityai-frontend",
    "savedhancredentials",
    "starttrading",
    "stoptrading",
    "submitdhancredentialsv2",
    "syncholdings"
)

Write-Host "`n=== InfinityAI.Pro - Legacy Service Cleanup ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT" -ForegroundColor Gray
Write-Host "Region: $REGION`n" -ForegroundColor Gray

Write-Host "Services to delete:" -ForegroundColor Yellow
$LEGACY_SERVICES | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

Write-Host "`nThese services are now handled by Firebase Functions (v2)." -ForegroundColor Yellow
Write-Host "Deleting them will reduce costs and simplify management.`n" -ForegroundColor Yellow

$confirmation = Read-Host "Continue with deletion? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 0
}

$deleted = 0
$failed = 0

foreach ($service in $LEGACY_SERVICES) {
    Write-Host "`n[Deleting] $service..." -ForegroundColor Cyan
    
    try {
        gcloud run services delete $service `
            --region=$REGION `
            --project=$PROJECT `
            --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Deleted successfully" -ForegroundColor Green
            $deleted++
        } else {
            Write-Host "  ✗ Failed to delete (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n=== Cleanup Summary ===" -ForegroundColor Cyan
Write-Host "Deleted: $deleted" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })

if ($deleted -gt 0) {
    Write-Host "`n✓ Cleanup complete! Estimated monthly savings: ~`$$($deleted * 2)-$($deleted * 5)" -ForegroundColor Green
}

Write-Host "`nRemaining production services:" -ForegroundColor Cyan
gcloud run services list --region=$REGION --project=$PROJECT --format="table(metadata.name,status.url)"

Write-Host "`nDone!" -ForegroundColor Green
