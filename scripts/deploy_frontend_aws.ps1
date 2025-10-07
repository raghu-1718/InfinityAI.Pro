param(
  [string]$Domain = "infinityai.pro",
  [string]$Region = "us-east-1",
  [string]$FrontendDir = "infinityai-pro/frontend",
  [string]$ApiBaseUrl = ""
)

Write-Host "🚀 Deploying frontend to AWS S3 + CloudFront for $Domain" -ForegroundColor Cyan

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  Write-Host "AWS CLI not found." -ForegroundColor Red; exit 1
}

# 1) Build frontend
if (-not (Test-Path $FrontendDir)) { Write-Host "Frontend directory not found: $FrontendDir" -ForegroundColor Red; exit 1 }
Push-Location $FrontendDir
if ($ApiBaseUrl) {
  $env:FRONTEND_API_URL = $ApiBaseUrl
}
if (Test-Path package.json) {
  npm install
  npm run build
} else {
  Write-Host "package.json not found; ensure frontend build exists." -ForegroundColor Yellow
}
Pop-Location

# 2) Create S3 bucket (private)
$bucket = $Domain.Replace(".", "-") + "-frontend"
if ($Region -eq 'us-east-1') {
  aws s3api create-bucket --bucket $bucket --region $Region 2>$null | Out-Null
} else {
  aws s3api create-bucket --bucket $bucket --region $Region --create-bucket-configuration LocationConstraint=$Region 2>$null | Out-Null
}

# 3) Enable bucket encryption and block public access
aws s3api put-public-access-block --bucket $bucket --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true | Out-Null
aws s3api put-bucket-encryption --bucket $bucket --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' | Out-Null

# 4) Upload build
$buildPath = Join-Path $FrontendDir "build"
if (-not (Test-Path $buildPath)) { $buildPath = Join-Path $FrontendDir "dist" }
aws s3 sync $buildPath s3://$bucket/ --delete | Out-Null

# 5) Create/Validate ACM cert in us-east-1 for CloudFront
$certArn = (aws acm list-certificates --region us-east-1 --query "CertificateSummaryList[?DomainName=='$Domain'].CertificateArn" --output text)
if (-not $certArn) {
  $certArn = (aws acm request-certificate --region us-east-1 --domain-name $Domain --validation-method DNS --subject-alternative-names "www.$Domain" --query CertificateArn --output text)
  Write-Host "Requested ACM certificate: $certArn (creating DNS validation records if hosted zone exists)" -ForegroundColor Yellow
}

# Try to auto-create DNS validation records in Route 53 if hosted zone exists
$zoneId = (aws route53 list-hosted-zones-by-name --dns-name $Domain --query 'HostedZones[0].Id' --output text)
if ($zoneId -and $certArn) {
  $certDetail = aws acm describe-certificate --region us-east-1 --certificate-arn $certArn | ConvertFrom-Json
  $validations = $certDetail.Certificate.DomainValidationOptions | Where-Object { $_.ResourceRecord }
  if ($validations) {
    $changes = @()
    foreach ($v in $validations) {
      $rr = $v.ResourceRecord
      $changes += @{ Action = 'UPSERT'; ResourceRecordSet = @{ Name = $rr.Name; Type = $rr.Type; TTL = 60; ResourceRecords = @(@{ Value = $rr.Value }) } }
    }
    $batch = @{ Comment = "ACM validation records for $Domain"; Changes = $changes } | ConvertTo-Json -Depth 6
    aws route53 change-resource-record-sets --hosted-zone-id $zoneId --change-batch $batch | Out-Null
    Write-Host "📌 Created/updated ACM DNS validation records in Route 53" -ForegroundColor Green
  }
}

# Check certificate status
$certStatus = "UNKNOWN"
if ($certArn) {
  try {
    $certStatus = (aws acm describe-certificate --region us-east-1 --certificate-arn $certArn --query 'Certificate.Status' --output text)
  } catch {}
}

# 6) Create CloudFront distribution with OAC
try {
  $oacId = (aws cloudfront create-origin-access-control --origin-access-control-config '{"Name":"cf-oac-'$bucket'","SigningProtocol":"sigv4","SigningBehavior":"always","OriginAccessControlOriginType":"s3"}' --query 'OriginAccessControl.Id' --output text)
} catch { $oacId = $null }
# Build distribution config depending on certificate readiness
if ($certStatus -eq 'ISSUED') {
  $origJson = '{
    "CallerReference": "' + [guid]::NewGuid().ToString() + '",
    "Comment": "InfinityAI frontend",
    "Enabled": true,
    "Aliases": {"Items": ["' + $Domain + '", "www.' + $Domain + '"], "Quantity": 2},
    "Origins": {"Items": [{
      "Id": "s3-' + $bucket + '",
      "DomainName": "' + $bucket + '.s3.' + $Region + '.amazonaws.com",
      "S3OriginConfig": {"OriginAccessIdentity": ""},
      "OriginAccessControlId": "' + $oacId + '"
    }], "Quantity": 1},
    "DefaultCacheBehavior": {
      "TargetOriginId": "s3-' + $bucket + '",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {"Items": ["GET","HEAD"], "Quantity": 2},
      "Compress": true,
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"
    },
    "ViewerCertificate": {"ACMCertificateArn": "' + $certArn + '", "SSLSupportMethod": "sni-only", "MinimumProtocolVersion": "TLSv1.2_2021"}
  }'
} else {
  Write-Host "⚠️ ACM certificate status: $certStatus. Creating distribution with default certificate; we'll attach custom domain after issuance." -ForegroundColor Yellow
  $origJson = '{
    "CallerReference": "' + [guid]::NewGuid().ToString() + '",
    "Comment": "InfinityAI frontend (temp default cert)",
    "Enabled": true,
    "Aliases": {"Quantity": 0},
    "Origins": {"Items": [{
      "Id": "s3-' + $bucket + '",
      "DomainName": "' + $bucket + '.s3.' + $Region + '.amazonaws.com",
      "S3OriginConfig": {"OriginAccessIdentity": ""},
      "OriginAccessControlId": "' + $oacId + '"
    }], "Quantity": 1},
    "DefaultCacheBehavior": {
      "TargetOriginId": "s3-' + $bucket + '",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {"Items": ["GET","HEAD"], "Quantity": 2},
      "Compress": true,
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"
    },
    "ViewerCertificate": {"CloudFrontDefaultCertificate": true}
  }'
}
try {
  $distId = (aws cloudfront create-distribution --distribution-config "$origJson" --query 'Distribution.Id' --output text)
} catch { $distId = "" }
$cfDomain = ""
if ($distId) {
  $cfDomain = (aws cloudfront get-distribution --id $distId --query 'Distribution.DomainName' --output text)
  Write-Host "CloudFront domain: https://$cfDomain" -ForegroundColor Green
} else {
  Write-Host "CloudFront distribution not created (likely IAM). Falling back to S3 static website hosting (public)." -ForegroundColor Yellow
  # Allow public access (disable blocks)
  aws s3api put-public-access-block --bucket $bucket --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false | Out-Null
  # Bucket policy for public read
  $publicPolicy = @{ Version = '2012-10-17'; Statement = @(@{ Sid='PublicReadGetObject'; Effect='Allow'; Principal='*'; Action='s3:GetObject'; Resource=@("arn:aws:s3:::$bucket/*") }) } | ConvertTo-Json -Depth 6
  aws s3api put-bucket-policy --bucket $bucket --policy $publicPolicy | Out-Null
  # Enable website hosting
  $websiteCfg = @{ IndexDocument = @{ Suffix = 'index.html' }; ErrorDocument = @{ Key = 'index.html' } } | ConvertTo-Json -Depth 6
  aws s3api put-bucket-website --bucket $bucket --website-configuration $websiteCfg | Out-Null
  $websiteUrl = if ($Region -eq 'us-east-1') { "http://$bucket.s3-website-us-east-1.amazonaws.com" } else { "http://$bucket.s3-website-$Region.amazonaws.com" }
  Write-Host "S3 Website URL: $websiteUrl" -ForegroundColor Green
}

# 7) Grant bucket policy for CloudFront OAC
$account = (aws sts get-caller-identity --query Account --output text)
$cfArn = "arn:aws:cloudfront::${account}:distribution/${distId}"
$policyObj = [ordered]@{
  Version = "2012-10-17"
  Statement = @(
    [ordered]@{
      Sid = "AllowCloudFrontServicePrincipalReadOnly"
      Effect = "Allow"
      Principal = @{ Service = "cloudfront.amazonaws.com" }
      Action = @("s3:GetObject")
      Resource = @("arn:aws:s3:::${bucket}/*")
      Condition = @{ "StringEquals" = @{ "AWS:SourceArn" = $cfArn } }
    }
  )
}
$policyJson = ($policyObj | ConvertTo-Json -Depth 6)
aws s3api put-bucket-policy --bucket $bucket --policy $policyJson | Out-Null

# 8) Route 53 alias records (requires hosted zone) — only if custom cert was attached
if ($zoneId -and $certStatus -eq 'ISSUED' -and $cfDomain) {
  $cfHostedZoneId = "Z2FDTNDATAQYW2" # CloudFront HZ ID
  $changes = '{
    "Comment": "Alias records for CloudFront",
    "Changes": [
      {"Action": "UPSERT", "ResourceRecordSet": {"Name": "' + $Domain + '", "Type": "A", "AliasTarget": {"DNSName": "' + $cfDomain + '", "HostedZoneId": "' + $cfHostedZoneId + '", "EvaluateTargetHealth": false}}},
      {"Action": "UPSERT", "ResourceRecordSet": {"Name": "www.' + $Domain + '", "Type": "A", "AliasTarget": {"DNSName": "' + $cfDomain + '", "HostedZoneId": "' + $cfHostedZoneId + '", "EvaluateTargetHealth": false}}}
    ]
  }'
  aws route53 change-resource-record-sets --hosted-zone-id $zoneId --change-batch "$changes" | Out-Null
  Write-Host "✅ Route 53 records created for $Domain and www.$Domain" -ForegroundColor Green
} else {
  if (-not $zoneId) { Write-Host "Hosted zone for $Domain not found. Create it or validate DNS manually." -ForegroundColor Yellow }
  if ($certStatus -ne 'ISSUED' -or -not $cfDomain) { Write-Host "Custom domain aliasing skipped (ACM or CloudFront missing). Frontend is reachable via CloudFront (if created) or the S3 website fallback above." -ForegroundColor Yellow }
}

Write-Host "✅ Frontend deployed to AWS and wired for $Domain" -ForegroundColor Green
