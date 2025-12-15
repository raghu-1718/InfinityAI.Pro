# Setup Cloud Scheduler for AI-Agent Automated Trading
# This script creates scheduler jobs for automated trading cycles

param(
    [string]$ProjectId = "gen-lang-client-0779271931",
    [string]$Region = "asia-south1",
    [string]$ServiceAccount = "429140669077-compute@developer.gserviceaccount.com"
)

$EngineCUrl = "https://engine-c.infinityai.pro"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI-Agent Automated Trading Setup" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

# ============================================
# Job 1: AI Agent Trading Cycle (Every 5 minutes during market hours)
# ============================================
Write-Host "`n📊 Creating AI Agent Trading Cycle Job..." -ForegroundColor Yellow

$aiTradingBody = @{
    user_id = "1101302170"
    watchlist = @("RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK")
    config = @{
        min_confidence = 0.7
        max_risk_per_trade = 0.02
        max_daily_trades = 10
        trading_amount = 1000
        strategy = "ai-agent-signals"
    }
} | ConvertTo-Json -Compress

# Delete existing job if present
gcloud scheduler jobs delete ai-agent-trading-cycle --location=$Region --quiet 2>$null

# Create new job - runs every 5 minutes during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
gcloud scheduler jobs create http ai-agent-trading-cycle `
    --location=$Region `
    --schedule="*/5 9-15 * * 1-5" `
    --time-zone="Asia/Kolkata" `
    --uri="$EngineCUrl/api/agent/auto-trade" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body=$aiTradingBody `
    --attempt-deadline="300s" `
    --oidc-service-account-email=$ServiceAccount `
    --description="AI Agent automated trading cycle - runs every 5 minutes during market hours"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ AI Agent Trading Cycle job created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create AI Agent Trading Cycle job" -ForegroundColor Red
}

# ============================================
# Job 2: Pre-Market Analysis (8:30 AM IST)
# ============================================
Write-Host "`n📈 Creating Pre-Market Analysis Job..." -ForegroundColor Yellow

$preMarketBody = @{
    user_id = "1101302170"
    message = "Provide pre-market analysis for today. Check global cues, SGX NIFTY, US markets overnight performance, and list the top 5 stocks to watch today with entry levels."
    context = @{
        analysis_type = "pre_market"
        market = "NSE"
    }
} | ConvertTo-Json -Compress

gcloud scheduler jobs delete pre-market-analysis --location=$Region --quiet 2>$null

gcloud scheduler jobs create http pre-market-analysis `
    --location=$Region `
    --schedule="30 8 * * 1-5" `
    --time-zone="Asia/Kolkata" `
    --uri="$EngineCUrl/api/agent/chat" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body=$preMarketBody `
    --attempt-deadline="120s" `
    --oidc-service-account-email=$ServiceAccount `
    --description="Pre-market analysis from AI Agent - runs daily at 8:30 AM IST"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Pre-Market Analysis job created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Pre-Market Analysis job" -ForegroundColor Red
}

# ============================================
# Job 3: Post-Market Summary (4:00 PM IST)
# ============================================
Write-Host "`n📊 Creating Post-Market Summary Job..." -ForegroundColor Yellow

$postMarketBody = @{
    user_id = "1101302170"
    message = "Provide end of day market summary. Summarize today's performance, key movers, FII/DII data, and outlook for tomorrow."
    context = @{
        analysis_type = "post_market"
        market = "NSE"
    }
} | ConvertTo-Json -Compress

gcloud scheduler jobs delete post-market-summary --location=$Region --quiet 2>$null

gcloud scheduler jobs create http post-market-summary `
    --location=$Region `
    --schedule="0 16 * * 1-5" `
    --time-zone="Asia/Kolkata" `
    --uri="$EngineCUrl/api/agent/chat" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body=$postMarketBody `
    --attempt-deadline="120s" `
    --oidc-service-account-email=$ServiceAccount `
    --description="Post-market summary from AI Agent - runs daily at 4:00 PM IST"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Post-Market Summary job created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Post-Market Summary job" -ForegroundColor Red
}

# ============================================
# Job 4: Weekly Portfolio Review (Saturday 10:00 AM IST)
# ============================================
Write-Host "`n📋 Creating Weekly Portfolio Review Job..." -ForegroundColor Yellow

$portfolioReviewBody = @{
    user_id = "1101302170"
    message = "Provide a comprehensive weekly portfolio review. Analyze performance, suggest rebalancing if needed, identify underperforming positions, and recommend new opportunities for next week."
    context = @{
        analysis_type = "portfolio_review"
        timeframe = "weekly"
    }
} | ConvertTo-Json -Compress

gcloud scheduler jobs delete weekly-portfolio-review --location=$Region --quiet 2>$null

gcloud scheduler jobs create http weekly-portfolio-review `
    --location=$Region `
    --schedule="0 10 * * 6" `
    --time-zone="Asia/Kolkata" `
    --uri="$EngineCUrl/api/agent/chat" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body=$portfolioReviewBody `
    --attempt-deadline="300s" `
    --oidc-service-account-email=$ServiceAccount `
    --description="Weekly portfolio review from AI Agent - runs every Saturday at 10:00 AM IST"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Weekly Portfolio Review job created" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Weekly Portfolio Review job" -ForegroundColor Red
}

# ============================================
# List all jobs
# ============================================
Write-Host "`n📋 Current Cloud Scheduler Jobs:" -ForegroundColor Cyan
gcloud scheduler jobs list --location=$Region --format="table(name,schedule,state,lastAttemptTime)"

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  AI-Agent Scheduler Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "`nJobs Created:"
Write-Host "  • ai-agent-trading-cycle: Every 5 min (9:15 AM - 3:30 PM)" -ForegroundColor White
Write-Host "  • pre-market-analysis: Daily at 8:30 AM" -ForegroundColor White
Write-Host "  • post-market-summary: Daily at 4:00 PM" -ForegroundColor White
Write-Host "  • weekly-portfolio-review: Saturday at 10:00 AM" -ForegroundColor White
