# Windows Scheduled Task Setup Script for Autonomous 30-Day Project Agent
# Registers a Windows Task Scheduler job that fires daily at 18:00 (6:00 PM)

$TaskName = "AutonomousProjectAgent_Daily"
$ProjectPath = (Get-Item -Path ".").FullName
$PythonExe = (Get-Command python).Source
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "main.py run" -WorkingDirectory $ProjectPath
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:00PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs the Autonomous 30-Day Project Agent at 6:00 PM daily" -Force

Write-Host "✅ Windows Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
Write-Host "Task will trigger every day at 6:00 PM IST." -ForegroundColor Cyan
Write-Host "To view task in Task Scheduler: taskschd.msc"
