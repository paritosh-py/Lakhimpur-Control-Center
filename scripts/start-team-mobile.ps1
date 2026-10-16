param([int]$Port = 8001)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & npm.cmd run build --prefix apps/web
    if ($LASTEXITCODE -ne 0) { throw 'Web build failed' }
    Write-Host "Phone: open http://<this-laptop-Wi-Fi-IP>:$Port/team-app.apk to download the debug APK."
    Write-Host "In the app, enter http://<this-laptop-Wi-Fi-IP>:$Port and tap Open."
    Write-Host 'Keep this terminal and the model service running. Ctrl+C stops this server.'
    & ./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port $Port
} finally { Pop-Location }
