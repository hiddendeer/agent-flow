# DeerFlow Windows 启动指南

## 🚀 快速启动

### 方法1: 使用启动脚本（推荐）

1. **双击运行** `check-network.bat` 检查环境
2. **双击运行** `start.bat` 启动服务
3. 访问 http://localhost:2026

### 方法2: 手动启动

```bash
# 1. 检查Docker是否运行
docker info

# 2. 设置环境变量
set DEER_FLOW_ROOT=e:/EMS/agent-flow

# 3. 启动服务
docker-compose -f docker/docker-compose-lite.yaml up -d --build
```

## ⚙️ 环境要求

- Windows 10/11
- Docker Desktop for Windows
- 至少 4GB RAM
- 至少 10GB 磁盘空间

## 🔧 常见问题

### Q1: Docker无法连接Docker Hub

**解决方案**：配置国内镜像源

1. 打开 **Docker Desktop**
2. 点击 **设置** → **Docker Engine**
3. 添加以下配置：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ],
  "dns": ["8.8.8.8", "114.114.114.114"]
}
```

4. 点击 **"Apply & restart"**

### Q2: 启动失败，提示端口被占用

**检查端口占用**：
```bash
netstat -ano | findstr ":8001"
netstat -ano | findstr ":2024"
netstat -ano | findstr ":2026"
```

**解决方案**：停止占用端口的程序或修改端口配置

### Q3: 服务启动成功但无法访问

**检查服务状态**：
```bash
docker ps
docker logs deer-flow-gateway
docker logs deer-flow-langgraph
```

**查看实时日志**：
```bash
docker logs -f deer-flow-gateway
```

## 📊 服务地址

启动成功后，可以访问：

| 服务 | 地址 | 说明 |
|-----|------|------|
| **主界面** | http://localhost:2026 | Web UI |
| **API文档** | http://localhost:2026/api/docs | Swagger文档 |
| **LangGraph** | http://localhost:2024 | LangGraph Studio |
| **Gateway API** | http://localhost:8001 | REST API |

## 🛑 停止服务

**方法1**: 双击 `stop.bat`

**方法2**: 命令行停止
```bash
docker-compose -f docker/docker-compose-lite.yaml down
```

**清理数据卷**（会删除所有数据）：
```bash
docker-compose -f docker/docker-compose-lite.yaml down -v
```

## 📝 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker/docker-compose-lite.yaml logs

# 查看特定服务日志
docker logs deer-flow-gateway
docker logs deer-flow-langgraph
docker logs deer-flow-nginx

# 实时查看日志
docker logs -f deer-flow-gateway
```

## 🔍 故障排查

### 检查服务状态
```bash
docker ps
```

### 重启特定服务
```bash
docker restart deer-flow-gateway
docker restart deer-flow-langgraph
```

### 重新构建镜像
```bash
docker-compose -f docker/docker-compose-lite.yaml build --no-cache
```

### 查看详细错误信息
```bash
docker-compose -f docker/docker-compose-lite.yaml up --build
```

## 📚 下一步

启动成功后：

1. ✅ 访问 http://localhost:2026
2. ✅ 创建对话测试智能体
3. ✅ 参考 [SMART_HOME_GUIDE.md](SMART_HOME_GUIDE.md) 了解智能家居功能
4. ✅ 配置Home Assistant（可选）

## 🆘 获取帮助

如果遇到问题：

1. 运行 `check-network.bat` 诊断环境
2. 查看日志文件 `logs/` 目录
3. 检查Docker Desktop是否正常运行
4. 确认端口8001、2024、2026未被占用

---

**祝您使用愉快！** 🎉
