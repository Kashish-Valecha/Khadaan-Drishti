$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$venvPython = @('.venv\Scripts\python.exe', '.venv\bin\python.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $venvPython) {
    throw 'Run .\scripts\setup.ps1 first.'
}

$api = Start-Process -FilePath $venvPython -ArgumentList '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
try {
    Write-Host 'API: http://127.0.0.1:8000/docs' -ForegroundColor Cyan
    Write-Host 'Dashboard: http://127.0.0.1:5173' -ForegroundColor Cyan
    npm --prefix frontend run dev -- --host 127.0.0.1
}
finally {
    if ($api -and -not $api.HasExited) {
        Stop-Process -Id $api.Id -Force
    }
}
