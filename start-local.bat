@echo off
setlocal

echo INFO: Starting 宅力觉醒智能体 Local Environment...

:: 1. Check prerequisites
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv not found. Please run: pip install uv
    pause && exit /b 1
)

:: 2. Sync dependencies
echo INFO: Syncing dependencies in backend folder...
pushd "%~dp0backend"
call uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo WARNING: Dependency sync might have failed.
)
popd

:: 3. Start Agent Layer (LangGraph)
echo INFO: Launching Agent Layer (LangGraph)...
start "宅力觉醒_Agent" cmd /k "cd /d %~dp0backend && uv run langgraph dev --no-browser --port 2024"

:: 4. Start Gateway API
echo INFO: Launching Gateway API (Gateway)...
set "PYTHONPATH=%~dp0\backend"
start "宅力觉醒_Gateway" cmd /k "cd /d %~dp0backend && uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"

echo ============================================
echo SUCCESS: Services are starting in new windows.
echo - Gateway: http://localhost:8001
echo - Agent:   http://localhost:2024
echo ============================================
pause
