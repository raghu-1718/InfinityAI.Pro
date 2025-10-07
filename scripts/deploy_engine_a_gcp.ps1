param(
  [string]$GcpProject,
  [string]$Region = 'us-central1',
  [string]$Service = 'infinityai-engine-a',
  [string]$SourceDir = 'infinityai-pro/backend/engines/engine-a',
  [string]$ConfigPath = 'multi-cloud-config.json'
)

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { Write-Host 'gcloud CLI not found.' -ForegroundColor Red; exit 1 }
if (-not $GcpProject) { Write-Host 'GcpProject is required.' -ForegroundColor Red; exit 1 }
if (-not (Test-Path $SourceDir)) { Write-Host "Source not found: $SourceDir" -ForegroundColor Red; exit 1 }

Write-Host "🚀 Deploying Engine A to GCP Cloud Run (project=$GcpProject, region=$Region)" -ForegroundColor Cyan

gcloud config set project $GcpProject 2>$null | Out-Null
gcloud config set run/region $Region 2>$null | Out-Null

$image = "gcr.io/$GcpProject/infinityai-engine-a:v1"

# Build with Cloud Build using Dockerfile in SourceDir
Push-Location $SourceDir
Write-Host "Building image via Cloud Build: $image" -ForegroundColor Yellow
gcloud builds submit --tag $image .
Pop-Location

# Deploy to Cloud Run
Write-Host "Deploying service $Service" -ForegroundColor Yellow
# Do not force a specific port; Cloud Run will set PORT (defaults to 8080). The container honors PORT automatically.
gcloud run deploy $Service --image $image --region $Region --platform managed --allow-unauthenticated --cpu 1 --memory 1Gi --timeout 600 --port 8000

$url = gcloud run services describe $Service --platform managed --region $Region --format='value(status.url)'
if ($url) { Write-Host "Service URL: $url" -ForegroundColor Green } else { Write-Host 'Failed to resolve service URL' -ForegroundColor Red }

# Update multi-cloud-config.json
try {
  if (Test-Path $ConfigPath) {
    $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    if ($cfg.clouds.google_cloud.services.engine_a) {
      $cfg.clouds.google_cloud.services.engine_a.endpoint = $url
      ($cfg | ConvertTo-Json -Depth 10) | Out-File -FilePath $ConfigPath -Encoding UTF8
      Write-Host "Updated $ConfigPath with Engine A endpoint" -ForegroundColor Green
    }
  }
} catch {}

Write-Host "✅ Engine A deployed to GCP Cloud Run" -ForegroundColor Green
