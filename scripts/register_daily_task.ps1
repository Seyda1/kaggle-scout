# Registers a Windows scheduled task that runs the daily report for the current user.
param(
    [string]$Time = "09:30",
    [string]$TaskName = "Kaggle Scout Daily Report"
)

$runner = Join-Path $PSScriptRoot "run_daily_report.ps1"
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
# StartWhenAvailable catches up on a missed run as soon as the PC is back on.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Ranks active Kaggle competitions against your profile and emails the report." `
    -Force | Out-Null

Write-Output "Registered '$TaskName' daily at $Time."
