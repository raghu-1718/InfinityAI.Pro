#!/usr/bin/env pwsh

Write-Host "🚀 InfinityAI.Pro - Complete End-to-End Deployment" -ForegroundColor Cyan
Write-Host "=" * 80

$PROJECT_ID = "infinity-ai-5ec7c"
$REGION = "us-central1"

# Function to print status
function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "Info"
    )

    $emoji = @{
        "Success" = "✅"
        "Error" = "❌"
        "Warning" = "⚠️"
        "Info" = "🔍"
    }

    Write-Host "$($emoji[$Status]) $Message" -ForegroundColor $(
        switch ($Status) {
            "Success" { "Green" }
            "Error" { "Red" }
            "Warning" { "Yellow" }
            default { "White" }
        }
    )
}

# Step 1: Deploy all engines with latest code
Write-Host "`n📦 Deploying All Engines..." -ForegroundColor Yellow

$engines = @("engine-a", "engine-b", "engine-c-execution", "engine-d")

foreach ($engine in $engines) {
    Write-Status "Deploying $engine..." "Info"

    Set-Location "engines\$engine"

    # Build container
    $buildResult = gcloud builds submit --tag "gcr.io/$PROJECT_ID/infinityai-$engine" --project=$PROJECT_ID 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Status "$engine container built successfully" "Success"

        # Deploy to Cloud Run
        $deployArgs = @(
            "run", "deploy", "infinityai-$engine",
            "--image", "gcr.io/$PROJECT_ID/infinityai-$engine",
            "--region", $REGION,
            "--project", $PROJECT_ID,
            "--allow-unauthenticated",
            "--memory", "1Gi",
            "--cpu", "1",
            "--set-env-vars", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
        )

        $deployResult = & gcloud @deployArgs 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "$engine deployed successfully" "Success"
        } else {
            Write-Status "$engine deployment failed: $deployResult" "Error"
        }
    } else {
        Write-Status "$engine build failed: $buildResult" "Error"
    }

    Set-Location "..\..\"
}

# Step 2: Deploy Firebase Functions
Write-Host "`n🔥 Deploying Firebase Functions..." -ForegroundColor Yellow

$functionsResult = firebase deploy --only functions --project=$PROJECT_ID 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Status "Firebase Functions deployed successfully" "Success"
} else {
    Write-Status "Firebase Functions deployment failed: $functionsResult" "Error"
}

# Step 3: Deploy Frontend
Write-Host "`n🌐 Deploying Frontend..." -ForegroundColor Yellow

Set-Location "frontend-new"

# Build frontend
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Status "Frontend built successfully" "Success"

    # Deploy frontend container
    $frontendBuildResult = gcloud builds submit --tag "gcr.io/$PROJECT_ID/infinityai-frontend" --project=$PROJECT_ID 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Status "Frontend container built successfully" "Success"

        $frontendDeployArgs = @(
            "run", "deploy", "infinityai-frontend",
            "--image", "gcr.io/$PROJECT_ID/infinityai-frontend",
            "--region", $REGION,
            "--project", $PROJECT_ID,
            "--allow-unauthenticated",
            "--memory", "1Gi",
            "--cpu", "1",
            "--set-env-vars", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
        )

        $frontendDeployResult = & gcloud @frontendDeployArgs 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Frontend deployed successfully" "Success"
        } else {
            Write-Status "Frontend deployment failed: $frontendDeployResult" "Error"
        }
    } else {
        Write-Status "Frontend container build failed: $frontendBuildResult" "Error"
    }
} else {
    Write-Status "Frontend build failed" "Error"
}

Set-Location ".."

# Step 4: Deploy Firebase Hosting
Write-Host "`n🏠 Deploying Firebase Hosting..." -ForegroundColor Yellow

$hostingResult = firebase deploy --only hosting --project=$PROJECT_ID 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Status "Firebase Hosting deployed successfully" "Success"
} else {
    Write-Status "Firebase Hosting deployment failed: $hostingResult" "Error"
}

# Step 5: Update Firestore rules and indexes
Write-Host "`n🗄️ Deploying Firestore Configuration..." -ForegroundColor Yellow

$firestoreRulesResult = firebase deploy --only firestore:rules --project=$PROJECT_ID 2>&1
$firestoreIndexesResult = firebase deploy --only firestore:indexes --project=$PROJECT_ID 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Status "Firestore rules and indexes deployed successfully" "Success"
} else {
    Write-Status "Firestore deployment failed" "Error"
}

# Step 6: Test all endpoints
Write-Host "`n🧪 Testing All Endpoints..." -ForegroundColor Yellow

$endpoints = @{
    "Engine A" = "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app/health"
    "Engine B" = "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/health"
    "Engine C" = "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/health"
    "Engine D" = "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health"
    "Frontend" = "https://infinityai-frontend-ckxt6xvshq-uc.a.run.app"
}

foreach ($name in $endpoints.Keys) {
    $url = $endpoints[$name]
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Status "$name: Healthy" "Success"
        } else {
            Write-Status "$name: Unhealthy (Status: $($response.StatusCode))" "Error"
        }
    } catch {
        Write-Status "$name: Connection failed - $($_.Exception.Message)" "Error"
    }
}

# Step 7: Test Gemini Integration
Write-Host "`n🤖 Testing Gemini Integration..." -ForegroundColor Yellow

$geminiPayload = @{
    prompt = "Test deployment verification"
    userId = "deployment_test"
    context = @{
        source = "deployment_script"
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
} | ConvertTo-Json

try {
    $geminiResponse = Invoke-RestMethod -Uri "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/api/gemini/analyze" -Method POST -Body $geminiPayload -ContentType "application/json" -TimeoutSec 30

    if ($geminiResponse.status -eq "success") {
        Write-Status "Gemini Integration: Working" "Success"
        Write-Host "📊 Test Response: $($geminiResponse.analysis.Substring(0, 100))..." -ForegroundColor Cyan
    } else {
        Write-Status "Gemini Integration: Failed" "Error"
    }
} catch {
    Write-Status "Gemini Integration: Error - $($_.Exception.Message)" "Error"
}

# Step 8: Generate deployment summary
Write-Host "`n📊 Deployment Summary" -ForegroundColor Magenta

Write-Host "Project ID: $PROJECT_ID" -ForegroundColor White
Write-Host "Region: $REGION" -ForegroundColor White
Write-Host "Deployment Time: $(Get-Date)" -ForegroundColor White

# List all Cloud Run services
Write-Host "`n🔍 Current Cloud Run Services:" -ForegroundColor Yellow
gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.url,status.conditions[0].status)"

# List Firebase Functions
Write-Host "`n🔥 Current Firebase Functions:" -ForegroundColor Yellow
firebase functions:list --project=$PROJECT_ID

Write-Host "`n✅ Complete End-to-End Deployment Finished!" -ForegroundColor Green
Write-Host "🎯 All components have been deployed and tested." -ForegroundColor White
Write-Host "📋 Check the output above for any deployment issues." -ForegroundColor White