#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Continuous DNS monitoring until propagation complete
.DESCRIPTION
    Checks DNS every 30 seconds until infinityai.pro resolves to 216.239.32.21
#>

$TARGET_IP = "216.239.32.21"
$DOMAIN = "infinityai.pro"
$CHECK_INTERVAL = 30
$MAX_CHECKS = 120  # 1 hour

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DNS Propagation Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Domain: $DOMAIN" -ForegroundColor White
Write-Host "Target IP: $TARGET_IP" -ForegroundColor Green
Write-Host "Check Interval: $CHECK_INTERVAL seconds`n" -ForegroundColor Gray

$checkCount = 0
$startTime = Get-Date

while ($checkCount -lt $MAX_CHECKS) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    
    Write-Host "[$timestamp] Check $checkCount (Elapsed: ${elapsed}m)" -ForegroundColor Yellow
    
    # Check multiple DNS servers
    $dnsServers = @{
        "Authoritative" = "dns1.registrar-servers.com"
        "Google DNS" = "8.8.8.8"
        "Cloudflare DNS" = "1.1.1.1"
    }
    
    $allUpdated = $true
    
    foreach ($server in $dnsServers.GetEnumerator()) {
        try {
            $result = nslookup $DOMAIN $server.Value 2>&1 | Out-String
            
            if ($result -match "Address:\s*(\d+\.\d+\.\d+\.\d+)") {
                $resolvedIP = $matches[1]
                
                if ($resolvedIP -eq $TARGET_IP) {
                    Write-Host "  ✅ $($server.Key): $resolvedIP" -ForegroundColor Green
                } else {
                    Write-Host "  ⏳ $($server.Key): $resolvedIP (still old)" -ForegroundColor Yellow
                    $allUpdated = $false
                }
            } else {
                Write-Host "  ❌ $($server.Key): No response" -ForegroundColor Red
                $allUpdated = $false
            }
        } catch {
            Write-Host "  ❌ $($server.Key): Error" -ForegroundColor Red
            $allUpdated = $false
        }
    }
    
    if ($allUpdated) {
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "🎉 DNS PROPAGATION COMPLETE!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "`n✅ All DNS servers now resolve $DOMAIN to $TARGET_IP" -ForegroundColor Green
        Write-Host "⏱️  Total propagation time: ${elapsed} minutes" -ForegroundColor Cyan
        Write-Host "`nNext step: SSL certificate provisioning (15-60 minutes)" -ForegroundColor Yellow
        Write-Host "Run: pwsh scripts/monitor_deployment.ps1`n" -ForegroundColor White
        
        # Test HTTPS
        Write-Host "Testing HTTPS endpoint..." -ForegroundColor Cyan
        try {
            $response = curl -I https://$DOMAIN 2>&1 | Out-String
            if ($response -match "HTTP/") {
                Write-Host "✅ HTTPS responding (certificate may still be provisioning)" -ForegroundColor Green
            }
        } catch {
            Write-Host "⏳ HTTPS not ready yet (SSL provisioning in progress)" -ForegroundColor Yellow
        }
        
        exit 0
    }
    
    Write-Host "`n⏳ DNS not fully propagated yet. Next check in $CHECK_INTERVAL seconds...`n" -ForegroundColor Gray
    Start-Sleep -Seconds $CHECK_INTERVAL
}

Write-Host "`n========================================" -ForegroundColor Red
Write-Host "⚠️  TIMEOUT REACHED" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host "`nDNS propagation not complete after ${elapsed} minutes." -ForegroundColor Yellow
Write-Host "`nPossible issues:" -ForegroundColor Yellow
Write-Host "1. A record was not updated correctly in Namecheap" -ForegroundColor White
Write-Host "2. DNS caching is taking longer than expected" -ForegroundColor White
Write-Host "3. Namecheap's DNS servers are slow to update" -ForegroundColor White
Write-Host "`nAction: Verify in Namecheap that A record = $TARGET_IP`n" -ForegroundColor Cyan
exit 1
