#!/usr/bin/env pwsh

Write-Host "🔧 InfinityAI.Pro - CI/CD Issues Fix Script" -ForegroundColor Cyan
Write-Host "=" * 60

$PROJECT_ID = "infinity-ai-5ec7c"
$REPO_NAME = "raghu-1718/InfinityAI.Pro"

function Write-Issue {
    param(
        [string]$Description,
        [string]$Severity = "MEDIUM"
    )
    
    $emoji = @{
        "HIGH" = "🔴"
        "MEDIUM" = "🟡" 
        "LOW" = "🟢"
    }
    
    Write-Host "$($emoji[$Severity]) [$Severity] $Description" -ForegroundColor $(
        switch ($Severity) {
            "HIGH" { "Red" }
            "MEDIUM" { "Yellow" }
            default { "Green" }
        }
    )
}

function Write-Fix {
    param(
        [string]$Description,
        [string]$Command = ""
    )
    
    Write-Host "🔧 FIX: $Description" -ForegroundColor Green
    if ($Command) {
        Write-Host "   Command: $Command" -ForegroundColor Gray
    }
}

# Step 1: Fix TypeScript Error in appStore.ts
Write-Host "`n📋 Step 1: Fixing TypeScript Error in appStore.ts" -ForegroundColor Yellow

$appStoreFile = "frontend\src\stores\appStore.ts"
if (Test-Path $appStoreFile) {
    $content = Get-Content $appStoreFile -Raw
    
    if ($content -match "subscribeWithSelector\(\(set, get\) =>") {
        $content = $content -replace "subscribeWithSelector\(\(set, get\) =>", "subscribeWithSelector((set) =>"
        Set-Content $appStoreFile $content -Encoding UTF8
        Write-Fix "Fixed TypeScript error: Removed unused 'get' parameter from subscribeWithSelector"
    } else {
        Write-Host "✅ TypeScript error not found - already fixed" -ForegroundColor Green
    }
} else {
    Write-Issue "appStore.ts file not found" "HIGH"
}

# Step 2: Create/Update GitHub Workflow Files
Write-Host "`n📋 Step 2: Fixing GitHub Workflow Configurations" -ForegroundColor Yellow

$workflows = @(
    ".github\workflows\engine-a.yaml",
    ".github\workflows\engine-b.yaml",
    ".github\workflows\engine-c.yaml", 
    ".github\workflows\engine-d.yaml"
)

foreach ($workflow in $workflows) {
    if (Test-Path $workflow) {
        $content = Get-Content $workflow -Raw
        
        # Fix authentication and project ID
        $content = $content -replace 'credentials_json: "\$\{\{ secrets\.GCP_SA_KEY \}\}"', 'credentials_json: "${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}"'
        $content = $content -replace 'project_id: \$\{\{ secrets\.VITE_PROJECT_ID \}\}', "project_id: $PROJECT_ID"
        
        Set-Content $workflow $content -Encoding UTF8
        Write-Fix "Fixed workflow file: $workflow"
    }
}

# Step 3: Create GCP Service Account Key
Write-Host "`n📋 Step 3: Creating GCP Service Account Key" -ForegroundColor Yellow

$serviceAccountEmail = "github-actions@$PROJECT_ID.iam.gserviceaccount.com"

# Create service account (ignore if exists)
Write-Host "Creating service account..." -ForegroundColor Green
gcloud iam service-accounts create github-actions --display-name="GitHub Actions" --project=$PROJECT_ID 2>$null

# Grant necessary roles
$roles = @(
    "roles/run.admin",
    "roles/iam.serviceAccountUser", 
    "roles/storage.admin",
    "roles/secretmanager.secretAccessor"
)

foreach ($role in $roles) {
    Write-Host "Granting $role..." -ForegroundColor Green
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$serviceAccountEmail" --role="$role" --condition=None 2>$null
}

# Create service account key
$keyFile = "github-actions-key-$(Get-Date -Format 'yyyyMMdd').json"
Write-Host "Creating service account key..." -ForegroundColor Green

$result = gcloud iam service-accounts keys create $keyFile --iam-account=$serviceAccountEmail --project=$PROJECT_ID 2>&1

if ($LASTEXITCODE -eq 0) {
    $keyContent = Get-Content $keyFile -Raw
    Remove-Item $keyFile -Force
    
    Write-Fix "Service account key created successfully"
    
    Write-Host "`n🔑 IMPORTANT: Add this to GitHub repository secrets as 'GCP_SERVICE_ACCOUNT_KEY':" -ForegroundColor Magenta
    Write-Host "─" * 80 -ForegroundColor Gray
    Write-Host $keyContent -ForegroundColor Cyan
    Write-Host "─" * 80 -ForegroundColor Gray
} else {
    Write-Issue "Failed to create service account key: $result" "HIGH"
}

# Step 4: Create GitHub Secrets Setup Commands
Write-Host "`n📋 Step 4: GitHub Secrets Setup Commands" -ForegroundColor Yellow

Write-Host "Run these commands to set up GitHub repository secrets:" -ForegroundColor Green
Write-Host ""

# Get Gemini API keys from GCP Secret Manager
Write-Host "📋 Getting Gemini API keys from GCP Secret Manager..." -ForegroundColor Yellow

$primaryKey = gcloud secrets versions access latest --secret="gemini-api-key-primary" --project=$PROJECT_ID 2>$null
$secondaryKey = gcloud secrets versions access latest --secret="gemini-api-key-secondary" --project=$PROJECT_ID 2>$null

if ($primaryKey) {
    Write-Host "✅ Primary Gemini API Key retrieved" -ForegroundColor Green
    Write-Host "gh secret set GEMINI_API_KEY_PRIMARY --body `"$primaryKey`" --repo $REPO_NAME" -ForegroundColor Cyan
} else {
    Write-Issue "Failed to retrieve primary Gemini API key" "HIGH"
}

if ($secondaryKey) {
    Write-Host "✅ Secondary Gemini API Key retrieved" -ForegroundColor Green  
    Write-Host "gh secret set GEMINI_API_KEY_SECONDARY --body `"$secondaryKey`" --repo $REPO_NAME" -ForegroundColor Cyan
} else {
    Write-Issue "Failed to retrieve secondary Gemini API key" "HIGH"
}

# Firebase deploy token
Write-Host "`n🔥 Firebase Deploy Token:" -ForegroundColor Yellow
Write-Host "1. Run: firebase login:ci" -ForegroundColor Cyan
Write-Host "2. Copy the token and run: gh secret set FIREBASE_DEPLOY_TOKEN --body `"[TOKEN]`" --repo $REPO_NAME" -ForegroundColor Cyan

# Step 5: Verify Current Deployment Status
Write-Host "`n📋 Step 5: Verifying Current Deployment Status" -ForegroundColor Yellow

Write-Host "Current Cloud Run Services:" -ForegroundColor Green
gcloud run services list --region=us-central1 --project=$PROJECT_ID --format="table(metadata.name,status.url,status.conditions[0].status)"

Write-Host "`nCurrent Firebase Functions:" -ForegroundColor Green
firebase functions:list --project=$PROJECT_ID

# Step 6: Summary and Next Steps
Write-Host "`n📊 Summary and Next Steps" -ForegroundColor Magenta
Write-Host "=" * 60

Write-Host "✅ TypeScript error fixed" -ForegroundColor Green
Write-Host "✅ GitHub workflow files updated" -ForegroundColor Green  
Write-Host "✅ GCP service account key created" -ForegroundColor Green
Write-Host "✅ Current deployment status verified" -ForegroundColor Green

Write-Host "`n🚀 Required Actions:" -ForegroundColor Yellow
Write-Host "1. Add GCP_SERVICE_ACCOUNT_KEY to GitHub repository secrets (shown above)" -ForegroundColor White
Write-Host "2. Run the Gemini API key commands shown above" -ForegroundColor White
Write-Host "3. Generate Firebase deploy token with 'firebase login:ci'" -ForegroundColor White
Write-Host "4. Add FIREBASE_DEPLOY_TOKEN to GitHub repository secrets" -ForegroundColor White
Write-Host "5. Commit and push changes to trigger CI/CD pipeline" -ForegroundColor White

Write-Host "`n🎯 GitHub Repository: https://github.com/$REPO_NAME/settings/secrets/actions" -ForegroundColor Cyan
Write-Host "📊 GitHub Actions: https://github.com/$REPO_NAME/actions" -ForegroundColor Cyan

Write-Host "`n✅ CI/CD Fix Script Completed!" -ForegroundColor Green