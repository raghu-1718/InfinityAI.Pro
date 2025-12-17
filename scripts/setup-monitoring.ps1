#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Cloud Monitoring uptime checks and alert policies for InfinityAI.Pro
.DESCRIPTION
    Creates uptime checks for all production services and configures alert policies
.NOTES
    Run this after initial deployment to enable production monitoring
#>

$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"
$NOTIFICATION_EMAIL = "<MONITORING_ALERT_EMAIL>"

Write-Host "🔍 Setting up Cloud Monitoring for InfinityAI.Pro..." -ForegroundColor Cyan

# Create notification channel for email alerts
Write-Host "`n📧 Creating email notification channel..." -ForegroundColor Yellow
$channelOutput = gcloud alpha monitoring channels create `
    --display-name="InfinityAI Production Alerts" `
    --type=email `
    --channel-labels=email_address=$NOTIFICATION_EMAIL `
    --format="value(name)" 2>&1

if ($LASTEXITCODE -eq 0) {
    $CHANNEL_ID = $channelOutput | Select-Object -Last 1
    Write-Host "✅ Notification channel created: $CHANNEL_ID" -ForegroundColor Green
} else {
    Write-Host "⚠️ Channel may already exist, fetching existing..." -ForegroundColor Yellow
    $CHANNEL_ID = (gcloud alpha monitoring channels list --filter="displayName='InfinityAI Production Alerts'" --format="value(name)" | Select-Object -First 1)
}

# Define services to monitor
$services = @(
    @{
        name = "engine-a-market-data-prod"
        url = "engine-a-market-data-prod-bprmddefsa-uc.a.run.app"
        path = "/health"
        display = "Engine A - Market Data"
    },
    @{
        name = "engine-b-ai-ml-prod"
        url = "engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app"
        path = "/health"
        display = "Engine B - AI/ML"
    },
    @{
        name = "engine-c-execution-prod"
        url = "engine-c-execution-prod-bprmddefsa-uc.a.run.app"
        path = "/health"
        display = "Engine C - Execution"
    },
    @{
        name = "engine-c-execution  # Engine D merged-prod"
        url = "engine-c-execution  # Engine D merged-prod-bprmddefsa-uc.a.run.app"
        path = "/health"
        display = "Engine D - Orchestration"
    },
    @{
        name = "frontend-new-prod"
        url = "frontend-new-prod-bprmddefsa-uc.a.run.app"
        path = "/"
        display = "Frontend Application"
    },
    @{
        name = "infinityai-domain"
        url = "infinityai.pro"
        path = "/"
        display = "Custom Domain (infinityai.pro)"
    }
)

# Create uptime checks for each service
Write-Host "`n🔍 Creating uptime checks..." -ForegroundColor Yellow
foreach ($service in $services) {
    Write-Host "  Creating check for $($service.display)..." -ForegroundColor Gray

    gcloud monitoring uptime create $service.name `
        --resource-type=uptime-url `
        --resource-labels="host=$($service.url)" `
        --http-check-path=$service.path `
        --period=60 `
        --timeout=10s `
        --display-name=$service.display `
        --project=$PROJECT_ID 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $($service.display)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $($service.display) (may already exist)" -ForegroundColor Yellow
    }
}

# Create alert policy for service downtime
Write-Host "`n🚨 Creating alert policy..." -ForegroundColor Yellow

$alertPolicy = @"
{
  "displayName": "InfinityAI Service Downtime Alert",
  "conditions": [
    {
      "displayName": "Uptime check failed",
      "conditionThreshold": {
        "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\"",
        "comparison": "COMPARISON_LT",
        "thresholdValue": 1,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_FRACTION_TRUE"
          }
        ]
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": ["$CHANNEL_ID"],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
"@

$alertPolicy | Out-File -FilePath "alert-policy.json" -Encoding UTF8

gcloud alpha monitoring policies create --policy-from-file=alert-policy.json --project=$PROJECT_ID 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Alert policy created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ Alert policy may already exist" -ForegroundColor Yellow
}

Remove-Item "alert-policy.json" -ErrorAction SilentlyContinue

# Set up budget alert
Write-Host "`n💰 Setting up budget alert..." -ForegroundColor Yellow
Write-Host "  Budget: `$200/month with alerts at 50%, 90%, 100%" -ForegroundColor Gray

# Note: Budget creation requires billing account ID - run manually if needed
Write-Host "  ℹ️ Budget alerts should be created via Console: https://console.cloud.google.com/billing/" -ForegroundColor Cyan

Write-Host "`n✅ Monitoring setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Check Cloud Monitoring Console: https://console.cloud.google.com/monitoring" -ForegroundColor White
Write-Host "  2. Verify uptime checks are running" -ForegroundColor White
Write-Host "  3. Test alert by stopping a service temporarily" -ForegroundColor White
Write-Host "  4. Configure budget alerts in Billing console" -ForegroundColor White
