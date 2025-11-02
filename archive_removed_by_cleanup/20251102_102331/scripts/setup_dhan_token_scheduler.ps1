# Setup Windows Task Scheduler for Dhan API Token Refresh
# This script creates a daily scheduled task to refresh Dhan API tokens

$taskName = "InfinityAI Dhan Token Refresh"
$scriptPath = "C:\Users\Raghu\InfinityAI.Pro\dhan_auto_refresh.py"
$pythonPath = "python"  # Assumes python is in PATH

# Check if the script exists
if (!(Test-Path $scriptPath)) {
    Write-Host "❌ Error: dhan_auto_refresh.py not found at $scriptPath" -ForegroundColor Red
    exit 1
}

# Create the scheduled task
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"  # Run daily at 9:00 AM (market open time)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automatically refresh Dhan API access tokens daily for InfinityAI.Pro"

Write-Host "✅ Scheduled task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "📅 Task will run daily at 9:00 AM" -ForegroundColor Cyan
Write-Host "🔧 You can modify the schedule in Task Scheduler if needed" -ForegroundColor Yellow