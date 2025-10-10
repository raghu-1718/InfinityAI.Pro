param(
  [Parameter(Mandatory = $true)] [string] $CertificateArn,
  [Parameter(Mandatory = $true)] [string] $DomainName,
  [Parameter(Mandatory = $true)] [string] $HostedZoneId,
  [Parameter(Mandatory = $true)] [string] $S3WebsiteDomainName,
  [Parameter(Mandatory = $true)] [string] $ALBDomainName,
  [string] $WwwAlias = "www.$DomainName",
  [int] $MaxMinutes = 30
)

$ErrorActionPreference = 'Stop'
$region = 'us-east-1'
$start = Get-Date
Write-Host "Watching ACM cert $CertificateArn for ISSUED (timeout ${MaxMinutes}m) ..." -ForegroundColor Cyan

while ((New-TimeSpan -Start $start -End (Get-Date)).TotalMinutes -lt $MaxMinutes) {
  try {
    $cert = aws acm describe-certificate --region $region --certificate-arn $CertificateArn | ConvertFrom-Json
    $status = $cert.Certificate.Status
    Write-Host "  Status: $status"
    if ($status -eq 'ISSUED') {
      Write-Host "Certificate ISSUED. Proceeding to create CloudFront distribution and Route53 aliases..." -ForegroundColor Green
      & (Join-Path $PSScriptRoot 'manual-deploy-cloudfront-continue.ps1') -DomainName $DomainName -HostedZoneId $HostedZoneId -S3WebsiteDomainName $S3WebsiteDomainName -ALBDomainName $ALBDomainName -CertificateArn $CertificateArn -WwwAlias $WwwAlias
      exit 0
    }
  } catch {
    Write-Warning $_
  }
  Start-Sleep -Seconds 15
}

Write-Error "Timed out waiting for certificate to be ISSUED. Try increasing -MaxMinutes or confirm DNS validation records."
