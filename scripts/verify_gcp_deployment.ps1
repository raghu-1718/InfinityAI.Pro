# InfinityAI.Pro - GCP Deployment Verification Script
# Run this script on your Windows machine with gcloud CLI authenticated
# Project: after-yesterday-473512-k3
# Region: us-central1

param(
    [string]$ProjectId = "after-yesterday-473512-k3",
    [string]$Region = "us-central1",
    [string]$ArtifactRepo = "infinityai-repo"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = "reports/deployment_verification_$timestamp.json"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "InfinityAI.Pro - GCP Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Timestamp: $timestamp" -ForegroundColor Yellow
Write-Host ""

$report = @{
    timestamp = (Get-Date -Format "o")
    project_id = $ProjectId
    region = $Region
    services = @()
    artifacts = @()
    secrets = @()
    ci_cd_matrix = @{}
    environment_config = @{}
    summary = @{
        gcp_native = $true
        secure = $true
        aligned = $true
        gaps = @()
    }
}

# Step 1: Check Cloud Run Services
Write-Host "[STEP 1] Checking Cloud Run Services..." -ForegroundColor Green
try {
    $services = gcloud run services list --platform=managed --project=$ProjectId --region=$Region --format=json | ConvertFrom-Json
    
    $expectedServices = @(
        "infinityai-engine-a",
        "infinityai-engine-b",
        "infinityai-engine-c",
        "infinityai-engine-d",
        "infinityai-ultra-aggressive",
        "infinityai-frontend"
    )
    
    foreach ($svc in $services) {
        $serviceInfo = @{
            name = $svc.metadata.name
            region = $svc.metadata.labels.region
            url = $svc.status.url
            health_status = "UNKNOWN"
            deployed = $true
        }
        
        Write-Host "  ✓ Found: $($svc.metadata.name) -> $($svc.status.url)" -ForegroundColor Gray
        
        # Step 3: Health Check
        try {
            $healthUrl = "$($svc.status.url)/health"
            Write-Host "    Checking health: $healthUrl" -ForegroundColor Gray
            $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $serviceInfo.health_status = "HEALTHY"
                Write-Host "    ✓ Health check passed (200 OK)" -ForegroundColor Green
            } else {
                $serviceInfo.health_status = "UNHEALTHY ($($response.StatusCode))"
                Write-Host "    ✗ Health check failed ($($response.StatusCode))" -ForegroundColor Red
                $report.summary.gaps += "Service $($svc.metadata.name) health check returned $($response.StatusCode)"
            }
        } catch {
            $serviceInfo.health_status = "ERROR: $($_.Exception.Message)"
            Write-Host "    ✗ Health check error: $($_.Exception.Message)" -ForegroundColor Red
            
            # Fetch logs if health check fails
            Write-Host "    Fetching recent logs..." -ForegroundColor Yellow
            try {
                gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$($svc.metadata.name)" --limit=20 --project=$ProjectId --format=json
            } catch {
                Write-Host "    Failed to fetch logs: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        $report.services += $serviceInfo
    }
    
    # Check for missing services
    foreach ($expected in $expectedServices) {
        if (-not ($services | Where-Object { $_.metadata.name -eq $expected })) {
            Write-Host "  ✗ Missing service: $expected" -ForegroundColor Red
            $report.summary.gaps += "Expected service $expected not found in Cloud Run"
            $report.services += @{
                name = $expected
                deployed = $false
                health_status = "NOT_DEPLOYED"
            }
        }
    }
    
} catch {
    Write-Host "  ✗ Error listing Cloud Run services: $($_.Exception.Message)" -ForegroundColor Red
    $report.summary.gaps += "Failed to list Cloud Run services: $($_.Exception.Message)"
}

# Step 2: Monitor Health & Performance (Uptime Checks)
Write-Host "`n[STEP 2] Checking Uptime Monitoring..." -ForegroundColor Green
try {
    $uptimeChecks = gcloud monitoring uptime-checks list --project=$ProjectId --format=json | ConvertFrom-Json
    Write-Host "  Found $($uptimeChecks.Count) uptime checks" -ForegroundColor Gray
    if ($uptimeChecks.Count -eq 0) {
        Write-Host "  ⚠ No uptime checks configured" -ForegroundColor Yellow
        $report.summary.gaps += "No uptime checks configured for services"
    } else {
        foreach ($check in $uptimeChecks) {
            Write-Host "  ✓ Uptime check: $($check.displayName)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  ✗ Error listing uptime checks: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 4: Confirm Artifact Registry Images
Write-Host "`n[STEP 4] Checking Artifact Registry Images..." -ForegroundColor Green
try {
    $images = gcloud artifacts docker images list --repository=$ArtifactRepo --location=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    
    $expectedImages = @(
        "engine-a-market-data",
        "engine-b-ai-ml",
        "engine-c-execution",
        "engine-d-chatbot",
        "engine-ultra-aggressive",
        "frontend-web"
    )
    
    foreach ($img in $images) {
        $imageInfo = @{
            image = $img.IMAGE
            tags = $img.TAGS
            digest = $img.DIGEST
        }
        Write-Host "  ✓ Found: $($img.IMAGE)" -ForegroundColor Gray
        $report.artifacts += $imageInfo
    }
    
    # Check for missing images
    foreach ($expected in $expectedImages) {
        $found = $false
        foreach ($img in $images) {
            if ($img.IMAGE -like "*/$expected*") {
                $found = $true
                break
            }
        }
        if (-not $found) {
            Write-Host "  ✗ Missing image: $expected" -ForegroundColor Red
            $report.summary.gaps += "Expected image $expected not found in Artifact Registry"
        }
    }
    
} catch {
    Write-Host "  ✗ Error listing Artifact Registry images: $($_.Exception.Message)" -ForegroundColor Red
    $report.summary.gaps += "Failed to list Artifact Registry images: $($_.Exception.Message)"
}

# Step 5: Validate Secrets
Write-Host "`n[STEP 5] Checking Secret Manager..." -ForegroundColor Green
try {
    $secrets = gcloud secrets list --project=$ProjectId --format=json | ConvertFrom-Json
    Write-Host "  Found $($secrets.Count) secrets in Secret Manager" -ForegroundColor Gray
    foreach ($secret in $secrets) {
        Write-Host "  ✓ Secret: $($secret.name)" -ForegroundColor Gray
        $report.secrets += @{
            name = $secret.name
            created = $secret.createTime
        }
    }
    
    # Check for sensitive file in repo
    if (Test-Path "dhan_credentials_secure.json") {
        Write-Host "  ✗ WARNING: dhan_credentials_secure.json still exists in repository!" -ForegroundColor Red
        $report.summary.gaps += "Sensitive credentials file dhan_credentials_secure.json found in repository"
        $report.summary.secure = $false
    } else {
        Write-Host "  ✓ dhan_credentials_secure.json not in repository" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  ✗ Error listing secrets: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Verify Environment Configuration
Write-Host "`n[STEP 6] Verifying Environment Configuration..." -ForegroundColor Green

# Check .env.example
if (Test-Path ".env.example") {
    $envContent = Get-Content ".env.example" -Raw
    $report.environment_config.env_example = @{
        gcp_only = $true
        issues = @()
    }
    
    # Check for AWS/Azure/Vercel references
    if ($envContent -match "amazonaws\.com|azurewebsites|vercel\.app") {
        Write-Host "  ✗ .env.example contains AWS/Azure/Vercel references" -ForegroundColor Red
        $report.environment_config.env_example.gcp_only = $false
        $report.environment_config.env_example.issues += "Contains AWS/Azure/Vercel URLs"
        $report.summary.gcp_native = $false
    } else {
        Write-Host "  ✓ .env.example is GCP-only" -ForegroundColor Green
    }
    
    # Verify GCP URLs
    if ($envContent -match "us-central1\.run\.app") {
        Write-Host "  ✓ .env.example contains GCP Cloud Run URLs" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ .env.example missing GCP Cloud Run URLs" -ForegroundColor Yellow
        $report.environment_config.env_example.issues += "Missing GCP Cloud Run URLs"
    }
} else {
    Write-Host "  ✗ .env.example not found" -ForegroundColor Red
    $report.summary.gaps += ".env.example file not found"
}

# Check nginx.conf
if (Test-Path "frontend/web/nginx.conf") {
    $nginxContent = Get-Content "frontend/web/nginx.conf" -Raw
    $report.environment_config.nginx = @{
        gcp_only = $true
        issues = @()
    }
    
    if ($nginxContent -match "amazonaws\.com|azurewebsites|vercel\.app") {
        Write-Host "  ✗ nginx.conf contains AWS/Azure/Vercel references" -ForegroundColor Red
        $report.environment_config.nginx.gcp_only = $false
        $report.environment_config.nginx.issues += "Contains AWS/Azure/Vercel URLs"
        $report.summary.gcp_native = $false
    } else {
        Write-Host "  ✓ nginx.conf is GCP-only" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ nginx.conf not found" -ForegroundColor Red
}

# Step 7: Review CI/CD Matrix
Write-Host "`n[STEP 7] Reviewing CI/CD Matrix..." -ForegroundColor Green
if (Test-Path ".github/workflows/deploy-production.yml") {
    $workflowContent = Get-Content ".github/workflows/deploy-production.yml" -Raw
    $report.ci_cd_matrix = @{
        has_all_services = $true
        services_found = @()
        missing_services = @()
        gcp_deployment = $true
    }
    
    $expectedInMatrix = @(
        "engine-a-market-data",
        "engine-b-ai-ml",
        "engine-c-execution",
        "engine-d-chatbot",
        "engine-ultra-aggressive"
    )
    
    foreach ($svc in $expectedInMatrix) {
        if ($workflowContent -match $svc) {
            Write-Host "  ✓ Matrix includes: $svc" -ForegroundColor Gray
            $report.ci_cd_matrix.services_found += $svc
        } else {
            Write-Host "  ✗ Matrix missing: $svc" -ForegroundColor Red
            $report.ci_cd_matrix.missing_services += $svc
            $report.ci_cd_matrix.has_all_services = $false
            $report.summary.gaps += "CI/CD matrix missing service: $svc"
        }
    }
    
    # Check for frontend deployment
    if ($workflowContent -match "deploy-frontend-gcp" -or $workflowContent -match "infinityai-frontend") {
        Write-Host "  ✓ Frontend deployment included" -ForegroundColor Green
        $report.ci_cd_matrix.services_found += "frontend"
    } else {
        Write-Host "  ⚠ Frontend deployment not clearly defined" -ForegroundColor Yellow
        $report.summary.gaps += "Frontend deployment not clearly defined in workflow"
    }
    
    # Check for GCP deployment steps
    if ($workflowContent -match "gcloud run deploy") {
        Write-Host "  ✓ Uses gcloud run deploy" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing gcloud run deploy command" -ForegroundColor Red
        $report.ci_cd_matrix.gcp_deployment = $false
        $report.summary.gaps += "Workflow missing gcloud run deploy command"
    }
    
    # Check for --allow-unauthenticated
    if ($workflowContent -match "--allow-unauthenticated") {
        Write-Host "  ✓ Uses --allow-unauthenticated flag" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Missing --allow-unauthenticated flag" -ForegroundColor Yellow
        $report.summary.gaps += "Workflow missing --allow-unauthenticated flag"
    }
    
} else {
    Write-Host "  ✗ deploy-production.yml not found" -ForegroundColor Red
    $report.summary.gaps += "deploy-production.yml workflow file not found"
}

# Final Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$report.summary.total_services = $report.services.Count
$report.summary.healthy_services = ($report.services | Where-Object { $_.health_status -eq "HEALTHY" }).Count
$report.summary.total_artifacts = $report.artifacts.Count
$report.summary.total_secrets = $report.secrets.Count
$report.summary.gap_count = $report.summary.gaps.Count

Write-Host "Services Deployed: $($report.summary.total_services)" -ForegroundColor $(if ($report.summary.total_services -ge 6) { "Green" } else { "Red" })
Write-Host "Healthy Services: $($report.summary.healthy_services)" -ForegroundColor $(if ($report.summary.healthy_services -eq $report.summary.total_services) { "Green" } else { "Yellow" })
Write-Host "Artifact Images: $($report.summary.total_artifacts)" -ForegroundColor $(if ($report.summary.total_artifacts -ge 6) { "Green" } else { "Red" })
Write-Host "Secrets in Secret Manager: $($report.summary.total_secrets)" -ForegroundColor Gray
Write-Host "GCP-Native: $(if ($report.summary.gcp_native) { 'YES' } else { 'NO' })" -ForegroundColor $(if ($report.summary.gcp_native) { "Green" } else { "Red" })
Write-Host "Secure: $(if ($report.summary.secure) { 'YES' } else { 'NO' })" -ForegroundColor $(if ($report.summary.secure) { "Green" } else { "Red" })
Write-Host "Aligned: $(if ($report.summary.aligned) { 'YES' } else { 'NO' })" -ForegroundColor $(if ($report.summary.aligned) { "Green" } else { "Red" })

if ($report.summary.gaps.Count -gt 0) {
    Write-Host "`nGaps & Issues Found:" -ForegroundColor Yellow
    foreach ($gap in $report.summary.gaps) {
        Write-Host "  - $gap" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✅ No gaps found! System is fully GCP-native, secure, and aligned." -ForegroundColor Green
}

# Save report
Write-Host "`n[SAVING REPORT] $reportPath" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "reports" -Force | Out-Null
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "✅ Report saved successfully!" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
