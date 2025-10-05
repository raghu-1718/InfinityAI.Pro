# PowerShell helper script to assume deployment role
param(
    [Parameter(Mandatory=$true)]
    [string]$RoleArn,
    
    [Parameter(Mandatory=$true)]
    [string]$ExternalId,
    
    [string]$SessionName = "DeploymentSession-$(Get-Date -Format 'HHmmss')",
    [int]$DurationSeconds = 3600
)

Write-Host "🔐 Assuming deployment role..." -ForegroundColor Green
Write-Host "Role ARN: $RoleArn" -ForegroundColor Cyan
Write-Host "External ID: $ExternalId" -ForegroundColor Cyan
Write-Host "Session Name: $SessionName" -ForegroundColor Cyan

try {
    # Assume the role
    Write-Host "📡 Making assume-role request..." -ForegroundColor Yellow
    
    $assumeRoleResult = aws sts assume-role `
        --role-arn $RoleArn `
        --role-session-name $SessionName `
        --external-id $ExternalId `
        --duration-seconds $DurationSeconds `
        --output json | ConvertFrom-Json
    
    if ($assumeRoleResult -and $assumeRoleResult.Credentials) {
        # Extract credentials
        $accessKeyId = $assumeRoleResult.Credentials.AccessKeyId
        $secretAccessKey = $assumeRoleResult.Credentials.SecretAccessKey
        $sessionToken = $assumeRoleResult.Credentials.SessionToken
        $expiration = $assumeRoleResult.Credentials.Expiration
        
        # Set environment variables
        $env:AWS_ACCESS_KEY_ID = $accessKeyId
        $env:AWS_SECRET_ACCESS_KEY = $secretAccessKey
        $env:AWS_SESSION_TOKEN = $sessionToken
        
        Write-Host "✅ Successfully assumed deployment role!" -ForegroundColor Green
        Write-Host "🕐 Credentials expire at: $expiration" -ForegroundColor Yellow
        
        # Verify the assumed identity
        Write-Host "🔍 Verifying assumed identity..." -ForegroundColor Yellow
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Host "✅ Current identity: $($identity.Arn)" -ForegroundColor Green
        
        # Test ECR access
        Write-Host "🧪 Testing ECR access..." -ForegroundColor Yellow
        try {
            aws ecr get-login-password --region us-east-1 | Out-Null
            Write-Host "✅ ECR access confirmed!" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️  ECR access test failed" -ForegroundColor Yellow
        }
        
        # Return credentials object for potential script chaining
        return @{
            AccessKeyId = $accessKeyId
            SecretAccessKey = $secretAccessKey
            SessionToken = $sessionToken
            Expiration = $expiration
            AssumedRoleArn = $identity.Arn
        }
    }
    else {
        Write-Host "❌ Failed to get credentials from assume-role response" -ForegroundColor Red
        return $null
    }
}
catch {
    Write-Host "❌ Failed to assume role: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔍 Common issues:" -ForegroundColor Yellow
    Write-Host "  • Check that the External ID is correct" -ForegroundColor Yellow
    Write-Host "  • Verify the role ARN exists" -ForegroundColor Yellow
    Write-Host "  • Ensure your user has permission to assume this role" -ForegroundColor Yellow
    Write-Host "  • Check if the role trust policy allows your user" -ForegroundColor Yellow
    return $null
}

# Usage examples
Write-Host ""
Write-Host "💡 Usage Examples:" -ForegroundColor Green
Write-Host ".\Assume-DeploymentRole.ps1 -RoleArn 'arn:aws:iam::152687308610:role/InfinityAI-Deployment-Role' -ExternalId 'your-external-id'" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 To use credentials in subsequent commands:" -ForegroundColor Yellow
Write-Host "  The environment variables are already set in this session!" -ForegroundColor Yellow
Write-Host "  • AWS_ACCESS_KEY_ID" -ForegroundColor Cyan
Write-Host "  • AWS_SECRET_ACCESS_KEY" -ForegroundColor Cyan  
Write-Host "  • AWS_SESSION_TOKEN" -ForegroundColor Cyan