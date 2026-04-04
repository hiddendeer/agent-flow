@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM 宅力觉醒智能体 - 统一启动脚本
REM ============================================

echo.
echo ╔══════════════════════════════════════════╗
echo ║  🎮 宅力觉醒智能体 - 启动菜单          ║
echo ╚══════════════════════════════════════════╝
echo.
echo 请选择启动模式:
echo.
echo [1] Docker 完整模式    ⭐ 推荐
echo     - 启动完整服务 (Gateway + LangGraph + Frontend + Nginx)
echo     - 适合生产环境和完整功能体验
echo.
echo [2] Docker 简化模式    💡 轻量
echo     - 仅启动核心服务 (Gateway + LangGraph)
echo     - 适合开发和测试，资源占用少
echo.
echo [3] 本地开发模式      🔧 开发
echo     - 本地Python环境，无需Docker
echo     - 适合开发者调试和修改代码
echo.
echo [4] 网络诊断         🔍 诊断
echo     - 检查Docker、网络和配置
echo.
echo [0] 退出
echo.

choice /c 12340 /m "请选择模式:"
if errorlevel 5 goto :eof
if errorlevel 4 goto diagnose
if errorlevel 3 goto local
if errorlevel 2 goto simple
if errorlevel 1 goto full

:full
echo.
echo ═════════════════════════════════════════
echo  🚀 启动 Docker 完整模式
echo ═════════════════════════════════════════
echo.
call :check_docker
if errorlevel 1 goto :eof

call :setup_env
call :start_docker_full
goto :end

:simple
echo.
echo ═════════════════════════════════════════
echo  💡 启动 Docker 简化模式
echo ═════════════════════════════════════════
echo.
call :check_docker
if errorlevel 1 goto :eof

call :setup_env
call :start_docker_simple
goto :end

:local
echo.
echo ═════════════════════════════════════════
echo  🔧 启动本地开发模式
echo ═════════════════════════════════════════
echo.
call :check_local
if errorlevel 1 goto :eof

call :start_local
goto :end

:diagnose
echo.
echo ═════════════════════════════════════════
echo  🔍 网络诊断
echo ═════════════════════════════════════════
echo.
call :run_diagnose
goto :eof

REM ===== 子程序 =====

:check_docker
echo 🔍 检查 Docker 环境...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker 运行正常
docker --version
exit /b 0

:check_local
echo 🔍 检查本地开发环境...
where uv >nul 2>&1
if errorlevel 1 (
    echo ❌ uv 包管理器未安装
    echo 请运行: pip install uv
    pause
    exit /b 1
)
echo ✅ uv 已安装
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装
    pause
    exit /b 1
)
echo ✅ Python 已安装
python --version
exit /b 0

:setup_env
echo.
echo 📁 设置项目环境...
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "DEER_FLOW_ROOT=%PROJECT_ROOT%"
set "UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "APT_MIRROR=mirrors.aliyun.com"
set "NPM_REGISTRY=https://registry.npmmirror.com"

echo 项目路径: %PROJECT_ROOT%
echo Python镜像: %UV_INDEX_URL%
echo APT镜像: %APT_MIRROR%
echo NPM镜像: %NPM_REGISTRY%
echo.

REM 创建必要目录
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"
if not exist "%PROJECT_ROOT%\backend\.deer-flow" mkdir "%PROJECT_ROOT%\backend\.deer-flow"

echo ✅ 环境设置完成
exit /b 0

:start_docker_full
echo 🔧 启动完整服务...
echo 使用配置: docker/docker-compose-lite.yaml
echo.

docker-compose -f "%PROJECT_ROOT%\docker\docker-compose-lite.yaml" down 2>nul
docker-compose -f "%PROJECT_ROOT%\docker\docker-compose-lite.yaml" up -d --build

if errorlevel 1 (
    echo.
    echo ❌ 启动失败！
    echo 请检查:
    echo   1. Docker Desktop 是否运行正常
    echo   2. 端口 8001、2024、2026 是否被占用
    echo   3. 网络连接是否正常
    pause
    exit /b 1
)

call :show_success_full
exit /b 0

:start_docker_simple
echo 🔧 启动简化服务...
echo 使用配置: docker/docker-compose-simple.yaml
echo.

docker-compose -f "%PROJECT_ROOT%\docker\docker-compose-simple.yaml" down 2>nul
docker-compose -f "%PROJECT_ROOT%\docker\docker-compose-simple.yaml" up -d --build

if errorlevel 1 (
    echo.
    echo ❌ 启动失败！
    echo 请检查:
    echo   1. Docker Desktop 是否运行正常
    echo   2. 端口 8001、2024 是否被占用
    echo   3. 网络连接是否正常
    pause
    exit /b 1
)

call :show_success_simple
exit /b 0

:start_local
echo 🔧 启动本地开发环境...
echo.

REM 同步依赖
echo 📦 同步 Python 依赖...
cd /d "%PROJECT_ROOT%\backend"
uv sync --index-url %UV_INDEX_URL%

if errorlevel 1 (
    echo ❌ 依赖同步失败！
    pause
    exit /b 1
)

REM 启动 LangGraph
echo 🚀 启动 LangGraph 服务 (端口 2024)...
start "宅力觉醒_LangGraph" cmd /k "cd /d %PROJECT_ROOT%\backend && uv run langgraph dev --no-browser --port 2024"

REM 等待 LangGraph 启动
echo ⏳ 等待 LangGraph 启动 (10秒)...
timeout /t 10 /nobreak >nul

REM 启动 Gateway
echo 🚀 启动 Gateway API (端口 8001)...
set "PYTHONPATH=%PROJECT_ROOT%\backend"
start "宅力觉醒_Gateway" cmd /k "cd /d %PROJECT_ROOT%\backend && uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"

echo.
call :show_success_local
exit /r 0

:show_success_full
echo.
echo ╔══════════════════════════════════════════╗
echo ║  ✅ 启动成功！                          ║
echo ╚══════════════════════════════════════════╝
echo.
echo 🌐 访问地址:
echo    主界面:     http://localhost:2026
echo    API文档:    http://localhost:2026/api/docs
echo    LangGraph:  http://localhost:2024
echo    Gateway:    http://localhost:8001
echo.
echo 📊 服务管理:
echo    查看日志:   docker-compose -f docker/docker-compose-lite.yaml logs -f
echo    停止服务:   stop.bat
echo    重启服务:   docker-compose -f docker/docker-compose-lite.yaml restart
echo.
echo ⏳ 等待服务完全启动 (约 30-60 秒)...
timeout /t 5 /nobreak >nul
echo.
echo 🎯 现在可以访问 http://localhost:2026
echo.
exit /r 0

:show_success_simple
echo.
echo ╔══════════════════════════════════════════╗
echo ║  ✅ 启动成功！                          ║
echo ╚══════════════════════════════════════════╝
echo.
echo 🌐 访问地址:
echo    LangGraph:  http://localhost:2024
echo    Gateway:    http://localhost:8001
echo.
echo 📊 服务管理:
echo    查看日志:   docker-compose -f docker/docker-compose-simple.yaml logs -f
echo    停止服务:   stop.bat
echo    重启服务:   docker-compose -f docker/docker-compose-simple.yaml restart
echo.
echo ⏳ 等待服务完全启动 (约 20-40 秒)...
timeout /t 5 /nobreak >nul
echo.
echo 🎯 现在可以访问 API 服务
echo.
exit /r 0

:show_success_local
echo.
echo ╔══════════════════════════════════════════╗
echo ║  ✅ 本地环境启动成功！                  ║
echo ╚══════════════════════════════════════════╝
echo.
echo 🌐 访问地址:
echo    LangGraph:  http://localhost:2024
echo    Gateway:    http://localhost:8001
echo.
echo 📊 已启动服务窗口:
echo    宅力觉醒_LangGraph (LangGraph 服务)
echo    宅力觉醒_Gateway (Gateway API)
echo.
echo 💡 开发提示:
echo    - 修改代码后需在对应窗口按 Ctrl+C 停止并重新启动
echo    - 日志输出在对应的服务窗口中
echo    - 停止所有服务: 关闭窗口或按 Ctrl+C
echo.
exit /b 0

:run_diagnose
echo 🔍 运行网络诊断...
echo.
call check-network.bat
goto :eof

:end
echo.
echo ═════════════════════════════════════════
echo  按任意键返回主菜单...
pause >nul
goto :eof
