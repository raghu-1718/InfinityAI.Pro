param(
  [Parameter(Mandatory=$true)][string]$DistributionId,
  [Parameter(Mandatory=$true)][string]$AlbDomainName,
  [string]$ApexDomain = 'infinityai.pro',
  [string]$WwwDomain = 'www.infinityai.pro'
)

$ErrorActionPreference = 'Stop'

function Get-ConfigWithEtag {
  param([string]$Id)
  $resp = aws cloudfront get-distribution-config --id $Id | ConvertFrom-Json
  return $resp
}

Write-Host "Patching CloudFront distribution $DistributionId..." -ForegroundColor Cyan
$resp = Get-ConfigWithEtag -Id $DistributionId
$etag = $resp.ETag
$cfg  = $resp.DistributionConfig

# Ensure Aliases include apex and www
$aliases = @($ApexDomain, $WwwDomain) | Where-Object { $_ -and $_.Trim() -ne '' } | Select-Object -Unique
$cfg.Aliases = @{ Quantity = $aliases.Count; Items = $aliases }

# Default root for SPA
if (-not $cfg.DefaultRootObject -or $cfg.DefaultRootObject -eq '') { $cfg.DefaultRootObject = 'index.html' }

# Ensure ALB origin exists
$origItems = @()
foreach ($o in $cfg.Origins.Items) { $origItems += $o }
if (-not ($origItems | Where-Object { $_.Id -eq 'AlbApiOrigin' })) {
  $origItems += @{ 
    Id='AlbApiOrigin'; 
    DomainName=$AlbDomainName; 
    OriginPath=''; 
    CustomHeaders=@{Quantity=0}; 
    CustomOriginConfig=@{ 
      HTTPPort=80; HTTPSPort=443; OriginProtocolPolicy='http-only'; 
      OriginSslProtocols=@{Quantity=1; Items=@('TLSv1.2')}; 
      OriginReadTimeout=30; OriginKeepaliveTimeout=5 
    }; 
    ConnectionAttempts=3; ConnectionTimeout=10; 
    OriginShield=@{Enabled=$false}; 
    OriginAccessControlId='' 
  }
}
$cfg.Origins = @{ Quantity = $origItems.Count; Items = $origItems }

# Build cache behaviors for API paths using managed policies (no ForwardedValues block)
$apiAllowed = @{ Quantity=7; Items=@('GET','HEAD','OPTIONS','PUT','POST','PATCH','DELETE'); CachedMethods=@{ Quantity=3; Items=@('GET','HEAD','OPTIONS') } }
$trusted = @{ Enabled=$false; Quantity=0 }
$emptyLambda = @{ Quantity=0 }
$emptyFunc   = @{ Quantity=0 }

# Managed policy IDs (AWS)
$cachePolicyNoCache = '413f1601-80d6-46d3-8b32-62a70f9fd3cf'           # CachingDisabled
$originReqAllNoHost = '88a5eaf4-2fd4-4709-b370-b4c650ea3fcf'           # AllViewerExceptHostHeader
$respHeadersCORS    = '5cc3b908-e619-4b99-88e5-2cf7f45965bd'           # CORS-With-Preflight

$cbItems = @(
  @{ PathPattern='engine-c/*'; TargetOriginId='AlbApiOrigin'; TrustedSigners=$trusted; TrustedKeyGroups=$trusted; ViewerProtocolPolicy='redirect-to-https'; AllowedMethods=$apiAllowed; SmoothStreaming=$false; Compress=$true; LambdaFunctionAssociations=$emptyLambda; FunctionAssociations=$emptyFunc; CachePolicyId=$cachePolicyNoCache; OriginRequestPolicyId=$originReqAllNoHost; ResponseHeadersPolicyId=$respHeadersCORS },
  @{ PathPattern='engine-d/*'; TargetOriginId='AlbApiOrigin'; TrustedSigners=$trusted; TrustedKeyGroups=$trusted; ViewerProtocolPolicy='redirect-to-https'; AllowedMethods=$apiAllowed; SmoothStreaming=$false; Compress=$true; LambdaFunctionAssociations=$emptyLambda; FunctionAssociations=$emptyFunc; CachePolicyId=$cachePolicyNoCache; OriginRequestPolicyId=$originReqAllNoHost; ResponseHeadersPolicyId=$respHeadersCORS }
)
$cfg.CacheBehaviors = @{ Quantity = $cbItems.Count; Items = $cbItems }

# SPA 404 -> index.html
$cfg.CustomErrorResponses = @{ Quantity=1; Items=@(@{ ErrorCode=404; ResponseCode='200'; ResponsePagePath='/index.html'; ErrorCachingMinTTL=0 }) }

# Write updated config and apply
$tmp = New-TemporaryFile
($cfg | ConvertTo-Json -Depth 100) | Out-File -Encoding utf8 $tmp
try {
  aws cloudfront update-distribution --id $DistributionId --if-match $etag --distribution-config file://$tmp | Out-Null
  Write-Host "Update submitted. CloudFront will deploy changes shortly." -ForegroundColor Green
} finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

# Output summary
$new = aws cloudfront get-distribution --id $DistributionId | ConvertFrom-Json
$newCfg = $new.Distribution.DistributionConfig
$status = $new.Distribution.Status
Write-Host "Status: $status" -ForegroundColor Yellow
Write-Host "Aliases:" (($newCfg.Aliases.Items | Where-Object { $_ }) -join ', ')
if ($newCfg.Origins.Items) {
  $origSummary = $newCfg.Origins.Items | ForEach-Object { "${($_.Id)} -> ${($_.DomainName)}" }
  Write-Host ("Origins: " + ($origSummary -join '; '))
}
if ($newCfg.CacheBehaviors.Items) {
  $behSummary = $newCfg.CacheBehaviors.Items | ForEach-Object { $_.PathPattern }
  Write-Host ("Behaviors: " + ($behSummary -join ', '))
} else {
  Write-Host "Behaviors: (none)"
}