param(
  [Parameter(Mandatory=$true)][string]$DistributionId,
  [Parameter(Mandatory=$true)][string]$AlbDomainName,
  [string]$ApexDomain = 'infinityai.pro',
  [string]$WwwDomain = 'www.infinityai.pro'
)

$ErrorActionPreference = 'Stop'

Write-Host "[CF] Patching distribution $DistributionId (legacy ForwardedValues style)" -ForegroundColor Cyan
$resp = aws cloudfront get-distribution-config --id $DistributionId | ConvertFrom-Json
$etag = $resp.ETag
$cfg  = $resp.DistributionConfig

# Aliases
$aliases = @($ApexDomain, $WwwDomain) | Where-Object { $_ } | Select-Object -Unique
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

# Allowed methods + cached methods
$apiAllowed = @{ Quantity=7; Items=@('GET','HEAD','OPTIONS','PUT','POST','PATCH','DELETE'); CachedMethods=@{ Quantity=3; Items=@('GET','HEAD','OPTIONS') } }
$trusted = @{ Enabled=$false; Quantity=0 }
$emptyLambda = @{ Quantity=0 }
$emptyFunc   = @{ Quantity=0 }
$headers = @{ Quantity=4; Items=@('Authorization','Origin','Content-Type','Sec-WebSocket-Protocol') }
$forwardApi = @{ QueryString=$true; Cookies=@{ Forward='all' }; Headers=$headers; QueryStringCacheKeys=@{ Quantity=0 } }

$cbItems = @(
  @{ PathPattern='engine-c/*'; TargetOriginId='AlbApiOrigin'; TrustedSigners=$trusted; TrustedKeyGroups=$trusted; ViewerProtocolPolicy='redirect-to-https'; AllowedMethods=$apiAllowed; SmoothStreaming=$false; Compress=$true; LambdaFunctionAssociations=$emptyLambda; FunctionAssociations=$emptyFunc; FieldLevelEncryptionId=''; ForwardedValues=$forwardApi; MinTTL=0; DefaultTTL=0; MaxTTL=0 },
  @{ PathPattern='engine-d/*'; TargetOriginId='AlbApiOrigin'; TrustedSigners=$trusted; TrustedKeyGroups=$trusted; ViewerProtocolPolicy='redirect-to-https'; AllowedMethods=$apiAllowed; SmoothStreaming=$false; Compress=$true; LambdaFunctionAssociations=$emptyLambda; FunctionAssociations=$emptyFunc; FieldLevelEncryptionId=''; ForwardedValues=$forwardApi; MinTTL=0; DefaultTTL=0; MaxTTL=0 }
)
$cfg.CacheBehaviors = @{ Quantity = $cbItems.Count; Items = $cbItems }

# SPA fallback for 404
$cfg.CustomErrorResponses = @{ Quantity=1; Items=@(@{ ErrorCode=404; ResponseCode='200'; ResponsePagePath='/index.html'; ErrorCachingMinTTL=0 }) }

$tmp = New-TemporaryFile
($cfg | ConvertTo-Json -Depth 100) | Out-File -Encoding utf8 $tmp
try {
  aws cloudfront update-distribution --id $DistributionId --if-match $etag --distribution-config file://$tmp | Out-Null
  Write-Host "[CF] Update submitted." -ForegroundColor Green
} finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

$after = aws cloudfront get-distribution --id $DistributionId | ConvertFrom-Json
$newCfg = $after.Distribution.DistributionConfig
Write-Host ("[CF] Status: " + $after.Distribution.Status) -ForegroundColor Yellow
Write-Host ("[CF] Aliases: " + (($newCfg.Aliases.Items | Where-Object { $_ }) -join ', '))
if ($newCfg.Origins.Items) {
  $origSummary = $newCfg.Origins.Items | ForEach-Object { "${($_.Id)} -> ${($_.DomainName)}" }
  Write-Host ("[CF] Origins: " + ($origSummary -join '; '))
}
if ($newCfg.CacheBehaviors.Items) {
  $behSummary = $newCfg.CacheBehaviors.Items | ForEach-Object { $_.PathPattern }
  Write-Host ("[CF] Behaviors: " + ($behSummary -join ', '))
} else {
  Write-Host "[CF] Behaviors: (none)"
}