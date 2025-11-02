param(
  [string]$Base = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com",
  [int]$TimeoutSec = 10
)

function Test-Endpoint {
  param([string]$Url, [string]$Method = 'GET', $Body = $null)
  try {
    $params = @{ Uri = $Url; Method = $Method; TimeoutSec = $TimeoutSec }
    if ($Body) { $params['Body'] = ($Body | ConvertTo-Json -Depth 5); $params['ContentType'] = 'application/json' }
    $r = Invoke-WebRequest @params -UseBasicParsing
    return [PSCustomObject]@{ url=$Url; status=$r.StatusCode; ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 300); length=$r.Content.Length }
  } catch {
    return [PSCustomObject]@{ url=$Url; status='error'; ok=$false; error=$_.Exception.Message }
  }
}

Write-Host "=== Engine D Status ==="
$engineDStatus = Test-Endpoint "$Base/engine-d/status"
$engineDHealth = Test-Endpoint "$Base/engine-d/health"

Write-Host "=== Engine C Health ==="
$engineCHealth = Test-Endpoint "$Base/engine-c/health"

Write-Host "=== Proxies: Dhan ==="
$dhanStatus = Test-Endpoint "$Base/engine-d/user/broker/dhan/status"
$dhanTokenProbe = Test-Endpoint "$Base/engine-d/user/broker/dhan/token" 'POST' @{ access_token = 'probe' }

Write-Host "=== Market Data (A via D) ==="
$chart = Test-Endpoint "$Base/engine-d/chart/NIFTY?timeframe=1D"
$overview = Test-Endpoint "$Base/engine-d/market/overview"

Write-Host "=== AI (B via D) ==="
$insights = Test-Endpoint "$Base/engine-d/insights"

Write-Host "=== Results ==="
$results = @($engineDStatus,$engineDHealth,$engineCHealth,$dhanStatus,$dhanTokenProbe,$chart,$overview,$insights)
$results | ConvertTo-Json -Depth 4 | Out-File -FilePath "$PSScriptRoot\verify-results.json" -Encoding utf8
Write-Host "Saved: $PSScriptRoot\verify-results.json"
