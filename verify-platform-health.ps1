#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive verification script for InfinityAI.Pro platform
    Tests all engines and their integration

.DESCRIPTION
    This script verifies:
    - All engines are deployed and healthy
    - Cross-engine communication works
    - Frontend can access all backend services
    - Trading functionality is operational

.EXAMPLE
    .\verify-platform-health.ps1 -Verbose
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$Verbose,
    
    [Parameter(Mandatory=$false)]
    [switch]$QuickCheck,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFile = "platform-health-report.json"
)

# Configuration
$ErrorActionPreference = "Continue"
$WarningPreference = "Continue"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )
    
    $healthCheck = @{
        service = $ServiceName
        url = $Url
        status = "unknown"
        response_time = 0
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        error = $null
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        $response = Invoke-RestMethod -Uri "$Url/health" -Method Get -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        
        $stopwatch.Stop()
        $healthCheck.response_time = $stopwatch.ElapsedMilliseconds
        
        if ($response.status -eq "healthy") {
            $healthCheck.status = "healthy"
            Write-ColorOutput "✅ $ServiceName: Healthy ($($healthCheck.response_time)ms)" "Success"
        } else {
            $healthCheck.status = "unhealthy"
            $healthCheck.error = "Service returned non-healthy status: $($response.status)"
            Write-ColorOutput "⚠️ $ServiceName: Unhealthy - $($response.status)" "Warning"
        }
    }
    catch {
        $stopwatch.Stop()
        $healthCheck.status = "error"
        $healthCheck.error = $_.Exception.Message
        $healthCheck.response_time = $stopwatch.ElapsedMilliseconds
        Write-ColorOutput "❌ $ServiceName: Error - $($_.Exception.Message)" "Error"
    }
    
    return $healthCheck
}

function Test-EngineAPIs {
    param([hashtable]$Services)
    
    Write-ColorOutput "`n🧪 Testing Engine APIs..." "Header"
    
    $apiTests = @()
    
    # Test Engine A - Market Signals
    try {
        Write-ColorOutput "📊 Testing Engine A - Market Data API..." "Info"
        $response = Invoke-RestMethod -Uri "$($Services['engine_a'])/api/signals" -Method Get -TimeoutSec 30
        
        if ($response.status -eq "success" -and $response.signals) {
            $apiTests += @{
                engine = "Engine A"
                api = "/api/signals"
                status = "success"
                data_count = $response.signals.Count
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            Write-ColorOutput "✅ Engine A API: Success ($($response.signals.Count) signals)" "Success"
        } else {
            throw "Invalid response format"
        }
    }
    catch {
        $apiTests += @{
            engine = "Engine A"
            api = "/api/signals"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Engine A API: Error - $($_.Exception.Message)" "Error"
    }
    
    # Test Engine B - AI Signals
    try {
        Write-ColorOutput "🤖 Testing Engine B - AI/ML API..." "Info"
        $response = Invoke-RestMethod -Uri "$($Services['engine_b'])/api/ai-signals" -Method Get -TimeoutSec 30
        
        if ($response.status -eq "success" -and $response.ai_signals) {
            $apiTests += @{
                engine = "Engine B"
                api = "/api/ai-signals"
                status = "success"
                data_count = $response.ai_signals.Count
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            Write-ColorOutput "✅ Engine B API: Success ($($response.ai_signals.Count) AI signals)" "Success"
        } else {
            throw "Invalid response format"
        }
    }
    catch {
        $apiTests += @{
            engine = "Engine B"
            api = "/api/ai-signals"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Engine B API: Error - $($_.Exception.Message)" "Error"
    }
    
    # Test Engine D - System Status
    try {
        Write-ColorOutput "🎯 Testing Engine D - Chatbot API..." "Info"
        $response = Invoke-RestMethod -Uri "$($Services['engine_d'])/api/status" -Method Get -TimeoutSec 30
        
        if ($response.overall_status) {
            $apiTests += @{
                engine = "Engine D"
                api = "/api/status"
                status = "success"
                overall_status = $response.overall_status
                engines_online = $response.engines_online
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            Write-ColorOutput "✅ Engine D API: Success (Status: $($response.overall_status))" "Success"
        } else {
            throw "Invalid response format"
        }
    }
    catch {
        $apiTests += @{
            engine = "Engine D"
            api = "/api/status"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Engine D API: Error - $($_.Exception.Message)" "Error"
    }
    
    return $apiTests
}

function Test-CrossEngineComm {
    Write-ColorOutput "`n🔗 Testing Cross-Engine Communication..." "Header"
    
    $commTests = @()
    
    # Test Engine D's ability to communicate with other engines
    try {
        Write-ColorOutput "🤖 Testing Engine D coordination..." "Info"
        $response = Invoke-RestMethod -Uri "$($Services['engine_d'])/api/engines" -Method Get -TimeoutSec 30
        
        if ($response.engines) {
            $onlineEngines = 0
            foreach ($engine in $response.engine_status.PSObject.Properties) {
                if ($engine.Value.status -eq "online") {
                    $onlineEngines++
                }
            }
            
            $commTests += @{
                test = "Engine D Coordination"
                status = "success"
                engines_reachable = $onlineEngines
                total_engines = $response.engines.PSObject.Properties.Count
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            
            Write-ColorOutput "✅ Cross-Engine Communication: $onlineEngines engines reachable" "Success"
        }
    }
    catch {
        $commTests += @{
            test = "Engine D Coordination"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Cross-Engine Communication: Error - $($_.Exception.Message)" "Error"
    }
    
    return $commTests
}

function Test-FrontendConnectivity {
    param([hashtable]$Services)
    
    Write-ColorOutput "`n🌐 Testing Frontend Connectivity..." "Header"
    
    $frontendTests = @()
    
    # Test if frontend can reach backend APIs
    $frontendUrl = "https://infinityai.pro"
    
    try {
        Write-ColorOutput "🌍 Testing frontend accessibility..." "Info"
        $response = Invoke-WebRequest -Uri $frontendUrl -Method Head -TimeoutSec 15 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $frontendTests += @{
                test = "Frontend Accessibility"
                status = "success"
                status_code = $response.StatusCode
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            Write-ColorOutput "✅ Frontend: Accessible (Status: $($response.StatusCode))" "Success"
        }
    }
    catch {
        $frontendTests += @{
            test = "Frontend Accessibility"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Frontend: Error - $($_.Exception.Message)" "Error"
    }
    
    return $frontendTests
}

function Test-TradingFunctionality {
    param([hashtable]$Services)
    
    if ($QuickCheck) {
        Write-ColorOutput "⏩ Skipping trading functionality tests (QuickCheck mode)" "Info"
        return @()
    }
    
    Write-ColorOutput "`n💰 Testing Trading Functionality..." "Header"
    
    $tradingTests = @()
    
    # Test Engine C - Account Info (read-only)
    try {
        Write-ColorOutput "💼 Testing account information retrieval..." "Info"
        # Note: This would require proper authentication in production
        $response = Invoke-RestMethod -Uri "$($Services['engine_c'])/metrics" -Method Get -TimeoutSec 30
        
        if ($response.service -eq "engine-c-execution") {
            $tradingTests += @{
                test = "Account Info Access"
                status = "success"
                total_orders = $response.total_orders
                active_positions = $response.active_positions
                timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            }
            Write-ColorOutput "✅ Trading Engine: Operational (Orders: $($response.total_orders), Positions: $($response.active_positions))" "Success"
        }
    }
    catch {
        $tradingTests += @{
            test = "Account Info Access"
            status = "error"
            error = $_.Exception.Message
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
        Write-ColorOutput "❌ Trading Engine: Error - $($_.Exception.Message)" "Error"
    }
    
    return $tradingTests
}

function Generate-HealthReport {
    param(
        [array]$HealthChecks,
        [array]$ApiTests,
        [array]$CommTests,
        [array]$FrontendTests,
        [array]$TradingTests
    )
    
    $report = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        platform = "InfinityAI.Pro"
        version = "1.0.0"
        environment = "production"
        summary = @{
            total_services = $HealthChecks.Count
            healthy_services = ($HealthChecks | Where-Object { $_.status -eq "healthy" }).Count
            overall_status = "unknown"
        }
        health_checks = $HealthChecks
        api_tests = $ApiTests
        communication_tests = $CommTests
        frontend_tests = $FrontendTests
        trading_tests = $TradingTests
    }
    
    # Determine overall status
    $healthyCount = $report.summary.healthy_services
    $totalCount = $report.summary.total_services
    
    if ($healthyCount -eq $totalCount) {
        $report.summary.overall_status = "healthy"
    } elseif ($healthyCount -gt 0) {
        $report.summary.overall_status = "degraded"
    } else {
        $report.summary.overall_status = "critical"
    }
    
    return $report
}

function Show-Summary {
    param([hashtable]$Report)
    
    Write-ColorOutput "`n📊 Platform Health Summary" "Header"
    Write-ColorOutput "===========================================" "Header"
    
    $status = $Report.summary.overall_status
    $color = switch ($status) {
        "healthy" { "Success" }
        "degraded" { "Warning" }
        "critical" { "Error" }
        default { "Info" }
    }
    
    Write-ColorOutput "🎯 Overall Status: $($status.ToUpper())" $color
    Write-ColorOutput "📡 Services: $($Report.summary.healthy_services)/$($Report.summary.total_services) healthy" "Info"
    
    Write-ColorOutput "`n🚀 Service Health:" "Info"
    foreach ($health in $Report.health_checks) {
        $icon = if ($health.status -eq "healthy") { "✅" } else { "❌" }
        Write-ColorOutput "$icon $($health.service): $($health.status) ($($health.response_time)ms)" "Info"
    }
    
    Write-ColorOutput "`n🔧 API Tests:" "Info"
    foreach ($api in $Report.api_tests) {
        $icon = if ($api.status -eq "success") { "✅" } else { "❌" }
        Write-ColorOutput "$icon $($api.engine): $($api.status)" "Info"
    }
    
    if ($Report.summary.overall_status -eq "healthy") {
        Write-ColorOutput "`n🎉 All systems operational! InfinityAI.Pro is ready for trading." "Success"
    } else {
        Write-ColorOutput "`n⚠️ Some issues detected. Please review the detailed report." "Warning"
    }
}

# Main execution
function Main {
    Write-ColorOutput "🔍 InfinityAI.Pro Platform Health Verification" "Header"
    Write-ColorOutput "===========================================" "Header"
    
    # Load environment variables
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
    }
    
    # Define services to test
    $services = @{
        engine_a = $env:ENGINE_A_URL ?? "https://engine-a-market-data-573866363639.us-central1.run.app"
        engine_b = $env:ENGINE_B_URL ?? "https://engine-b-ai-ml-573866363639.us-central1.run.app"
        engine_c = $env:ENGINE_C_URL ?? "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c"
        engine_d = $env:ENGINE_D_URL ?? "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d"
        ultra_aggressive = $env:ULTRA_AGGRESSIVE_URL ?? "https://infinityai-ultra-aggressive-573866363639.us-central1.run.app"
    }
    
    # Run health checks
    Write-ColorOutput "`n💓 Checking Service Health..." "Header"
    $healthChecks = @()
    
    foreach ($service in $services.GetEnumerator()) {
        $healthChecks += Test-ServiceHealth -ServiceName $service.Key -Url $service.Value
    }
    
    # Run API tests
    $apiTests = Test-EngineAPIs -Services $services
    
    # Run cross-engine communication tests
    $commTests = Test-CrossEngineComm
    
    # Run frontend tests
    $frontendTests = Test-FrontendConnectivity -Services $services
    
    # Run trading functionality tests
    $tradingTests = Test-TradingFunctionality -Services $services
    
    # Generate comprehensive report
    $report = Generate-HealthReport -HealthChecks $healthChecks -ApiTests $apiTests -CommTests $commTests -FrontendTests $frontendTests -TradingTests $tradingTests
    
    # Save report to file
    $report | ConvertTo-Json -Depth 10 | Out-File $OutputFile -Encoding UTF8
    Write-ColorOutput "`n💾 Detailed report saved to: $OutputFile" "Info"
    
    # Show summary
    Show-Summary -Report $report
    
    # Return status code based on overall health
    if ($report.summary.overall_status -eq "critical") {
        exit 1
    } elseif ($report.summary.overall_status -eq "degraded") {
        exit 2
    } else {
        exit 0
    }
}

# Execute main function
Main