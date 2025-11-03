#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create Cloud Monitoring uptime checks for all services
.DESCRIPTION
    Sets up automated uptime monitoring with alerts for all InfinityAI services
#>

$PROJECT = "after-yesterday-473512-k3"
$REGION = "us-central1"

$SERVICES = @(
    @{Name="infinityai-pro-frontend"; URL="https://infinityai.pro"; Type="HTTPS"},
    @{Name="infinityai-pro-www"; URL="https://www.infinityai.pro"; Type="HTTPS"},
    @{Name="engine-a-health"; URL="https://engine-a.infinityai.pro/health"; Type="HTTPS"},
    @{Name="engine-b-health"; URL="https://engine-b.infinityai.pro/health"; Type="HTTPS"},
    @{Name="engine-c-health"; URL="https://engine-c.infinityai.pro/health"; Type="HTTPS"},
    @{Name="engine-d-health"; URL="https://engine-d.infinityai.pro/health"; Type="HTTPS"}
)

Write-Host "`n=== Cloud Monitoring Setup ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT`n" -ForegroundColor Gray

# Create uptime checks
Write-Host "[Creating Uptime Checks]" -ForegroundColor Cyan
$created = 0
$failed = 0

foreach ($service in $SERVICES) {
    Write-Host "`n  $($service.Name)" -ForegroundColor White
    Write-Host "  URL: $($service.URL)" -ForegroundColor Gray
    
    try {
        # Check if uptime check already exists
        $existing = gcloud monitoring uptime list --project=$PROJECT --format="value(name)" 2>&1 | 
            Where-Object { $_ -match $service.Name }
        
        if ($existing) {
            Write-Host "  ⚠️  Already exists, skipping" -ForegroundColor Yellow
            continue
        }
        
        # Create uptime check
        $result = gcloud monitoring uptime create $service.Name `
            --project=$PROJECT `
            --resource-type="uptime-url" `
            --host=$service.URL.Replace("https://", "").Replace("/health", "") `
            --path=$(if ($service.URL -match "/health") { "/health" } else { "/" }) `
            --port=443 `
            --check-interval=5m `
            --timeout=10s `
            --quiet 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Created uptime check" -ForegroundColor Green
            $created++
        } else {
            Write-Host "  ❌ Failed: $result" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

# Create notification channel
Write-Host "`n[Creating Notification Channel]" -ForegroundColor Cyan

try {
    # Check for existing notification channels
    $channels = gcloud alpha monitoring channels list --project=$PROJECT --format="value(name)" 2>&1
    
    if ($channels -match "email") {
        Write-Host "  ⚠️  Email notification channel already exists" -ForegroundColor Yellow
    } else {
        Write-Host "  Creating email notification channel..." -ForegroundColor White
        Write-Host "  (Manual configuration required in Cloud Console)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️  Unable to check notification channels" -ForegroundColor Yellow
}

# Create alert policy
Write-Host "`n[Creating Alert Policies]" -ForegroundColor Cyan

$alertPolicies = @(
    @{
        Name="uptime-check-failures"
        Condition="Uptime check failures > 1 in 5 minutes"
        Description="Alert when any uptime check fails"
    },
    @{
        Name="high-error-rate"
        Condition="Error rate > 5% for 5 minutes"
        Description="Alert when error rate exceeds 5%"
    },
    @{
        Name="high-latency"
        Condition="Latency > 3s for 5 minutes"
        Description="Alert when response time exceeds 3 seconds"
    }
)

foreach ($policy in $alertPolicies) {
    Write-Host "`n  $($policy.Name)" -ForegroundColor White
    Write-Host "  $($policy.Description)" -ForegroundColor Gray
    
    try {
        $existing = gcloud alpha monitoring policies list --project=$PROJECT --format="value(displayName)" 2>&1 | 
            Where-Object { $_ -match $policy.Name }
        
        if ($existing) {
            Write-Host "  ⚠️  Already exists" -ForegroundColor Yellow
        } else {
            Write-Host "  ℹ️  Manual configuration required in Cloud Console" -ForegroundColor Cyan
            Write-Host "     https://console.cloud.google.com/monitoring/alerting?project=$PROJECT" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ℹ️  Configure manually in Cloud Console" -ForegroundColor Cyan
    }
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Green
Write-Host "Monitoring Setup Summary" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "Uptime Checks Created: $created" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Configure email notifications in Cloud Console" -ForegroundColor White
Write-Host "2. Set up alert policies for uptime checks" -ForegroundColor White
Write-Host "3. Configure budget alerts" -ForegroundColor White
Write-Host "`nCloud Console Monitoring: " -ForegroundColor Gray
Write-Host "https://console.cloud.google.com/monitoring?project=$PROJECT" -ForegroundColor Cyan

Write-Host "`nDone!" -ForegroundColor Green
