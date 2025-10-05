# PowerShell automation script for Windows IAM permission fix
param(
    [string]$AccountId = "152687308610",
    [string]$Region = "us-east-1",
    [string]$UserName = "infinityai-deploy",
    [string]$RoleName = "InfinityAI-Deployment-Role"
)

$ExternalId = "infinityai-deploy-$(Get-Date -Format 'yyyyMMdd')"

Write-Host "🚀 Starting automated IAM permission fix..." -ForegroundColor Green
Write-Host "Account ID: $AccountId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "External ID: $ExternalId" -ForegroundColor Cyan

# Function to check current identity
function Test-AWSIdentity {
    Write-Host "🔍 Checking current AWS identity..." -ForegroundColor Yellow
    
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Host "✅ Current identity: $($identity.Arn)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Failed to get AWS identity" -ForegroundColor Red
        return $false
    }
}

# Function to remove quarantine policy
function Remove-QuarantinePolicy {
    Write-Host "🧹 Removing AWSCompromisedKeyQuarantineV3 policy..." -ForegroundColor Yellow
    
    try {
        aws iam detach-user-policy --user-name $UserName --policy-arn "arn:aws:iam::aws:policy/AWSCompromisedKeyQuarantineV3" 2>$null
        Write-Host "✅ Quarantine policy removed" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Quarantine policy not found or already removed" -ForegroundColor Yellow
    }
}

# Function to create trust policy file
function New-TrustPolicy {
    Write-Host "📋 Creating trust policy..." -ForegroundColor Yellow
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    AWS = "arn:aws:iam::${AccountId}:root"
                }
                Action = "sts:AssumeRole"
                Condition = @{
                    StringEquals = @{
                        "sts:ExternalId" = $ExternalId
                    }
                }
            }
            @{
                Effect = "Allow"
                Principal = @{
                    Service = @("ec2.amazonaws.com", "codebuild.amazonaws.com")
                }
                Action = "sts:AssumeRole"
            }
        )
    }
    
    $trustPolicy | ConvertTo-Json -Depth 10 | Out-File -FilePath "trust-policy.json" -Encoding UTF8
    Write-Host "✅ Trust policy created" -ForegroundColor Green
}

# Function to create permissions policy
function New-PermissionsPolicy {
    Write-Host "📋 Creating permissions policy..." -ForegroundColor Yellow
    
    $permissionsPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Sid = "ECRFullAccess"
                Effect = "Allow"
                Action = @(
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability", 
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:DescribeRepositories",
                    "ecr:CreateRepository",
                    "ecr:ListImages",
                    "ecr:DescribeImages"
                )
                Resource = "*"
            }
            @{
                Sid = "ECSFullAccess"
                Effect = "Allow"
                Action = @(
                    "ecs:RegisterTaskDefinition",
                    "ecs:DescribeTaskDefinition",
                    "ecs:UpdateService",
                    "ecs:DescribeServices",
                    "ecs:ListTasks",
                    "ecs:DescribeTasks",
                    "ecs:StopTask",
                    "ecs:RunTask",
                    "ecs:ListClusters",
                    "ecs:DescribeClusters",
                    "ecs:CreateService",
                    "ecs:DeleteService"
                )
                Resource = "*"
            }
            @{
                Sid = "IAMPassRole"
                Effect = "Allow"
                Action = @("iam:PassRole")
                Resource = "arn:aws:iam::${AccountId}:role/*"
            }
            @{
                Sid = "LogsAccess"
                Effect = "Allow"
                Action = @(
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream", 
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams"
                )
                Resource = "*"
            }
        )
    }
    
    $permissionsPolicy | ConvertTo-Json -Depth 10 | Out-File -FilePath "deployment-permissions.json" -Encoding UTF8
    Write-Host "✅ Permissions policy created" -ForegroundColor Green
}

# Function to create IAM role
function New-IAMRole {
    Write-Host "🏗️  Creating IAM role: $RoleName..." -ForegroundColor Yellow
    
    # Delete existing role if it exists
    try {
        aws iam delete-role-policy --role-name $RoleName --policy-name DeploymentPermissions 2>$null
        aws iam delete-role --role-name $RoleName 2>$null
    }
    catch { }
    
    # Create new role
    try {
        aws iam create-role --role-name $RoleName --assume-role-policy-document file://trust-policy.json --description "Automated deployment role for InfinityAI"
        Write-Host "✅ IAM role created" -ForegroundColor Green
        
        # Attach permissions policy
        aws iam put-role-policy --role-name $RoleName --policy-name DeploymentPermissions --policy-document file://deployment-permissions.json
        Write-Host "✅ Permissions attached to role" -ForegroundColor Green
        
        return $true
    }
    catch {
        Write-Host "❌ Failed to create IAM role" -ForegroundColor Red
        return $false
    }
}

# Function to fix user permissions (fallback)
function Fix-UserPermissions {
    Write-Host "🔧 Fixing user permissions as fallback..." -ForegroundColor Yellow
    
    # Remove quarantine policy
    Remove-QuarantinePolicy
    
    # Add correct permissions to user
    try {
        aws iam put-user-policy --user-name $UserName --policy-name FixedDeploymentPermissions --policy-document file://deployment-permissions.json
        Write-Host "✅ User permissions fixed" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Failed to fix user permissions" -ForegroundColor Red
        return $false
    }
}

# Function to test permissions
function Test-Permissions {
    Write-Host "🧪 Testing permissions..." -ForegroundColor Yellow
    
    # Test ECR access
    try {
        aws ecr get-login-password --region $Region | Out-Null
        Write-Host "✅ ECR access working" -ForegroundColor Green
        $script:ECRWorking = $true
    }
    catch {
        Write-Host "❌ ECR access failed" -ForegroundColor Red
        $script:ECRWorking = $false
    }
    
    # Test ECS access  
    try {
        aws ecs describe-clusters --region $Region | Out-Null
        Write-Host "✅ ECS access working" -ForegroundColor Green
        $script:ECSWorking = $true
    }
    catch {
        Write-Host "❌ ECS access failed" -ForegroundColor Red
        $script:ECSWorking = $false
    }
}

# Function to assume role and set environment
function Set-DeploymentCredentials {
    Write-Host "🔐 Assuming deployment role..." -ForegroundColor Yellow
    
    $roleArn = "arn:aws:iam::${AccountId}:role/${RoleName}"
    $sessionName = "AutoDeployment-$(Get-Date -Format 'HHmmss')"
    
    try {
        $roleCreds = aws sts assume-role --role-arn $roleArn --role-session-name $sessionName --external-id $ExternalId --output json | ConvertFrom-Json
        
        if ($roleCreds) {
            $env:AWS_ACCESS_KEY_ID = $roleCreds.Credentials.AccessKeyId
            $env:AWS_SECRET_ACCESS_KEY = $roleCreds.Credentials.SecretAccessKey
            $env:AWS_SESSION_TOKEN = $roleCreds.Credentials.SessionToken
            
            Write-Host "✅ Deployment credentials set!" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Failed to get role credentials" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Failed to assume role" -ForegroundColor Red
        return $false
    }
}

# Function to generate usage instructions
function Show-UsageInstructions {
    Write-Host "📋 Usage Instructions:" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔐 To assume the role for future deployments:" -ForegroundColor Yellow
    Write-Host "aws sts assume-role --role-arn arn:aws:iam::${AccountId}:role/${RoleName} --role-session-name DeploymentSession --external-id $ExternalId"
    Write-Host ""
    Write-Host "🌍 Or set environment variables:" -ForegroundColor Yellow
    Write-Host "`$env:AWS_ACCESS_KEY_ID='<access-key-from-assume-role>'"
    Write-Host "`$env:AWS_SECRET_ACCESS_KEY='<secret-key-from-assume-role>'"
    Write-Host "`$env:AWS_SESSION_TOKEN='<session-token-from-assume-role>'"
    Write-Host ""
    Write-Host "🔑 External ID for this session: $ExternalId" -ForegroundColor Cyan
    Write-Host "💾 Save this External ID - you'll need it for future deployments!" -ForegroundColor Green
}

# Main execution
function Main {
    Write-Host "🔧 Automated IAM Permission Fix Tool" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    
    # Check AWS identity
    if (-not (Test-AWSIdentity)) {
        Write-Host "Please configure your AWS credentials first" -ForegroundColor Red
        exit 1
    }
    
    # Create policy files
    New-TrustPolicy
    New-PermissionsPolicy
    
    # Try to create IAM role first (preferred method)
    if (New-IAMRole) {
        Write-Host "✅ IAM Role approach successful" -ForegroundColor Green
        
        # Wait for role to be available
        Start-Sleep -Seconds 10
        
        if (Set-DeploymentCredentials) {
            Test-Permissions
            Show-UsageInstructions
        }
    }
    else {
        Write-Host "⚠️  IAM Role creation failed, trying user permission fix..." -ForegroundColor Yellow
        if (Fix-UserPermissions) {
            Write-Host "✅ User permissions fixed as fallback" -ForegroundColor Green
            Test-Permissions
        }
        else {
            Write-Host "❌ Both approaches failed. Manual intervention required." -ForegroundColor Red
            exit 1
        }
    }
    
    # Cleanup temporary files
    Remove-Item -Path "trust-policy.json", "deployment-permissions.json" -ErrorAction SilentlyContinue
    
    Write-Host "🎉 Automation complete!" -ForegroundColor Green
    
    # Return external ID for use by deployment script
    return $ExternalId
}

# Execute main function and store external ID
$script:ExternalId = Main