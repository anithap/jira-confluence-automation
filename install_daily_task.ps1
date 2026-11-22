$ErrorActionPreference = "Stop"

$workspace = $PSScriptRoot
$scriptPath = Join-Path $workspace "generate_sprint_report.py"
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "Report generator not found: $scriptPath"
}

$pythonCommand = Get-Command python -ErrorAction Stop
$pythonPath = $pythonCommand.Source
$defaultConfig = Join-Path $workspace "config.json"
$configInput = Read-Host "Config file path [$defaultConfig]"
$configPath = if ([string]::IsNullOrWhiteSpace($configInput)) { $defaultConfig } else { $configInput }
$configPath = [System.IO.Path]::GetFullPath($configPath)
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Config file not found: $configPath"
}

$runTime = Read-Host "Daily run time in local 24-hour format (HH:mm)"
$parsedTime = [datetime]::MinValue
if (-not [datetime]::TryParseExact(
    $runTime,
    "HH:mm",
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::None,
    [ref]$parsedTime
)) {
    throw "Enter the run time as HH:mm, for example 16:30."
}

$taskName = "Daily Jira Stakeholder Status Report"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $existingTask) {
    throw "A scheduled task named '$taskName' already exists. Review it in Task Scheduler before changing it."
}

$arguments = '"{0}" --config "{1}"' -f $scriptPath, $configPath
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $arguments `
    -WorkingDirectory $workspace
$trigger = New-ScheduledTaskTrigger -Daily -At $parsedTime
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings | Out-Null

Write-Output "Scheduled '$taskName' daily at $($parsedTime.ToString('HH:mm')) local time."
Write-Output "The report will be generated at the output_path configured in $configPath."
