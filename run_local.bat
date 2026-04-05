@echo off
chcp 65001 >nul
setlocal
echo INFO: 正在检查环境...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 uv。请先安装: pip install uv
    pause
    exit /b 1
)
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%~dp0backend"
echo INFO: 正在同步后端依赖...
cd /d "%~dp0backend"
call uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [警告] 依赖同步可能失败。
)
echo INFO: 正在启动 Agent 层 (LangGraph)...
start "DeerFlow_Agent" cmd /k "cd /d %~dp0backend && uv run langgraph dev --no-browser --port 2024"
timeout /t 5 /nobreak >nul
echo INFO: 正在启动网关 API (Uvicorn)...
start "DeerFlow_Gateway" cmd /k "cd /d %~dp0backend && uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"
echo ============================================
echo   启动成功！请查看弹出的两个窗口。
echo   网关文档: http://localhost:8001/docs
echo   Agent 可视化: http://localhost:2024
echo ============================================
pause
