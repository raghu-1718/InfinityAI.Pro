param(
  [Parameter(Mandatory = $true)] [string] $DomainName,
  [Parameter(Mandatory = $true)] [string] $HostedZoneId,
  [Parameter(Mandatory = $true)] [string] $S3WebsiteDomainName,
  [Parameter(Mandatory = $true)] [string] $ALBDomainName,
  [string] $WwwAlias = "www.$DomainName"
)

$ErrorActionPreference = 'Stop'
$region = 'us-east-1' # ACM for CloudFront must be in us-east-1

Write-Host "[1/6] Requesting ACM certificate for $DomainName and $WwwAlias ..." -ForegroundColor Cyan
$req = aws acm request-certificate `
  --region $region `
  --domain-name $DomainName `
  --validation-method DNS `
  --subject-alternative-names $WwwAlias `
  --options CertificateTransparencyLoggingPreference=ENABLED | ConvertFrom-Json

$certArn = $req.CertificateArn
Write-Host "Requested certificate: $certArn" -ForegroundColor Green

Start-Sleep -Seconds 5

Write-Host "[2/6] Fetching domain validation options ..." -ForegroundColor Cyan
$cert = aws acm describe-certificate --region $region --certificate-arn $certArn | ConvertFrom-Json
$dvo = $cert.Certificate.DomainValidationOptions

foreach ($opt in $dvo) {
  $rr = $opt.ResourceRecord
  Write-Host "Creating Route53 CNAME for validation: $($rr.Name) -> $($rr.Value)" -ForegroundColor Yellow
  $changeBatch = @{
    Changes = @(@{
      Action = "UPSERT"
      ResourceRecordSet = @{
        Name = $rr.Name
        Type = $rr.Type
        TTL = 300
        ResourceRecords = @(@{ Value = $rr.Value })
      }
    })
  } | ConvertTo-Json -Depth 10

  $tmp = New-TemporaryFile
  $changeBatch | Out-File -Encoding utf8 $tmp
  aws route53 change-resource-record-sets --hosted-zone-id $HostedZoneId --change-batch file://$tmp | Out-Null
  Remove-Item $tmp -Force
}

Write-Host "[3/6] Waiting for certificate to be ISSUED ... (this may take a few minutes)" -ForegroundColor Cyan
for ($i=0; $i -lt 40; $i++) {
  $status = (aws acm describe-certificate --region $region --certificate-arn $certArn | ConvertFrom-Json).Certificate.Status
  Write-Host "  ACM status: $status"
  if ($status -eq 'ISSUED') { break }
  Start-Sleep -Seconds 15
}

if ($status -ne 'ISSUED') { throw "Certificate not issued yet; please wait and rerun this script's next step." }

Write-Host "[4/6] Creating CloudFront distribution ..." -ForegroundColor Cyan
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
    AllowedMethods = @{ Quantity = 3; Items = @("GET","HEAD","OPTIONS") }
    CachedMethods  = @{ Quantity = 3; Items = @("GET","HEAD","OPTIONS") }
    Compress = $true
    CachePolicyId = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    ResponseHeadersPolicyId = "67f7725c-6f97-4210-82d7-5512b31e9d03" # CORS+Sec
  }
  CacheBehaviors = @{
    Quantity = 3
    Items = @(
      @{ PathPattern = "engine-c/*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=7; Items=@("GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE") }; CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" },
      @{ PathPattern = "engine-d/*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=7; Items=@("GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE") }; CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" },
      @{ PathPattern = "engine-*/ws*"; TargetOriginId = "AlbApiOrigin"; ViewerProtocolPolicy = "redirect-to-https"; AllowedMethods = @{ Quantity=3; Items=@("GET","HEAD","OPTIONS") }; CachedMethods=@{ Quantity=3; Items=@("GET","HEAD","OPTIONS") }; CachePolicyId="216adef6-5c7f-47e4-b989-5492eafa07d3"; OriginRequestPolicyId="88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"; ResponseHeadersPolicyId="67f7725c-6f97-4210-82d7-5512b31e9d03" }
    )
  }
  CustomErrorResponses = @{
    Quantity = 1
    Items = @(@{ ErrorCode = 404; ResponseCode = 200; ResponsePagePath = "/index.html" })
  }
  ViewerCertificate = @{
    ACMCertificateArn = $certArn
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

Write-Host "[5/6] Creating Route53 alias records for apex and www ..." -ForegroundColor Cyan
$cfHzId = "Z2FDTNDATAQYW2" # CloudFront hosted zone ID

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

Write-Host "[6/6] Done. It may take ~10-20 minutes for CloudFront to propagate. Domain: https://$DomainName" -ForegroundColor Green
