#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up old Artifact Registry images
.DESCRIPTION
    Lists and deletes old container image versions, retaining only the latest 3 per service
#>

$PROJECT = "after-yesterday-473512-k3"
$REPOSITORY = "gcr.io"

$SERVICES = @(
    "infinityai-engine-a",
    "infinityai-engine-b",
    "infinityai-engine-c-execution",
    "infinityai-engine-d"
)

Write-Host "`n=== Artifact Registry Cleanup ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT" -ForegroundColor Gray
Write-Host "Repository: $REPOSITORY" -ForegroundColor Gray
Write-Host "Retention: Keep latest 3 versions per service`n" -ForegroundColor Gray

$totalDeleted = 0
$totalRetained = 0
$estimatedSavings = 0

foreach ($service in $SERVICES) {
    Write-Host "`n[Analyzing] $service..." -ForegroundColor Cyan
    
    try {
        # List all images for this service
        $images = gcloud container images list-tags "$REPOSITORY/$PROJECT/$service" `
            --format="get(digest,timestamp)" `
            --sort-by="~timestamp" `
            --limit=100 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ⚠️  No images found or access denied" -ForegroundColor Yellow
            continue
        }
        
        # Parse images
        $imageList = $images | Where-Object { $_ -match '\S' } | ForEach-Object {
            $parts = $_.Trim() -split '\s+'
            if ($parts.Count -ge 2) {
                @{
                    Digest = $parts[0]
                    Timestamp = $parts[1]
                }
            }
        }
        
        $totalImages = $imageList.Count
        Write-Host "  Found: $totalImages image versions" -ForegroundColor White
        
        if ($totalImages -le 3) {
            Write-Host "  ✅ Only $totalImages versions exist. No cleanup needed." -ForegroundColor Green
            $totalRetained += $totalImages
            continue
        }
        
        # Keep latest 3, delete the rest
        $toKeep = $imageList | Select-Object -First 3
        $toDelete = $imageList | Select-Object -Skip 3
        
        Write-Host "  📦 Keeping: 3 latest versions" -ForegroundColor Green
        Write-Host "  🗑️  Deleting: $($toDelete.Count) old versions" -ForegroundColor Yellow
        
        $deleted = 0
        foreach ($image in $toDelete) {
            $imageUrl = "$REPOSITORY/$PROJECT/$service@$($image.Digest)"
            
            try {
                gcloud container images delete $imageUrl --quiet 2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    $deleted++
                    # Estimate 100-500 MB per image
                    $estimatedSavings += 0.3  # ~$0.30 per image (rough estimate)
                } else {
                    Write-Host "    ⚠️  Failed to delete: $($image.Digest)" -ForegroundColor Red
                }
            } catch {
                Write-Host "    ⚠️  Error deleting: $($image.Digest)" -ForegroundColor Red
            }
        }
        
        Write-Host "  ✅ Deleted: $deleted images" -ForegroundColor Green
        $totalDeleted += $deleted
        $totalRetained += 3
        
    } catch {
        Write-Host "  ❌ Error processing ${service}: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Green
Write-Host "Cleanup Summary" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "Images Deleted: $totalDeleted" -ForegroundColor Yellow
Write-Host "Images Retained: $totalRetained" -ForegroundColor Green
Write-Host "Estimated Storage Savings: ~$$([math]::Round($estimatedSavings, 2))/month" -ForegroundColor Cyan

if ($totalDeleted -gt 0) {
    Write-Host "`n✅ Artifact Registry cleanup complete!" -ForegroundColor Green
    Write-Host "Storage costs reduced by removing old image versions." -ForegroundColor Gray
} else {
    Write-Host "`n✅ No cleanup needed - all services have optimal image counts." -ForegroundColor Green
}

Write-Host "`nCurrent Image Counts:" -ForegroundColor Cyan
foreach ($service in $SERVICES) {
    try {
        $count = (gcloud container images list-tags "$REPOSITORY/$PROJECT/$service" --limit=100 2>&1 | Measure-Object -Line).Lines
        Write-Host "  $service`: $count versions" -ForegroundColor White
    } catch {
        Write-Host "  $service`: Error getting count" -ForegroundColor Red
    }
}

Write-Host "`nDone!" -ForegroundColor Green
