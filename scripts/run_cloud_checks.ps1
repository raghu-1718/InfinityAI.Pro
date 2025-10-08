# Cloud checks for InfinityAI.Pro
param(
	[string]$BaseUrl = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com",
	[string]$OutFile = "cloud_check_output.txt"
)

$ErrorActionPreference = 'Stop'
Write-Host "Running cloud checks against $BaseUrl" -ForegroundColor Cyan

$targets = @(
	"/engine-d/health",
	"/engine-d/status",
	"/engine-c/health"
)

$log = Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) -ChildPath $OutFile
"Cloud Checks: $(Get-Date -Format o)" | Out-File $log -Encoding utf8
"BaseUrl: $BaseUrl" | Out-File $log -Append

foreach ($t in $targets) {
	$url = "$BaseUrl$t"
	try {
		$resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
		"${url} :: $($resp.StatusCode)" | Out-File $log -Append
	}
	catch {
		"${url} :: ERROR :: $($_.Exception.Message)" | Out-File $log -Append
	}
}

"Completed." | Out-File $log -Append
Write-Host "Cloud checks complete. See $log" -ForegroundColor Green
