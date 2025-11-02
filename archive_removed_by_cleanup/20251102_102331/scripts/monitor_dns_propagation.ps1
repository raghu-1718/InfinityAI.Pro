<#
.SYNOPSIS
    Monitor DNS propagation for InfinityAI.Pro subdomains with auto-refresh.

.DESCRIPTION
    This script continuously monitors DNS propagation for api.infinityai.pro and
    engine.infinityai.pro, checking every 5 minutes until both CNAMEs resolve.

.PARAMETER IntervalSeconds
    Time between checks in seconds (default: 300 = 5 minutes)

.PARAMETER MaxAttempts
    Maximum number of check attempts (default: 24 = 2 hours with 5-min intervals)

.EXAMPLE
    .\monitor_dns_propagation.ps1
    # Monitor with default 5-minute intervals

.EXAMPLE
    .\monitor_dns_propagation.ps1 -IntervalSeconds 60 -MaxAttempts 60
    # Monitor every minute for up to 1 hour

.NOTES
    Author: InfinityAI.Pro DevOps
    Version: 1.0.0
    Last Updated: 2025-10-21
#>

param(
    [Parameter(Mandatory=$false)]
    [int]$IntervalSeconds = 300,  # 5 minutes

    [Parameter(Mandatory=$false)]
    [int]$MaxAttempts = 24  # 2 hours with 5-minute intervals
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Section { param($Message) Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta; Write-Host "  $Message" -ForegroundColor Magenta; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Magenta }

$Domains = @("api.infinityai.pro", "engine.infinityai.pro")
$ResolvedDomains = @{}
$Attempt = 0

Write-Section "InfinityAI.Pro - DNS Propagation Monitor"
Write-Info "Monitoring domains: $($Domains -join ', ')"
Write-Info "Check interval: $IntervalSeconds seconds"
Write-Info "Max attempts: $MaxAttempts"
Write-Info "Press Ctrl+C to stop monitoring"
Write-Info ""

function Test-DnsCname {
    param(
        [string]$Domain,
        [string]$DnsServer = "8.8.8.8"
    )
    
    try {
        $output = nslookup $Domain $DnsServer 2>&1 | Out-String
        
        if ($output -match "canonical name\s+=\s+ghs\.googlehosted\.com") {
            return @{
                Resolved = $true
                CNAME = "ghs.googlehosted.com"
            }
        } elseif ($output -match "canonical name\s+=\s+(.+)") {
            return @{
                Resolved = $true
                CNAME = $matches[1].Trim()
            }
        } else {
            return @{
                Resolved = $false
                CNAME = $null
            }
        }
    } catch {
        return @{
            Resolved = $false
            CNAME = $null
        }
    }
}

# Main monitoring loop
while ($Attempt -lt $MaxAttempts) {
    $Attempt++
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    
    Write-Section "Check #$Attempt - $timestamp"
    
    $allResolved = $true
    
    foreach ($domain in $Domains) {
        if ($ResolvedDomains.ContainsKey($domain)) {
            Write-Success "$domain - Already resolved ✓"
            continue
        }
        
        Write-Info "Checking $domain..."
        
        # Test with multiple DNS servers
        $googleResult = Test-DnsCname -Domain $domain -DnsServer "8.8.8.8"
        $cloudflareResult = Test-DnsCname -Domain $domain -DnsServer "1.1.1.1"
        
        if ($googleResult.Resolved -and $googleResult.CNAME -eq "ghs.googlehosted.com") {
            Write-Success "  ✓ Resolved on Google DNS (8.8.8.8): $($googleResult.CNAME)"
            $ResolvedDomains[$domain] = $timestamp
        } elseif ($cloudflareResult.Resolved -and $cloudflareResult.CNAME -eq "ghs.googlehosted.com") {
            Write-Success "  ✓ Resolved on Cloudflare DNS (1.1.1.1): $($cloudflareResult.CNAME)"
            $ResolvedDomains[$domain] = $timestamp
        } else {
            Write-Warning "  ⚠ Not yet propagated (checked 8.8.8.8 and 1.1.1.1)"
            $allResolved = $false
        }
    }
    
    Write-Info ""
    Write-Info "Status Summary:"
    Write-Info "  Resolved: $($ResolvedDomains.Count) / $($Domains.Count)"
    Write-Info "  Pending: $($Domains.Count - $ResolvedDomains.Count)"
    
    if ($allResolved) {
        Write-Info ""
        Write-Section "🎉 All Domains Resolved!"
        Write-Success "DNS propagation complete for all subdomains"
        Write-Info ""
        Write-Info "Resolved domains:"
        foreach ($domain in $ResolvedDomains.Keys) {
            Write-Success "  ✓ $domain - Resolved at $($ResolvedDomains[$domain])"
        }
        Write-Info ""
        Write-Info "Next Steps:"
        Write-Info "1. Wait for SSL certificate provisioning (automatic, up to 24 hours)"
        Write-Info "2. Run verification script:"
        Write-Host "   .\scripts\verify_dns_and_ssl.ps1" -ForegroundColor Cyan
        Write-Info "3. Check SSL status:"
        Write-Host "   gcloud beta run domain-mappings describe api.infinityai.pro --region=us-central1 --project=infinity-ai-5ec7c" -ForegroundColor Cyan
        Write-Host "   gcloud beta run domain-mappings describe engine.infinityai.pro --region=us-central1 --project=infinity-ai-5ec7c" -ForegroundColor Cyan
        exit 0
    }
    
    if ($Attempt -lt $MaxAttempts) {
        Write-Info ""
        Write-Warning "Waiting $IntervalSeconds seconds before next check..."
        Write-Info "Next check in: $(Get-Date).AddSeconds($IntervalSeconds).ToString('HH:mm:ss')"
        Start-Sleep -Seconds $IntervalSeconds
    }
}

# Max attempts reached
Write-Info ""
Write-Section "Monitoring Complete"
Write-Warning "Reached maximum attempts ($MaxAttempts)"
Write-Info ""
Write-Info "Resolved domains: $($ResolvedDomains.Count) / $($Domains.Count)"
if ($ResolvedDomains.Count -gt 0) {
    foreach ($domain in $ResolvedDomains.Keys) {
        Write-Success "  ✓ $domain"
    }
}

$pendingDomains = $Domains | Where-Object { -not $ResolvedDomains.ContainsKey($_) }
if ($pendingDomains.Count -gt 0) {
    Write-Info ""
    Write-Warning "Still pending:"
    foreach ($domain in $pendingDomains) {
        Write-Warning "  ⚠ $domain"
    }
    Write-Info ""
    Write-Info "Suggestions:"
    Write-Info "1. Verify CNAME records are correctly configured in Namecheap"
    Write-Info "2. Check that no conflicting records exist"
    Write-Info "3. Wait longer and run this script again"
    Write-Info "4. Manual check:"
    Write-Host "   nslookup $($pendingDomains[0]) 8.8.8.8" -ForegroundColor Cyan
}

exit 1
