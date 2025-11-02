param(
  [string]$Project = "infinity-ai",
  [string]$GatewayName = "infinityai-gateway",
  [string]$Domain = "engines.infinityai.pro",
  [string]$Region = "eu-west-1" # adjust if needed
)

# Requires northflank CLI installed and NF_TOKEN environment variable or prior login
# Example login: northflank auth login --token $Env:NORTHFLANK_TOKEN

Write-Host "Creating Northflank API Gateway '$GatewayName' in project '$Project'..."

# Create gateway
northflank api-gateways create `
  --project $Project `
  --name $GatewayName `
  --protocol https `
  --region $Region `
  --public true | Tee-Object -Variable gatewayOut | Out-Host

# Extract gateway ID
$gatewayId = ($gatewayOut | Select-String -Pattern 'id\s*:\s*(?<id>[-\w]+)' -AllMatches).Matches[0].Groups['id'].Value
if (-not $gatewayId) {
  Write-Error "Failed to obtain gateway ID. Check CLI output above."
  exit 1
}

Write-Host "Gateway ID: $gatewayId"

# Attach custom domain
Write-Host "Attaching domain $Domain to gateway..."
northflank api-gateways domains add `
  --project $Project `
  --gateway $gatewayId `
  --domain $Domain | Out-Host

# Create routes to services
$routes = @(
  @{ path = "/engine-a"; service = "engine-a" },
  @{ path = "/engine-b"; service = "engine-b" },
  @{ path = "/engine-c"; service = "engine-c-execution" },
  @{ path = "/engine-d"; service = "engine-d" }
)

foreach ($r in $routes) {
  Write-Host "Creating route $($r.path) -> $($r.service)"
  northflank api-gateways routes create `
    --project $Project `
    --gateway $gatewayId `
    --path $($r.path) `
    --service $($r.service) `
    --protocol https `
    --preservePath true | Out-Host
}

# Fetch domain mapping to print CNAME target for DNS
Write-Host "Fetching domain mapping for CNAME..."
$domains = northflank api-gateways domains list --project $Project --gateway $gatewayId --json | ConvertFrom-Json
$dns = $domains | Where-Object { $_.domain -eq $Domain }
if ($dns) {
  Write-Host "Add this CNAME at Namecheap:"
  Write-Host "Name: engines"
  Write-Host "Type: CNAME"
  Write-Host ("Target: {0}" -f $dns.cname)
} else {
  Write-Warning "Could not retrieve CNAME automatically. Check the Northflank UI for the exact target."
}
