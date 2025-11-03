#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monitor DNS propagation and SSL certificate provisioning
.DESCRIPTION
    Continuously checks DNS resolution and HTTPS endpoints until fully operational
#>

param(
    [int]$MaxAttempts = 60,
    [int]$IntervalSeconds = 30
)

$PROJECT = "after-yesterday-473512-k3"
$REGION = "us-central1"

$DOMAINS = @(
    "infinityai.pro",
    "www.infinityai.pro",
    "engine-a.infinityai.pro",
    "engine-b.infinityai.pro",
    "engine-c.infinityai.pro",
    "engine-d.infinityai.pro"
)

function Test-DnsResolution {
    param([string]$Domain)
    
    try {
        $result = nslookup $Domain 8.8.8.8 2>&1 | Out-String
        
        if ($Domain -eq "infinityai.pro") {
            # Should resolve to 216.239.32.21
            if ($result -match "216\.239\.32\.21") {
                return @{Success=$true; IP="216.239.32.21"; Status="✅ Correct"}
            } elseif ($result -match "199\.36\.158\.100") {
                return @{Success=$false; IP="199.36.158.100"; Status="❌ Old Vercel IP"}
            } else {
                return @{Success=$false; IP="Unknown"; Status="❌ Unknown"}
            }
        } else {
            # Should resolve to ghs.googlehosted.com
            if ($result -match "ghs\.googlehosted\.com") {
                return @{Success=$true; IP="ghs.googlehosted.com"; Status="✅ Correct"}
            } else {
                return @{Success=$false; IP="Unknown"; Status="❌ Not resolving"}
            }
        }
    } catch {
        return @{Success=$false; IP="Error"; Status="❌ DNS Error"}
    }
}

function Test-HttpsEndpoint {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 10 -ErrorAction Stop
        return @{Success=$true; Status=$response.StatusCode; Message="✅ HTTPS Working"}
    } catch {
        $errorMessage = $_.Exception.Message
        if ($errorMessage -match "SSL") {
            return @{Success=$false; Status=0; Message="⏳ SSL Provisioning"}
        } elseif ($errorMessage -match "404") {
            return @{Success=$false; Status=404; Message="⚠️ 404 Not Found"}
        } else {
            return @{Success=$false; Status=0; Message="❌ Connection Failed"}
        }
    }
}

Write-Host "`n=== InfinityAI.Pro - Deployment Monitoring ===" -ForegroundColor Cyan
Write-Host "Max Attempts: $MaxAttempts | Interval: $IntervalSeconds seconds`n" -ForegroundColor Gray

$attempt = 0
$allReady = $false

while ($attempt -lt $MaxAttempts -and -not $allReady) {
    $attempt++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Attempt $attempt/$MaxAttempts" -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Gray
    
    # DNS Check
    Write-Host "`nDNS Resolution:" -ForegroundColor Cyan
    $dnsResults = @{}
    foreach ($domain in $DOMAINS) {
        $result = Test-DnsResolution -Domain $domain
        $dnsResults[$domain] = $result
        Write-Host "  $domain" -ForegroundColor White
        Write-Host "    IP: $($result.IP) | $($result.Status)" -ForegroundColor Gray
    }
    
    # HTTPS Check (only if DNS is correct)
    Write-Host "`nHTTPS Endpoints:" -ForegroundColor Cyan
    $httpsResults = @{}
    
    if ($dnsResults["infinityai.pro"].Success) {
        $result = Test-HttpsEndpoint -Url "https://infinityai.pro"
        $httpsResults["infinityai.pro"] = $result
        Write-Host "  https://infinityai.pro" -ForegroundColor White
        Write-Host "    $($result.Message)" -ForegroundColor Gray
    } else {
        Write-Host "  https://infinityai.pro" -ForegroundColor White
        Write-Host "    ⏭️ Skipped (DNS not ready)" -ForegroundColor Gray
    }
    
    foreach ($subdomain in @("www", "engine-a", "engine-b", "engine-c", "engine-d")) {
        $domain = "$subdomain.infinityai.pro"
        if ($dnsResults[$domain].Success) {
            $url = if ($subdomain -eq "www") { "https://$domain" } else { "https://$domain/health" }
            $result = Test-HttpsEndpoint -Url $url
            $httpsResults[$domain] = $result
            Write-Host "  $url" -ForegroundColor White
            Write-Host "    $($result.Message)" -ForegroundColor Gray
        } else {
            Write-Host "  https://$domain" -ForegroundColor White
            Write-Host "    ⏭️ Skipped (DNS not ready)" -ForegroundColor Gray
        }
    }
    
    # Check if all ready
    $dnsReady = ($dnsResults.Values | Where-Object { -not $_.Success }).Count -eq 0
    $httpsReady = ($httpsResults.Values | Where-Object { -not $_.Success }).Count -eq 0
    $allReady = $dnsReady -and $httpsReady -and $httpsResults.Count -gt 0
    
    if ($allReady) {
        Write-Host "`n" + ("=" * 80) -ForegroundColor Green
        Write-Host "🎉 ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Green
        Write-Host "`nDNS: ✅ All domains resolving correctly" -ForegroundColor Green
        Write-Host "SSL: ✅ All certificates provisioned" -ForegroundColor Green
        Write-Host "HTTPS: ✅ All endpoints responding" -ForegroundColor Green
        break
    } else {
        Write-Host "`n" + ("=" * 80) -ForegroundColor Yellow
        if (-not $dnsReady) {
            Write-Host "⏳ Waiting for DNS propagation..." -ForegroundColor Yellow
            Write-Host "   ACTION REQUIRED: Update Namecheap A record to 216.239.32.21" -ForegroundColor Red
        } elseif (-not $httpsReady) {
            Write-Host "⏳ DNS ready. Waiting for SSL certificates..." -ForegroundColor Yellow
            Write-Host "   (Google is provisioning certificates automatically)" -ForegroundColor Gray
        }
        
        if ($attempt -lt $MaxAttempts) {
            Write-Host "`nNext check in $IntervalSeconds seconds...`n" -ForegroundColor Gray
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
}

if (-not $allReady) {
    Write-Host "`n" + ("=" * 80) -ForegroundColor Red
    Write-Host "⚠️ MONITORING TIMEOUT" -ForegroundColor Red
    Write-Host ("=" * 80) -ForegroundColor Red
    Write-Host "`nDeployment not fully operational after $MaxAttempts attempts." -ForegroundColor Yellow
    Write-Host "This is normal and may require manual verification." -ForegroundColor Gray
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Verify Namecheap DNS A record is set to 216.239.32.21" -ForegroundColor White
    Write-Host "2. Wait 15-60 minutes for SSL certificate provisioning" -ForegroundColor White
    Write-Host "3. Manually test: curl -I https://infinityai.pro" -ForegroundColor White
}

Write-Host "`nDone!" -ForegroundColor Green
