@echo off
REM DeerFlow 停止脚本 (Windows)
REM 用法: 双击运行或在CMD中执行

echo ========================================
echo 停止宅力觉醒智能体服务
echo ========================================
echo.

REM 停止服务
docker-compose -f docker/docker-compose-lite.yaml down

echo.
echo ✅ 服务已停止
echo.
echo 📊 清理数据卷 (可选):
echo    docker-compose -f docker/docker-compose-lite.yaml down -v
echo.
pause
