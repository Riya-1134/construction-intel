# Starts the FastAPI backend (creates the venv and installs deps on first run).
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"
if (-not (Test-Path ".venv")) {
  python -m venv .venv
  .\.venv\Scripts\python -m pip install -r requirements.txt
}
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created backend\.env from .env.example - add your GROQ_API_KEY to enable live AI." }
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
