param(
  [Parameter(Mandatory = $true)] [string] $StackName,
  [Parameter(Mandatory = $true)] [string] $DomainName, # e.g., infinityai.pro
  [Parameter(Mandatory = $true)] [string] $HostedZoneId, # e.g., Z123456ABCDEFG
  [Parameter(Mandatory = $true)] [string] $S3BucketName, # e.g., infinityai-pro-frontend
  [Parameter(Mandatory = $true)] [string] $S3WebsiteDomainName, # e.g., infinityai-pro-frontend.s3-website-us-east-1.amazonaws.com
  [Parameter(Mandatory = $true)] [string] $ALBDomainName, # e.g., infinityai-alb-XXXX.us-east-1.elb.amazonaws.com
  [string] $WwwAlias = "www.$DomainName",
  [string] $Region = "us-east-1"
)

Write-Host "Deploying CloudFront + Route53 stack $StackName for $DomainName ..." -ForegroundColor Cyan

$TemplatePath = Join-Path $PSScriptRoot 'cloudfront-route53.yaml'

aws cloudformation deploy `
  --region $Region `
  --stack-name $StackName `
  --template-file $TemplatePath `
  --capabilities CAPABILITY_NAMED_IAM `
  --parameter-overrides `
    DomainName=$DomainName `
    HostedZoneId=$HostedZoneId `
    S3BucketName=$S3BucketName `
    S3WebsiteDomainName=$S3WebsiteDomainName `
    ALBDomainName=$ALBDomainName `
    WwwAlias=$WwwAlias

if ($LASTEXITCODE -ne 0) {
  Write-Error "CloudFormation deploy failed. Check CloudFormation console for details."
  exit 1
}

Write-Host "Stack deployed. Fetching outputs ..." -ForegroundColor Green

$Outputs = aws cloudformation describe-stacks --region $Region --stack-name $StackName | ConvertFrom-Json
$Outputs.Stacks[0].Outputs | Format-Table -AutoSize

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "- Wait for ACM validation records to be auto-created in Route53 (stack did it) and for CloudFront to finish deploying (~10-20 min)."
Write-Host "- Update frontend API base to use https://$DomainName (we'll set this in api-config)."
Write-Host "- Configure Dhan Redirect URL: https://$DomainName/engine-c/auth/dhan/callback"
Write-Host "- Configure Dhan Postback URL: https://$DomainName/engine-c/webhooks/dhan/postback"
