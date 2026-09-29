$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path '.venv')) {
    python -m venv .venv
}

$venvPython = @('.venv\Scripts\python.exe', '.venv\bin\python.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $venvPython) {
    throw 'A Python virtual environment could not be created. Install Python 3.11 or newer and retry.'
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r backend\requirements.txt
Push-Location frontend
npm install
Pop-Location
& $venvPython scripts\generate_samples.py
& $venvPython scripts\seed.py --reset

Write-Host "Setup complete. Run: powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1" -ForegroundColor Green
