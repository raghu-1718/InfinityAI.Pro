#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create Cloud Run domain mappings for all 4 engines
.DESCRIPTION
    Creates custom domain mappings (engine-a/b/c/d.infinityai.pro) for all engines
    Retrieves DNS records needed for Namecheap configuration
#>

$ErrorActionPreference = "Stop"
$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"
$DOMAIN_BASE = "infinityai.pro"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "InfinityAI.Pro - Domain Mapping Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Define service-to-domain mappings
$mappings = @(
    @{ Service = "infinityai-engine-a"; Domain = "engine-a.$DOMAIN_BASE" },
    @{ Service = "infinityai-engine-b"; Domain = "engine-b.$DOMAIN_BASE" },
    @{ Service = "infinityai-engine-c-execution"; Domain = "engine-c.$DOMAIN_BASE" },
    @{ Service = "infinityai-engine-d"; Domain = "engine-d.$DOMAIN_BASE" }
)

$results = @()

foreach ($mapping in $mappings) {
    $service = $mapping.Service
    $domain = $mapping.Domain
    
    Write-Host "[Step] Creating domain mapping: $domain -> $service" -ForegroundColor Yellow
    
    try {
        # Check if mapping already exists
        $existing = gcloud beta run domain-mappings list --region $REGION --project $PROJECT_ID --filter "metadata.name:$domain" --format json 2>$null | ConvertFrom-Json
        
        if ($existing -and $existing.Count -gt 0) {
            Write-Host "  ✓ Domain mapping already exists" -ForegroundColor Green
            $status = "exists"
        } else {
            # Create domain mapping
            $output = gcloud beta run domain-mappings create `
                --service $service `
                --domain $domain `
                --region $REGION `
                --project $PROJECT_ID `
                --format json 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Domain mapping created successfully" -ForegroundColor Green
                $status = "created"
            } else {
                Write-Host "  ✗ Failed to create domain mapping" -ForegroundColor Red
                Write-Host "    Error: $output" -ForegroundColor Red
                $status = "failed"
            }
        }
        
        # Get DNS records
        Write-Host "  [Info] Fetching DNS records for $domain..." -ForegroundColor Cyan
        $dnsRecords = gcloud beta run domain-mappings describe $domain --region $REGION --project $PROJECT_ID --format json 2>$null | ConvertFrom-Json
        
        $results += @{
            Domain = $domain
            Service = $service
            Status = $status
            DNSRecords = $dnsRecords.status.resourceRecords
        }
        
    } catch {
        Write-Host "  ✗ Error processing $domain : $_" -ForegroundColor Red
        $results += @{
            Domain = $domain
            Service = $service
            Status = "error"
            Error = $_.Exception.Message
        }
    }
    
    Write-Host ""
}

# Display DNS configuration summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DNS Configuration for Namecheap" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$dnsInstructions = @"
Add the following DNS records in Namecheap Advanced DNS:

CNAME Records (for Cloud Run engines):
"@

Write-Host $dnsInstructions -ForegroundColor White

foreach ($result in $results) {
    if ($result.Status -ne "error") {
        $subdomain = $result.Domain -replace "\.$DOMAIN_BASE$", ""
        Write-Host "Host: $subdomain" -ForegroundColor Yellow
        Write-Host "Type: CNAME" -ForegroundColor Yellow
        Write-Host "Value: ghs.googlehosted.com" -ForegroundColor Yellow
        Write-Host "TTL: Automatic`n" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Commands" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. List all domain mappings:" -ForegroundColor White
Write-Host "   gcloud beta run domain-mappings list --region $REGION --project $PROJECT_ID`n" -ForegroundColor Gray

Write-Host "2. Check DNS propagation (after adding CNAMEs):" -ForegroundColor White
Write-Host "   nslookup engine-a.$DOMAIN_BASE" -ForegroundColor Gray
Write-Host "   nslookup engine-b.$DOMAIN_BASE" -ForegroundColor Gray
Write-Host "   nslookup engine-c.$DOMAIN_BASE" -ForegroundColor Gray
Write-Host "   nslookup engine-d.$DOMAIN_BASE`n" -ForegroundColor Gray

Write-Host "3. Test HTTPS endpoints (after DNS propagation):" -ForegroundColor White
Write-Host "   Invoke-RestMethod https://engine-a.$DOMAIN_BASE/health" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod https://engine-b.$DOMAIN_BASE/health" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod https://engine-c.$DOMAIN_BASE/health" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod https://engine-d.$DOMAIN_BASE/health`n" -ForegroundColor Gray

# Save results to JSON
$resultsFile = "DOMAIN_MAPPING_RESULTS.json"
$results | ConvertTo-Json -Depth 10 | Out-File $resultsFile -Encoding UTF8
Write-Host "✓ Results saved to: $resultsFile`n" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Domain Mapping Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
