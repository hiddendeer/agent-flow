#!/usr/bin/env bash
#
# scripts/fix-linux-docker.sh - 一键配置 Linux 上的 Docker 镜像加速源
# 用法: sudo ./scripts/fix-linux-docker.sh

set -e

# ── 检查权限 ──────────────────────────────────────────────────────────────────

if [ "$EUID" -ne 0 ]; then
    echo -e "\033[0;31m请以 root 权限运行此脚本 (使用 sudo)\033[0m"
    exit 1
fi

# ── 配置镜像源 ──────────────────────────────────────────────────────────────

CONFIG_FILE="/etc/docker/daemon.json"
echo -e "\033[0;34m正在配置 Docker 镜像加速源...\033[0m"

mkdir -p /etc/docker

# 这里的镜像列表采用你本地已通的地址
cat > "$CONFIG_FILE" <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

echo -e "\033[0;32m✓ 镜像配置文件已写入: $CONFIG_FILE\033[0m"

# ── 重启 Docker ──────────────────────────────────────────────────────────────

echo -e "\033[0;34m正在重启 Docker 服务以生效...\033[0m"

# 根据不同的发行版尝试重启
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload
    systemctl restart docker
    echo -e "\033[0;32m✓ Docker 服务已通过 systemctl 重启\033[0m"
else
    service docker restart || true
    echo -e "\033[1;33m! 请手动重启 Docker 服务以确保配置生效\033[0m"
fi

# ── 验证结果 ──────────────────────────────────────────────────────────────────

echo -e "\n\033[0;36m==========================================\033[0m"
echo -e "\033[0;36m  当前 Docker 镜像池列表: \033[0m"
docker info | grep -A 5 "Registry Mirrors" || cat "$CONFIG_FILE"
echo -e "\033[0;36m==========================================\033[0m"

echo -e "\n\033[0;32m配置完成！现在你可以尝试在 Linux 上重新运行部署脚本了：\033[0m"
echo -e "\033[1;37m./scripts/deploy-backend-only.sh up\033[0m\n"
