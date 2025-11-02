param(
    [string]$ContextName = "northflank-ci"
)

Write-Host "[Northflank] CLI login helper" -ForegroundColor Cyan

# Verify CLI is installed
if (-not (Get-Command northflank -ErrorAction SilentlyContinue)) {
    Write-Error "Northflank CLI not found. Install with: npm install -g @northflank/cli"
    exit 1
}

# Get token from env or prompt
$token = $env:NORTHFLANK_TOKEN
if (-not $token) {
    Write-Host "Paste your Northflank API token (input hidden):" -ForegroundColor Yellow
    $secure = Read-Host -AsSecureString -Prompt "NORTHFLANK API token"
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $token = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

if (-not $token) {
    Write-Error "No token provided. Set $env:NORTHFLANK_TOKEN or paste when prompted."
    exit 1
}

Write-Host "Logging in to Northflank..." -ForegroundColor Cyan
northflank login --token-login --token $token --name $ContextName --override
if ($LASTEXITCODE -ne 0) {
    Write-Error "Login failed (exit code $LASTEXITCODE)."
    exit $LASTEXITCODE
}

Write-Host "Login successful. Verifying access..." -ForegroundColor Green
try {
    northflank list projects
} catch {
    Write-Host "Login OK. Listing projects may require specific org/project context. You can run: 'northflank context' to review or set contexts." -ForegroundColor Yellow
}
