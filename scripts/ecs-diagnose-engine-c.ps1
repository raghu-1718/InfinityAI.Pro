<#
.SYNOPSIS
  Diagnose ECS Engine C service stability issues: service events, target health, task details, and container logs.

.PARAMETER Cluster
  ECS Cluster name. Default: infinityai-pro-cluster

.PARAMETER Service
  ECS Service name. Default: infinityai-engine-c-service

.PARAMETER Region
  AWS region. Default: us-east-1

.PARAMETER LookbackMinutes
  How far back to fetch CloudWatch logs. Default: 60

.DESCRIPTION
  - Prints recent ECS service events
  - Shows target group health for the service's attached target group
  - Describes the latest task, including container health check status
  - Optionally streams the last N minutes of application logs from CloudWatch
#>
param(
  [string]$Cluster = 'infinityai-pro-cluster',
  [string]$Service = 'infinityai-engine-c-service',
  [string]$Region = 'us-east-1',
  [int]$LookbackMinutes = 60
)

$ErrorActionPreference = 'Stop'

function Jq($json, $query){
  try { return ($json | ConvertFrom-Json | ConvertTo-Json -Depth 100) } catch { return $json }
}

function Section($t){ Write-Host "`n=== $t ===" -ForegroundColor Cyan }

Section "ECS Service Events"
$svc = aws ecs describe-services --region $Region --cluster $Cluster --services $Service --output json | ConvertFrom-Json
if(-not $svc.services -or $svc.services.Count -eq 0){ throw "Service not found: $Service" }
$service = $svc.services[0]
$service.events | Sort-Object -Property createdAt | Select-Object -Last 15 | ForEach-Object {
  Write-Host ("[{0}] {1}" -f $_.createdAt, $_.message)
}

Section "Target Group Health"
$lbArn = $service.loadBalancers[0].targetGroupArn
if($lbArn){
  $tg = aws elbv2 describe-target-health --region $Region --target-group-arn $lbArn --output json | ConvertFrom-Json
  foreach($d in $tg.TargetHealthDescriptions){
    Write-Host ("Target {0}:{1} -> {2} ({3})" -f $d.Target.Id, $d.Target.Port, $d.TargetHealth.State, $d.TargetHealth.Reason)
  }
} else {
  Write-Host "No target group attached to service." -ForegroundColor Yellow
}

Section "Latest Task Detail"
$tasksArns = aws ecs list-tasks --region $Region --cluster $Cluster --service-name $Service --desired-status RUNNING --output text --query 'taskArns'
if([string]::IsNullOrWhiteSpace($tasksArns)){
  Write-Host "No RUNNING tasks. Checking PENDING tasks..." -ForegroundColor Yellow
  $tasksArns = aws ecs list-tasks --region $Region --cluster $Cluster --service-name $Service --desired-status PENDING --output text --query 'taskArns'
}
if(-not [string]::IsNullOrWhiteSpace($tasksArns)){
  $taskArn = $tasksArns.Split()[0]
  $task = aws ecs describe-tasks --region $Region --cluster $Cluster --tasks $taskArn --output json | ConvertFrom-Json
  $tdArn = $task.tasks[0].taskDefinitionArn
  Write-Host "Task: $taskArn" -ForegroundColor Green
  Write-Host "TaskDef: $tdArn" -ForegroundColor Green
  $cont = $task.tasks[0].containers[0]
  Write-Host ("Container {0} lastStatus={1} health={2}" -f $cont.name, $cont.lastStatus, $cont.healthStatus)
} else {
  Write-Host "No tasks found." -ForegroundColor Red
}

Section "Container Health Check from Task Definition"
$tdArn = if($tdArn){ $tdArn } else { (aws ecs describe-services --region $Region --cluster $Cluster --services $Service --query 'services[0].taskDefinition' --output text) }
if($tdArn -and $tdArn -ne 'None'){
  $td = aws ecs describe-task-definition --region $Region --task-definition $tdArn --output json | ConvertFrom-Json
  $hc = $td.taskDefinition.containerDefinitions[0].healthCheck
  if($hc){
    Write-Host ("HealthCheck command: {0}" -f ($hc.command -join ' '))
    Write-Host ("Interval={0}s Retries={1} Timeout={2}s StartPeriod={3}s" -f $hc.interval, $hc.retries, $hc.timeout, $hc.startPeriod)
  } else {
    Write-Host "No container health check configured." -ForegroundColor Yellow
  }
} else {
  Write-Host "Task definition not found." -ForegroundColor Red
}

Section "CloudWatch Logs (last $LookbackMinutes minutes)"
$logGroup = aws ecs describe-task-definition --region $Region --task-definition $tdArn --query 'taskDefinition.containerDefinitions[0].logConfiguration.options.log-group-name' --output text 2>$null
if($logGroup -and $logGroup -ne 'None'){
  $end = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $start = ([DateTimeOffset]::UtcNow.AddMinutes(-$LookbackMinutes)).ToUnixTimeMilliseconds()
  try {
    $streams = aws logs describe-log-streams --region $Region --log-group-name $logGroup --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text
    if($streams -and $streams -ne 'None'){
      aws logs get-log-events --region $Region --log-group-name $logGroup --log-stream-name $streams --start-time $start --end-time $end --limit 200 --output text --query 'events[].message'
    } else { Write-Host "No log streams found." -ForegroundColor Yellow }
  } catch { Write-Host "Log fetch failed: $_" -ForegroundColor Red }
} else {
  Write-Host "No log group configured in task definition." -ForegroundColor Yellow
}

Write-Host "\nTips:" -ForegroundColor Cyan
Write-Host " - If targets are Unhealthy: verify container listens on the target port and health path returns 200." -ForegroundColor Cyan
Write-Host " - Check security groups allow ALB->ECS on target port and egress to the internet if needed." -ForegroundColor Cyan
Write-Host " - Increase health check grace period/startPeriod during rollout to avoid premature fail." -ForegroundColor Cyan
