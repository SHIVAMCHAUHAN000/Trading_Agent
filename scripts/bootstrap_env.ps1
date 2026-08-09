# Stage 2 helper: create Python 3.11 venv and install the project
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$py = Get-Command "py" -ErrorAction SilentlyContinue
if (-not $py) {
  Write-Error "Python launcher 'py' not found. Install Python 3.11 first."
}

py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -e ".[dev]"

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example — fill Supabase credentials later."
}

Write-Host "Bootstrap complete. Activate with: .\.venv\Scripts\Activate.ps1"
