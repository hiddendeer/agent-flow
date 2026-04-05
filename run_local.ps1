Write-Host "INFO: Checking environment..." -ForegroundColor Cyan

if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: uv not found. Please install it: pip install uv" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

$ProjectRoot = Get-Location
$Env:PYTHONPATH = "$ProjectRoot\backend"

Write-Host "INFO: Syncing backend dependencies..." -ForegroundColor Cyan
Set-Location "$ProjectRoot\backend"
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

Write-Host "INFO: Starting Agent Layer (LangGraph)..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k cd /d $ProjectRoot\backend && uv run langgraph dev --no-browser --port 2024"

Start-Sleep -Seconds 5

Write-Host "INFO: Starting Gateway API (Uvicorn)..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k cd /d $ProjectRoot\backend && uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"

Write-Host "============================================" -ForegroundColor Green
Write-Host "SUCCESS: Services are starting in new windows." -ForegroundColor Green
Write-Host "Gateway Docs: http://localhost:8001/docs"
Write-Host "Agent UI:     http://localhost:2024"
Write-Host "============================================" -ForegroundColor Green
Read-Host "Press Enter to exit"
