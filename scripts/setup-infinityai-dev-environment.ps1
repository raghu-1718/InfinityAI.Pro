#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete setup script for InfinityAI.Pro development environment
    
.DESCRIPTION
    This script installs and configures:
    - Node.js and Firebase CLI
    - GitHub CLI
    - Python and Firebase Admin SDK
    - Google Cloud SDK
    - Vertex AI and Gemini SDKs
    - Visual Studio Code extensions
    - Authentication for all services
    
.EXAMPLE
    .\setup-infinityai-dev-environment.ps1
    
.NOTES
    Run this script in PowerShell with Administrator privileges for best results.
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipAuth,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipVSCodeExtensions
)

$ErrorActionPreference = "Continue"

# ASCII Art Banner
Write-Host @"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ___        __ _       _ _           _    ___         ║
║    |_ _|_ __  / _(_)_ __ (_) |_ _   _  / \  |_ _|        ║
║     | || '_ \| |_| | '_ \| | __| | | |/ _ \  | |         ║
║     | || | | |  _| | | | | | |_| |_| / ___ \ | |         ║
║    |___|_| |_|_| |_|_| |_|_|\__|\__, /_/   \_\___|        ║
║                                 |___/                     ║
║                                                           ║
║        🚀 Development Environment Setup v1.0              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host ""
Write-Host "🔧 Starting InfinityAI.Pro development environment setup..." -ForegroundColor Yellow
Write-Host ""

# Helper function for status messages
function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $icon = switch ($Type) {
        "Success" { "✅" }
        "Error" { "❌" }
        "Warning" { "⚠️" }
        "Info" { "ℹ️" }
        default { "•" }
    }
    
    $color = switch ($Type) {
        "Success" { "Green" }
        "Error" { "Red" }
        "Warning" { "Yellow" }
        "Info" { "Cyan" }
        default { "White" }
    }
    
    Write-Host "$icon $Message" -ForegroundColor $color
}

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Status "Not running as Administrator. Some installations may require elevated privileges." "Warning"
}

# 1. Install Node.js
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📦 Step 1: Installing Node.js" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Status "Node.js is already installed: $nodeVersion" "Success"
    } else {
        throw "Node.js not found"
    }
} catch {
    Write-Status "Installing Node.js..." "Info"
    winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Node.js installed successfully" "Success"
        Write-Status "Please restart your terminal to use Node.js" "Warning"
    } else {
        Write-Status "Failed to install Node.js. Please install manually from https://nodejs.org" "Error"
    }
}

# 2. Install Firebase CLI
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔥 Step 2: Installing Firebase CLI" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $firebaseVersion = firebase --version 2>$null
    if ($firebaseVersion) {
        Write-Status "Firebase CLI is already installed: $firebaseVersion" "Success"
    } else {
        throw "Firebase CLI not found"
    }
} catch {
    Write-Status "Installing Firebase CLI..." "Info"
    npm install -g firebase-tools
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Firebase CLI installed successfully" "Success"
    } else {
        Write-Status "Failed to install Firebase CLI" "Error"
    }
}

# 3. Install GitHub CLI
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🐙 Step 3: Installing GitHub CLI" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $ghVersion = gh --version 2>$null
    if ($ghVersion) {
        Write-Status "GitHub CLI is already installed" "Success"
    } else {
        throw "GitHub CLI not found"
    }
} catch {
    Write-Status "Installing GitHub CLI..." "Info"
    winget install GitHub.cli --silent --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "GitHub CLI installed successfully" "Success"
    } else {
        Write-Status "Failed to install GitHub CLI" "Error"
    }
}

# 4. Install Python
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🐍 Step 4: Installing Python 3.11" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Status "Python is already installed: $pythonVersion" "Success"
    } else {
        throw "Python not found"
    }
} catch {
    Write-Status "Installing Python 3.11..." "Info"
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Python installed successfully" "Success"
        Write-Status "Please restart your terminal to use Python" "Warning"
    } else {
        Write-Status "Failed to install Python" "Error"
    }
}

# 5. Install Python packages
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📦 Step 5: Installing Python SDKs" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

$pythonPackages = @(
    "firebase-admin",
    "google-cloud-aiplatform",
    "google-generativeai",
    "google-cloud-secret-manager",
    "google-cloud-firestore",
    "google-auth",
    "fastapi",
    "uvicorn[standard]",
    "aiohttp",
    "pandas",
    "numpy"
)

Write-Status "Upgrading pip..." "Info"
python -m pip install --upgrade pip --quiet

foreach ($package in $pythonPackages) {
    Write-Status "Installing $package..." "Info"
    python -m pip install $package --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "$package installed" "Success"
    } else {
        Write-Status "Failed to install $package" "Warning"
    }
}

# 6. Install Google Cloud SDK
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "☁️ Step 6: Installing Google Cloud SDK" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $gcloudVersion = gcloud --version 2>$null
    if ($gcloudVersion) {
        Write-Status "Google Cloud SDK is already installed" "Success"
    } else {
        throw "gcloud not found"
    }
} catch {
    Write-Status "Downloading Google Cloud SDK installer..." "Info"
    $installerPath = "$env:TEMP\GoogleCloudSDKInstaller.exe"
    
    Invoke-WebRequest -Uri "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe" -OutFile $installerPath
    
    Write-Status "Running Google Cloud SDK installer..." "Info"
    Write-Status "Follow the installation wizard that opens" "Warning"
    
    Start-Process -FilePath $installerPath -Wait
    
    Write-Status "Google Cloud SDK installation completed" "Success"
    Write-Status "Please restart your terminal to use gcloud CLI" "Warning"
}

# 7. Install VS Code Extensions (if not skipped)
if (-not $SkipVSCodeExtensions) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🧰 Step 7: Installing VS Code Extensions" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    
    $extensions = @(
        "GoogleCloudTools.cloudcode",
        "ms-python.python",
        "ms-python.vscode-pylance",
        "GitHub.copilot",
        "GitHub.vscode-pull-request-github",
        "ms-azuretools.vscode-docker",
        "esbenp.prettier-vscode"
    )
    
    try {
        $codeVersion = code --version 2>$null
        if ($codeVersion) {
            Write-Status "Visual Studio Code is installed" "Success"
            
            foreach ($ext in $extensions) {
                Write-Status "Installing extension: $ext..." "Info"
                code --install-extension $ext --force 2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "$ext installed" "Success"
                } else {
                    Write-Status "Failed to install $ext" "Warning"
                }
            }
        } else {
            Write-Status "Visual Studio Code not found. Skipping extensions." "Warning"
        }
    } catch {
        Write-Status "Could not install VS Code extensions" "Warning"
    }
}

# 8. Authentication (if not skipped)
if (-not $SkipAuth) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🔐 Step 8: Authentication Setup" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Status "Firebase Authentication" "Info"
    Write-Host "Run this command when ready: firebase login" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Status "GitHub Authentication" "Info"
    Write-Host "Run this command when ready: gh auth login" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Status "Google Cloud Authentication" "Info"
    Write-Host "Run this command when ready: gcloud init" -ForegroundColor Yellow
    Write-Host "Or for application default: gcloud auth application-default login" -ForegroundColor Yellow
}

# 9. Create project configuration files
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📝 Step 9: Creating Configuration Templates" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# Check if we're in the InfinityAI.Pro directory
if (Test-Path ".\backend") {
    Write-Status "Creating .env.template for environment variables..." "Info"
    
    $envTemplate = @"
# InfinityAI.Pro Environment Variables Template
# Copy this to .env and fill in your actual values

# Google Cloud Project
GCP_PROJECT_ID=after-yesterday-473512-k3
GCP_REGION=us-central1

# Firebase Project
FIREBASE_PROJECT_ID=infinity-ai-5ec7c

# Engine URLs (Canonical Cloud Run service URLs)
ENGINE_A_URL=https://infinityai-engine-a-573866363639.us-central1.run.app
ENGINE_B_URL=https://infinityai-engine-b-573866363639.us-central1.run.app
ENGINE_C_URL=https://infinityai-engine-c-execution-573866363639.us-central1.run.app
# ENGINE_D_URL merged into ENGINE_C_URLhttps://infinityai-engine-c-execution-26140490557.us-central1.run.app

# Secrets (use Secret Manager in production)
# FIREBASE_SERVICE_ACCOUNT=<from Secret Manager>
# DHAN_API_KEY=<your key>
# DHAN_CLIENT_ID=<your id>

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
"@
    
    $envTemplate | Out-File -FilePath ".env.template" -Encoding UTF8
    Write-Status "Created .env.template" "Success"
    
    # Add to .gitignore if not already there
    if (Test-Path ".gitignore") {
        $gitignore = Get-Content ".gitignore" -Raw
        if ($gitignore -notmatch "\.env$") {
            Add-Content -Path ".gitignore" -Value "`n# Environment variables`n.env`n*.env`n!.env.template"
            Write-Status "Updated .gitignore" "Success"
        }
    }
} else {
    Write-Status "Not in InfinityAI.Pro root directory. Skipping config creation." "Warning"
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Write-Host "📋 What was installed:" -ForegroundColor Cyan
Write-Host "  ✓ Node.js & npm" -ForegroundColor White
Write-Host "  ✓ Firebase CLI" -ForegroundColor White
Write-Host "  ✓ GitHub CLI" -ForegroundColor White
Write-Host "  ✓ Python 3.11" -ForegroundColor White
Write-Host "  ✓ Python SDKs (Firebase Admin, Vertex AI, etc.)" -ForegroundColor White
Write-Host "  ✓ Google Cloud SDK" -ForegroundColor White
if (-not $SkipVSCodeExtensions) {
    Write-Host "  ✓ VS Code Extensions" -ForegroundColor White
}

Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Restart your terminal/PowerShell to load new PATH variables" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Authenticate with services:" -ForegroundColor Yellow
Write-Host "   firebase login" -ForegroundColor White
Write-Host "   gh auth login" -ForegroundColor White
Write-Host "   gcloud init" -ForegroundColor White
Write-Host "   gcloud auth application-default login" -ForegroundColor White
Write-Host ""
Write-Host "3. Set your Firebase project:" -ForegroundColor Yellow
Write-Host "   firebase use infinity-ai-5ec7c" -ForegroundColor White
Write-Host ""
Write-Host "4. Set your GCP project:" -ForegroundColor Yellow
Write-Host "   gcloud config set project after-yesterday-473512-k3" -ForegroundColor White
Write-Host ""
Write-Host "5. Test Firebase secret access:" -ForegroundColor Yellow
Write-Host "   gcloud secrets versions access latest --secret=firebase-service-account" -ForegroundColor White
Write-Host ""
Write-Host "6. Copy .env.template to .env and fill in values" -ForegroundColor Yellow
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  • Firebase Setup: docs/FIREBASE_SETUP.md" -ForegroundColor White
Write-Host "  • Integration Examples: docs/FIREBASE_INTEGRATION_EXAMPLES.md" -ForegroundColor White
Write-Host "  • Deployment Guide: DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Your InfinityAI.Pro development environment is ready!" -ForegroundColor Green
Write-Host ""
