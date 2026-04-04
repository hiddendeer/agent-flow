@echo off
REM 网络诊断脚本 - 检查Docker和Python环境

echo ========================================
echo 宅力觉醒智能体 环境诊断工具
echo ========================================
echo.

echo 1. 检查Docker状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行
    echo    请启动Docker Desktop
) else (
    echo ✅ Docker正在运行
    docker --version
)
echo.

echo 2. 检查Docker镜像源...
docker info | findstr "Registry" || echo "未找到镜像源配置"
echo.

echo 3. 测试网络连接...
ping -n 1 registry-1.docker.io >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 无法连接Docker Hub
    echo    建议配置国内镜像源
) else (
    echo ✅ Docker Hub连接正常
)
echo.

echo 4. 检查Python环境...
python --version 2>nul || echo ❌ Python未安装
where uv 2>nul || echo ❌ uv包管理器未安装
echo.

echo 5. 检查配置文件...
if exist config.yaml (
    echo ✅ config.yaml 存在
) else (
    echo ❌ config.yaml 缺失
)

if exist .env (
    echo ✅ .env 存在
) else (
    echo ❌ .env 缺失
)
echo.

echo 6. 推荐解决方案...
echo.
echo 如果Docker无法连接：
echo 1. 打开Docker Desktop
echo 2. 进入设置 → Docker Engine
echo 3. 添加以下配置：
echo    {
echo      "registry-mirrors": [
echo        "https://docker.mirrors.ustc.edu.cn",
echo        "https://mirror.ccs.tencentyun.com"
echo      ]
echo    }
echo 4. 点击 "Apply & restart"
echo.
echo ========================================
pause
