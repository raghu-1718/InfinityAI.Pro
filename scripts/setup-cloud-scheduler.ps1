# Cloud Scheduler Setup for Background Trading
# Run this script to set up automated trading execution during market hours

$PROJECT_ID = "gen-lang-client-0779271931"
$REGION = "us-central1"
$ENGINE_C_URL = "https://engine-c.infinityai.pro"

Write-Host "Setting up Cloud Scheduler for Background Trading..." -ForegroundColor Cyan

# Create scheduler job for trading execution (every 5 minutes during market hours)
# Market hours: 9:15 AM - 3:30 PM IST (3:45 AM - 10:00 AM UTC)
gcloud scheduler jobs create http background-trading-executor `
    --project=$PROJECT_ID `
    --location=$REGION `
    --schedule="*/5 3-10 * * 1-5" `
    --uri="$ENGINE_C_URL/api/background-trading/execute-cycle" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{}' `
    --time-zone="UTC" `
    --description="Execute background trading for all active sessions every 5 minutes during market hours" `
    --attempt-deadline="300s"

Write-Host "✅ Created background-trading-executor job" -ForegroundColor Green

# Create scheduler job for pre-market analysis (8:30 AM IST = 3:00 AM UTC)
gcloud scheduler jobs create http pre-market-analysis `
    --project=$PROJECT_ID `
    --location=$REGION `
    --schedule="0 3 * * 1-5" `
    --uri="$ENGINE_C_URL/api/background-trading/execute-cycle" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{"pre_market": true}' `
    --time-zone="UTC" `
    --description="Pre-market analysis and signal generation" `
    --attempt-deadline="300s"

Write-Host "✅ Created pre-market-analysis job" -ForegroundColor Green

# Create scheduler job for daily summary (4:00 PM IST = 10:30 AM UTC)
gcloud scheduler jobs create http daily-trading-summary `
    --project=$PROJECT_ID `
    --location=$REGION `
    --schedule="30 10 * * 1-5" `
    --uri="$ENGINE_C_URL/api/background-trading/execute-cycle" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{"daily_summary": true}' `
    --time-zone="UTC" `
    --description="Generate daily trading summary after market close" `
    --attempt-deadline="300s"

Write-Host "✅ Created daily-trading-summary job" -ForegroundColor Green

# List all jobs
Write-Host "`nScheduled Jobs:" -ForegroundColor Cyan
gcloud scheduler jobs list --project=$PROJECT_ID --location=$REGION

Write-Host "`n✅ Cloud Scheduler setup complete!" -ForegroundColor Green
Write-Host "Background trading will now execute automatically during market hours." -ForegroundColor Yellow
Write-Host "Users just need to click 'Start Trading' once - it will continue even if browser is closed." -ForegroundColor Yellow
