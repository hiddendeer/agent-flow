# DeerFlow Docker部署完整指南

## 📊 问题诊断总结

### 核心问题
- **网络速度极慢**: 下载速度只有几十KB/s
- **连接不稳定**: 频繁超时和重试
- **IPv6解析问题**: DNS优先返回IPv6地址

### 已完成的优化
1. ✅ 配置国内npm镜像源 (registry.npmmirror.com)
2. ✅ 配置国内PyPI镜像源 (pypi.tuna.tsinghua.edu.cn)
3. ✅ 增加pnpm超时和重试配置
4. ✅ Frontend镜像构建成功

### 当前状态
- **Frontend**: ✅ 构建成功 (1.05GB)
- **Backend**: ⏳ 正在构建中 (网络速度慢)
- **Network**: 🐌 下载速度极慢

## 🚀 快速启动方案

### 方案1: 耐心等待 (推荐)
```bash
# 让当前构建继续进行，预计需要15-30分钟
docker compose -f docker-compose-dev.yaml logs -f gateway
```

### 方案2: 停止并重新配置
```bash
# 停止当前构建
docker compose -f docker-compose-dev.yaml down

# 使用优化的启动脚本
./docker-start-china.sh
```

### 方案3: 混合部署 (推荐给开发者)
```bash
# Frontend本地运行，Backend使用Docker
cd backend
make dev

# 另一个终端
cd frontend
pnpm dev
```

## 🔧 网络优化配置

### 1. Docker镜像加速器
在Docker Desktop中配置:
```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.nju.edu.cn",
    "https://docker.1ms.run"
  ]
}
```

### 2. 容器DNS配置
在docker-compose-dev.yaml中添加:
```yaml
services:
  frontend:
    dns:
      - 8.8.8.8
      - 114.114.114.114
```

### 3. IPv6禁用 (可选)
```bash
# 在Windows中禁用IPv6
# 网络适配器设置 → 属性 → 取消勾选IPv6
```

## 📋 常用命令

### 查看构建状态
```bash
docker compose -f docker-compose-dev.yaml ps
docker compose -f docker-compose-dev.yaml logs -f
```

### 重启服务
```bash
docker compose -f docker-compose-dev.yaml restart
```

### 清理和重新构建
```bash
docker compose -f docker-compose-dev.yaml down
docker system prune -a
docker compose -f docker-compose-dev.yaml up --build -d
```

## 💡 最佳实践

1. **首次构建**: 选择网络较好的时间段
2. **开发调试**: 使用本地开发模式 `make dev`
3. **生产部署**: 使用 `make up` 进行优化部署
4. **监控日志**: 实时查看构建进度
5. **网络优化**: 配置代理或VPN

## 🎯 总结

**Docker部署是可行的**，但由于网络环境限制，需要：
- ✅ 使用国内镜像源 (已配置)
- ✅ 增加超时和重试 (已配置)
- ⏳ 耐心等待构建完成 (正在进行)
- 🔧 可选的网络优化 (VPN/代理)

**推荐方案**: 等待当前构建完成，或使用本地开发模式。
