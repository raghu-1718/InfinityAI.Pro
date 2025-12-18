#!/usr/bin/env pwsh

Write-Host "🔧 InfinityAI.Pro - GitHub CI/CD Pipeline Fix Script" -ForegroundColor Cyan
Write-Host "=" * 60

# Step 1: Generate Firebase CI Token
Write-Host "📋 Step 1: Generate Firebase CI Token" -ForegroundColor Yellow
Write-Host "Run this command and copy the token to GitHub secrets:"
Write-Host "firebase login:ci" -ForegroundColor Green
Write-Host ""
Write-Host "Then add the token as FIREBASE_DEPLOY_TOKEN in GitHub repository secrets."
Write-Host ""

# Step 2: Check Gemini API Keys
Write-Host "📋 Step 2: Verify Gemini API Keys" -ForegroundColor Yellow
$geminiConfig = Get-Content "gemini-api-config.json" | ConvertFrom-Json
$primaryKey = $geminiConfig.gemini_api_keys.primary
$secondaryKey = $geminiConfig.gemini_api_keys.secondary

Write-Host "Primary Key: $($primaryKey.Substring(0,20))..." -ForegroundColor Green
Write-Host "Secondary Key: $($secondaryKey.Substring(0,20))..." -ForegroundColor Green
Write-Host ""

# Step 3: GitHub Secrets Setup
Write-Host "📋 Step 3: Required GitHub Secrets" -ForegroundColor Yellow
Write-Host "Add these secrets to your GitHub repository:"
Write-Host ""
Write-Host "FIREBASE_DEPLOY_TOKEN: [from firebase login:ci]" -ForegroundColor Cyan
if ($primaryKey) { Write-Host "GEMINI_API_KEY_PRIMARY: $($primaryKey.Substring(0,6))... (redacted)" -ForegroundColor Cyan } else { Write-Host "GEMINI_API_KEY_PRIMARY: <not configured>" -ForegroundColor Yellow }
if ($secondaryKey) { Write-Host "GEMINI_API_KEY_SECONDARY: $($secondaryKey.Substring(0,6))... (redacted)" -ForegroundColor Cyan } else { Write-Host "GEMINI_API_KEY_SECONDARY: <not configured>" -ForegroundColor Yellow }
Write-Host "GCP_SA_KEY: [Service Account JSON key]" -ForegroundColor Cyan
Write-Host ""

# Step 4: Fix TypeScript Issues
Write-Host "📋 Step 4: Fix TypeScript Build Issues" -ForegroundColor Yellow
Set-Location "frontend-new"

Write-Host "Installing dependencies..." -ForegroundColor Green
npm install

Write-Host "Running type check..." -ForegroundColor Green
npm run type-check

Write-Host "Building project..." -ForegroundColor Green
npm run build

Set-Location ".."

# Step 5: Test Local Firebase Functions
Write-Host "📋 Step 5: Test Firebase Functions Locally" -ForegroundColor Yellow
Set-Location "functions"

Write-Host "Installing function dependencies..." -ForegroundColor Green
npm install

Write-Host "Starting Firebase emulator..." -ForegroundColor Green
Start-Process -FilePath "firebase" -ArgumentList "emulators:start" -NoNewWindow

Set-Location ".."

# Step 6: Verify Platform Health
Write-Host "📋 Step 6: Platform Health Verification" -ForegroundColor Yellow
Write-Host "Running comprehensive platform check..." -ForegroundColor Green

python3 production_verification_suite.py

Write-Host ""
Write-Host "🎯 Summary of Required Actions:" -ForegroundColor Magenta
Write-Host "1. Run 'firebase login:ci' and add token to GitHub secrets" -ForegroundColor White
Write-Host "2. Add Gemini API keys to GitHub secrets" -ForegroundColor White
Write-Host "3. Create GCP service account key and add to GitHub secrets" -ForegroundColor White
Write-Host "4. Push changes to trigger GitHub Actions workflow" -ForegroundColor White
Write-Host ""
Write-Host "✅ Pipeline fix script completed!" -ForegroundColor Green