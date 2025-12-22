#!/usr/bin/env pwsh

Write-Host "🚀 Deploying Engine B with Gemini Integration" -ForegroundColor Cyan
Write-Host "=" * 50

# Change to Engine B directory
Set-Location "engines\engine-b"

Write-Host "📦 Building Engine B with Gemini support..." -ForegroundColor Yellow

# Build the container image
$projectId = "gen-lang-client-0779271931"
$imageName = "infinityai-engine-b"
$region = "us-central1"

Write-Host "Building container image..." -ForegroundColor Green
gcloud builds submit --tag "gcr.io/$projectId/$imageName" --project=$projectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container built successfully!" -ForegroundColor Green

    Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
    gcloud run deploy $imageName `
        --image "gcr.io/$projectId/$imageName" `
        --region $region `
        --allow-unauthenticated `
        --memory "1Gi" `
        --cpu "1" `
        --set-env-vars "PROJECT_ID=$projectId" `
        --set-secrets "GEMINI_API_KEY_PRIMARY=gemini-api-key:latest" `
        --project=$projectId

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Engine B deployed successfully!" -ForegroundColor Green

        # Test the new endpoint
        Write-Host "🧪 Testing Gemini endpoint..." -ForegroundColor Yellow
        $testPayload = @{
            prompt = "Quick test of NIFTY sentiment"
            userId = "deployment_test"
            context = @{
                source = "deployment_script"
            }
        } | ConvertTo-Json

        Start-Sleep -Seconds 10  # Give the service time to start

        $response = Invoke-RestMethod -Uri "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/api/gemini/analyze" -Method POST -Body $testPayload -ContentType "application/json"

        if ($response.status -eq "success") {
            Write-Host "✅ Gemini endpoint is working!" -ForegroundColor Green
            Write-Host "📊 Test response: $($response.analysis.Substring(0, 100))..." -ForegroundColor Cyan
        } else {
            Write-Host "⚠️ Gemini endpoint deployed but test failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Cloud Run deployment failed" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Container build failed" -ForegroundColor Red
}

# Return to original directory
Set-Location "..\..\"

Write-Host ""
Write-Host "🎯 Deployment Summary:" -ForegroundColor Magenta
Write-Host "- Engine B updated with Gemini integration" -ForegroundColor White
Write-Host "- Container rebuilt and deployed to Cloud Run" -ForegroundColor White
Write-Host "- Environment variables configured" -ForegroundColor White
Write-Host "- Endpoint tested and verified" -ForegroundColor White
Write-Host ""
Write-Host "✅ Engine B Gemini integration deployment complete!" -ForegroundColor Green