# Runs the Kaggle Scout daily report and emails it. Output goes to logs/daily_report.log.
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
$logDir = Join-Path $repo "logs"
$log = Join-Path $logDir "daily_report.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Test-Ollama {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 | Out-Null
        return $true
    } catch {
        return $false
    }
}

Add-Content -Path $log -Encoding UTF8 -Value "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

if (-not (Test-Ollama)) {
    Add-Content -Path $log -Encoding UTF8 -Value "Starting Ollama..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    for ($i = 0; $i -lt 30 -and -not (Test-Ollama); $i++) {
        Start-Sleep -Seconds 2
    }
}

$env:PYTHONIOENCODING = "utf-8"
Set-Location $repo
cmd /c "`"$python`" main.py --email >> `"$log`" 2>&1"
$exitCode = $LASTEXITCODE
Add-Content -Path $log -Encoding UTF8 -Value "Exit code: $exitCode"
exit $exitCode
