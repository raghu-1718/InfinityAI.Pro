# InfinityAI.Pro Multi-Cloud Deployment Script
# Deploys AWS infrastructure and connects to Google Cloud engines

param(
    [string]$Environment = "production",
    [string]$DomainName = "infinityai.pro",
    [string]$HostedZoneId = "Z094987524IM4ED7WYTQO",
    [switch]$SkipCloudFront,
    [switch]$UpdateOnly
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting InfinityAI.Pro Multi-Cloud Deployment" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Domain: $DomainName" -ForegroundColor Yellow

# Configuration
$Config = @{
    AWS = @{
        Region = "us-east-1"
        S3Bucket = "infinityai-pro-frontend"
        ALBDomain = "infinityai-alb-124143296.us-east-1.elb.amazonaws.com"
        StackName = "infinityai-pro-cdn"
    }
    GCP = @{
        Region = "us-central1"
        ProjectId = "infinityai-pro"
        EngineA = "infinityai-engine-a-573866363639.us-central1.run.app"
        EngineB = "infinityai-engine-b-573866363639.us-central1.run.app"
    }
}

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        Write-Host "✅ AWS CLI: $awsVersion" -ForegroundColor Green
    } catch {
        throw "AWS CLI not found. Please install AWS CLI."
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Host "✅ AWS Identity: $($identity.Arn)" -ForegroundColor Green
    } catch {
        throw "AWS credentials not configured. Run 'aws configure'."
    }
    
    # Check Google Cloud CLI (optional)
    try {
        $gcloudVersion = gcloud version --format="value(Google Cloud SDK)" 2>$null
        Write-Host "✅ Google Cloud CLI: $gcloudVersion" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Google Cloud CLI not found (optional)" -ForegroundColor Yellow
    }
}

function Deploy-Frontend {
    Write-Host "📦 Deploying frontend to S3..." -ForegroundColor Blue
    
    $frontendPath = "c:\Users\Raghu\InfinityAI.Pro\infinityai-pro\frontend"
    $buildPath = "$frontendPath\build"
    
    if (-not (Test-Path $buildPath)) {
        Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
        Push-Location $frontendPath
        try {
            npm run build
        } finally {
            Pop-Location
        }
    }
    
    # Sync to S3
    Write-Host "⬆️  Uploading to S3..." -ForegroundColor Yellow
    aws s3 sync $buildPath "s3://$($Config.AWS.S3Bucket)" --delete --cache-control "public, max-age=120"
    
    Write-Host "✅ Frontend deployed to S3" -ForegroundColor Green
}

function Deploy-CloudFront {
    if ($SkipCloudFront) {
        Write-Host "⏭️  Skipping CloudFront deployment" -ForegroundColor Yellow
        return
    }
    
    Write-Host "🌐 Deploying CloudFront distribution..." -ForegroundColor Blue
    
    $templatePath = "c:\Users\Raghu\InfinityAI.Pro\deploy\aws\cloudfront-route53.yaml"
    $s3WebsiteDomain = "$($Config.AWS.S3Bucket).s3-website-$($Config.AWS.Region).amazonaws.com"
    
    $parameters = @(
        "ParameterKey=DomainName,ParameterValue=$DomainName",
        "ParameterKey=HostedZoneId,ParameterValue=$HostedZoneId",
        "ParameterKey=S3BucketName,ParameterValue=$($Config.AWS.S3Bucket)",
        "ParameterKey=S3WebsiteDomainName,ParameterValue=$s3WebsiteDomain",
        "ParameterKey=ALBDomainName,ParameterValue=$($Config.AWS.ALBDomain)",
        "ParameterKey=WwwAlias,ParameterValue=www.$DomainName"
    )
    
    try {
        if ($UpdateOnly) {
            Write-Host "🔄 Updating existing CloudFormation stack..." -ForegroundColor Yellow
            aws cloudformation update-stack `
                --region $Config.AWS.Region `
                --stack-name $Config.AWS.StackName `
                --template-body "file://$templatePath" `
                --capabilities CAPABILITY_NAMED_IAM `
                --parameters $parameters
        } else {
            Write-Host "🆕 Creating new CloudFormation stack..." -ForegroundColor Yellow
            aws cloudformation create-stack `
                --region $Config.AWS.Region `
                --stack-name $Config.AWS.StackName `
                --template-body "file://$templatePath" `
                --capabilities CAPABILITY_NAMED_IAM `
                --parameters $parameters
        }
        
        Write-Host "⏳ Waiting for CloudFormation deployment..." -ForegroundColor Yellow
        aws cloudformation wait stack-create-complete --region $Config.AWS.Region --stack-name $Config.AWS.StackName
        
        Write-Host "✅ CloudFront distribution deployed" -ForegroundColor Green
    } catch {
        Write-Host "❌ CloudFormation deployment failed: $_" -ForegroundColor Red
        throw
    }
}

function Test-MultiCloudConnectivity {
    Write-Host "🔗 Testing multi-cloud connectivity..." -ForegroundColor Blue
    
    $endpoints = @{
        "AWS Engine C" = "http://$($Config.AWS.ALBDomain)/engine-c/health"
        "AWS Engine D" = "http://$($Config.AWS.ALBDomain)/engine-d/health"
        "GCP Engine A" = "https://$($Config.GCP.EngineA)/health"
        "GCP Engine B" = "https://$($Config.GCP.EngineB)/health"
    }
    
    $results = @{}
    
    foreach ($name in $endpoints.Keys) {
        $url = $endpoints[$name]
        try {
            Write-Host "  Testing $name..." -ForegroundColor Gray
            $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 10
            $results[$name] = @{ Status = "✅ OK"; Response = $response }
            Write-Host "    ✅ ${name}: OK" -ForegroundColor Green
        } catch {
            $results[$name] = @{ Status = "❌ FAIL"; Error = $_.Exception.Message }
            Write-Host "    ❌ ${name}: FAIL - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    return $results
}

function Update-MultiCloudConfig {
    Write-Host "⚙️  Updating multi-cloud configuration..." -ForegroundColor Blue
    
    $configPath = "c:\Users\Raghu\InfinityAI.Pro\deploy\multi-cloud-config.yaml"
    
    # Update configuration with current endpoints
    $config = Get-Content $configPath -Raw
    $config = $config -replace "infinityai-alb-\d+\.us-east-1\.elb\.amazonaws\.com", $Config.AWS.ALBDomain
    $config = $config -replace "infinityai-engine-a-\d+\.us-central1\.run\.app", $Config.GCP.EngineA
    $config = $config -replace "infinityai-engine-b-\d+\.us-central1\.run\.app", $Config.GCP.EngineB
    
    Set-Content $configPath -Value $config
    
    Write-Host "✅ Multi-cloud configuration updated" -ForegroundColor Green
}

function Show-DeploymentSummary {
    param($ConnectivityResults)
    
    Write-Host "`n🎉 Deployment Summary" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    
    Write-Host "`n📍 Endpoints:" -ForegroundColor Yellow
    Write-Host "  Frontend: https://$DomainName" -ForegroundColor White
    Write-Host "  API: https://$DomainName/engine-d" -ForegroundColor White
    Write-Host "  Trading: https://$DomainName/engine-c" -ForegroundColor White
    
    Write-Host "`n🌐 Multi-Cloud Architecture:" -ForegroundColor Yellow
    Write-Host "  AWS (Primary): Trading & User Management" -ForegroundColor White
    Write-Host "    - Engine C: $($Config.AWS.ALBDomain)/engine-c" -ForegroundColor Gray
    Write-Host "    - Engine D: $($Config.AWS.ALBDomain)/engine-d" -ForegroundColor Gray
    Write-Host "  Google Cloud: AI Processing" -ForegroundColor White
    Write-Host "    - Engine A: $($Config.GCP.EngineA)" -ForegroundColor Gray
    Write-Host "    - Engine B: $($Config.GCP.EngineB)" -ForegroundColor Gray
    
    Write-Host "`n🔍 Connectivity Status:" -ForegroundColor Yellow
    foreach ($name in $ConnectivityResults.Keys) {
        Write-Host "  ${name}: $($ConnectivityResults[$name].Status)" -ForegroundColor White
    }
    
    Write-Host "`n🚀 Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Verify DNS propagation: nslookup $DomainName" -ForegroundColor White
    Write-Host "  2. Test frontend: https://$DomainName" -ForegroundColor White
    Write-Host "  3. Monitor CloudWatch logs for any issues" -ForegroundColor White
    Write-Host "  4. Run integration tests" -ForegroundColor White
}

# Main deployment flow
try {
    Test-Prerequisites
    
    Deploy-Frontend
    
    Deploy-CloudFront
    
    Update-MultiCloudConfig
    
    Start-Sleep -Seconds 30  # Allow time for DNS propagation
    
    $connectivityResults = Test-MultiCloudConnectivity
    
    Show-DeploymentSummary -ConnectivityResults $connectivityResults
    
    Write-Host "`n✅ Multi-cloud deployment completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ Deployment failed: $_" -ForegroundColor Red
    Write-Host "Check the logs above for details." -ForegroundColor Red
    exit 1
}