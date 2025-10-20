<#
.SYNOPSIS
    Inject and rotate GCP Secret Manager secrets into Cloud Run services.

.DESCRIPTION
    This script securely injects secrets from GCP Secret Manager into Cloud Run services,
    ensuring sensitive credentials are never stored in plaintext. Supports dry-run mode
    and per-service secret mapping.

.PARAMETER DryRun
    Preview changes without executing (default: true)

.PARAMETER Project
    GCP project ID (default: infinity-ai-5ec7c)

.PARAMETER Region
    Cloud Run region (default: us-central1)

.EXAMPLE
    .\secret_injection_and_rotation.ps1 -DryRun $false
    # Execute secret injection for all services

.EXAMPLE
    .\secret_injection_and_rotation.ps1
    # Preview changes (dry-run mode)

.NOTES
    Author: InfinityAI.Pro DevOps
    Version: 1.0.0
    Last Updated: 2025-10-20
#>

param(
    [Parameter(Mandatory=$false)]
    [bool]$DryRun = $true,

    [Parameter(Mandatory=$false)]
    [string]$Project = "infinity-ai-5ec7c",

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Info "=========================================="
Write-Info "InfinityAI.Pro - Secret Injection & Rotation"
Write-Info "=========================================="
Write-Info "Project: $Project"
Write-Info "Region: $Region"
Write-Info "Mode: $(if ($DryRun) { 'DRY-RUN (Preview Only)' } else { 'LIVE EXECUTION' })"
Write-Info ""

# Secret mapping per service
$SecretMappings = @{
    "infinityai-engine-a" = @(
        "VERTEX_AI_API_KEY:gemini-api-key:latest",
        "HUGGINGFACE_API_TOKEN:huggingface-token:latest"
    )
    "infinityai-engine-b" = @(
        "VERTEX_AI_API_KEY:gemini-api-key:latest",
        "HUGGINGFACE_API_TOKEN:huggingface-token:latest"
    )
    "infinityai-engine-c-execution" = @(
        "TELEGRAM_BOT_TOKEN:telegram-bot-token:latest",
        "TELEGRAM_CHAT_ID:telegram-chat-id:latest",
        "WEBHOOK_VERIFICATION_TOKEN:webhook-verification-token:latest"
    )
    "infinityai-engine-d" = @(
        "JWT_SECRET_KEY:trading-engine-secret:latest",
        "TELEGRAM_BOT_TOKEN:telegram-bot-token:latest",
        "TELEGRAM_CHAT_ID:telegram-chat-id:latest"
    )
}

# Canonical engine URLs (for Engine D orchestrator)
$EngineUrls = @{
    "ENGINE_A_URL" = "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app"
    "ENGINE_B_URL" = "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app"
    "ENGINE_C_URL" = "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app"
}

# Verify secrets exist
Write-Info "Step 1: Verifying secrets exist in Secret Manager..."
$ExistingSecretsRaw = gcloud secrets list --project=$Project --format="value(name)"
$ExistingSecrets = @()
if ($ExistingSecretsRaw) {
    $ExistingSecrets = $ExistingSecretsRaw -split "`r?`n" | Where-Object { $_ -ne "" }
}

$RequiredSecrets = @(
    "gemini-api-key",
    "huggingface-token",
    "telegram-bot-token",
    "telegram-chat-id",
    "webhook-verification-token",
    "trading-engine-secret"
)

# Optional secrets (warn but don't fail)
$OptionalSecrets = @(
    "dhan-access-token",
    "dhan-client-id"
)

$MissingSecrets = @()
foreach ($secret in $RequiredSecrets) {
    if ($ExistingSecrets -notcontains $secret) {
        $MissingSecrets += $secret
        Write-Warning "Secret '$secret' not found in Secret Manager"
    } else {
        Write-Success "Secret '$secret' exists"
    }
}

# Check optional secrets
foreach ($secret in $OptionalSecrets) {
    if ($ExistingSecrets -notcontains $secret) {
        Write-Warning "Optional secret '$secret' not found (Dhan features disabled)"
    } else {
        Write-Success "Secret '$secret' exists"
    }
}

if ($MissingSecrets.Count -gt 0) {
    Write-Error "Missing secrets detected. Please create the following secrets first:"
    foreach ($secret in $MissingSecrets) {
        Write-Host "  - $secret" -ForegroundColor Red
    }
    Write-Info ""
    Write-Info "To create secrets, use:"
    Write-Host "  echo 'YOUR_SECRET_VALUE' | gcloud secrets create SECRET_NAME --data-file=- --project=$Project" -ForegroundColor Yellow
    exit 1
}

Write-Success "All required secrets exist in Secret Manager"
Write-Info ""

# Inject secrets into each service
Write-Info "Step 2: Injecting secrets into Cloud Run services..."
foreach ($service in $SecretMappings.Keys) {
    Write-Info "---"
    Write-Info "Service: $service"
    
    $updateSecretsArgs = @()
    foreach ($mapping in $SecretMappings[$service]) {
        $parts = $mapping -split ":"
        $envVar = $parts[0]
        $secretName = $parts[1]
        $version = $parts[2]
        
        $updateSecretsArgs += "${envVar}=${secretName}:${version}"
        Write-Info "  • $envVar → $secretName ($version)"
    }
    
    # Add canonical engine URLs for Engine D
    $setEnvVarsArgs = @()
    if ($service -eq "infinityai-engine-d") {
        foreach ($envVar in $EngineUrls.Keys) {
            $url = $EngineUrls[$envVar]
            $setEnvVarsArgs += "${envVar}=${url}"
            Write-Info "  • $envVar = $url"
        }
    }
    
    if ($DryRun) {
        Write-Warning "  [DRY-RUN] Would execute:"
        Write-Host "    gcloud run services update $service \" -ForegroundColor Yellow
        Write-Host "      --region=$Region \" -ForegroundColor Yellow
        Write-Host "      --project=$Project \" -ForegroundColor Yellow
        if ($updateSecretsArgs.Count -gt 0) {
            Write-Host "      --update-secrets=$($updateSecretsArgs -join ',') \" -ForegroundColor Yellow
        }
        if ($setEnvVarsArgs.Count -gt 0) {
            Write-Host "      --set-env-vars=$($setEnvVarsArgs -join ',')" -ForegroundColor Yellow
        }
    } else {
        try {
            $gcloudArgs = @(
                "run", "services", "update", $service,
                "--region=$Region",
                "--project=$Project"
            )
            if ($updateSecretsArgs.Count -gt 0) {
                $gcloudArgs += "--update-secrets=$($updateSecretsArgs -join ',')"
            }
            if ($setEnvVarsArgs.Count -gt 0) {
                $gcloudArgs += "--set-env-vars=$($setEnvVarsArgs -join ',')"
            }
            
            & gcloud @gcloudArgs
            Write-Success "  ✓ Secrets injected into $service"
        } catch {
            Write-Error "  ✗ Failed to inject secrets into $service : $_"
        }
    }
}

Write-Info ""
Write-Info "=========================================="
if ($DryRun) {
    Write-Warning "DRY-RUN COMPLETE - No changes made"
    Write-Info "To execute changes, run with -DryRun `$false"
} else {
    Write-Success "SECRET INJECTION COMPLETE"
    Write-Info ""
    Write-Info "Next Steps:"
    Write-Info "1. Verify services are healthy:"
    Write-Host "   .\verify-platform-health.ps1" -ForegroundColor Cyan
    Write-Info "2. Remove any plaintext secrets from local files"
    Write-Info "3. Commit changes to version control"
}
Write-Info "=========================================="
