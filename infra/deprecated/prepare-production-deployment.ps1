#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Prepare and Deploy InfinityAI.Pro to Production (3-Engine Architecture)
.DESCRIPTION
    Automated script that:
    1. Verifies GCP/Firebase configuration
    2. Resolves project mismatches
    3. Updates deployment scripts with correct directory names
    4. Deploys to production with optimal configuration
.NOTES
    Date: November 26, 2025
    Verified: 32 CPU quota available (only 2 in use)
#>

param(
    [switch]$SkipVerification,
    [switch]$SkipBuild,
    [switch]$DryRun  # Show what would be done without executing
)

Write-Host "`n🚀 InfinityAI.Pro - Production Deployment Preparation`n" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# ============================================================================
# STEP 1: VERIFY CONFIGURATION
# ============================================================================

if (-not $SkipVerification) {
    Write-Host "`n📋 STEP 1: Verifying Configuration..." -ForegroundColor Yellow
    
    # Check GCP project
    $gcpProject = gcloud config get-value project 2>$null
    Write-Host "   GCP Project: $gcpProject" -ForegroundColor Cyan
    
    # Check Firebase project
    $firebaseProject = (firebase use 2>&1 | Select-String -Pattern "Active Project: \w+ \(([^)]+)\)").Matches[0].Groups[1].Value
    Write-Host "   Firebase Project: $firebaseProject" -ForegroundColor Cyan
    
    # Check if projects match
    if ($gcpProject -ne $firebaseProject) {
        Write-Host "`n⚠️  PROJECT MISMATCH DETECTED" -ForegroundColor Yellow
        Write-Host "   GCP: $gcpProject" -ForegroundColor White
        Write-Host "   Firebase: $firebaseProject" -ForegroundColor White
        Write-Host ""
        Write-Host "   Which project contains your production data?" -ForegroundColor Yellow
        Write-Host "   1. $gcpProject (current gcloud)" -ForegroundColor White
        Write-Host "   2. $firebaseProject (current firebase)" -ForegroundColor White
        Write-Host "   3. Skip (I'll handle manually)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            $choice = Read-Host "`n   Enter choice (1/2/3)"
            
            switch ($choice) {
                "1" {
                    Write-Host "   Switching Firebase to $gcpProject..." -ForegroundColor Cyan
                    firebase use $gcpProject
                    $PROJECT_ID = $gcpProject
                }
                "2" {
                    Write-Host "   Switching gcloud to $firebaseProject..." -ForegroundColor Cyan
                    gcloud config set project $firebaseProject
                    $PROJECT_ID = $firebaseProject
                }
                "3" {
                    Write-Host "   ⚠️  Proceeding with current configuration" -ForegroundColor Yellow
                    $PROJECT_ID = $gcpProject
                }
                default {
                    Write-Host "   ❌ Invalid choice. Exiting." -ForegroundColor Red
                    exit 1
                }
            }
        } else {
            Write-Host "   [DRY RUN] Would prompt for project selection" -ForegroundColor Gray
            $PROJECT_ID = $gcpProject
        }
    } else {
        Write-Host "   ✅ Projects matched: $gcpProject" -ForegroundColor Green
        $PROJECT_ID = $gcpProject
    }
    
    # Verify CPU quota
    Write-Host "`n   Checking CPU quota..." -ForegroundColor Cyan
    $cpuQuota = gcloud compute regions describe us-central1 --format=json 2>$null | ConvertFrom-Json
    $cpuLimit = ($cpuQuota.quotas | Where-Object { $_.metric -eq "CPUS" }).limit
    $cpuUsage = ($cpuQuota.quotas | Where-Object { $_.metric -eq "CPUS" }).usage
    
    Write-Host "   CPU Quota: $cpuUsage / $cpuLimit" -ForegroundColor Cyan
    if ($cpuLimit -ge 10) {
        Write-Host "   ✅ Sufficient quota for production deployment (min-instances=1)" -ForegroundColor Green
        $useProductionMode = $true
    } else {
        Write-Host "   ⚠️  Limited quota - will use on-demand mode (min-instances=0)" -ForegroundColor Yellow
        $useProductionMode = $false
    }
} else {
    Write-Host "`n📋 STEP 1: Skipped (using current configuration)" -ForegroundColor Gray
    $PROJECT_ID = gcloud config get-value project 2>$null
    $useProductionMode = $true
}

$REGION = "us-central1"

# ============================================================================
# STEP 2: MAP DIRECTORY NAMES TO SERVICE NAMES
# ============================================================================

Write-Host "`n📦 STEP 2: Mapping Backend Engines..." -ForegroundColor Yellow

$ENGINE_MAP = @{
    "engine-analytics" = @{
        serviceName = "infinityai-engine-a"
        directory = "backend/engine-analytics"
        port = 8001
        memory = "512Mi"
        cpu = 1
        minInstances = if ($useProductionMode) { 1 } else { 0 }
        maxInstances = 10
    }
    "engine-core" = @{
        serviceName = "infinityai-engine-b"
        directory = "backend/engine-core"
        port = 8002
        memory = "1Gi"
        cpu = 2
        minInstances = if ($useProductionMode) { 1 } else { 0 }
        maxInstances = 5
    }
    "engine-execution" = @{
        serviceName = "infinityai-engine-c-execution"
        directory = "backend/engine-execution"
        port = 8003
        memory = "512Mi"
        cpu = 1
        minInstances = if ($useProductionMode) { 1 } else { 0 }
        maxInstances = 10
        envVars = "ENABLE_WEBSOCKET=true,ENABLE_CHATBOT=true,ENABLE_HEALTH_ORCHESTRATOR=true"
    }
}

foreach ($engine in $ENGINE_MAP.Keys) {
    $info = $ENGINE_MAP[$engine]
    if (Test-Path $info.directory) {
        Write-Host "   ✅ $engine → $($info.serviceName)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $engine directory not found: $($info.directory)" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# STEP 3: BUILD AND DEPLOY ENGINES
# ============================================================================

Write-Host "`n🔧 STEP 3: Building and Deploying Engines..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "   [DRY RUN] Would build and deploy:" -ForegroundColor Gray
    foreach ($engine in $ENGINE_MAP.Keys) {
        $info = $ENGINE_MAP[$engine]
        Write-Host "   - $($info.serviceName) (min-instances=$($info.minInstances))" -ForegroundColor Gray
    }
} else {
    foreach ($engine in $ENGINE_MAP.Keys) {
        $info = $ENGINE_MAP[$engine]
        Write-Host "`n   📦 Deploying $($info.serviceName)..." -ForegroundColor Cyan
        
        $fullPath = Join-Path $PSScriptRoot ".." $info.directory
        Set-Location $fullPath
        
        # Build container
        if (-not $SkipBuild) {
            Write-Host "      🏗️  Building container..." -ForegroundColor Gray
            $buildResult = gcloud builds submit --tag "gcr.io/$PROJECT_ID/$($info.serviceName)" --project=$PROJECT_ID 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "      ❌ Build failed" -ForegroundColor Red
                Write-Host $buildResult
                Set-Location $PSScriptRoot/../..
                exit 1
            }
            Write-Host "      ✅ Build complete" -ForegroundColor Green
        }
        
        # Deploy to Cloud Run
        Write-Host "      🚀 Deploying to Cloud Run..." -ForegroundColor Gray
        $deployArgs = @(
            "run", "deploy", $info.serviceName,
            "--image", "gcr.io/$PROJECT_ID/$($info.serviceName)",
            "--region", $REGION,
            "--project", $PROJECT_ID,
            "--platform", "managed",
            "--allow-unauthenticated",
            "--memory", $info.memory,
            "--cpu", $info.cpu.ToString(),
            "--min-instances", $info.minInstances.ToString(),
            "--max-instances", $info.maxInstances.ToString(),
            "--timeout", "300s",
            "--set-env-vars", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
        )
        
        # Add engine-specific env vars (PORT is set automatically by Cloud Run)
        if ($info.envVars) {
            $deployArgs[$deployArgs.IndexOf("--set-env-vars")+1] += ",$($info.envVars)"
        }
        
        $deployResult = & gcloud @deployArgs 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      ✅ Deployed successfully" -ForegroundColor Green
            $serviceUrl = (gcloud run services describe $info.serviceName --region=$REGION --format="value(status.url)" 2>$null)
            Write-Host "      🔗 $serviceUrl" -ForegroundColor Cyan
        } else {
            Write-Host "      ❌ Deployment failed" -ForegroundColor Red
            Write-Host $deployResult
        }
        
        Set-Location $PSScriptRoot/../..
    }
}

# ============================================================================
# STEP 4: DEPLOY FRONTEND
# ============================================================================

Write-Host "`n🌐 STEP 4: Deploying Frontend..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "   [DRY RUN] Would build and deploy frontend to Firebase Hosting" -ForegroundColor Gray
} else {
    $frontendPath = Join-Path $PSScriptRoot ".." "frontend" "web"
    Set-Location $frontendPath
    
    if (-not $SkipBuild) {
        Write-Host "   📦 Building frontend..." -ForegroundColor Gray
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ❌ Frontend build failed" -ForegroundColor Red
            Set-Location $PSScriptRoot/../..
            exit 1
        }
        Write-Host "   ✅ Build complete" -ForegroundColor Green
    }
    
    Write-Host "   🚀 Deploying to Firebase Hosting..." -ForegroundColor Gray
    firebase deploy --only hosting --project $PROJECT_ID
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Frontend deployed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Frontend deployment failed" -ForegroundColor Red
    }
    
    Set-Location $PSScriptRoot/../..
}

# ============================================================================
# STEP 5: VERIFY DEPLOYMENT
# ============================================================================

Write-Host "`n🏥 STEP 5: Verifying Deployment..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "   [DRY RUN] Would verify all services are healthy" -ForegroundColor Gray
} else {
    Start-Sleep -Seconds 10
    
    foreach ($engine in $ENGINE_MAP.Keys) {
        $info = $ENGINE_MAP[$engine]
        $serviceUrl = (gcloud run services describe $info.serviceName --region=$REGION --format="value(status.url)" 2>$null)
        
        if ($serviceUrl) {
            try {
                $response = Invoke-WebRequest -Uri "$serviceUrl/" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
                Write-Host "   ✅ $($info.serviceName): HTTP $($response.StatusCode)" -ForegroundColor Green
            } catch {
                $statusCode = $_.Exception.Response.StatusCode.value__
                if ($statusCode -eq 404) {
                    Write-Host "   ⚠️  $($info.serviceName): HTTP 404 (may need /health endpoint)" -ForegroundColor Yellow
                } else {
                    Write-Host "   ❌ $($info.serviceName): Failed - $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "   ❌ $($info.serviceName): Service URL not found" -ForegroundColor Red
        }
    }
}

# ============================================================================
# STEP 6: PUSH CHANGES TO GITHUB
# ============================================================================

Write-Host "`n📤 STEP 6: Pushing Changes to GitHub..." -ForegroundColor Yellow

$unpushedCommits = git rev-list --count origin/feature/3-engine-architecture..HEAD 2>$null
if ($null -eq $unpushedCommits) {
    $unpushedCommits = git rev-list --count main..HEAD 2>$null
}

if ($unpushedCommits -gt 0) {
    Write-Host "   Found $unpushedCommits unpushed commit(s)" -ForegroundColor Cyan
    
    if ($DryRun) {
        Write-Host "   [DRY RUN] Would push to origin/feature/3-engine-architecture" -ForegroundColor Gray
    } else {
        Write-Host "   Push changes to GitHub? (y/N): " -NoNewline
        $push = Read-Host
        
        if ($push -eq "y" -or $push -eq "Y") {
            git push origin feature/3-engine-architecture
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Changes pushed to GitHub" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Push failed" -ForegroundColor Red
            }
        } else {
            Write-Host "   ⏭️  Skipped" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ✅ All changes already pushed" -ForegroundColor Green
}

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

Write-Host "`n" + ("═" * 80) -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ("═" * 80) -ForegroundColor Cyan

Write-Host "`n📊 Configuration:" -ForegroundColor Yellow
Write-Host "   Project: $PROJECT_ID" -ForegroundColor White
Write-Host "   Region: $REGION" -ForegroundColor White
Write-Host "   Mode: $(if ($useProductionMode) { 'Production (min-instances=1)' } else { 'On-Demand (min-instances=0)' })" -ForegroundColor White

Write-Host "`n🔗 Service URLs:" -ForegroundColor Yellow
foreach ($engine in $ENGINE_MAP.Keys) {
    $info = $ENGINE_MAP[$engine]
    $serviceUrl = (gcloud run services describe $info.serviceName --region=$REGION --format="value(status.url)" 2>$null)
    if ($serviceUrl) {
        Write-Host "   $($info.serviceName):" -ForegroundColor Cyan
        Write-Host "      $serviceUrl" -ForegroundColor White
    }
}

Write-Host "`n📚 Documentation:" -ForegroundColor Yellow
Write-Host "   Migration Details: MIGRATION_ENGINE_D_TO_C.md" -ForegroundColor White
Write-Host "   Verification Report: PRODUCTION_VERIFICATION_REPORT.md" -ForegroundColor White
Write-Host "   Next Steps: NEXT_STEPS.md" -ForegroundColor White

Write-Host "`n✅ Success Checklist:" -ForegroundColor Yellow
Write-Host "   [ ] Open frontend: https://infinityai.pro (or your domain)" -ForegroundColor White
Write-Host "   [ ] Check WebSocket connection (DevTools → Network → WS)" -ForegroundColor White
Write-Host "   [ ] Verify all 3 engines responding" -ForegroundColor White
Write-Host "   [ ] Test chatbot functionality" -ForegroundColor White
Write-Host "   [ ] Confirm no Engine D references in console" -ForegroundColor White

Write-Host ""
