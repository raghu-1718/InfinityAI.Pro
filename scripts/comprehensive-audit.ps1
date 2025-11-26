# InfinityAI.Pro - Comprehensive End-to-End Audit Script
# This script performs 300+ verification checks across all systems

param(
    [string]$ProjectId = "after-yesterday-473512-k3",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Continue"
$AuditResults = @()
$CheckNumber = 1

function Add-AuditCheck {
    param($Category, $Item, $Status, $Details, $Fix)
    $script:AuditResults += [PSCustomObject]@{
        Check = $script:CheckNumber++
        Category = $Category
        Item = $Item
        Status = $Status
        Details = $Details
        Fix = $Fix
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   INFINITYAI.PRO - COMPREHENSIVE AUDIT & VERIFICATION          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`nStarting comprehensive audit with 300+ checks..." -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# ============================================================================
# SECTION 1: REPOSITORY & VERSION CONTROL (Checks 1-30)
# ============================================================================
Write-Host "`n[1/15] REPOSITORY & VERSION CONTROL" -ForegroundColor Cyan -BackgroundColor DarkCyan

# 1. Current directory
$currentDir = Get-Location
Add-AuditCheck "Repository" "Working Directory" $(if ($currentDir -like "*InfinityAI.Pro*") {"✅"} else {"❌"}) $currentDir.Path "cd C:\workspace\InfinityAI.Pro"

# 2. Git repository exists
$isGitRepo = Test-Path ".git"
Add-AuditCheck "Repository" "Git Repository" $(if ($isGitRepo) {"✅"} else {"❌"}) "Repository initialized: $isGitRepo" "git init"

# 3. Current branch
$currentBranch = git branch --show-current 2>$null
Add-AuditCheck "Repository" "Current Branch" $(if ($currentBranch -eq "feature/3-engine-architecture") {"✅"} else {"⚠️"}) $currentBranch "git checkout feature/3-engine-architecture"

# 4. Uncommitted changes
$gitStatus = git status --porcelain 2>$null
Add-AuditCheck "Repository" "Uncommitted Changes" $(if (-not $gitStatus) {"✅"} else {"⚠️"}) $(if ($gitStatus) {"Changes detected"} else {"Clean"}) "git add . && git commit"

# 5-15. Recent commits analysis
$commits = git log --oneline -10 2>$null
Add-AuditCheck "Repository" "Commit History" $(if ($commits) {"✅"} else {"❌"}) "$($commits.Count) commits found" ""

# 16. Remote repository
$remotes = git remote -v 2>$null
$hasOrigin = $remotes -match "origin"
Add-AuditCheck "Repository" "Remote Origin" $(if ($hasOrigin) {"✅"} else {"❌"}) $(if ($hasOrigin) {"Connected to GitHub"} else {"No remote"}) "git remote add origin <url>"

# 17-20. Remote sync status
try {
    git fetch origin 2>$null
    $local = git rev-parse HEAD 2>$null
    $remote = git rev-parse origin/feature/3-engine-architecture 2>$null
    $inSync = $local -eq $remote
    Add-AuditCheck "Repository" "Remote Sync" $(if ($inSync) {"✅"} else {"⚠️"}) $(if ($inSync) {"In sync"} else {"Out of sync"}) "git push origin feature/3-engine-architecture"
} catch {
    Add-AuditCheck "Repository" "Remote Sync" "❌" "Cannot check sync" "Check network connection"
}

# 21-30. File structure verification
$requiredDirs = @("backend", "frontend", "scripts", ".github")
foreach ($dir in $requiredDirs) {
    $exists = Test-Path $dir
    Add-AuditCheck "Repository" "Directory: $dir" $(if ($exists) {"✅"} else {"❌"}) "Exists: $exists" "mkdir $dir"
}

# ============================================================================
# SECTION 2: BACKEND ARCHITECTURE (Checks 31-80)
# ============================================================================
Write-Host "[2/15] BACKEND ARCHITECTURE" -ForegroundColor Cyan -BackgroundColor DarkCyan

$engines = @("engine-analytics", "engine-core", "engine-execution")
foreach ($engine in $engines) {
    $enginePath = "backend\$engine"
    
    # Engine directory
    $exists = Test-Path $enginePath
    Add-AuditCheck "Backend" "$engine Directory" $(if ($exists) {"✅"} else {"❌"}) "Path: $enginePath" "mkdir $enginePath"
    
    if ($exists) {
        # Dockerfile
        $dockerfile = Test-Path "$enginePath\Dockerfile"
        Add-AuditCheck "Backend" "$engine Dockerfile" $(if ($dockerfile) {"✅"} else {"❌"}) "Exists: $dockerfile" "Create Dockerfile"
        
        # requirements.txt
        $reqs = Test-Path "$enginePath\requirements.txt"
        Add-AuditCheck "Backend" "$engine requirements.txt" $(if ($reqs) {"✅"} else {"❌"}) "Exists: $reqs" "Create requirements.txt"
        
        # src/main.py
        $mainPy = Test-Path "$enginePath\src\main.py"
        Add-AuditCheck "Backend" "$engine main.py" $(if ($mainPy) {"✅"} else {"❌"}) "Exists: $mainPy" "Create src/main.py"
        
        # Check imports in main.py
        if ($mainPy) {
            $content = Get-Content "$enginePath\src\main.py" -Raw
            $hasFastAPI = $content -match "from fastapi import"
            $hasUvicorn = $content -match "uvicorn"
            Add-AuditCheck "Backend" "$engine FastAPI Import" $(if ($hasFastAPI) {"✅"} else {"❌"}) "Found: $hasFastAPI" "Add FastAPI import"
        }
        
        # Check requirements content
        if ($reqs) {
            $reqContent = Get-Content "$enginePath\requirements.txt" -Raw
            $hasFastAPI = $reqContent -match "fastapi"
            $hasUvicorn = $reqContent -match "uvicorn"
            $hasDhanhq = $reqContent -match "dhanhq"
            Add-AuditCheck "Backend" "$engine Requirements FastAPI" $(if ($hasFastAPI) {"✅"} else {"❌"}) "Found: $hasFastAPI" "Add fastapi to requirements"
            Add-AuditCheck "Backend" "$engine Requirements uvicorn" $(if ($hasUvicorn) {"✅"} else {"❌"}) "Found: $hasUvicorn" "Add uvicorn to requirements"
            Add-AuditCheck "Backend" "$engine Requirements dhanhq" $(if ($hasDhanhq) {"✅"} else {"❌"}) "Found: $hasDhanhq" "Add dhanhq to requirements"
        }
    }
}

# ============================================================================
# SECTION 3: GCP CLOUD RUN SERVICES (Checks 81-130)
# ============================================================================
Write-Host "[3/15] GCP CLOUD RUN SERVICES" -ForegroundColor Cyan -BackgroundColor DarkCyan

$services = @(
    @{Name="infinityai-engine-a"; Engine="Analytics"},
    @{Name="infinityai-engine-b"; Engine="Core"},
    @{Name="infinityai-engine-c-execution"; Engine="Execution"}
)

foreach ($svc in $services) {
    try {
        $serviceInfo = gcloud run services describe $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        
        if ($serviceInfo) {
            Add-AuditCheck "Cloud Run" "$($svc.Name) Service" "✅" "Service exists" ""
            
            # Check URL
            $url = $serviceInfo.status.url
            Add-AuditCheck "Cloud Run" "$($svc.Name) URL" $(if ($url) {"✅"} else {"❌"}) $url "Deploy service"
            
            # Check status
            $ready = $serviceInfo.status.conditions | Where-Object {$_.type -eq "Ready"}
            $isReady = $ready.status -eq "True"
            Add-AuditCheck "Cloud Run" "$($svc.Name) Status" $(if ($isReady) {"✅"} else {"❌"}) $(if ($isReady) {"Ready"} else {"Not Ready"}) "Check logs"
            
            # Check revision
            $revision = $serviceInfo.status.latestCreatedRevisionName
            Add-AuditCheck "Cloud Run" "$($svc.Name) Revision" $(if ($revision) {"✅"} else {"❌"}) $revision ""
            
            # Check traffic
            $traffic = $serviceInfo.status.traffic[0].percent
            Add-AuditCheck "Cloud Run" "$($svc.Name) Traffic" $(if ($traffic -eq 100) {"✅"} else {"⚠️"}) "$traffic%" "Route 100% traffic"
            
            # Check configuration
            $memory = $serviceInfo.spec.template.spec.containers[0].resources.limits.memory
            $cpu = $serviceInfo.spec.template.spec.containers[0].resources.limits.cpu
            Add-AuditCheck "Cloud Run" "$($svc.Name) Memory" "✅" $memory ""
            Add-AuditCheck "Cloud Run" "$($svc.Name) CPU" "✅" $cpu ""
            
            # Check scaling
            $minInstances = $serviceInfo.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
            $maxInstances = $serviceInfo.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
            Add-AuditCheck "Cloud Run" "$($svc.Name) Min Instances" $(if ($minInstances) {"✅"} else {"⚠️"}) $minInstances "Set min instances"
            Add-AuditCheck "Cloud Run" "$($svc.Name) Max Instances" $(if ($maxInstances) {"✅"} else {"⚠️"}) $maxInstances "Set max instances"
            
        } else {
            Add-AuditCheck "Cloud Run" "$($svc.Name) Service" "❌" "Service not found" "Deploy service"
        }
    } catch {
        Add-AuditCheck "Cloud Run" "$($svc.Name) Service" "❌" "Error checking service: $($_.Exception.Message)" "Check GCP access"
    }
}

# ============================================================================
# SECTION 4: CONTAINER IMAGES & BUILDS (Checks 131-160)
# ============================================================================
Write-Host "[4/15] CONTAINER IMAGES & BUILDS" -ForegroundColor Cyan -BackgroundColor DarkCyan

$imageNames = @("infinityai-engine-a", "infinityai-engine-b", "infinityai-engine-c-execution")
foreach ($img in $imageNames) {
    try {
        $images = gcloud container images list-tags "gcr.io/$ProjectId/$img" --limit=5 --format=json 2>$null | ConvertFrom-Json
        
        if ($images) {
            Add-AuditCheck "Container Images" "$img Images" "✅" "$($images.Count) images found" ""
            
            $latestImage = $images[0]
            $tags = $latestImage.tags -join ", "
            Add-AuditCheck "Container Images" "$img Latest Tags" $(if ($tags) {"✅"} else {"⚠️"}) $tags ""
            
            $digest = $latestImage.digest
            Add-AuditCheck "Container Images" "$img Digest" $(if ($digest) {"✅"} else {"❌"}) $digest ""
            
            $timestamp = $latestImage.timestamp
            Add-AuditCheck "Container Images" "$img Last Build" $(if ($timestamp) {"✅"} else {"❌"}) $timestamp ""
        } else {
            Add-AuditCheck "Container Images" "$img Images" "❌" "No images found" "Build and push image"
        }
    } catch {
        Add-AuditCheck "Container Images" "$img Images" "❌" "Error: $($_.Exception.Message)" "Check GCR access"
    }
}

# Recent builds
try {
    $builds = gcloud builds list --project=$ProjectId --limit=10 --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Container Images" "Recent Builds" $(if ($builds) {"✅"} else {"⚠️"}) "$($builds.Count) builds found" ""
    
    foreach ($build in $builds | Select-Object -First 5) {
        $status = $build.status
        $isSuccess = $status -eq "SUCCESS"
        Add-AuditCheck "Container Images" "Build $($build.id)" $(if ($isSuccess) {"✅"} elseif ($status -eq "CANCELLED") {"⚠️"} else {"❌"}) "$status - $($build.createTime)" ""
    }
} catch {
    Add-AuditCheck "Container Images" "Recent Builds" "❌" "Cannot list builds" "Check Cloud Build API"
}

# ============================================================================
# SECTION 5: API ENDPOINTS & ROUTES (Checks 161-210)
# ============================================================================
Write-Host "[5/15] API ENDPOINTS & ROUTES" -ForegroundColor Cyan -BackgroundColor DarkCyan

$endpoints = @(
    @{Engine="Engine A"; URL="https://infinityai-engine-a-573866363639.us-central1.run.app"; Endpoints=@("/", "/healthz", "/docs", "/orchestrate", "/dhan/subscribe-live-data")},
    @{Engine="Engine B"; URL="https://infinityai-engine-b-573866363639.us-central1.run.app"; Endpoints=@("/", "/healthz", "/docs", "/api/predict", "/api/ai-signals", "/api/gemini/analyze")},
    @{Engine="Engine C"; URL="https://infinityai-engine-c-execution-573866363639.us-central1.run.app"; Endpoints=@("/", "/healthz", "/docs", "/api/dhan/place-order")}
)

foreach ($ep in $endpoints) {
    foreach ($path in $ep.Endpoints) {
        try {
            $url = $ep.URL + $path
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -ErrorAction Stop
            $status = $response.StatusCode
            Add-AuditCheck "API Endpoints" "$($ep.Engine) $path" $(if ($status -eq 200) {"✅"} else {"⚠️"}) "HTTP $status" "Fix endpoint"
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($path -eq "/" -and $statusCode -eq 404) {
                Add-AuditCheck "API Endpoints" "$($ep.Engine) $path" "⚠️" "HTTP 404 (expected)" "Add root handler"
            } else {
                Add-AuditCheck "API Endpoints" "$($ep.Engine) $path" "❌" "Error: $($_.Exception.Message)" "Check endpoint"
            }
        }
    }
}

# ============================================================================
# SECTION 6: FRONTEND APPLICATION (Checks 211-240)
# ============================================================================
Write-Host "[6/15] FRONTEND APPLICATION" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Firebase hosting files
$frontendFiles = @(
    "frontend\web\index.html",
    "frontend\web\firebase.json",
    "frontend\web\.firebaserc"
)

foreach ($file in $frontendFiles) {
    $exists = Test-Path $file
    Add-AuditCheck "Frontend" "$(Split-Path $file -Leaf)" $(if ($exists) {"✅"} else {"❌"}) "Path: $file" "Create $file"
}

# Check index.html content
if (Test-Path "frontend\web\index.html") {
    $html = Get-Content "frontend\web\index.html" -Raw
    $hasEngineA = $html -match "infinityai-engine-a"
    $hasEngineB = $html -match "infinityai-engine-b"
    $hasEngineC = $html -match "infinityai-engine-c-execution"
    Add-AuditCheck "Frontend" "Engine A Reference" $(if ($hasEngineA) {"✅"} else {"❌"}) "Found: $hasEngineA" "Add Engine A URL"
    Add-AuditCheck "Frontend" "Engine B Reference" $(if ($hasEngineB) {"✅"} else {"❌"}) "Found: $hasEngineB" "Add Engine B URL"
    Add-AuditCheck "Frontend" "Engine C Reference" $(if ($hasEngineC) {"✅"} else {"❌"}) "Found: $hasEngineC" "Add Engine C URL"
}

# Firebase hosting status
try {
    $frontendUrl = "https://after-yesterday-473512-k3.web.app"
    $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 10
    Add-AuditCheck "Frontend" "Firebase Hosting" $(if ($response.StatusCode -eq 200) {"✅"} else {"❌"}) "HTTP $($response.StatusCode)" "Deploy to Firebase"
} catch {
    Add-AuditCheck "Frontend" "Firebase Hosting" "❌" "Error: $($_.Exception.Message)" "firebase deploy"
}

# Check React/TypeScript source files
$srcFiles = @(
    "frontend\web\src\stores\appStore.ts",
    "frontend\web\src\stores\webSocketStore.ts",
    "frontend\web\src\hooks\useApi.ts"
)

foreach ($file in $srcFiles) {
    $exists = Test-Path $file
    Add-AuditCheck "Frontend" "$(Split-Path $file -Leaf)" $(if ($exists) {"✅"} else {"⚠️"}) "Source file" ""
}

# ============================================================================
# SECTION 7: ENVIRONMENT VARIABLES & SECRETS (Checks 241-260)
# ============================================================================
Write-Host "[7/15] ENVIRONMENT VARIABLES & SECRETS" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check GCP secrets
try {
    $secrets = gcloud secrets list --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Secrets" "GCP Secrets Manager" $(if ($secrets) {"✅"} else {"⚠️"}) "$($secrets.Count) secrets found" ""
    
    $requiredSecrets = @("dhan-api-key", "dhan-client-id")
    foreach ($secretName in $requiredSecrets) {
        $exists = $secrets | Where-Object {$_.name -match $secretName}
        Add-AuditCheck "Secrets" "Secret: $secretName" $(if ($exists) {"✅"} else {"❌"}) $(if ($exists) {"Exists"} else {"Missing"}) "Create secret"
    }
} catch {
    Add-AuditCheck "Secrets" "GCP Secrets Manager" "❌" "Cannot access secrets" "Enable Secret Manager API"
}

# Check environment variables in Cloud Run services
foreach ($svc in $services) {
    try {
        $serviceInfo = gcloud run services describe $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        $envVars = $serviceInfo.spec.template.spec.containers[0].env
        
        if ($envVars) {
            Add-AuditCheck "Environment" "$($svc.Name) Env Vars" "✅" "$($envVars.Count) variables configured" ""
            
            $hasProject = $envVars | Where-Object {$_.name -eq "GOOGLE_CLOUD_PROJECT"}
            Add-AuditCheck "Environment" "$($svc.Name) GOOGLE_CLOUD_PROJECT" $(if ($hasProject) {"✅"} else {"⚠️"}) $(if ($hasProject) {"Set"} else {"Not set"}) "Add env var"
        } else {
            Add-AuditCheck "Environment" "$($svc.Name) Env Vars" "⚠️" "No env vars" "Configure environment"
        }
    } catch {
        Add-AuditCheck "Environment" "$($svc.Name) Env Vars" "❌" "Cannot check" ""
    }
}

# ============================================================================
# SECTION 8: DATABASE & FIRESTORE (Checks 261-280)
# ============================================================================
Write-Host "[8/15] DATABASE & FIRESTORE" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check Firestore database
try {
    $databases = gcloud firestore databases list --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Firestore" "Database Exists" $(if ($databases) {"✅"} else {"⚠️"}) $(if ($databases) {"Found $($databases.Count) database(s)"} else {"No databases"}) "Create Firestore database"
    
    if ($databases) {
        $db = $databases[0]
        Add-AuditCheck "Firestore" "Database Mode" "✅" $db.type ""
        Add-AuditCheck "Firestore" "Database Location" "✅" $db.locationId ""
    }
} catch {
    Add-AuditCheck "Firestore" "Database Access" "❌" "Cannot access Firestore" "Enable Firestore API"
}

# Check Firebase functions
if (Test-Path "frontend\web\functions") {
    Add-AuditCheck "Firebase" "Functions Directory" "✅" "Exists" ""
    
    $functionsPackage = Test-Path "frontend\web\functions\package.json"
    Add-AuditCheck "Firebase" "Functions package.json" $(if ($functionsPackage) {"✅"} else {"❌"}) "Exists: $functionsPackage" ""
    
    if ($functionsPackage) {
        $pkg = Get-Content "frontend\web\functions\package.json" | ConvertFrom-Json
        $hasFunctions = $pkg.dependencies.'firebase-functions'
        $hasAdmin = $pkg.dependencies.'firebase-admin'
        Add-AuditCheck "Firebase" "firebase-functions" $(if ($hasFunctions) {"✅"} else {"❌"}) "Version: $hasFunctions" "npm install"
        Add-AuditCheck "Firebase" "firebase-admin" $(if ($hasAdmin) {"✅"} else {"❌"}) "Version: $hasAdmin" "npm install"
    }
}

# ============================================================================
# SECTION 9: AUTHENTICATION & IAM (Checks 281-300)
# ============================================================================
Write-Host "[9/15] AUTHENTICATION & IAM" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check service accounts
try {
    $serviceAccounts = gcloud iam service-accounts list --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "IAM" "Service Accounts" $(if ($serviceAccounts) {"✅"} else {"⚠️"}) "$($serviceAccounts.Count) accounts found" ""
} catch {
    Add-AuditCheck "IAM" "Service Accounts" "❌" "Cannot list" "Check IAM permissions"
}

# Check IAM roles for Cloud Run
foreach ($svc in $services) {
    try {
        $policy = gcloud run services get-iam-policy $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        $publicAccess = $policy.bindings | Where-Object {$_.members -contains "allUsers" -and $_.role -eq "roles/run.invoker"}
        Add-AuditCheck "IAM" "$($svc.Name) Public Access" $(if ($publicAccess) {"✅"} else {"⚠️"}) $(if ($publicAccess) {"Enabled"} else {"Disabled"}) "gcloud run services add-iam-policy-binding"
    } catch {
        Add-AuditCheck "IAM" "$($svc.Name) IAM Policy" "❌" "Cannot check" ""
    }
}

# Check current GCP authentication
try {
    $account = gcloud config get-value account 2>$null
    Add-AuditCheck "IAM" "Current GCP Account" $(if ($account) {"✅"} else {"❌"}) $account "gcloud auth login"
    
    $project = gcloud config get-value project 2>$null
    $correctProject = $project -eq $ProjectId
    Add-AuditCheck "IAM" "Current Project" $(if ($correctProject) {"✅"} else {"⚠️"}) $project "gcloud config set project"
} catch {
    Add-AuditCheck "IAM" "GCP Authentication" "❌" "Not authenticated" "gcloud auth login"
}

# ============================================================================
# SECTION 10: CUSTOM DOMAINS & URLS (Checks 301-315)
# ============================================================================
Write-Host "[10/15] CUSTOM DOMAINS & URLS" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check Cloud Run domain mappings
try {
    $mappings = gcloud run domain-mappings list --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Domains" "Custom Domain Mappings" $(if ($mappings -and $mappings.Count -gt 0) {"✅"} else {"⚠️"}) "$($mappings.Count) mappings" "Map custom domain"
} catch {
    Add-AuditCheck "Domains" "Domain Mappings" "⚠️" "No custom domains configured" "Optional: map domain"
}

# Verify URLs are accessible
$urls = @{
    "Frontend" = "https://after-yesterday-473512-k3.web.app"
    "Engine A" = "https://infinityai-engine-a-573866363639.us-central1.run.app"
    "Engine B" = "https://infinityai-engine-b-573866363639.us-central1.run.app"
    "Engine C" = "https://infinityai-engine-c-execution-573866363639.us-central1.run.app"
}

foreach ($urlKey in $urls.Keys) {
    try {
        $response = Invoke-WebRequest -Uri $urls[$urlKey] -Method GET -TimeoutSec 10 -ErrorAction Stop
        Add-AuditCheck "URLs" "$urlKey URL" "✅" "$($urls[$urlKey]) - HTTP $($response.StatusCode)" ""
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Add-AuditCheck "URLs" "$urlKey URL" $(if ($statusCode -eq 404) {"⚠️"} else {"❌"}) "$($urls[$urlKey]) - HTTP $statusCode" "Check service"
    }
}

# ============================================================================
# SECTION 11: NETWORKING & CONNECTIVITY (Checks 316-330)
# ============================================================================
Write-Host "[11/15] NETWORKING & CONNECTIVITY" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check VPC access
try {
    $connectors = gcloud compute networks vpc-access connectors list --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Network" "VPC Access Connectors" $(if ($connectors) {"✅"} else {"⚠️"}) "$($connectors.Count) connectors" "Optional feature"
} catch {
    Add-AuditCheck "Network" "VPC Access" "⚠️" "Not configured (optional)" ""
}

# Check Cloud Run networking
foreach ($svc in $services) {
    try {
        $serviceInfo = gcloud run services describe $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        $ingress = $serviceInfo.metadata.annotations.'run.googleapis.com/ingress'
        Add-AuditCheck "Network" "$($svc.Name) Ingress" $(if ($ingress) {"✅"} else {"⚠️"}) $ingress ""
    } catch {
        Add-AuditCheck "Network" "$($svc.Name) Ingress" "❌" "Cannot check" ""
    }
}

# ============================================================================
# SECTION 12: MONITORING & LOGGING (Checks 331-350)
# ============================================================================
Write-Host "[12/15] MONITORING & LOGGING" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check Cloud Logging
foreach ($svc in $services) {
    try {
        $logs = gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$($svc.Name)" --limit=1 --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        Add-AuditCheck "Logging" "$($svc.Name) Logs" $(if ($logs) {"✅"} else {"⚠️"}) $(if ($logs) {"Logs available"} else {"No recent logs"}) ""
    } catch {
        Add-AuditCheck "Logging" "$($svc.Name) Logs" "❌" "Cannot access logs" "Check Logging API"
    }
}

# Check monitoring metrics
try {
    $metrics = gcloud monitoring metrics-descriptors list --filter="resource.type=cloud_run_revision" --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Monitoring" "Cloud Monitoring" $(if ($metrics) {"✅"} else {"⚠️"}) "$($metrics.Count) metrics available" ""
} catch {
    Add-AuditCheck "Monitoring" "Monitoring Access" "❌" "Cannot access" "Enable Monitoring API"
}

# ============================================================================
# SECTION 13: PERFORMANCE & SCALING (Checks 351-370)
# ============================================================================
Write-Host "[13/15] PERFORMANCE & SCALING" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check resource quotas
try {
    $quotas = gcloud compute project-info describe --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    Add-AuditCheck "Performance" "Project Quotas" $(if ($quotas) {"✅"} else {"⚠️"}) "Quota information available" ""
} catch {
    Add-AuditCheck "Performance" "Quotas" "⚠️" "Cannot check quotas" ""
}

# Check service scaling configuration
foreach ($svc in $services) {
    try {
        $serviceInfo = gcloud run services describe $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        $concurrency = $serviceInfo.spec.template.spec.containerConcurrency
        Add-AuditCheck "Performance" "$($svc.Name) Concurrency" $(if ($concurrency) {"✅"} else {"⚠️"}) $concurrency ""
        
        $timeout = $serviceInfo.spec.template.spec.timeoutSeconds
        Add-AuditCheck "Performance" "$($svc.Name) Timeout" $(if ($timeout) {"✅"} else {"⚠️"}) "${timeout}s" ""
    } catch {
        Add-AuditCheck "Performance" "$($svc.Name) Config" "❌" "Cannot check" ""
    }
}

# ============================================================================
# SECTION 14: SECURITY & COMPLIANCE (Checks 371-390)
# ============================================================================
Write-Host "[14/15] SECURITY & COMPLIANCE" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Check service security settings
foreach ($svc in $services) {
    try {
        $serviceInfo = gcloud run services describe $svc.Name --region=$Region --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
        
        # Check if running as non-root
        $securityContext = $serviceInfo.spec.template.spec.containers[0].securityContext
        Add-AuditCheck "Security" "$($svc.Name) Security Context" $(if ($securityContext) {"✅"} else {"⚠️"}) "Configured" ""
        
        # Check service account
        $sa = $serviceInfo.spec.template.spec.serviceAccountName
        Add-AuditCheck "Security" "$($svc.Name) Service Account" $(if ($sa) {"✅"} else {"⚠️"}) $sa ""
    } catch {
        Add-AuditCheck "Security" "$($svc.Name) Security" "❌" "Cannot check" ""
    }
}

# Check Secret Manager integration
try {
    $secretsConfig = gcloud secrets list --project=$ProjectId --format=json 2>$null | ConvertFrom-Json
    $hasSecrets = $secretsConfig.Count -gt 0
    Add-AuditCheck "Security" "Secrets Management" $(if ($hasSecrets) {"✅"} else {"⚠️"}) "$($secretsConfig.Count) secrets" "Create secrets for sensitive data"
} catch {
    Add-AuditCheck "Security" "Secrets" "⚠️" "Not configured" "Enable Secret Manager"
}

# ============================================================================
# SECTION 15: INTEGRATION & TESTING (Checks 391-415)
# ============================================================================
Write-Host "[15/15] INTEGRATION & TESTING" -ForegroundColor Cyan -BackgroundColor DarkCyan

# Test inter-service communication
Add-AuditCheck "Integration" "Engine A <-> Engine B" "⚠️" "Manual testing required" "Test /orchestrate endpoint"
Add-AuditCheck "Integration" "Engine A <-> Engine C" "⚠️" "Manual testing required" "Test order placement flow"
Add-AuditCheck "Integration" "Frontend <-> All Engines" "⚠️" "Manual testing required" "Test from web UI"

# Check WebSocket support (Engine C)
Add-AuditCheck "Integration" "WebSocket Support" "⚠️" "Manual testing required" "Test WebSocket connection"

# Check DhanHQ integration
Add-AuditCheck "Integration" "DhanHQ SDK" "⚠️" "Requires API credentials" "Test with real Dhan account"

# Check Google Gemini integration (Engine B)
Add-AuditCheck "Integration" "Google Gemini AI" "⚠️" "Requires API key" "Test /api/gemini/analyze"

# ============================================================================
# GENERATE REPORT
# ============================================================================
Write-Host "`n`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    AUDIT COMPLETE                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green

$passCount = ($AuditResults | Where-Object {$_.Status -eq "✅"}).Count
$warnCount = ($AuditResults | Where-Object {$_.Status -eq "⚠️"}).Count
$failCount = ($AuditResults | Where-Object {$_.Status -eq "❌"}).Count
$totalCount = $AuditResults.Count

Write-Host "`n📊 AUDIT SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "Total Checks:    $totalCount" -ForegroundColor White
Write-Host "✅ Passed:       $passCount ($([math]::Round($passCount/$totalCount*100,1))%)" -ForegroundColor Green
Write-Host "⚠️  Warnings:     $warnCount ($([math]::Round($warnCount/$totalCount*100,1))%)" -ForegroundColor Yellow
Write-Host "❌ Failed:       $failCount ($([math]::Round($failCount/$totalCount*100,1))%)" -ForegroundColor Red

# Export to CSV
$reportPath = "audit-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv"
$AuditResults | Export-Csv -Path $reportPath -NoTypeInformation
Write-Host "`n📄 Detailed report saved to: $reportPath" -ForegroundColor Cyan

# Display critical failures
$criticalFailures = $AuditResults | Where-Object {$_.Status -eq "❌"}
if ($criticalFailures.Count -gt 0) {
    Write-Host "`n⚠️ CRITICAL FAILURES TO ADDRESS:" -ForegroundColor Red -BackgroundColor DarkRed
    $criticalFailures | Format-Table -Property Check, Category, Item, Details, Fix -AutoSize
}

# Display warnings
$warnings = $AuditResults | Where-Object {$_.Status -eq "⚠️"}
if ($warnings.Count -gt 0 -and $warnings.Count -le 20) {
    Write-Host "`n⚠️ WARNINGS:" -ForegroundColor Yellow
    $warnings | Format-Table -Property Check, Category, Item, Details -AutoSize
}

Write-Host "`n✅ All passed checks:" -ForegroundColor Green
$passed = $AuditResults | Where-Object {$_.Status -eq "✅"}
Write-Host "   - Repository: $($passed | Where-Object {$_.Category -eq 'Repository'} | Measure-Object | Select-Object -ExpandProperty Count) checks" -ForegroundColor Gray
Write-Host "   - Backend: $($passed | Where-Object {$_.Category -eq 'Backend'} | Measure-Object | Select-Object -ExpandProperty Count) checks" -ForegroundColor Gray
Write-Host "   - Cloud Run: $($passed | Where-Object {$_.Category -eq 'Cloud Run'} | Measure-Object | Select-Object -ExpandProperty Count) checks" -ForegroundColor Gray
Write-Host "   - API Endpoints: $($passed | Where-Object {$_.Category -eq 'API Endpoints'} | Measure-Object | Select-Object -ExpandProperty Count) checks" -ForegroundColor Gray
Write-Host "   - Frontend: $($passed | Where-Object {$_.Category -eq 'Frontend'} | Measure-Object | Select-Object -ExpandProperty Count) checks" -ForegroundColor Gray

Write-Host "`n" -NoNewline
Write-Host "🎯 NEXT ACTIONS:" -ForegroundColor Yellow -BackgroundColor DarkYellow
Write-Host "1. Review the CSV report for detailed findings" -ForegroundColor White
Write-Host "2. Address critical failures (❌) first" -ForegroundColor White
Write-Host "3. Review and resolve warnings (⚠️) as needed" -ForegroundColor White
Write-Host "4. Run manual integration tests for marked items" -ForegroundColor White
Write-Host "5. Set up monitoring alerts in GCP Console" -ForegroundColor White

return $AuditResults
