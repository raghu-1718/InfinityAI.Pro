param(
  [Parameter(Mandatory=$true)][string]$ApiToken,
  [Parameter(Mandatory=$true)][string]$Project,           # e.g. "infinity-ai"
  [Parameter(Mandatory=$true)][string]$GatewaySlug,       # e.g. "infinityai-gateway"
  [Parameter(Mandatory=$true)][string]$Domain,            # e.g. "engines.infinityai.pro"
  [Parameter(Mandatory=$true)][string]$EngineAService,    # e.g. service slug in Northflank
  [Parameter(Mandatory=$true)][string]$EngineBService,
  [Parameter(Mandatory=$true)][string]$EngineCService,
  [Parameter(Mandatory=$true)][string]$EngineDService
)

# NOTE: Verify endpoints in Northflank API docs if they change. Base URL is assumed.
$BaseUrl = "https://api.northflank.com/v1"
$Headers = @{ 'Authorization' = "Bearer $ApiToken"; 'Content-Type' = 'application/json' }

Write-Host "Creating/ensuring API Gateway '$GatewaySlug' in project '$Project'..."
$gatewayBody = @{ slug = $GatewaySlug; name = $GatewaySlug; description = "InfinityAI unified gateway" } | ConvertTo-Json
try {
  $null = Invoke-RestMethod -Method POST -Uri "$BaseUrl/projects/$Project/gateways" -Headers $Headers -Body $gatewayBody -ErrorAction Stop
} catch {
  Write-Host "Gateway may already exist or creation failed: $($_.Exception.Message)"
}

Write-Host "Attaching domain '$Domain' to gateway '$GatewaySlug'..."
$domainBody = @{ domain = $Domain } | ConvertTo-Json
try {
  $addDomain = Invoke-RestMethod -Method POST -Uri "$BaseUrl/projects/$Project/gateways/$GatewaySlug/domains" -Headers $Headers -Body $domainBody -ErrorAction Stop
  if ($addDomain -and $addDomain.cnameTarget) {
    Write-Host "Add CNAME record in DNS: $Domain -> $($addDomain.cnameTarget)"
  } else {
    Write-Host "Domain attached. Retrieve CNAME from Northflank UI if not returned here."
  }
} catch {
  Write-Host "Domain attach error (may already be attached): $($_.Exception.Message)"
}

function Add-Route($pathPrefix, $serviceSlug) {
  Write-Host "Adding route $pathPrefix -> service $serviceSlug"
  $routeBody = @{ pathPrefix = $pathPrefix; service = $serviceSlug } | ConvertTo-Json
  try {
    $null = Invoke-RestMethod -Method POST -Uri "$BaseUrl/projects/$Project/gateways/$GatewaySlug/routes" -Headers $Headers -Body $routeBody -ErrorAction Stop
  } catch {
    Write-Host ("Route add error for {0}: {1}" -f $pathPrefix, $_.Exception.Message)
  }
}

Add-Route -pathPrefix "/engine-a" -serviceSlug $EngineAService
Add-Route -pathPrefix "/engine-b" -serviceSlug $EngineBService
Add-Route -pathPrefix "/engine-c" -serviceSlug $EngineCService
Add-Route -pathPrefix "/engine-d" -serviceSlug $EngineDService

Write-Host "Gateway setup attempted. Verify in Northflank UI and ensure DNS CNAME is configured for $Domain."