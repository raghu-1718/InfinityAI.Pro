param(
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'

Write-Host "Starting local end-to-end verification (engines via Docker Compose)..." -ForegroundColor Cyan

# Ensure Docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not available on PATH. Install Docker Desktop and retry."
}

# Compose up
$composeCmd = @('compose','-f','docker-compose.yml','up','-d')
if ($Rebuild) { $composeCmd += '--build' }

Write-Host "Bringing up services with docker ${composeCmd -join ' '}" -ForegroundColor Yellow
& docker @composeCmd | Write-Output

# Wait for health endpoints
$services = @(
    @{ name='engine-a'; url='http://localhost:8100/health' },
    @{ name='engine-b'; url='http://localhost:8101/health' },
    @{ name='engine-c-execution'; url='http://localhost:8102/health' },
    @{ name='engine-d'; url='http://localhost:8103/health' }
)

function Wait-Healthy([string]$name, [string]$url, [int]$timeoutSec=120) {
    $start = Get-Date
    while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($timeoutSec)) {
        try {
            $resp = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 10
            if ($resp.StatusCode -eq 200) {
                Write-Host "[$name] healthy" -ForegroundColor Green
                return $true
            }
        } catch {}
        Start-Sleep -Seconds 3
    }
    Write-Warning "[$name] did not become healthy within $timeoutSec seconds"
    return $false
}

$allHealthy = $true
foreach ($s in $services) {
    if (-not (Wait-Healthy -name $s.name -url $s.url)) { $allHealthy = $false }
}

# Write local config override
$localConfigPath = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath 'infrastructure' | Join-Path -ChildPath 'config.local.json'
$env:INFRA_CONFIG_PATH = (Resolve-Path $localConfigPath).Path
Write-Host "Using config: $env:INFRA_CONFIG_PATH" -ForegroundColor Yellow

# Run verifier
Write-Host "Running verification suite against local endpoints..." -ForegroundColor Cyan
python .\infinityai_system_verifier.py --config "$env:INFRA_CONFIG_PATH"

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Verification script exited with non-zero code ($LASTEXITCODE). Check logs above."
} else {
    Write-Host "Local verification completed." -ForegroundColor Green
}
