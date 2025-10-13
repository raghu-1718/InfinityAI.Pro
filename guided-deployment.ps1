#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Guided deployment script for InfinityAI.Pro
    Interactive setup with validation and testing

.DESCRIPTION
    This script guides you through:
    1. Credential setup and validation
    2. Environment configuration
    3. Step-by-step deployment
    4. Health checks and verification
    5. Git deployment

.EXAMPLE
    .\guided-deployment.ps1
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipPrompts
)

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
    Prompt = "White"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Read-UserInput {
    param([string]$Prompt, [string]$Default = "", [switch]$Secure)
    
    if ($SkipPrompts -and $Default) {
        return $Default
    }
    
    if ($Secure) {
        $input = Read-Host -Prompt $Prompt -AsSecureString
        return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($input))
    } else {
        $promptText = "$Prompt"
        if ($Default) {
            $promptText += " [$Default]"
        }
        $input = Read-Host -Prompt $promptText
        if ($input) { return $input } else { return $Default }
    }
}

function Test-Prerequisites {
    Write-ColorOutput "`n🔍 Step 1: Checking Prerequisites..." "Header"
    
    $prerequisites = @(
        @{ Name = "AWS CLI"; Command = "aws --version"; Required = $true }
        @{ Name = "GCloud CLI"; Command = "gcloud version --format='value(Google Cloud SDK)'"; Required = $true }
        @{ Name = "Docker"; Command = "docker --version"; Required = $true }
        @{ Name = "Node.js"; Command = "node --version"; Required = $false }
        @{ Name = "Git"; Command = "git --version"; Required = $true }
    )
    
    $allGood = $true
    
    foreach ($prereq in $prerequisites) {
        try {
            $version = Invoke-Expression $prereq.Command 2>$null
            Write-ColorOutput "✅ $($prereq.Name): Installed" "Success"
        }
        catch {
            if ($prereq.Required) {
                Write-ColorOutput "❌ $($prereq.Name): NOT FOUND (Required)" "Error"
                $allGood = $false
            } else {
                Write-ColorOutput "⚠️ $($prereq.Name): Not found (Optional)" "Warning"
            }
        }
    }
    
    if (-not $allGood) {
        Write-ColorOutput "`n❌ Please install missing prerequisites before continuing." "Error"
        exit 1
    }
    
    Write-ColorOutput "✅ All prerequisites satisfied!" "Success"
}

function Setup-Credentials {
    Write-ColorOutput "`n🔑 Step 2: Setting up Credentials..." "Header"
    
    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-ColorOutput "📝 Creating .env file from template..." "Info"
        Copy-Item ".env.example" ".env" -Force
    }
    
    Write-ColorOutput "`n🔐 Dhan API Configuration Required:" "Info"
    Write-ColorOutput "You need to configure Dhan API with these URLs:" "Info"
    Write-ColorOutput "• Postback URL: https://infinityai.pro/api/webhooks/dhan" "Prompt"
    Write-ColorOutput "• Redirect URL: https://infinityai.pro/auth/dhan/callback" "Prompt"
    Write-ColorOutput "• Get credentials from: https://dhanhq.co/api" "Prompt"
    
    if (-not $SkipPrompts) {
        Read-Host "`nPress Enter after you've configured Dhan API URLs..."
    }
    
    # Get Dhan credentials
    Write-ColorOutput "`n🔑 Enter your Dhan API credentials:" "Header"
    
    $dhanClientId = Read-UserInput "Dhan Client ID" "your_dhan_client_id_here"
    $dhanAccessToken = Read-UserInput "Dhan Access Token" "your_dhan_access_token_here" -Secure
    
    # Update .env file
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "DHAN_CLIENT_ID=.*", "DHAN_CLIENT_ID=$dhanClientId"
    $envContent = $envContent -replace "DHAN_ACCESS_TOKEN=.*", "DHAN_ACCESS_TOKEN=$dhanAccessToken"
    
    # Generate secure secrets
    $apiSecret = -join ((1..32) | ForEach-Object { [char]((65..90) + (97..122) + (48..57) | Get-Random) })
    $jwtSecret = -join ((1..32) | ForEach-Object { [char]((65..90) + (97..122) + (48..57) | Get-Random) })
    
    $envContent = $envContent -replace "API_SECRET_KEY=.*", "API_SECRET_KEY=$apiSecret"
    $envContent = $envContent -replace "JWT_SECRET=.*", "JWT_SECRET=$jwtSecret"
    
    $envContent | Set-Content ".env"
    
    Write-ColorOutput "✅ Credentials configured and secrets generated!" "Success"
}

function Test-CloudConnectivity {
    Write-ColorOutput "`n☁️ Step 3: Testing Cloud Connectivity..." "Header"
    
    # Test AWS
    Write-ColorOutput "🔍 Testing AWS connectivity..." "Info"
    try {
        $awsIdentity = aws sts get-caller-identity | ConvertFrom-Json
        Write-ColorOutput "✅ AWS Connected - Account: $($awsIdentity.Account)" "Success"
    }
    catch {
        Write-ColorOutput "❌ AWS Connection Failed: $($_.Exception.Message)" "Error"
        exit 1
    }
    
    # Test GCP
    Write-ColorOutput "🔍 Testing GCP connectivity..." "Info"
    try {
        $gcpProject = gcloud config get-value project 2>$null
        if (-not $gcpProject) {
            $gcpProject = Read-UserInput "GCP Project ID" "infinityai-pro"
            gcloud config set project $gcpProject
        }
        Write-ColorOutput "✅ GCP Connected - Project: $gcpProject" "Success"
    }
    catch {
        Write-ColorOutput "❌ GCP Connection Failed: $($_.Exception.Message)" "Error"
        exit 1
    }
    
    # Test Docker
    Write-ColorOutput "🔍 Testing Docker..." "Info"
    try {
        docker ps > $null
        Write-ColorOutput "✅ Docker is running" "Success"
    }
    catch {
        Write-ColorOutput "❌ Docker is not running. Please start Docker Desktop." "Error"
        exit 1
    }
}

function Deploy-Engines {
    Write-ColorOutput "`n🚀 Step 4: Deploying Engines..." "Header"
    
    $deploymentChoice = Read-UserInput "Deploy engines? (y/n)" "y"
    
    if ($deploymentChoice -eq "y" -or $deploymentChoice -eq "Y") {
        Write-ColorOutput "🎯 Starting engine deployment..." "Info"
        
        try {
            # Run the main deployment script
            & ".\deploy-complete-platform.ps1" -Environment production
            
            Write-ColorOutput "✅ Engine deployment completed!" "Success"
        }
        catch {
            Write-ColorOutput "❌ Engine deployment failed: $($_.Exception.Message)" "Error"
            
            $retryChoice = Read-UserInput "Retry deployment? (y/n)" "n"
            if ($retryChoice -eq "y" -or $retryChoice -eq "Y") {
                & ".\deploy-complete-platform.ps1" -Environment production
            }
        }
    }
}

function Test-Deployment {
    Write-ColorOutput "`n🧪 Step 5: Testing Deployment..." "Header"
    
    $testChoice = Read-UserInput "Run health checks? (y/n)" "y"
    
    if ($testChoice -eq "y" -or $testChoice -eq "Y") {
        Write-ColorOutput "🔍 Running comprehensive health checks..." "Info"
        
        try {
            & ".\verify-platform-health.ps1" -Verbose
            Write-ColorOutput "✅ Health checks completed!" "Success"
        }
        catch {
            Write-ColorOutput "⚠️ Some health checks failed. Check the detailed report." "Warning"
        }
    }
}

function Deploy-To-Git {
    Write-ColorOutput "`n📤 Step 6: Git Deployment..." "Header"
    
    $gitChoice = Read-UserInput "Commit and push to GitHub? (y/n)" "y"
    
    if ($gitChoice -eq "y" -or $gitChoice -eq "Y") {
        Write-ColorOutput "📝 Preparing Git deployment..." "Info"
        
        try {
            # Check git status
            $gitStatus = git status --porcelain 2>$null
            
            if ($gitStatus) {
                Write-ColorOutput "📋 Changes detected. Committing..." "Info"
                
                # Add all changes
                git add .
                
                # Create commit message
                $commitMessage = Read-UserInput "Commit message" "Deploy InfinityAI.Pro platform - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
                
                # Commit changes
                git commit -m $commitMessage
                
                # Push to origin
                $pushChoice = Read-UserInput "Push to GitHub? (y/n)" "y"
                if ($pushChoice -eq "y" -or $pushChoice -eq "Y") {
                    git push origin main
                    Write-ColorOutput "✅ Code pushed to GitHub!" "Success"
                }
            } else {
                Write-ColorOutput "ℹ️ No changes to commit." "Info"
            }
        }
        catch {
            Write-ColorOutput "❌ Git deployment failed: $($_.Exception.Message)" "Error"
        }
    }
}

function Show-Final-Summary {
    Write-ColorOutput "`n🎉 Deployment Complete!" "Header"
    Write-ColorOutput "===========================================" "Header"
    
    Write-ColorOutput "`n🌐 Your InfinityAI.Pro Platform URLs:" "Info"
    Write-ColorOutput "• Frontend: https://infinityai.pro" "Prompt"
    Write-ColorOutput "• Engine A (Market Data): https://engine-a-market-data-573866363639.us-central1.run.app" "Prompt"
    Write-ColorOutput "• Engine B (AI/ML): https://engine-b-ai-ml-573866363639.us-central1.run.app" "Prompt"
    Write-ColorOutput "• Engine C (Trading): http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c" "Prompt"
    Write-ColorOutput "• Engine D (Chatbot): http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d" "Prompt"
    Write-ColorOutput "• Ultra Aggressive: https://infinityai-ultra-aggressive-573866363639.us-central1.run.app" "Prompt"
    
    Write-ColorOutput "`n🔗 Dhan API URLs (for your Dhan configuration):" "Info"
    Write-ColorOutput "• Postback URL: https://infinityai.pro/api/webhooks/dhan" "Prompt"
    Write-ColorOutput "• Redirect URL: https://infinityai.pro/auth/dhan/callback" "Prompt"
    
    Write-ColorOutput "`n📋 Next Steps:" "Info"
    Write-ColorOutput "1. Update Dhan API configuration with the URLs above" "Info"
    Write-ColorOutput "2. Test trading functionality with small amounts" "Info"
    Write-ColorOutput "3. Monitor system health regularly" "Info"
    Write-ColorOutput "4. Set up alerting and monitoring" "Info"
    
    Write-ColorOutput "`n🚨 Important Security Reminders:" "Warning"
    Write-ColorOutput "• Never commit your .env file to Git" "Warning"
    Write-ColorOutput "• Monitor your trading activities closely" "Warning"
    Write-ColorOutput "• Use kill switch for emergency stops" "Warning"
    Write-ColorOutput "• Rotate API tokens regularly" "Warning"
    
    Write-ColorOutput "`n✅ Your InfinityAI.Pro platform is now LIVE and ready for trading!" "Success"
}

# Main execution flow
function Main {
    Write-ColorOutput "🚀 InfinityAI.Pro Guided Deployment" "Header"
    Write-ColorOutput "Welcome to the complete deployment wizard!" "Info"
    Write-ColorOutput "This will deploy your trading platform to AWS and GCP." "Info"
    Write-ColorOutput "===========================================" "Header"
    
    if (-not $SkipPrompts) {
        $continueChoice = Read-UserInput "Ready to start deployment? (y/n)" "y"
        if ($continueChoice -ne "y" -and $continueChoice -ne "Y") {
            Write-ColorOutput "Deployment cancelled by user." "Info"
            exit 0
        }
    }
    
    Test-Prerequisites
    Setup-Credentials
    Test-CloudConnectivity
    Deploy-Engines
    Test-Deployment
    Deploy-To-Git
    Show-Final-Summary
    
    Write-ColorOutput "`n🎊 Deployment wizard completed successfully!" "Success"
}

# Execute main function
Main