param(
  [Parameter(Mandatory = $true)] [string] $CertificateArn,
  [Parameter(Mandatory = $true)] [string] $DomainName,
  [Parameter(Mandatory = $true)] [string] $HostedZoneId,
  [Parameter(Mandatory = $true)] [string] $S3WebsiteDomainName,
  [Parameter(Mandatory = $true)] [string] $ALBDomainName,
  [string] $WwwAlias = "www.$DomainName",
  [int] $MaxMinutes = 60
)

$ErrorActionPreference = 'Stop'
$region = 'us-east-1'
Write-Host "[auto] Watching ACM until ISSUED, then finishing CDN and verification..." -ForegroundColor Cyan

# 1) Watch ACM
$start = Get-Date
while ((New-TimeSpan -Start $start -End (Get-Date)).TotalMinutes -lt $MaxMinutes) {
  $cert = aws acm describe-certificate --region $region --certificate-arn $CertificateArn | ConvertFrom-Json
  $status = $cert.Certificate.Status
  Write-Host "  ACM: $status"
  if ($status -eq 'ISSUED') { break }
  Start-Sleep -Seconds 15
}
if ($status -ne 'ISSUED') { throw "[auto] Timed out waiting for ACM to be ISSUED" }

# 2) Create CloudFront + Route53
& (Join-Path $PSScriptRoot 'manual-deploy-cloudfront-continue.ps1') -DomainName $DomainName -HostedZoneId $HostedZoneId -S3WebsiteDomainName $S3WebsiteDomainName -ALBDomainName $ALBDomainName -CertificateArn $CertificateArn -WwwAlias $WwwAlias

# 3) Wait for CloudFront Deployed
Write-Host "[auto] Waiting for CloudFront to deploy..." -ForegroundColor Cyan
$distId = (aws cloudfront list-distributions | ConvertFrom-Json).DistributionList.Items | Where-Object { $_.Aliases.Items -contains $DomainName } | Select-Object -First 1 -ExpandProperty Id
if (-not $distId) { Write-Warning "[auto] Could not find distribution by alias; continuing" }
for ($i=0; $i -lt 60; $i++) {
  if (-not $distId) { break }
  $st = (aws cloudfront get-distribution --id $distId | ConvertFrom-Json).Distribution.Status
  Write-Host "  CF: $st"
  if ($st -eq 'Deployed') { break }
  Start-Sleep -Seconds 15
}

# 4) Verify domain endpoints
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$verifyScript = Join-Path $repoRoot 'scripts\verify-backend-extended.ps1'
if (Test-Path $verifyScript) {
  & $verifyScript -BaseUrl "https://$DomainName" | Out-Null
} else {
  Write-Warning "[auto] verify-backend-extended.ps1 not found at $verifyScript"
}

# 5) Fetch today's analysis
$analysisScript = Join-Path $repoRoot 'scripts\fetch-todays-analysis.ps1'
if (Test-Path $analysisScript) {
  & $analysisScript -BaseUrl "https://$DomainName" -Symbol 'NIFTY' | Out-Null
} else {
  Write-Warning "[auto] fetch-todays-analysis.ps1 not found at $analysisScript"
}

Write-Host "[auto] Completed. Verification and analysis artifacts are in the scripts folder." -ForegroundColor Green
