#!/usr/bin/env pwsh
# InfinityAI.Pro - Final Fix & Verify
# Reverts Engine A Dockerfile to known working format and verifies with dynamic URLs.

$ErrorActionPreference = "Stop"
Write-Host "InfinityAI.Pro - Final Fix & Verification" -ForegroundColor Cyan
Write-Host "========================================="

$PROJECT_ID = "gen-lang-client-0779271931"
$REGION = "us-central1"

# 1. Fix Engine A Dockerfile (Match Engine B Pattern)
Write-Host "`n[1/3] Fixing Engine A Dockerfile..." -ForegroundColor Yellow
$dockerfile_content = @"
# =====================================================================
# InfinityAI.Pro - Engine A (Orchestration & Risk Management)
# ML: Scikit-learn, NumPy, Pandas, CVXPY (Portfolio Optimization)
# =====================================================================
FROM python:3.11-slim

# Install build dependencies for CVXPY
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./src /app/src

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"]
"@
Set-Content -Path "backend\engine-a\Dockerfile" -Value $dockerfile_content
Write-Host "  > Dockerfile updated." -ForegroundColor Green

# 2. Redeploy Engine A
Write-Host "`n[2/3] Redeploying Engine A..." -ForegroundColor Yellow
Push-Location "backend\engine-a"
try {
    $service = "engine-a"
    $tag = "gcr.io/$PROJECT_ID/$service"
    
    Write-Host "  > Building..."
    gcloud builds submit --tag $tag --project=$PROJECT_ID --quiet
    
    Write-Host "  > Deploying..."
    gcloud run deploy $service `
        --image $tag `
        --region $REGION `
        --project $PROJECT_ID `
        --allow-unauthenticated `
        --memory "2Gi" `
        --cpu "1" `
        --timeout 600 `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
        --quiet
        
    Write-Host "  > SUCCESS" -ForegroundColor Green
}
catch {
    Write-Host "  > FAILED: $_" -ForegroundColor Red
}
Pop-Location

# 3. Dynamic Verification
Write-Host "`n[3/3] Dynamic Verification..." -ForegroundColor Yellow

# Fetch URLs dynamically
$Services = @("engine-a", "engine-b", "engine-c")
foreach ($svc in $Services) {
    try {
        $url = gcloud run services describe $svc --region $REGION --format="value(status.url)"
        if (-not $url) {
            Write-Host "  [ERR] Could not find URL for $svc" -ForegroundColor Red
            continue
        }
        
        $health_path = "/health"
        if ($svc -eq "engine-b") { $health_path = "/healthz" }
        
        $check_url = "$url$health_path"
        Write-Host "  Checking $svc ($check_url)..."
        
        $res = Invoke-WebRequest -Uri $check_url -Method Get -TimeoutSec 10
        if ($res.StatusCode -eq 200) {
            Write-Host "  [OK] $svc is Healthy" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] $svc returned $($res.StatusCode)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  [ERR] Failed to verify $svc : $_" -ForegroundColor Red
    }
}

Write-Host "`nMission Complete." -ForegroundColor Cyan
