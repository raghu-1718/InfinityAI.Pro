param(
  [string]$Region = "us-east-1",
  [string]$ConfigPath = "multi-cloud-config.json"
)

Write-Host "🔧 Fixing AWS ALB routing for Engine C/D..." -ForegroundColor Yellow

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  Write-Host "AWS CLI not found. Please install/configure AWS CLI." -ForegroundColor Red
  exit 1
}

if (-not (Test-Path $ConfigPath)) {
  Write-Host "Config file not found: $ConfigPath" -ForegroundColor Red
  exit 1
}

$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$aws = $cfg.clouds.aws.services
$listenerArn = $aws.load_balancer.listener_arn
$tgC = $aws.'engine_c'.connections_target_group_arn
$tgD = $aws.'engine_d'.connections_target_group_arn

# Fallback to values inside target_groups map if direct arns not found
if (-not $tgC) { $tgC = $aws.load_balancer.target_groups.'engine-c'.arn }
if (-not $tgD) { $tgD = $aws.load_balancer.target_groups.'engine-d'.arn }

if (-not $listenerArn -or -not $tgC -or -not $tgD) {
  Write-Host "Missing listener or target group ARNs in config. Please update multi-cloud-config.json." -ForegroundColor Red
  exit 1
}

Write-Host "Listener ARN: $listenerArn" -ForegroundColor Cyan
Write-Host "TG Engine C: $tgC" -ForegroundColor Cyan
Write-Host "TG Engine D: $tgD" -ForegroundColor Cyan

# Ensure target group health checks and ports
Write-Host "➡️  Setting TG engine-c health path=/health, health-check-port=traffic-port" -ForegroundColor Yellow
aws elbv2 modify-target-group --target-group-arn $tgC --health-check-path /health --health-check-port traffic-port --region $Region | Out-Null

Write-Host "➡️  Setting TG engine-d health path=/health, health-check-port=traffic-port" -ForegroundColor Yellow
aws elbv2 modify-target-group --target-group-arn $tgD --health-check-path /health --health-check-port traffic-port --region $Region | Out-Null

# Find existing rules to update or create new ones
$rules = aws elbv2 describe-rules --listener-arn $listenerArn --region $Region | ConvertFrom-Json

function Set-PathRule {
  param(
    [string]$PathPattern,
    [string]$TargetGroupArn,
    [int]$Priority
  )
  $script:rules = aws elbv2 describe-rules --listener-arn $listenerArn --region $Region | ConvertFrom-Json
  $existing = $script:rules.Rules | Where-Object { $_.Conditions | Where-Object { $_.Field -eq 'path-pattern' -and ($_.Values -contains $PathPattern) } }
  if ($existing) {
    $ruleArn = $existing.RuleArn
    Write-Host "✏️  Modifying rule $ruleArn for $PathPattern" -ForegroundColor Yellow
    $conds = @(@{ Field = 'path-pattern'; PathPatternConfig = @{ Values = @($PathPattern) } }) | ConvertTo-Json -Compress
    $acts  = @(@{ Type = 'forward'; TargetGroupArn = $TargetGroupArn }) | ConvertTo-Json -Compress
    aws elbv2 modify-rule --rule-arn $ruleArn --conditions $conds --actions $acts --region $Region | Out-Null
  } else {
    # Find unused priority starting at desired
    $used = @()
    foreach ($r in $script:rules.Rules) {
      if ($r.Priority -and $r.Priority -match '^[0-9]+$') { $used += [int]$r.Priority }
    }
    $p = [int]$Priority
    while ($used -contains $p) { $p++ }
    Write-Host "➕ Creating new rule for $PathPattern (priority $p)" -ForegroundColor Yellow
    $conds = @(@{ Field = 'path-pattern'; PathPatternConfig = @{ Values = @($PathPattern) } }) | ConvertTo-Json -Compress
    $acts  = @(@{ Type = 'forward'; TargetGroupArn = $TargetGroupArn }) | ConvertTo-Json -Compress
    aws elbv2 create-rule --listener-arn $listenerArn --priority $p --conditions $conds --actions $acts --region $Region | Out-Null
  }
}

# Ensure path-based rules
# Prefer explicit patterns to avoid broad matches
Set-PathRule -PathPattern "/engine-c/*" -TargetGroupArn $tgC -Priority 5
Set-PathRule -PathPattern "/engine-d/*" -TargetGroupArn $tgD -Priority 6

Write-Host "✅ ALB routing configured. Please allow a minute for health checks to pass." -ForegroundColor Green
