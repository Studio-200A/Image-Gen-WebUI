#!/usr/bin/env pwsh
# Run the Image-Gen-WebUI server (Windows)
# This script assumes it lives in the project root

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

Write-Host "Starting Image-Gen-WebUI..."
Write-Host "Project directory: $ScriptDir"

# Detect python (try python3 first, then python)
$pythonBin = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonBin) {
    $pythonBin = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $pythonBin) {
    Write-Host "Python not found. Please install Python 3."
    Read-Host "Press enter to close..."
    exit 1
}

# Create venv if missing
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    & $pythonBin.Source -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Install dependencies if needed
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies..."
    python -m pip install -r requirements.txt
}

# Start Flask in background
$proc = Start-Process -FilePath python -ArgumentList "app.py" -NoNewWindow -PassThru

# Give Flask a moment to start then open browser
Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:5000"

Write-Host "Server is running. Press Enter to stop..."
try {
    Read-Host | Out-Null
} finally {
    if ($proc -and !$proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    deactivate -ErrorAction SilentlyContinue
}

Read-Host "Press enter to close..."
