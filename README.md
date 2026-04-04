# 🎮 宅力觉醒智能体 - 2.0

English | [中文](./README_zh.md) | [日本語](./README_ja.md) | [Français](./README_fr.md) | [Русский](./README_ru.md)

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](./backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=node.js&logoColor=white)](./Makefile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

宅力觉醒智能体 is an open-source **super agent harness** that orchestrates **sub-agents**, **memory**, and **sandboxes** to do almost anything — powered by **extensible skills**.

## ✨ 核心特性

- 🤖 **多智能体协作** - 复杂任务自动分解，并行处理
- 🧠 **长期记忆** - 跨会话学习用户偏好和工作模式
- 🔧 **沙盒执行** - 安全的隔离环境，真实的文件系统操作
- 🎯 **可扩展技能** - 内置丰富技能，支持自定义扩展
- 🔌 **MCP 集成** - 支持模型上下文协议服务器
- 💬 **多渠道接入** - Telegram、Slack、飞书等即时通讯集成

## 🚀 快速开始

### 1️⃣ 克隆项目

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
```

### 2️⃣ 配置环境

```bash
# 生成配置文件
make config

# 编辑 config.yaml，配置至少一个模型
# 编辑 .env 文件，设置 API 密钥
```

**最简配置示例** (`config.yaml`)

```yaml
models:
  - name: gpt-4
    display_name: GPT-4
    use: langchain_openai:ChatOpenAI
    model: gpt-4
    api_key: $OPENAI_API_KEY
    max_tokens: 4096
    temperature: 0.7
```

**环境变量配置** (`.env`)

```bash
OPENAI_API_KEY=your-key-here
TAVILY_API_KEY=your-tavily-key  # 网页搜索
```

### 3️⃣ 启动服务

**Windows 用户** - 双击运行启动脚本

```batch
start.bat
```

**Linux/Mac 用户** - 使用 Docker

```bash
make docker-init    # 首次运行，拉取镜像
make docker-start   # 启动服务
```

**本地开发模式**

```bash
make install        # 安装依赖
make dev            # 启动开发服务器
```

### 4️⃣ 访问应用

- 🌐 主界面: `http://localhost:2026`
- 📡 API 文档: `http://localhost:2026/api/docs`
- 🤖 LangGraph: `http://localhost:2024`

## 🏗️ 技术架构

```
宅力觉醒智能体
├── 🧠 思考层 (LangGraph)
│   ├── 主智能体 - 任务规划和协调
│   ├── 子智能体 - 专门任务执行
│   └── 中间件 - 记忆、工具调用、上下文管理
├── 🔧 执行层 (沙盒环境)
│   ├── 文件系统 - 隔离的工作空间
│   ├── 工具集 - 网页搜索、文件操作、代码执行
│   └── MCP 服务器 - 外部能力扩展
├── 💾 记忆层
│   ├── 长期记忆 - 用户偏好和知识积累
│   ├── 会话记忆 - 上下文压缩和摘要
│   └── 技能库 - 可扩展的工作流程
└── 🌐 接入层
    ├── Web 界面 - Next.js 前端
    ├── API 网关 - FastAPI 后端
    └── IM 渠道 - 多平台消息接入
```

## 🎯 核心能力

### 智能任务分解

- 自动识别复杂任务的依赖关系
- 动态创建专门子智能体处理不同方面
- 并行执行和结果综合
- 支持从几分钟到几小时的长任务

### 安全执行环境

- 每个任务独立的文件系统隔离
- 支持本地执行和 Docker 容器执行
- 完整的文件读写、代码执行能力
- 审计日志和资源限制

### 渐进式技能加载

- 按需加载相关技能，保持上下文精简
- 内置研究、报告生成、演示文稿制作等技能
- 支持自定义技能和第三方技能包
- 技能组合和复用

### 智能记忆管理

- 跨会话持久化用户偏好
- 自动提取和存储重要信息
- 去重和置信度评估
- 上下文压缩和摘要

## 🔧 高级配置

### 沙盒模式选择

**本地执行模式** (`config.yaml`)

```yaml
sandbox:
  use: deerflow.sandbox.local:LocalSandboxProvider
  allow_host_bash: false  # 安全考虑默认关闭
```

**Docker 隔离模式**

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  image: enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest
```

### IM 渠道配置

```yaml
channels:
  langgraph_url: http://localhost:2024
  gateway_url: http://localhost:8001

  telegram:
    enabled: true
    bot_token: $TELEGRAM_BOT_TOKEN

  feishu:
    enabled: true
    app_id: $FEISHU_APP_ID
    app_secret: $FEISHU_APP_SECRET
```

### 可观测性集成

**LangSmith 追踪**

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=your-project
```

**Langfuse 追踪**

```bash
LANGFUSE_TRACING=true
LANGFUSE_PUBLIC_KEY=your-key
LANGFUSE_SECRET_KEY=your-secret
```

## 📚 文档

- [贡献指南](CONTRIBUTING.md) - 开发环境搭建
- [配置指南](backend/docs/CONFIGURATION.md) - 详细配置说明
- [架构概览](backend/CLAUDE.md) - 技术架构文档
- [API 参考](backend/docs/API.md) - 后端 API 文档

## ⚠️ 安全说明

宅力觉醒智能体具备系统命令执行、文件操作等高权限能力，**建议部署在本地可信网络环境中**。如需跨网络部署，必须：

1. **IP 白名单** - 配置防火墙规则，限制访问来源
2. **身份认证** - 启用反向代理和强认证机制
3. **网络隔离** - 使用专用 VLAN 隔离部署环境
4. **定期更新** - 及时获取安全功能更新

## 🤝 贡献

欢迎贡献代码和建议！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目基于 [MIT License](./LICENSE) 开源。

## 🙏 致谢

宅力觉醒智能体建立在开源社区的卓越工作之上：

- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM 交互和链式调用框架
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - 多智能体编排框架
- **[Next.js](https://nextjs.org/)** - 现代 Web 应用框架

感谢所有为这个项目做出贡献的开发者！

---

<div align="center">

**[⭐ Star](https://github.com/bytedance/deer-flow)** to support our work!

</div>
