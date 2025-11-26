#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up all Engine D references from InfinityAI.Pro codebase
.DESCRIPTION
    Engine D's functionality (WebSocket aggregation, chatbot, health orchestrator, event broadcaster, auth service)
    has been migrated to Engine C (Execution). This script removes all stale Engine D references.
.NOTES
    Author: InfinityAI.Pro Migration Team
    Date: 2024
    Part of 3-engine architecture migration
#>

Write-Host "🧹 InfinityAI.Pro - Engine D Cleanup Script" -ForegroundColor Cyan
Write-Host "=" * 80

$PROJECT_ROOT = "C:\workspace\InfinityAI.Pro"
Set-Location $PROJECT_ROOT

$engineDReferences = @(
    "domain_mapping_reapply.ps1",
    "fetch-todays-analysis.ps1",
    "grant-firebase-secret-access.ps1",
    "optimize-production.ps1",
    "secret_injection_and_rotation.ps1",
    "setup-infinityai-dev-environment.ps1",
    "setup-monitoring.ps1",
    "traffic_shift_and_cleanup.ps1",
    "verify_dns_and_ssl.ps1",
    "verify_gcp_deployment.ps1",
    "verify-backend-extended.ps1",
    "verify-backend.ps1"
)

function Update-ScriptFile {
    param(
        [string]$FilePath
    )
    
    Write-Host "📝 Processing: $FilePath" -ForegroundColor Yellow
    
    if (Test-Path $FilePath) {
        $content = Get-Content $FilePath -Raw
        $originalContent = $content
        
        # Replace common Engine D patterns
        $content = $content -replace 'infinityai-engine-d-[a-z0-9-]+\.us-central1\.run\.app', 'infinityai-engine-c-execution-26140490557.us-central1.run.app'
        $content = $content -replace 'infinityai-engine-d-[a-z0-9-]+\.uc\.a\.run\.app', 'infinityai-engine-c-execution-26140490557.us-central1.run.app'
        $content = $content -replace '"engine-d"', '"engine-c-execution"  # Engine D merged'
        $content = $content -replace "'engine-d'", "'engine-c-execution'  # Engine D merged"
        $content = $content -replace 'engine-d-orchestration', 'engine-c-execution  # Engine D merged'
        $content = $content -replace '\$ENGINE_D_URL', '$ENGINE_C_URL  # Engine D merged into C'
        $content = $content -replace 'ENGINE_D_URL=', '# ENGINE_D_URL merged into ENGINE_C_URL'
        
        # Remove engine-d from arrays
        $content = $content -replace '@\("engine-a",\s*"engine-b",\s*"engine-c-execution",\s*"engine-d"\)', '@("engine-a", "engine-b", "engine-c-execution")  # Engine D merged'
        
        if ($content -ne $originalContent) {
            Set-Content -Path $FilePath -Value $content -NoNewline
            Write-Host "  ✅ Updated: $FilePath" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ℹ️  No changes needed: $FilePath" -ForegroundColor Gray
            return $false
        }
    } else {
        Write-Host "  ⚠️  File not found: $FilePath" -ForegroundColor Yellow
        return $false
    }
}

# Process all scripts
Write-Host "`n🔄 Updating PowerShell scripts..." -ForegroundColor Cyan
$updateCount = 0

foreach ($script in $engineDReferences) {
    $scriptPath = Join-Path "scripts" $script
    if (Update-ScriptFile -FilePath $scriptPath) {
        $updateCount++
    }
}

Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "  Total scripts processed: $($engineDReferences.Count)" -ForegroundColor White
Write-Host "  Scripts updated: $updateCount" -ForegroundColor Green
Write-Host "  Scripts unchanged: $($engineDReferences.Count - $updateCount)" -ForegroundColor Gray

Write-Host "`n✅ Engine D cleanup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review changes: git diff" -ForegroundColor White
Write-Host "  2. Test frontend WebSocket: npm run dev (in frontend/web/)" -ForegroundColor White
Write-Host "  3. Verify Engine C deployment: ./scripts/verify-backend.ps1" -ForegroundColor White
Write-Host "  4. Deploy updated configuration: ./scripts/complete-deployment.ps1" -ForegroundColor White
