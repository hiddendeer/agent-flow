@echo off
REM DeerFlow 健康检查脚本
REM 检查所有服务是否正常运行

echo ========================================
echo 宅力觉醒智能体 服务健康检查
echo ========================================
echo.

echo 1. 检查Docker容器状态...
docker ps --filter "name=deer-flow" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo 2. 检查服务健康状态...
echo.

REM 检查Nginx
curl -s http://localhost:2026 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Nginx (2026) - 运行正常
) else (
    echo ❌ Nginx (2026) - 无法访问
)

REM 检查Gateway API
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Gateway API (8001) - 运行正常
) else (
    echo ❌ Gateway API (8001) - 无法访问
)

REM 检查LangGraph
curl -s http://localhost:2024 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ LangGraph (2024) - 运行正常
) else (
    echo ❌ LangGraph (2024) - 无法访问
)

echo.
echo 3. 查看最近日志...
echo.
echo === Gateway 日志 (最后10行) ===
docker logs deer-flow-gateway --tail 10 2>&1
echo.
echo === LangGraph 日志 (最后10行) ===
docker logs deer-flow-langgraph --tail 10 2>&1

echo.
echo ========================================
echo 💡 如果服务未就绪，请等待30-60秒后重试
echo ========================================
pause
