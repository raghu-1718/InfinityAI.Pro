<#
.SYNOPSIS
    Traffic shift and legacy service cleanup script for InfinityAI.Pro.

.DESCRIPTION
    This script manages traffic migration from legacy to canonical Cloud Run services
    and safely deletes legacy deployments after verification.

.PARAMETER DryRun
    Preview changes without executing (default: true)

.PARAMETER Project
    GCP project ID (default: infinity-ai-5ec7c)

.PARAMETER Region
    Cloud Run region (default: us-central1)

.EXAMPLE
    .\traffic_shift_and_cleanup.ps1
    # Preview traffic shift (dry-run mode)

.EXAMPLE
    .\traffic_shift_and_cleanup.ps1 -DryRun $false
    # Execute traffic shift and cleanup

.NOTES
    Author: InfinityAI.Pro DevOps
    Version: 1.0.0
    Last Updated: 2025-01-20
#>

param(
    [Parameter(Mandatory=$false)]
    [bool]$DryRun = $true,

    [Parameter(Mandatory=$false)]
    [string]$Project = "infinity-ai-5ec7c",

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Info "=========================================="
Write-Info "InfinityAI.Pro - Traffic Shift & Cleanup"
Write-Info "=========================================="
Write-Info "Project: $Project"
Write-Info "Region: $Region"
Write-Info "Mode: $(if ($DryRun) { 'DRY-RUN (Preview Only)' } else { 'LIVE EXECUTION' })"
Write-Info ""

# Canonical services (target)
$CanonicalServices = @(
    "infinityai-engine-a",
    "infinityai-engine-b",
    "infinityai-engine-c-execution",
    "infinityai-engine-d",
    "infinityai-frontend"
)

# Legacy services to clean up (if they exist)
$LegacyServices = @(
    "engine-a-market-data-prod",
    "engine-b-ai-ml-prod",
    "engine-c-execution-prod",
    "engine-d-chatbot-prod"
)

# Step 1: Verify canonical services are healthy
Write-Info "Step 1: Verifying canonical services health..."
$AllHealthy = $true

foreach ($service in $CanonicalServices) {
    try {
        $serviceInfo = gcloud run services describe $service --region=$Region --project=$Project --format="value(status.url)" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $url = $serviceInfo.Trim()
            
            # Try health check
            try {
                $response = Invoke-WebRequest -Uri "$url/health" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Success "  ✓ $service is healthy (200 OK)"
                } else {
                    Write-Warning "  ⚠ $service returned status $($response.StatusCode)"
                    $AllHealthy = $false
                }
            } catch {
                Write-Warning "  ⚠ $service health check failed: $_"
                $AllHealthy = $false
            }
        } else {
            Write-Error "  ✗ $service not found"
            $AllHealthy = $false
        }
    } catch {
        Write-Error "  ✗ Failed to check $service : $_"
        $AllHealthy = $false
    }
}

if (-not $AllHealthy) {
    Write-Error ""
    Write-Error "Some canonical services are unhealthy. Please fix before proceeding."
    exit 1
}

Write-Success "All canonical services are healthy!"
Write-Info ""

# Step 2: List and identify legacy services
Write-Info "Step 2: Identifying legacy services..."
$ExistingServices = gcloud run services list --region=$Region --project=$Project --format="value(SERVICE)" 2>&1 | Out-String
$ExistingServicesList = $ExistingServices.Trim() -split "`r?`n" | Where-Object { $_ -ne "" }

$LegacyToDelete = @()
foreach ($legacy in $LegacyServices) {
    if ($ExistingServicesList -contains $legacy) {
        $LegacyToDelete += $legacy
        Write-Warning "  Found legacy service: $legacy"
    }
}

if ($LegacyToDelete.Count -eq 0) {
    Write-Success "No legacy services found - cleanup already complete!"
    Write-Info ""
    Write-Info "Current canonical services:"
    foreach ($service in $CanonicalServices) {
        Write-Host "  • $service" -ForegroundColor Cyan
    }
    exit 0
}

Write-Info ""

# Step 3: Restrict ingress on legacy services (safety measure)
Write-Info "Step 3: Restricting ingress on legacy services..."
foreach ($service in $LegacyToDelete) {
    if ($DryRun) {
        Write-Warning "  [DRY-RUN] Would restrict ingress for: $service"
    } else {
        try {
            gcloud run services update $service --region=$Region --project=$Project --ingress=internal 2>&1 | Out-Null
            Write-Success "  ✓ Restricted $service to internal-only"
        } catch {
            Write-Warning "  ⚠ Failed to restrict $service (may already be deleted)"
        }
    }
}

Write-Info ""

# Step 4: Delete legacy services
Write-Info "Step 4: Deleting legacy services..."
foreach ($service in $LegacyToDelete) {
    if ($DryRun) {
        Write-Warning "  [DRY-RUN] Would delete: $service"
    } else {
        try {
            Write-Info "  Deleting $service..."
            gcloud run services delete $service --region=$Region --project=$Project --quiet
            Write-Success "  ✓ Deleted $service"
        } catch {
            Write-Error "  ✗ Failed to delete $service : $_"
        }
    }
}

Write-Info ""

# Step 5: Final verification
Write-Info "Step 5: Final verification..."
if ($DryRun) {
    Write-Warning "[DRY-RUN] Would verify only canonical services remain"
} else {
    $FinalServices = gcloud run services list --region=$Region --project=$Project --format="value(SERVICE)"
    $FinalServicesList = $FinalServices -split "`r?`n" | Where-Object { $_ -ne "" }
    
    Write-Info "Remaining services:"
    foreach ($service in $FinalServicesList) {
        if ($CanonicalServices -contains $service) {
            Write-Success "  ✓ $service (canonical)"
        } else {
            Write-Warning "  ⚠ $service (unexpected - manual review needed)"
        }
    }
}

Write-Info ""
Write-Info "=========================================="
if ($DryRun) {
    Write-Warning "DRY-RUN COMPLETE - No changes made"
    Write-Info "To execute cleanup, run with -DryRun `$false"
} else {
    Write-Success "TRAFFIC SHIFT & CLEANUP COMPLETE"
    Write-Info ""
    Write-Info "Next Steps:"
    Write-Info "1. Verify services are accessible via custom domains"
    Write-Info "2. Update DNS records at domain registrar (see DEPLOYMENT_STATUS.md)"
    Write-Info "3. Monitor logs for any errors"
}
Write-Info "=========================================="
