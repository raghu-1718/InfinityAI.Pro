<#
.SYNOPSIS
    Comprehensive DNS, SSL, and endpoint health verification for InfinityAI.Pro.

.DESCRIPTION
    This script performs a complete verification of:
    - DNS propagation (apex and subdomains)
    - SSL certificate provisioning status
    - Endpoint health checks
    - Domain mapping status

.PARAMETER Project
    GCP project ID (default: infinity-ai-5ec7c)

.PARAMETER Region
    Cloud Run region (default: us-central1)

.EXAMPLE
    .\verify_dns_and_ssl.ps1
    # Run complete verification

.NOTES
    Author: InfinityAI.Pro DevOps
    Version: 1.0.0
    Last Updated: 2025-10-20
#>

param(
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
function Write-Section { param($Message) Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta; Write-Host "  $Message" -ForegroundColor Magenta; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Magenta }

$VerificationResults = @{
    DNS = @{}
    SSL = @{}
    Endpoints = @{}
    Overall = $true
}

Write-Section "InfinityAI.Pro - DNS, SSL & Endpoint Verification"
Write-Info "Project: $Project"
Write-Info "Region: $Region"
Write-Info "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Domain configuration
$Domains = @(
    @{
        Domain = "infinityai.pro"
        Type = "apex"
        Service = "infinityai-frontend"
        ExpectedRecords = @{
            A = @("216.239.32.21", "216.239.34.21", "216.239.36.21", "216.239.38.21")
            AAAA = @("2001:4860:4802:32::15", "2001:4860:4802:34::15", "2001:4860:4802:36::15", "2001:4860:4802:38::15")
        }
        HealthPath = "/"
    },
    @{
        Domain = "api.infinityai.pro"
        Type = "subdomain"
        Service = "infinityai-engine-c-execution"
        ExpectedRecords = @{
            CNAME = @("ghs.googlehosted.com.")
        }
        HealthPath = "/health"
    },
    @{
        Domain = "engine.infinityai.pro"
        Type = "subdomain"
        Service = "infinityai-engine-d"
        ExpectedRecords = @{
            CNAME = @("ghs.googlehosted.com.")
        }
        HealthPath = "/health"
    }
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: DNS Propagation Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Section "Step 1: DNS Propagation Check"

foreach ($domain in $Domains) {
    $domainName = $domain.Domain
    Write-Info "Checking DNS for: $domainName"
    
    $dnsResult = @{
        Domain = $domainName
        Resolved = $false
        Records = @()
        Issues = @()
    }
    
    # Try Google DNS (8.8.8.8) for reliable results
    try {
        $output = nslookup $domainName 8.8.8.8 2>&1 | Out-String
        
        if ($output -match "can't find|Server failed|timed out") {
            Write-Error "  ✗ DNS lookup failed for $domainName"
            $dnsResult.Issues += "DNS lookup failed - domain not found"
            $VerificationResults.Overall = $false
        } else {
            # Parse DNS records from nslookup output
            $lines = $output -split "`r?`n"
            $foundRecords = @()
            
            foreach ($line in $lines) {
                if ($line -match "Address:\s+(.+)") {
                    $address = $matches[1].Trim()
                    # Skip DNS server addresses
                    if ($address -ne "8.8.8.8") {
                        $foundRecords += $address
                    }
                }
                if ($line -match "canonical name\s+=\s+(.+)") {
                    $cname = $matches[1].Trim()
                    $foundRecords += $cname
                }
            }
            
            if ($foundRecords.Count -gt 0) {
                $dnsResult.Resolved = $true
                $dnsResult.Records = $foundRecords
                Write-Success "  ✓ DNS resolved: $($foundRecords -join ', ')"
                
                # Verify expected records
                if ($domain.Type -eq "apex") {
                    # Check for at least one A record match
                    $matchedA = $false
                    foreach ($record in $foundRecords) {
                        if ($domain.ExpectedRecords.A -contains $record) {
                            $matchedA = $true
                            break
                        }
                    }
                    if (-not $matchedA) {
                        Write-Warning "  ⚠ No matching A records found for apex domain"
                        $dnsResult.Issues += "Expected A records not found"
                    }
                } else {
                    # Check for CNAME
                    $matchedCNAME = $false
                    foreach ($record in $foundRecords) {
                        if ($domain.ExpectedRecords.CNAME -contains $record) {
                            $matchedCNAME = $true
                            break
                        }
                    }
                    if (-not $matchedCNAME) {
                        Write-Warning "  ⚠ Expected CNAME (ghs.googlehosted.com.) not found"
                        $dnsResult.Issues += "Expected CNAME not found"
                    }
                }
            } else {
                Write-Warning "  ⚠ DNS query returned no usable records"
                $dnsResult.Issues += "No records found in DNS response"
            }
        }
    } catch {
        Write-Error "  ✗ Error checking DNS: $_"
        $dnsResult.Issues += "DNS query error: $_"
        $VerificationResults.Overall = $false
    }
    
    $VerificationResults.DNS[$domainName] = $dnsResult
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: SSL Certificate Status Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Section "Step 2: SSL Certificate Status Check"

foreach ($domain in $Domains) {
    $domainName = $domain.Domain
    Write-Info "Checking SSL certificate for: $domainName"
    
    $sslResult = @{
        Domain = $domainName
        Status = "Unknown"
        CertificateMode = "AUTOMATIC"
        Ready = $false
        Issues = @()
    }
    
    try {
        $output = gcloud beta run domain-mappings describe --domain=$domainName --region=$Region --project=$Project --format=json 2>&1 | ConvertFrom-Json
        
        # Extract status from conditions
        $conditions = $output.status.conditions
        $readyCondition = $conditions | Where-Object { $_.type -eq "Ready" }
        $certCondition = $conditions | Where-Object { $_.type -eq "CertificateProvisioned" }
        
        if ($readyCondition.status -eq "True") {
            $sslResult.Status = "ACTIVE"
            $sslResult.Ready = $true
            Write-Success "  ✓ Domain mapping is ACTIVE"
            Write-Success "  ✓ SSL certificate is provisioned"
        } elseif ($certCondition.status -eq "Unknown" -and $certCondition.reason -eq "CertificatePending") {
            $sslResult.Status = "PENDING"
            $sslResult.Ready = $false
            Write-Warning "  ⚠ SSL certificate provisioning is PENDING"
            Write-Info "    Reason: $($certCondition.message)"
            $sslResult.Issues += $certCondition.message
            $VerificationResults.Overall = $false
        } else {
            $sslResult.Status = "Unknown"
            Write-Warning "  ⚠ SSL certificate status: $($readyCondition.status)"
            $sslResult.Issues += "Certificate status: $($readyCondition.status)"
        }
        
        # Show resource records
        if ($output.status.resourceRecords) {
            Write-Info "  Required DNS records:"
            foreach ($record in $output.status.resourceRecords) {
                $recordName = if ($record.name) { $record.name } else { "@" }
                Write-Host "    $($record.type)  $recordName  $($record.rrdata)" -ForegroundColor Cyan
            }
        }
        
    } catch {
        Write-Error "  ✗ Failed to check SSL status: $_"
        $sslResult.Issues += "Failed to query domain mapping: $_"
        $VerificationResults.Overall = $false
    }
    
    $VerificationResults.SSL[$domainName] = $sslResult
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: Endpoint Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Section "Step 3: Endpoint Health Check"

foreach ($domain in $Domains) {
    $domainName = $domain.Domain
    $healthUrl = "https://$domainName$($domain.HealthPath)"
    
    Write-Info "Testing endpoint: $healthUrl"
    
    $endpointResult = @{
        URL = $healthUrl
        Accessible = $false
        StatusCode = 0
        ResponseTime = 0
        Issues = @()
    }
    
    try {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 30 -UseBasicParsing 2>&1
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        
        if ($response.StatusCode -eq 200) {
            $endpointResult.Accessible = $true
            $endpointResult.StatusCode = 200
            $endpointResult.ResponseTime = [math]::Round($responseTime, 0)
            Write-Success "  ✓ Endpoint is ACCESSIBLE (200 OK) - ${responseTime}ms"
        } else {
            $endpointResult.StatusCode = $response.StatusCode
            Write-Warning "  ⚠ Endpoint returned status: $($response.StatusCode)"
            $endpointResult.Issues += "Non-200 status code: $($response.StatusCode)"
        }
    } catch {
        $errorMessage = $_.Exception.Message
        Write-Error "  ✗ Endpoint is NOT ACCESSIBLE"
        Write-Info "    Error: $errorMessage"
        
        if ($errorMessage -match "Could not resolve|DNS|No such host") {
            $endpointResult.Issues += "DNS not yet propagated or configured"
        } elseif ($errorMessage -match "SSL|certificate") {
            $endpointResult.Issues += "SSL certificate not yet provisioned"
        } else {
            $endpointResult.Issues += $errorMessage
        }
        
        $VerificationResults.Overall = $false
    }
    
    $VerificationResults.Endpoints[$domainName] = $endpointResult
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: Summary Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Section "Verification Summary"

# DNS Summary
Write-Info "DNS Status:"
foreach ($domain in $VerificationResults.DNS.Keys) {
    $result = $VerificationResults.DNS[$domain]
    if ($result.Resolved) {
        Write-Success "  ✓ $domain - Resolved"
    } else {
        Write-Error "  ✗ $domain - Not Resolved"
    }
    if ($result.Issues.Count -gt 0) {
        foreach ($issue in $result.Issues) {
            Write-Warning "    ⚠ $issue"
        }
    }
}

Write-Info ""

# SSL Summary
Write-Info "SSL Certificate Status:"
foreach ($domain in $VerificationResults.SSL.Keys) {
    $result = $VerificationResults.SSL[$domain]
    if ($result.Ready) {
        Write-Success "  ✓ $domain - ACTIVE"
    } else {
        Write-Warning "  ⚠ $domain - PENDING"
    }
    if ($result.Issues.Count -gt 0) {
        foreach ($issue in $result.Issues) {
            Write-Info "    → $issue"
        }
    }
}

Write-Info ""

# Endpoint Summary
Write-Info "Endpoint Health:"
foreach ($domain in $VerificationResults.Endpoints.Keys) {
    $result = $VerificationResults.Endpoints[$domain]
    if ($result.Accessible) {
        Write-Success "  ✓ https://$domain - Accessible ($($result.ResponseTime)ms)"
    } else {
        Write-Error "  ✗ https://$domain - Not Accessible"
    }
    if ($result.Issues.Count -gt 0) {
        foreach ($issue in $result.Issues) {
            Write-Warning "    ⚠ $issue"
        }
    }
}

Write-Info ""

# Overall Status
Write-Section "Overall Status"
if ($VerificationResults.Overall) {
    Write-Success "✓ All checks passed - Platform is fully operational"
    exit 0
} else {
    Write-Warning "⚠ Some checks failed - See details above"
    Write-Info ""
    Write-Info "Common Issues & Solutions:"
    Write-Info "1. DNS not propagated → Wait 5-60 minutes, check with: nslookup <domain> 8.8.8.8"
    Write-Info "2. SSL pending → SSL provisioning can take up to 24 hours after DNS propagates"
    Write-Info "3. Endpoints not accessible → Ensure DNS + SSL are both ready"
    Write-Info ""
    Write-Info "For detailed troubleshooting, see: docs/MIGRATION_COMPLETION_REPORT.md"
    exit 1
}
