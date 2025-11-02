<#
.SYNOPSIS
    Domain mapping setup and reapplication script for InfinityAI.Pro.

.DESCRIPTION
    This script creates or updates custom domain mappings for Cloud Run services
    and displays required DNS records for domain registrar configuration.

.PARAMETER DryRun
    Preview changes without executing (default: true)

.PARAMETER Project
    GCP project ID (default: infinity-ai-5ec7c)

.PARAMETER Region
    Cloud Run region (default: us-central1)

.EXAMPLE
    .\domain_mapping_reapply.ps1
    # Preview domain mapping (dry-run mode)

.EXAMPLE
    .\domain_mapping_reapply.ps1 -DryRun $false
    # Create/update domain mappings

.NOTES
    Author: InfinityAI.Pro DevOps
    Version: 1.0.0
    Last Updated: 2025-01-20
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
Write-Info "InfinityAI.Pro - Domain Mapping Setup"
Write-Info "=========================================="
Write-Info "Project: $Project"
Write-Info "Region: $Region"
Write-Info "Mode: $(if ($DryRun) { 'DRY-RUN (Preview Only)' } else { 'LIVE EXECUTION' })"
Write-Info ""

# Domain mappings configuration
$DomainMappings = @(
    @{
        Domain = "infinityai.pro"
        Service = "infinityai-frontend"
        Type = "apex"
    },
    @{
        Domain = "api.infinityai.pro"
        Service = "infinityai-engine-c-execution"
        Type = "subdomain"
    },
    @{
        Domain = "engine.infinityai.pro"
        Service = "infinityai-engine-d"
        Type = "subdomain"
    }
)

# DNS records storage
$DnsRecords = @{}

# Step 1: Check for existing domain mappings
Write-Info "Step 1: Checking existing domain mappings..."
$ExistingMappings = gcloud beta run domain-mappings list --region=$Region --project=$Project --format="value(DOMAIN)" 2>&1 | Out-String
$ExistingMappingsList = $ExistingMappings.Trim() -split "`r?`n" | Where-Object { $_ -ne "" }

foreach ($mapping in $DomainMappings) {
    if ($ExistingMappingsList -contains $mapping.Domain) {
        Write-Warning "  Domain mapping exists: $($mapping.Domain) (will update/recreate)"
    } else {
        Write-Info "  New domain mapping: $($mapping.Domain)"
    }
}

Write-Info ""

# Step 2: Create/update domain mappings
Write-Info "Step 2: Creating/updating domain mappings..."
foreach ($mapping in $DomainMappings) {
    $domain = $mapping.Domain
    $service = $mapping.Service
    
    Write-Info "---"
    Write-Info "Domain: $domain → Service: $service"
    
    if ($DryRun) {
        Write-Warning "  [DRY-RUN] Would create/update domain mapping"
        Write-Host "  Command: gcloud beta run domain-mappings create $domain --service=$service --region=$Region --project=$Project --force-override" -ForegroundColor Yellow
        
        # Show sample DNS records for dry-run
        if ($mapping.Type -eq "apex") {
            Write-Info "  DNS Records (A and AAAA required for apex domain):"
            Write-Host "    A      @  216.239.32.21" -ForegroundColor Cyan
            Write-Host "    A      @  216.239.34.21" -ForegroundColor Cyan
            Write-Host "    A      @  216.239.36.21" -ForegroundColor Cyan
            Write-Host "    A      @  216.239.38.21" -ForegroundColor Cyan
            Write-Host "    AAAA   @  2001:4860:4802:32::15" -ForegroundColor Cyan
            Write-Host "    AAAA   @  2001:4860:4802:34::15" -ForegroundColor Cyan
            Write-Host "    AAAA   @  2001:4860:4802:36::15" -ForegroundColor Cyan
            Write-Host "    AAAA   @  2001:4860:4802:38::15" -ForegroundColor Cyan
        } else {
            Write-Info "  DNS Record (CNAME required for subdomain):"
            Write-Host "    CNAME  $($domain.Split('.')[0])  ghs.googlehosted.com." -ForegroundColor Cyan
        }
    } else {
        try {
            # Delete existing mapping if present (to avoid conflicts)
            if ($ExistingMappingsList -contains $domain) {
                Write-Info "  Deleting existing mapping..."
                gcloud beta run domain-mappings delete $domain --region=$Region --project=$Project --quiet 2>&1 | Out-Null
                Start-Sleep -Seconds 2
            }
            
            # Create new mapping
            Write-Info "  Creating domain mapping..."
            $output = gcloud beta run domain-mappings create $domain --service=$service --region=$Region --project=$Project --force-override 2>&1 | Out-String
            
            # Extract DNS records from output
            if ($output -match "Please add the following DNS records") {
                Write-Success "  ✓ Domain mapping created successfully"
                Write-Info "  DNS Records to add at domain registrar:"
                
                # Parse and display DNS records
                $lines = $output -split "`r?`n"
                foreach ($line in $lines) {
                    if ($line -match "^\s+(A|AAAA|CNAME)\s+") {
                        Write-Host "    $($line.Trim())" -ForegroundColor Cyan
                        
                        # Store for summary
                        if (-not $DnsRecords.ContainsKey($domain)) {
                            $DnsRecords[$domain] = @()
                        }
                        $DnsRecords[$domain] += $line.Trim()
                    }
                }
            } else {
                Write-Success "  ✓ Domain mapping created"
            }
        } catch {
            Write-Error "  ✗ Failed to create domain mapping: $_"
        }
    }
}

Write-Info ""

# Step 3: Display DNS configuration summary
Write-Info "=========================================="
Write-Info "DNS CONFIGURATION SUMMARY"
Write-Info "=========================================="
Write-Info ""
Write-Info "Add these DNS records at your domain registrar:"
Write-Info ""

if ($DryRun) {
    Write-Warning "[DRY-RUN] Sample DNS records shown above"
} else {
    if ($DnsRecords.Count -gt 0) {
        foreach ($domain in $DnsRecords.Keys) {
            Write-Info "Domain: $domain"
            foreach ($record in $DnsRecords[$domain]) {
                Write-Host "  $record" -ForegroundColor Cyan
            }
            Write-Info ""
        }
    } else {
        Write-Warning "No DNS records captured. Run gcloud beta run domain-mappings describe <domain> to view records."
    }
}

# Step 4: Verification instructions
Write-Info "=========================================="
Write-Info "VERIFICATION STEPS"
Write-Info "=========================================="
Write-Info ""
Write-Info "1. Add DNS records at your domain registrar (GoDaddy, Namecheap, etc.)"
Write-Info ""
Write-Info "2. Wait for DNS propagation (5-60 minutes):"
Write-Host "   nslookup infinityai.pro" -ForegroundColor Cyan
Write-Host "   nslookup api.infinityai.pro" -ForegroundColor Cyan
Write-Host "   nslookup engine.infinityai.pro" -ForegroundColor Cyan
Write-Info ""
Write-Info "3. Check SSL certificate provisioning:"
Write-Host "   gcloud beta run domain-mappings describe infinityai.pro --region=$Region --project=$Project" -ForegroundColor Cyan
Write-Info ""
Write-Info "4. Test endpoints once SSL is active:"
Write-Host "   curl https://infinityai.pro" -ForegroundColor Cyan
Write-Host "   curl https://api.infinityai.pro/health" -ForegroundColor Cyan
Write-Host "   curl https://engine.infinityai.pro/health" -ForegroundColor Cyan
Write-Info ""

Write-Info "=========================================="
if ($DryRun) {
    Write-Warning "DRY-RUN COMPLETE - No changes made"
    Write-Info "To create domain mappings, run with -DryRun `$false"
} else {
    Write-Success "DOMAIN MAPPING SETUP COMPLETE"
    Write-Info ""
    Write-Info "Next Steps:"
    Write-Info "1. Add DNS records shown above to domain registrar"
    Write-Info "2. Monitor SSL certificate provisioning (can take up to 24 hours)"
    Write-Info "3. Update application configs to use custom domains"
}
Write-Info "=========================================="
