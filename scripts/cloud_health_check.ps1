# Cloud Health Check for InfinityAI.Pro Engines and Traders
# Checks AWS ECS services, Kubernetes deployments, and GCP Cloud Run (if CLIs are available). Azure removed.
# Outputs a summarized table and a JSON report (cloud_health_report.json)

param(
    [string]$Namespace = "infinityai",
    [string]$AwsRegion = "us-east-1",
    [string]$GcpRegion = "us-central1"
)

$report = [ordered]@{
    timestamp = (Get-Date).ToString("s")
    engines = @{}
    traders = @{}
    clouds = @{
        aws = @{}
        k8s = @{}
        gcp = @{}
    azure = @{}
    }
}

Write-Host "\n=== InfinityAI.Pro - Cloud Health Check ===" -ForegroundColor Cyan

# Helper
function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# 1) Kubernetes (Engine A/B/C/D)
if (Test-Command kubectl) {
    Write-Host "\nKubernetes detected - checking namespace '$Namespace'..." -ForegroundColor Yellow
    try {
        $deploys = kubectl get deploy -n $Namespace -o json | ConvertFrom-Json
        $services = kubectl get svc -n $Namespace -o json | ConvertFrom-Json

        $names = @("engine-a","engine-b","engine-c","engine-d","ultra-aggressive")
        foreach ($name in $names) {
            $d = $deploys.items | Where-Object { $_.metadata.name -eq $name }
            if ($d) {
                $ready = $d.status.readyReplicas
                $desired = $d.spec.replicas
                $status = if ($ready -ge 1) { "Healthy" } else { "Degraded" }
                $svc = $services.items | Where-Object { $_.metadata.name -eq "$name-service" }
                $svcType = if ($svc) { $svc.spec.type } else { "N/A" }

                $report.engines[$name] = [ordered]@{
                    platform = "k8s"
                    desired = $desired
                    ready = $ready
                    serviceType = $svcType
                    status = $status
                }
            }
        }
        $report.clouds.k8s = @{ namespace = $Namespace; deployments = $deploys.items.Count }
    }
    catch {
        Write-Host "Kubernetes check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "Kubernetes CLI not found (kubectl). Skipping k8s checks." -ForegroundColor DarkGray
}

# 2) AWS ECS (Engine C/D)
if (Test-Command aws) {
    Write-Host "\nAWS CLI detected - checking ECS services (region $AwsRegion)..." -ForegroundColor Yellow
    try {
        # Load config if available for accurate cluster and service names
        $cfgPath = Join-Path (Get-Location) 'multi-cloud-config.json'
        $cfg = $null
        if (Test-Path $cfgPath) { $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json }
        # Default cluster/service names
        $cluster = "infinityai-pro-cluster"
        $svcC = "engine-c-service"
        $svcD = "engine-d-service"
        $svcUltra = "ultra-aggressive-service"
        if ($cfg) {
            try {
                if ($cfg.clouds.aws.services.'engine_c'.cluster) { $cluster = $cfg.clouds.aws.services.'engine_c'.cluster }
                if ($cfg.clouds.aws.services.'engine_c'.service) { $svcC = $cfg.clouds.aws.services.'engine_c'.service }
                if ($cfg.clouds.aws.services.'engine_d'.service) { $svcD = $cfg.clouds.aws.services.'engine_d'.service }
            } catch { }
        }
        $svcNames = @($svcC,$svcD,$svcUltra)
    # Pass services as separate args so AWS CLI parses them correctly
    $awsArgs = @("ecs","describe-services","--cluster",$cluster,"--services") + $svcNames + @("--region",$AwsRegion,"--output","json")
    $json = aws @awsArgs
    $desc = $json | ConvertFrom-Json
        foreach ($svc in $desc.services) {
            $name = $svc.serviceName
            $ready = $svc.runningCount
            $desired = $svc.desiredCount
            $status = if ($ready -ge 1 -and $svc.status -eq "ACTIVE") { "Healthy" } else { "Degraded" }
            $report.engines[$name] = [ordered]@{
                platform = "aws-ecs"
                desired = $desired
                ready = $ready
                status = $status
                cluster = $cluster
            }
        }
        $report.clouds.aws = @{ region = $AwsRegion; cluster = $cluster }

        # Optional: probe ALB endpoints if config provides DNS
        try {
            $cfgPath2 = Join-Path (Get-Location) 'multi-cloud-config.json'
            if (Test-Path $cfgPath2) {
                $cfg2 = Get-Content $cfgPath2 -Raw | ConvertFrom-Json
                $albDns = $cfg2.clouds.aws.services.load_balancer.dns
                if ($albDns) {
                    $base = "http://$albDns"
                    $probes = @(
                        @{ name = 'alb-engine-c'; url = "$base/engine-c/health" },
                        @{ name = 'alb-engine-d'; url = "$base/engine-d/health" }
                    )
                    foreach ($p in $probes) {
                        try {
                            $respAlb = Invoke-WebRequest -Uri $p.url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                            $ok = ($respAlb.StatusCode -ge 200 -and $respAlb.StatusCode -lt 300)
                            $report.engines[$p.name] = [ordered]@{
                                platform = 'aws-alb'
                                desired = '-'
                                ready = if ($ok) { 1 } else { 0 }
                                status = if ($ok) { 'Healthy' } else { 'Degraded' }
                                url = $p.url
                            }
                        } catch {
                            $report.engines[$p.name] = [ordered]@{
                                platform = 'aws-alb'
                                desired = '-'
                                ready = 0
                                status = 'Degraded'
                                url = $p.url
                            }
                        }
                    }
                }
            }
        } catch {}
    }
    catch {
        Write-Host "AWS ECS check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "AWS CLI not found. Skipping AWS ECS checks." -ForegroundColor DarkGray
}

# 3) GCP Cloud Run (Engine B + Ultra Aggressive)
if (Test-Command gcloud) {
    Write-Host "\nGCloud detected - checking Cloud Run (region $GcpRegion)..." -ForegroundColor Yellow
    try {
        # Engine B
        $svcB = "infinityai-engine-b"
        $descB = gcloud run services describe $svcB --platform managed --region $GcpRegion --format json 2>$null | ConvertFrom-Json
        if ($descB) {
            $trafficB = ($descB.status.traffic | Measure-Object -Property percent -Sum).Sum
            $urlB = $descB.status.url
            $statusB = if ($trafficB -gt 0 -and $urlB) { "Healthy" } else { "Degraded" }
            $report.engines[$svcB] = [ordered]@{
                platform = "gcp-cloudrun"
                desired = "-"
                ready = if ($statusB -eq "Healthy") { 1 } else { 0 }
                status = $statusB
                url = $urlB
            }
            # HTTP probe
            if ($urlB) {
                try {
                    $respB = Invoke-WebRequest -Uri ("{0}/health" -f $urlB) -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                    if ($respB.StatusCode -ge 200 -and $respB.StatusCode -lt 300) {
                        $report.engines[$svcB].ready = 1
                        $report.engines[$svcB].status = "Healthy"
                    }
                } catch {}
            }
        }

        # Ultra Aggressive
        $service = "infinityai-ultra-aggressive"
        $desc = gcloud run services describe $service --platform managed --region $GcpRegion --format json 2>$null | ConvertFrom-Json
        if ($desc) {
            $traffic = ($desc.status.traffic | Measure-Object -Property percent -Sum).Sum
            $url = $desc.status.url
            $status = if ($traffic -gt 0 -and $url) { "Healthy" } else { "Degraded" }
            $report.traders["ultra-aggressive"] = [ordered]@{
                platform = "gcp-cloudrun"
                url = $url
                status = $status
                trafficPercent = $traffic
            }
        }
        $report.clouds.gcp = @{ region = $GcpRegion }
    }
    catch {
        Write-Host "GCP Cloud Run check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "gcloud not found. Skipping GCP checks." -ForegroundColor DarkGray
}

# Azure checks removed as environment is now AWS + GCP only.

# Print summary (after collecting from all clouds)
Write-Host "\nSummary:" -ForegroundColor Cyan
$rows = @()
foreach ($k in $report.engines.Keys) {
    $e = $report.engines[$k]
    $rows += [pscustomobject]@{ Name=$k; Platform=$e.platform; Desired=$e.desired; Ready=$e.ready; Status=$e.status }
}
foreach ($k in $report.traders.Keys) {
    $t = $report.traders[$k]
    $rows += [pscustomobject]@{ Name=$k; Platform=$t.platform; Desired="-"; Ready="-"; Status=$t.status }
}
if ($rows.Count -gt 0) { $rows | Format-Table -AutoSize } else { Write-Host "No resources detected by available CLIs." -ForegroundColor DarkGray }

# Save report
$reportPath = Join-Path (Get-Location) "cloud_health_report.json"
($report | ConvertTo-Json -Depth 6) | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "\nReport saved to: $reportPath" -ForegroundColor Green
