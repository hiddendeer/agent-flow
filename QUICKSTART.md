# 🚀 宅力觉醒智能体 - Windows 快速启动

## 📋 前提条件

- ✅ Windows 10/11
- ✅ Docker Desktop（已安装并运行）
- ✅ 至少 4GB RAM
- ✅ 网络连接（或已配置镜像源）

## 🎯 一键启动（推荐）

### 方式1: 使用修复版启动脚本

```batch
双击运行: start-fixed.bat
```

这个脚本会自动：
- ✅ 检查Docker状态
- ✅ 配置Python镜像源（清华源）
- ✅ 启动所有服务
- ✅ 显示访问地址

### 方式2: 手动启动

```batch
# 1. 设置环境变量
set DEER_FLOW_ROOT=e:/EMS/agent-flow
set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 启动服务
docker-compose -f docker/docker-compose-lite.yaml up -d --build

# 3. 等待30-60秒，然后访问
# http://localhost:2026
```

## 🔍 检查服务状态

### 运行健康检查

```batch
双击运行: health-check.bat
```

### 手动检查

```batch
# 查看容器状态
docker ps

# 查看日志
docker logs deer-flow-gateway
docker logs deer-flow-langgraph

# 实时日志
docker logs -f deer-flow-gateway
```

## 📱 访问地址

启动成功后，访问以下地址：

| 服务 | 地址 | 说明 |
|-----|------|------|
| **🌐 主界面** | http://localhost:2026 | Web UI |
| **📚 API文档** | http://localhost:2026/api/docs | Swagger文档 |
| **🔧 LangGraph** | http://localhost:2024 | LangGraph Studio |
| **⚡ Gateway** | http://localhost:8001 | REST API |

## 🛑 停止服务

```batch
双击运行: stop.bat
```

或手动停止：

```batch
docker-compose -f docker/docker-compose-lite.yaml down
```

## 📊 可用脚本

| 脚本 | 功能 |
|------|------|
| **start-fixed.bat** | 一键启动（推荐） |
| **stop.bat** | 停止所有服务 |
| **health-check.bat** | 检查服务健康状态 |
| **check-network.bat** | 网络诊断 |

## ⚙️ 配置说明

### 已配置的AI模型

系统已配置智谱AI (GLM-4)：

```yaml
模型: glm-4-plus
API: https://open.bigmodel.cn/api/coding/paas/v4
```

API密钥已在 `.env` 文件中配置。

### 智能家居功能

系统包含以下智能家居功能：

- 🏠 **设备控制**: Home Assistant + MQTT设备管理
- 🎬 **场景自动化**: 创建和管理智能场景
- 📹 **安全监控**: 摄像头和传感器监控
- ⚡ **能耗管理**: 电力监测和优化

详细说明请参考：[SMART_HOME_GUIDE.md](SMART_HOME_GUIDE.md)

## 🔧 常见问题

### Q1: 启动失败，端口被占用

**检查端口占用**：
```batch
netstat -ano | findstr ":8001"
netstat -ano | findstr ":2024"
netstat -ano | findstr ":2026"
```

**解决方法**：停止占用端口的程序

### Q2: Docker镜像拉取失败

**解决方法**：配置Docker镜像加速器

1. 打开 Docker Desktop
2. 设置 → Docker Engine
3. 添加配置：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
```
4. Apply & restart

### Q3: 服务启动但无法访问

**可能原因**：
- 服务还在启动中（等待30-60秒）
- 防火墙阻止了连接
- 端口配置错误

**解决方法**：
```batch
# 运行健康检查
health-check.bat

# 查看详细日志
docker logs deer-flow-gateway
```

### Q4: 智能家居功能不工作

智能家居功能需要配置Home Assistant：

1. 复制环境变量模板：
```batch
copy .env.smarthome.example .env.smarthome
```

2. 编辑 `.env.smarthome`，配置Home Assistant和MQTT

3. 使用完整配置启动：
```batch
docker-compose -f docker/docker-compose-smarthome.yaml up -d
```

## 📚 下一步

### 基础测试

1. ✅ 访问 http://localhost:2026
2. ✅ 创建新对话
3. ✅ 发送消息："你好，请介绍一下你自己"
4. ✅ 测试工具调用："今天天气怎么样？"

### 智能家居测试

1. 配置Home Assistant（可选）
2. 测试设备控制："帮我打开客厅的灯"
3. 创建场景："创建一个回家模式"
4. 查看能耗："分析今天的能耗"

详细指南：[SMART_HOME_GUIDE.md](SMART_HOME_GUIDE.md)

## 🆘 获取帮助

遇到问题？

1. 运行 `health-check.bat` 查看服务状态
2. 运行 `check-network.bat` 诊断网络问题
3. 查看日志文件 `logs/` 目录
4. 参考完整文档：[WINDOWS_SETUP.md](WINDOWS_SETUP.md)

---

## 📝 环境信息

- **项目路径**: `e:\EMS\agent-flow`
- **Python镜像**: 清华大学 PyPI 镜像
- **Docker镜像**: 中科大 Docker Hub 镜像
- **AI模型**: 智谱AI GLM-4 Plus

---

**祝您使用愉快！** 🎉
