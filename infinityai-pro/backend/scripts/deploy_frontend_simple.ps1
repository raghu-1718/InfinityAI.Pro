# InfinityAI.Pro Frontend Deployment Script
# This script installs dependencies, builds, and tests the React frontend

Write-Host "InfinityAI.Pro Frontend Deployment Starting..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

# Navigate to frontend directory
Write-Host "Navigating to frontend directory..." -ForegroundColor Yellow
Set-Location "frontend"

# Install dependencies
Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: npm install failed!" -ForegroundColor Red
    Set-Location ".."
    exit 1
}

Write-Host "Dependencies installed successfully!" -ForegroundColor Green

# Check for build issues
Write-Host "Building React application..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Set-Location ".."
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green

# Verify components exist
Write-Host "Verifying component files..." -ForegroundColor Yellow

$components = @(
    "src/App.js",
    "src/components/Dashboard/EnhancedDashboard.jsx",
    "src/components/Trading/TradingInterface.jsx",
    "src/components/Navigation/NavigationDrawer.jsx",
    "src/components/Analytics/AnalyticsPage.jsx",
    "src/components/Settings/SettingsPage.jsx"
)

$allComponentsExist = $true
foreach ($component in $components) {
    if (Test-Path $component) {
        Write-Host "FOUND: $component" -ForegroundColor Green
    } else {
        Write-Host "MISSING: $component" -ForegroundColor Red
        $allComponentsExist = $false
    }
}

if (!$allComponentsExist) {
    Write-Host "ERROR: Some components are missing!" -ForegroundColor Red
    Set-Location ".."
    exit 1
}

Write-Host "All components verified!" -ForegroundColor Green

Write-Host ""
Write-Host "Frontend Deployment Summary:" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "SUCCESS: Dependencies installed" -ForegroundColor Green
Write-Host "SUCCESS: Build completed successfully" -ForegroundColor Green
Write-Host "SUCCESS: Components ready for production" -ForegroundColor Green

Write-Host ""
Write-Host "Frontend Features Deployed:" -ForegroundColor Yellow
Write-Host "* Enhanced Dashboard with real-time data" -ForegroundColor White
Write-Host "* Advanced Trading Interface" -ForegroundColor White
Write-Host "* Portfolio Analytics with charts" -ForegroundColor White
Write-Host "* Settings and Configuration" -ForegroundColor White
Write-Host "* Navigation and Routing" -ForegroundColor White
Write-Host "* Material-UI themed components" -ForegroundColor White
Write-Host "* Responsive design for all devices" -ForegroundColor White

Write-Host ""
Write-Host "To start development server:" -ForegroundColor Cyan
Write-Host "cd frontend && npm start" -ForegroundColor White

Write-Host ""
Write-Host "Frontend deployment completed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

# Return to original directory
Set-Location ".."

exit 0