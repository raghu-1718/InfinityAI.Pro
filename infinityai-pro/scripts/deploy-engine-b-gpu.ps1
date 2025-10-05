# Deploy Engine B with GPU acceleration to Google Cloud Run
# InfinityAI.Pro Trading Platform
# PowerShell script for Windows

param(
    [string]$ProjectId = "after-yesterday-473512-k3",
    [string]$ServiceName = "infinityai-engine-b-gpu", 
    [string]$Region = "us-central1"
)

# Configuration
$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "🚀 Deploying Engine B with GPU acceleration to Google Cloud" -ForegroundColor Green
Write-Host "Project ID: $ProjectId"
Write-Host "Service: $ServiceName"
Write-Host "Region: $Region"

try {
    # Step 1: Build and push the Docker image
    Write-Host "📦 Building Docker image with GPU support..." -ForegroundColor Yellow
    
    # Build using Google Cloud Build
    gcloud builds submit `
        --config=backend/engines/engine-b/cloudbuild.yaml `
        --project=$ProjectId `
        backend/engines/engine-b

    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }
    
    Write-Host "✅ Docker image built and pushed successfully" -ForegroundColor Green

    # Step 2: Deploy to Cloud Run with GPU
    Write-Host "🚀 Deploying to Cloud Run with GPU..." -ForegroundColor Yellow

    gcloud run deploy $ServiceName `
        --image="$ImageName`:latest" `
        --platform=managed `
        --region=$Region `
        --allow-unauthenticated `
        --port=8000 `
        --memory=8Gi `
        --cpu=4 `
        --gpu=1 `
        --gpu-type=nvidia-tesla-t4 `
        --max-instances=10 `
        --min-instances=1 `
        --concurrency=50 `
        --timeout=300 `
        --execution-environment=gen2 `
        --set-env-vars="USE_GPU=true,CUDA_VISIBLE_DEVICES=0,NVIDIA_VISIBLE_DEVICES=all,NVIDIA_DRIVER_CAPABILITIES=compute,utility" `
        --project=$ProjectId

    if ($LASTEXITCODE -ne 0) {
        throw "Cloud Run deployment failed"
    }

    # Step 3: Get the service URL
    $ServiceUrl = gcloud run services describe $ServiceName `
        --platform=managed `
        --region=$Region `
        --format="value(status.url)" `
        --project=$ProjectId

    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "🌐 Service URL: $ServiceUrl" -ForegroundColor Cyan
    Write-Host "🔍 Health check: $ServiceUrl/health" -ForegroundColor Cyan

    # Step 4: Test the deployment
    Write-Host "🧪 Testing the deployment..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10  # Wait for service to be ready

    try {
        $HealthResponse = Invoke-RestMethod -Uri "$ServiceUrl/health" -TimeoutSec 30
        Write-Host "Health check response received" -ForegroundColor Green
        
        if ($HealthResponse.status -eq "healthy" -or $HealthResponse -like "*healthy*") {
            Write-Host "✅ Health check passed!" -ForegroundColor Green
            if ($HealthResponse.gpu_info) {
                Write-Host "🔥 GPU Status: Available = $($HealthResponse.gpu_info.available), Count = $($HealthResponse.gpu_info.count)" -ForegroundColor Cyan
            }
        } else {
            Write-Host "❌ Health check failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️  Health check request failed, but service may still be starting..." -ForegroundColor Yellow
    }

    # Step 5: Update load balancer configuration
    Write-Host "🔄 Updating load balancer configuration..." -ForegroundColor Yellow

    $LoadBalancerConfig = "load-balancer-config.json"
    if (Test-Path $LoadBalancerConfig) {
        try {
            $config = Get-Content $LoadBalancerConfig | ConvertFrom-Json
            $config.load_balancer_configuration.engines.engine_b.endpoint = $ServiceUrl
            $config.load_balancer_configuration.engines.engine_b.status = "operational-gpu"
            $config | ConvertTo-Json -Depth 10 | Set-Content $LoadBalancerConfig
            
            Write-Host "✅ Load balancer configuration updated" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Failed to update load balancer config: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Load balancer config not found, skipping update" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "🎯 GPU-accelerated Engine B deployment summary:" -ForegroundColor Cyan
    Write-Host "   • Service URL: $ServiceUrl"
    Write-Host "   • GPU Type: NVIDIA Tesla T4"
    Write-Host "   • Memory: 8GB"
    Write-Host "   • CPU: 4 cores"
    Write-Host "   • Max instances: 10"
    Write-Host "   • Region: $Region"
    Write-Host ""
    Write-Host "🚀 Engine B is now GPU-accelerated and ready for high-performance AI processing!" -ForegroundColor Green

    # Return service details
    return @{
        ServiceUrl = $ServiceUrl
        ProjectId = $ProjectId
        ServiceName = $ServiceName
        Region = $Region
        Status = "Success"
    }

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    return @{
        Status = "Failed"
        Error = $_.Exception.Message
    }
}