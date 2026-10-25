# Starts the Vite dev server (installs node modules on first run).
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\frontend"
if (-not (Test-Path "node_modules")) { npm install }
npm run dev
