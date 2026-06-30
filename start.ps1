# 智农溯源 - 一键启动脚本
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
$ErrorActionPreference = "Continue"

$port = 8000
$url = "http://127.0.0.1:$port"

Clear-Host
Write-Host ""
Write-Host "   ZhiSu NongLian - Starting..." -ForegroundColor Green
Write-Host ""

# Check Python
try {
    python --version 2>&1 | Out-Null
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Start Django server in background
$serverJob = Start-Job -ScriptBlock {
    param($dir, $p)
    Set-Location $dir
    $env:PYTHONIOENCODING = "utf-8"
    python manage.py runserver "127.0.0.1:$p"
} -ArgumentList (Get-Location).Path, $port

# Wait for server to be ready (max 15 seconds)
Write-Host "Waiting for server to start..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $null = Invoke-WebRequest -Uri $url -TimeoutSec 1 -UseBasicParsing
        $ready = $true
        break
    } catch {}
}

# Open browser
if ($ready) {
    Write-Host "Server ready! Opening browser..." -ForegroundColor Green
    Start-Process $url
    Write-Host "Visit: $url" -ForegroundColor Cyan
} else {
    Write-Host "Timeout. Visit manually: $url" -ForegroundColor Yellow
}

# Show Tailscale address
try {
    $ts = & tailscale status 2>$null
    if ($ts -match "(\d+\.\d+\.\d+\.\d+)") {
        Write-Host "Tailscale: http://$($matches[1]):$port" -ForegroundColor DarkGray
    }
} catch {}

Write-Host ""
Write-Host "Press any key to stop server..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop server
Stop-Job $serverJob -ErrorAction SilentlyContinue
Remove-Job $serverJob -ErrorAction SilentlyContinue
Write-Host "Server stopped." -ForegroundColor Yellow