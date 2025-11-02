# InfinityAI.Pro - Domain Mapping Setup Script
# This script helps set up domain mapping for infinityai.pro

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "🌐 InfinityAI.Pro - Domain Mapping Setup" -ForegroundColor Cyan
Write-Host "================================================================================`n" -ForegroundColor Cyan

# Configuration
$DOMAIN = "infinityai.pro"
$WWW_DOMAIN = "www.infinityai.pro"
$SERVICE_NAME = "infinityai-frontend"
$REGION = "us-central1"
$PROJECT_ID = "after-yesterday-473512-k3"
$DNS_ZONE = "infinityai-pro-zone"

# Step 1: Check Domain Verification
Write-Host "ℹ️  Step 1: Checking domain verification status..." -ForegroundColor Yellow
$verifiedDomains = gcloud domains list-user-verified 2>&1 | Out-String

if ($verifiedDomains -match $DOMAIN) {
    Write-Host "✅ Domain $DOMAIN is verified" -ForegroundColor Green
    $domainVerified = $true
} else {
    Write-Host "⚠️  Domain $DOMAIN is NOT verified yet" -ForegroundColor Yellow
    Write-Host "`nℹ️  To verify your domain:" -ForegroundColor Cyan
    Write-Host "   1. Visit: https://search.google.com/search-console/welcome" -ForegroundColor White
    Write-Host "   2. Select 'Domain' property type" -ForegroundColor White
    Write-Host "   3. Enter: $DOMAIN" -ForegroundColor White
    Write-Host "   4. Copy the TXT record provided" -ForegroundColor White
    Write-Host "   5. Add it to Cloud DNS using:" -ForegroundColor White
    Write-Host "      gcloud dns record-sets create $DOMAIN. ``" -ForegroundColor Gray
    Write-Host "        --rrdatas=`"google-site-verification=YOUR_TOKEN_HERE`" ``" -ForegroundColor Gray
    Write-Host "        --type=TXT --ttl=3600 --zone=$DNS_ZONE" -ForegroundColor Gray
    Write-Host "   6. Wait 10-15 minutes and run this script again`n" -ForegroundColor White
    
    $response = Read-Host "Do you want to open Google Search Console now? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Start-Process "https://search.google.com/search-console/welcome"
    }
    
    $domainVerified = $false
}

# Step 2: List Current DNS Records
Write-Host "`nℹ️  Step 2: Current DNS records in $DNS_ZONE..." -ForegroundColor Yellow
try {
    gcloud dns record-sets list --zone=$DNS_ZONE --filter="type=A OR type=CNAME OR type=TXT" 2>&1
    Write-Host "✅ DNS zone accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ Error accessing DNS zone: $_" -ForegroundColor Red
}

# Step 3: Check if domain mappings already exist
Write-Host "`nℹ️  Step 3: Checking existing domain mappings..." -ForegroundColor Yellow
$existingMappings = gcloud beta run domain-mappings list --region=$REGION 2>&1 | Out-String

if ($existingMappings -match $DOMAIN) {
    Write-Host "✅ Domain mapping for $DOMAIN already exists" -ForegroundColor Green
    $mappingExists = $true
} else {
    Write-Host "⚠️  No domain mapping found for $DOMAIN" -ForegroundColor Yellow
    $mappingExists = $false
}

# Step 4: Create Domain Mapping (if domain is verified)
if ($domainVerified -and -not $mappingExists) {
    Write-Host "`nℹ️  Step 4: Creating domain mapping for $DOMAIN..." -ForegroundColor Yellow
    
    try {
        $mappingResult = gcloud beta run domain-mappings create `
            --service=$SERVICE_NAME `
            --domain=$DOMAIN `
            --region=$REGION 2>&1 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Domain mapping created for $DOMAIN" -ForegroundColor Green
            Write-Host "`nℹ️  Please add the following DNS records:" -ForegroundColor Cyan
            Write-Host $mappingResult
        } else {
            Write-Host "❌ Failed to create domain mapping: $mappingResult" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error creating domain mapping: $_" -ForegroundColor Red
    }
    
    # Create www subdomain mapping
    Write-Host "`nℹ️  Creating domain mapping for $WWW_DOMAIN..." -ForegroundColor Yellow
    try {
        $wwwMappingResult = gcloud beta run domain-mappings create `
            --service=$SERVICE_NAME `
            --domain=$WWW_DOMAIN `
            --region=$REGION 2>&1 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Domain mapping created for $WWW_DOMAIN" -ForegroundColor Green
            Write-Host "`nℹ️  Please add the following DNS records:" -ForegroundColor Cyan
            Write-Host $wwwMappingResult
        } else {
            Write-Host "❌ Failed to create www domain mapping: $wwwMappingResult" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error creating www domain mapping: $_" -ForegroundColor Red
    }
} elseif (-not $domainVerified) {
    Write-Host "`n⚠️  Step 4: Skipping domain mapping creation (domain not verified)" -ForegroundColor Yellow
} elseif ($mappingExists) {
    Write-Host "`n✅ Step 4: Domain mapping already exists" -ForegroundColor Green
}

# Step 5: Check DNS Record Requirements
Write-Host "`nℹ️  Step 5: Recommended DNS Records..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Try to get domain mapping details
if ($domainVerified -and $mappingExists) {
    Write-Host "`nℹ️  Fetching DNS requirements from domain mapping..." -ForegroundColor Yellow
    try {
        $domainDetails = gcloud beta run domain-mappings describe $DOMAIN --region=$REGION --format=json 2>&1 | ConvertFrom-Json
        
        if ($domainDetails.status.resourceRecords) {
            Write-Host "`n📋 Required DNS Records:" -ForegroundColor Cyan
            foreach ($record in $domainDetails.status.resourceRecords) {
                Write-Host "   Type: $($record.type)" -ForegroundColor White
                Write-Host "   Name: $($record.name)" -ForegroundColor White
                Write-Host "   Value: $($record.rrdata)" -ForegroundColor White
                Write-Host ""
            }
        }
    } catch {
        Write-Host "⚠️  Could not fetch DNS requirements automatically" -ForegroundColor Yellow
    }
}

# Provide manual DNS record guidance
Write-Host "`n📝 Manual DNS Record Setup:" -ForegroundColor Cyan
Write-Host "   If domain mapping is created, Cloud Run will provide specific DNS records." -ForegroundColor White
Write-Host "   Typically, you need:" -ForegroundColor White
Write-Host "   1. CNAME record for www.$DOMAIN → ghs.googlehosted.com" -ForegroundColor Gray
Write-Host "   2. A records for $DOMAIN → (IP addresses provided by Cloud Run)" -ForegroundColor Gray
Write-Host ""

# Step 6: DNS Propagation Check
Write-Host "`nℹ️  Step 6: DNS Propagation Status..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Check nameservers
Write-Host "`n🔍 Nameserver Check:" -ForegroundColor Cyan
try {
    $nsRecords = Resolve-DnsName -Name $DOMAIN -Type NS -ErrorAction SilentlyContinue
    if ($nsRecords) {
        Write-Host "✅ Nameservers configured:" -ForegroundColor Green
        foreach ($ns in $nsRecords | Where-Object {$_.Type -eq "NS"}) {
            Write-Host "   - $($ns.NameHost)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  Could not resolve nameservers" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Nameserver check failed: $_" -ForegroundColor Yellow
}

# Check A records
Write-Host "`n🔍 A Record Check:" -ForegroundColor Cyan
try {
    $aRecords = Resolve-DnsName -Name $DOMAIN -Type A -ErrorAction SilentlyContinue
    if ($aRecords -and $aRecords.IP4Address) {
        Write-Host "✅ A records found:" -ForegroundColor Green
        foreach ($ip in $aRecords.IP4Address) {
            Write-Host "   - $ip" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  No A records found (this is normal until domain mapping is complete)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  A record check failed: $_" -ForegroundColor Yellow
}

# Check CNAME for www
Write-Host "`n🔍 CNAME Check (www):" -ForegroundColor Cyan
try {
    $cnameRecords = Resolve-DnsName -Name $WWW_DOMAIN -Type CNAME -ErrorAction SilentlyContinue
    if ($cnameRecords -and $cnameRecords.NameHost) {
        Write-Host "✅ CNAME record found:" -ForegroundColor Green
        Write-Host "   - $($cnameRecords.NameHost)" -ForegroundColor White
    } else {
        Write-Host "⚠️  No CNAME record found for www (this is normal until DNS records are added)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  CNAME check failed: $_" -ForegroundColor Yellow
}

# Step 7: Summary and Next Steps
Write-Host "`n" -ForegroundColor Gray
Write-Host "================================================================================`n" -ForegroundColor Cyan
Write-Host "📊 Summary" -ForegroundColor Cyan
Write-Host "================================================================================`n" -ForegroundColor Cyan

Write-Host "Domain Verification: " -NoNewline
if ($domainVerified) {
    Write-Host "✅ VERIFIED" -ForegroundColor Green
} else {
    Write-Host "⏳ PENDING" -ForegroundColor Yellow
}

Write-Host "Domain Mapping: " -NoNewline
if ($mappingExists) {
    Write-Host "✅ EXISTS" -ForegroundColor Green
} else {
    Write-Host "⏳ PENDING" -ForegroundColor Yellow
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
if (-not $domainVerified) {
    Write-Host "   1. ⏳ Complete domain verification in Google Search Console" -ForegroundColor Yellow
    Write-Host "   2. ⏳ Add TXT record to Cloud DNS" -ForegroundColor Yellow
    Write-Host "   3. ⏳ Run this script again after 10-15 minutes" -ForegroundColor Yellow
} elseif (-not $mappingExists) {
    Write-Host "   1. ✅ Domain is verified" -ForegroundColor Green
    Write-Host "   2. ⏳ Create domain mapping (will be done automatically)" -ForegroundColor Yellow
    Write-Host "   3. ⏳ Add DNS records as instructed above" -ForegroundColor Yellow
} else {
    Write-Host "   1. ✅ Domain is verified" -ForegroundColor Green
    Write-Host "   2. ✅ Domain mapping exists" -ForegroundColor Green
    Write-Host "   3. ⏳ Ensure DNS records are added (check output above)" -ForegroundColor Yellow
    Write-Host "   4. ⏳ Wait 24-48 hours for DNS propagation" -ForegroundColor Yellow
    Write-Host "   5. ⏳ Test at https://$DOMAIN" -ForegroundColor Yellow
}

Write-Host "`n📍 Current Working URL:" -ForegroundColor Cyan
Write-Host "   https://infinityai-frontend-bprmddefsa-uc.a.run.app" -ForegroundColor White
Write-Host "   (Use this URL while DNS propagates)`n" -ForegroundColor Gray

Write-Host "================================================================================`n" -ForegroundColor Cyan
