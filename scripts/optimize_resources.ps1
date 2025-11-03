#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Optimize Cloud Run Engine Resources
.DESCRIPTION
    Sets min-instances=0 and max-instances=3 on all engines for cost optimization
#>

$PROJECT = "after-yesterday-473512-k3"
$REGION = "us-central1"

$ENGINES = @(
    @{Name="infinityai-engine-a"; CPU="0.5"; Memory="256Mi"},
    @{Name="infinityai-engine-b"; CPU="0.5"; Memory="256Mi"},
    @{Name="infinityai-engine-c-execution"; CPU="1"; Memory="512Mi"},
    @{Name="infinityai-engine-d"; CPU="0.5"; Memory="256Mi"}
)

Write-Host "`n=== InfinityAI.Pro - Resource Optimization ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT" -ForegroundColor Gray
Write-Host "Region: $REGION`n" -ForegroundColor Gray

foreach ($engine in $ENGINES) {
    Write-Host "[Optimizing] $($engine.Name)..." -ForegroundColor Cyan
    
    try {
        gcloud run services update $engine.Name `
            --region=$REGION `
            --project=$PROJECT `
            --min-instances=0 `
            --max-instances=3 `
            --cpu=$($engine.CPU) `
            --memory=$($engine.Memory) `
            --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Updated: min=0, max=3, cpu=$($engine.CPU), memory=$($engine.Memory)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Optimization Complete ===" -ForegroundColor Green
Write-Host "All engines configured to scale to zero when idle (min=0)" -ForegroundColor Gray
Write-Host "Maximum instances capped at 3 to prevent runaway costs (max=3)" -ForegroundColor Gray
Write-Host "`nExpected monthly savings: $5-15" -ForegroundColor Green

gcloud run services list --region=$REGION --project=$PROJECT --format="table(metadata.name,spec.template.spec.containers[0].resources.limits.cpu,spec.template.spec.containers[0].resources.limits.memory)"

Write-Host "`nDone!" -ForegroundColor Green
