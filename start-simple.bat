@echo off
REM DeerFlow 简体环境一键启动脚本 (Windows)
REM 仅启动网关和 Agent 层，不含沙盒(Provisioner)和 WebUI(Frontend/Nginx)
REM 针对国内网络环境自动配置镜像源

echo ============================================
echo   宅力觉醒智能体 简体环境启动 - 国内优化版
echo ============================================
echo.

REM 1. 检查Docker运行状态
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

REM 2. 设置镜像源环境变量
set "APT_MIRROR=mirrors.aliyun.com"
set "UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "UV_IMAGE=enterprise-public-cn-beijing.cr.volces.com/vefaas-public/uv:0.7.20"

REM 若 ghcr.io 访问困难，推荐配置 Docker Desktop 的 registry-mirrors
REM 镜像源可以在 Docker Desktop -> Settings -> Docker Engine 中配置

REM 3. 准备配置文件
if not exist config.yaml (
    echo [警告] config.yaml 不存在，尝试从 config.example.yaml 复制...
    copy config.example.yaml config.yaml
)

if not exist .env (
    echo [提示] .env 不存在，创建基础 .env 文件...
    echo DEER_FLOW_ROOT=%~dp0>.env
)

REM 4. 启动服务
echo [INFO] 开始构建/启动网关和 Agent 层...
echo [INFO] 首次构建视网络情况需要 5-15 分钟
echo.

docker compose -f docker\docker-compose-simple.yaml up --build -d

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   宅力觉醒智能体 启动成功！
    echo ============================================
    echo.
    echo   网关服务地址: http://localhost:8001
    echo   Agent 服务地址 (LangGraph): http://localhost:2024
    echo.
    echo   查看日志: docker compose -f docker\docker-compose-simple.yaml logs -f
    echo   停止服务: docker compose -f docker\docker-compose-simple.yaml down
    echo.
) else (
    echo.
    echo [错误] 启动失败，请检查上方构建日志。
    echo 常见问题：
    echo 1. 网络超时：请在 Docker Desktop 中配置国内镜像源 (如 百度、阿里、中科大等)
    echo 2. 端口冲突：检查 8001 和 2024 端口是否被占用
)

pause
