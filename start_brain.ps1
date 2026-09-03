# Windows PowerShell Launcher for Personal Live Quant Brain
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       STARTING PERSONAL LIVE QUANT BRAIN" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check virtual environment
if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonExe = ".\.venv\Scripts\python.exe"
} else {
    $PythonExe = "python"
}

# Create .env if missing
if (-not (Test-Path ".env")) {
    Write-Host "No .env found. Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "Using Python: $PythonExe" -ForegroundColor Gray
Write-Host "Launching Unified Production Server (Web App + Telegram)..." -ForegroundColor Green
Write-Host "Dashboard will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop services." -ForegroundColor Gray
Write-Host ""

& $PythonExe deployment/run_production.py
