param(
  [Parameter(Mandatory = $true)] [string] $DomainName,
  [Parameter(Mandatory = $true)] [string] $HostedZoneId,
  [Parameter(Mandatory = $true)] [string] $S3WebsiteDomainName,
  [Parameter(Mandatory = $true)] [string] $ALBDomainName,
  [Parameter(Mandatory = $true)] [string] $CertificateArn,
  [string] $WwwAlias = "www.$DomainName"
)

$ErrorActionPreference = 'Stop'
Write-Host "Continuing deployment for $DomainName using cert $CertificateArn ..." -ForegroundColor Cyan

$cfConfig = @{
  CallerReference = (New-Guid).ToString()
  Comment        = "InfinityAI.Pro CDN"
  Enabled        = $true
  Aliases        = @{ Quantity = 2; Items = @($DomainName, $WwwAlias) }
  DefaultRootObject = "index.html"
  Origins = @{
    Quantity = 2
    Items = @(
      @{ Id = "S3WebsiteOrigin"; DomainName = $S3WebsiteDomainName; CustomOriginConfig = @{ HTTPPort = 80; HTTPSPort = 443; OriginProtocolPolicy = "http-only" } },
      @{ Id = "AlbApiOrigin";    DomainName = $ALBDomainName;      CustomOriginConfig = @{ HTTPPort = 80; HTTPSPort = 443; OriginProtocolPolicy = "http-only" } }
    )
  }
  DefaultCacheBehavior = @{
    TargetOriginId = "S3WebsiteOrigin"
    ViewerProtocolPolicy = "redirect-to-https"
    AllowedMethods = @{ Quantity = 3; Items = @("GET","HEAD","OPTIONS"); CachedMethods = @{ Quantity = 3; Items = @("GET","HEAD","OPTIONS") } }
    Compress = $true
    CachePolicyId = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    ResponseHeadersPolicyId = "67f7725c-6f97-4210-82d7-5512b31e9d03"
  }
  CacheBehaviors = @{
    Quantity = 3
    Items = @(
      @{ PathPattern = "engine-c/*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=7; Items=@("GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"); CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") } }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" },
      @{ PathPattern = "engine-d/*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=7; Items=@("GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"); CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") } }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" },
      @{ PathPattern = "engine-*/ws*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=3; Items=@("GET","HEAD","OPTIONS"); CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") } }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" }
    )
  }
  CustomErrorResponses = @{
    Quantity = 1
    Items = @(@{ ErrorCode = 404; ResponseCode = "200"; ResponsePagePath = "/index.html" })
  }
  ViewerCertificate = @{
    ACMCertificateArn = $CertificateArn
    SSLSupportMethod = "sni-only"
    MinimumProtocolVersion = "TLSv1.2_2021"
  }
} | ConvertTo-Json -Depth 20

$tmpCfg = New-TemporaryFile
$cfConfig | Out-File -Encoding utf8 $tmpCfg
$cf = aws cloudfront create-distribution --distribution-config file://$tmpCfg | ConvertFrom-Json
Remove-Item $tmpCfg -Force

$cfDomain = $cf.Distribution.DomainName
Write-Host "Created CloudFront distribution: $cfDomain" -ForegroundColor Green

$cfHzId = "Z2FDTNDATAQYW2"

foreach ($name in @($DomainName, $WwwAlias)) {
  $batch = @{
    Changes = @(@{
      Action = "UPSERT"
      ResourceRecordSet = @{
        Name = $name
        Type = "A"
        AliasTarget = @{
          DNSName = $cfDomain
          HostedZoneId = $cfHzId
          EvaluateTargetHealth = $false
        }
      }
    },@{
      Action = "UPSERT"
      ResourceRecordSet = @{
        Name = $name
        Type = "AAAA"
        AliasTarget = @{
          DNSName = $cfDomain
          HostedZoneId = $cfHzId
          EvaluateTargetHealth = $false
        }
      }
    })
  } | ConvertTo-Json -Depth 20
  $tmp = New-TemporaryFile
  $batch | Out-File -Encoding utf8 $tmp
  aws route53 change-resource-record-sets --hosted-zone-id $HostedZoneId --change-batch file://$tmp | Out-Null
  Remove-Item $tmp -Force
}

Write-Host "Done. CloudFront will propagate in ~10-20 minutes. Domain: https://$DomainName" -ForegroundColor Green
