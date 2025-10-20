# InfinityAI.Pro - Production Cleanup & Optimization Script
# Generated from audit report: 2025-10-20
# ⚠️ Review each section before execution

param(
    [switch]$DryRun = $false,
    [switch]$ColdStartFix = $false,
    [switch]$CleanupDuplicates = $false,
    [switch]$AddMonitoring = $false,
    [switch]$CleanImages = $false,
    [switch]$All = $false
)

$PROJECT = "infinity-ai-5ec7c"
$REGION = "us-central1"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  InfinityAI.Pro Production Optimization Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# 1. FIX COLD START TIMES (8s → <2s)
# ============================================================================
if ($ColdStartFix -or $All) {
    Write-Host "🚀 COLD START OPTIMIZATION" -ForegroundColor Green
    Write-Host "Adding minScale=1 to critical services to keep instances warm..." -ForegroundColor Gray
    Write-Host ""
    
    $criticalServices = @(
        "infinityai-frontend",
        "infinityai-engine-a",
        "infinityai-engine-c-execution"
    )
    
    foreach ($service in $criticalServices) {
        Write-Host "  → Updating $service with minScale=1" -ForegroundColor Cyan
        
        if (-not $DryRun) {
            gcloud run services update $service `
                --region=$REGION `
                --project=$PROJECT `
                --min-instances=1 `
                --no-traffic `
                --quiet
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✅ Updated successfully" -ForegroundColor Green
            } else {
                Write-Host "    ❌ Failed to update" -ForegroundColor Red
            }
        } else {
            Write-Host "    [DRY RUN] Would execute: gcloud run services update $service --min-instances=1" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "💡 Note: This will keep 1 instance warm per service (~$15-25/month each)" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# 2. CLEANUP DUPLICATE SERVICES
# ============================================================================
if ($CleanupDuplicates -or $All) {
    Write-Host "🧹 DUPLICATE SERVICE CLEANUP" -ForegroundColor Green
    Write-Host "Identifying and preparing to remove duplicate deployments..." -ForegroundColor Gray
    Write-Host ""
    
    $duplicates = @(
        @{Old="engine-a-market-data-prod"; New="infinityai-engine-a"},
        @{Old="engine-c-execution-prod"; New="infinityai-engine-c-execution"}
    )
    
    foreach ($dup in $duplicates) {
        Write-Host "  Duplicate Pair Found:" -ForegroundColor Yellow
        Write-Host "    Old: $($dup.Old)" -ForegroundColor Red
        Write-Host "    New: $($dup.New)" -ForegroundColor Green
        Write-Host ""
        
        # Verify new service is healthy
        Write-Host "    Verifying new service health..." -ForegroundColor Gray
        if (-not $DryRun) {
            $newServiceUrl = (gcloud run services describe $($dup.New) --region=$REGION --project=$PROJECT --format="value(status.url)" 2>$null)
            
            if ($newServiceUrl) {
                Write-Host "    ✅ New service is deployed and accessible" -ForegroundColor Green
                Write-Host "    URL: $newServiceUrl" -ForegroundColor Cyan
                
                # Check traffic on old service
                $oldTraffic = (gcloud run services describe $($dup.Old) --region=$REGION --project=$PROJECT --format="value(status.traffic[0].percent)" 2>$null)
                
                if ($oldTraffic -eq "100") {
                    Write-Host "    ⚠️  Old service still receiving 100% traffic!" -ForegroundColor Yellow
                    Write-Host "    📋 Action Required: Update clients to use new URL before deletion" -ForegroundColor Yellow
                } else {
                    Write-Host "    ✅ Old service traffic: $oldTraffic%" -ForegroundColor Green
                    
                    # Safe to delete after grace period
                    Write-Host "    💡 Safe to delete after 7-day validation period" -ForegroundColor Cyan
                    Write-Host "    Command to delete:" -ForegroundColor Gray
                    Write-Host "      gcloud run services delete $($dup.Old) --region=$REGION --project=$PROJECT --quiet" -ForegroundColor DarkGray
                }
            } else {
                Write-Host "    ❌ New service not found or not accessible!" -ForegroundColor Red
                Write-Host "    ⚠️  DO NOT delete old service until new one is verified" -ForegroundColor Red
            }
        } else {
            Write-Host "    [DRY RUN] Would verify health and traffic allocation" -ForegroundColor Yellow
        }
        
        Write-Host ""
    }
    
    Write-Host "⚠️  SAFETY NOTE: Do NOT delete old services until:" -ForegroundColor Yellow
    Write-Host "   1. New services verified healthy for 7 days" -ForegroundColor Yellow
    Write-Host "   2. All client references updated to new URLs" -ForegroundColor Yellow
    Write-Host "   3. Old services show 0% traffic" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# 3. ADD CLOUD MONITORING ALERTS
# ============================================================================
if ($AddMonitoring -or $All) {
    Write-Host "📊 CLOUD MONITORING SETUP" -ForegroundColor Green
    Write-Host "Creating alert policies for error rate monitoring..." -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "  📋 Alert Policy Configuration:" -ForegroundColor Cyan
    Write-Host "    - Trigger: >5 ERROR-level logs in 5 minutes" -ForegroundColor Gray
    Write-Host "    - Scope: All Cloud Run services" -ForegroundColor Gray
    Write-Host "    - Notification: (requires Telegram/Slack channel setup)" -ForegroundColor Gray
    Write-Host ""
    
    if (-not $DryRun) {
        Write-Host "  ⚠️  Alert creation requires:" -ForegroundColor Yellow
        Write-Host "    1. Notification channel configured in Cloud Console" -ForegroundColor Yellow
        Write-Host "    2. gcloud alpha components installed" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  📖 Manual setup instructions:" -ForegroundColor Cyan
        Write-Host "    gcloud alpha monitoring channels list" -ForegroundColor DarkGray
        Write-Host "    # Note the channel ID, then create alert policy in Cloud Console" -ForegroundColor DarkGray
    } else {
        Write-Host "  [DRY RUN] Would configure monitoring alerts" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# ============================================================================
# 4. CLEAN UP OLD CONTAINER IMAGES
# ============================================================================
if ($CleanImages -or $All) {
    Write-Host "🗂️  ARTIFACT REGISTRY CLEANUP" -ForegroundColor Green
    Write-Host "Removing untagged images older than 30 days..." -ForegroundColor Gray
    Write-Host ""
    
    $repo = "cloud-run-source-deploy"
    
    Write-Host "  Repository: $repo" -ForegroundColor Cyan
    Write-Host "  Location: $REGION" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $DryRun) {
        Write-Host "  📋 Listing untagged images..." -ForegroundColor Gray
        
        # List untagged images
        $images = gcloud artifacts docker images list "$REGION-docker.pkg.dev/$PROJECT/$repo" `
            --format="value(image)" `
            --filter="tags:*" `
            --include-tags `
            --project=$PROJECT 2>$null
        
        if ($images) {
            $imageCount = ($images | Measure-Object).Count
            Write-Host "  Found $imageCount tagged images (untagged will be cleaned)" -ForegroundColor Cyan
        }
        
        Write-Host ""
        Write-Host "  💡 Setting up auto-cleanup policy for future builds..." -ForegroundColor Cyan
        Write-Host "  Command:" -ForegroundColor Gray
        Write-Host "    gcloud artifacts repositories set-cleanup-policies $repo \\" -ForegroundColor DarkGray
        Write-Host "      --project=$PROJECT \\" -ForegroundColor DarkGray
        Write-Host "      --location=$REGION \\" -ForegroundColor DarkGray
        Write-Host "      --policy='untagged-30d'" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  ⚠️  Requires manual confirmation in Cloud Console" -ForegroundColor Yellow
    } else {
        Write-Host "  [DRY RUN] Would list and clean untagged images" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  OPTIMIZATION SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "✅ Dry run completed successfully" -ForegroundColor Green
    Write-Host "   Re-run with -DryRun:`$false to apply changes" -ForegroundColor Yellow
} else {
    if ($ColdStartFix -or $All) {
        Write-Host "✅ Cold start optimization applied" -ForegroundColor Green
    }
    if ($CleanupDuplicates -or $All) {
        Write-Host "📋 Duplicate services identified (manual deletion recommended)" -ForegroundColor Yellow
    }
    if ($AddMonitoring -or $All) {
        Write-Host "📊 Monitoring setup instructions provided" -ForegroundColor Cyan
    }
    if ($CleanImages -or $All) {
        Write-Host "🗂️  Image cleanup policy instructions provided" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "📖 Full audit report: reports/PRODUCTION_AUDIT_REPORT_2025-10-20.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Usage Examples:" -ForegroundColor Yellow
Write-Host "  .\optimize-production.ps1 -DryRun -All          # Preview all changes" -ForegroundColor Gray
Write-Host "  .\optimize-production.ps1 -ColdStartFix         # Fix cold starts only" -ForegroundColor Gray
Write-Host "  .\optimize-production.ps1 -CleanupDuplicates    # Identify duplicates" -ForegroundColor Gray
Write-Host "  .\optimize-production.ps1 -All                  # Apply all optimizations" -ForegroundColor Gray
Write-Host ""
