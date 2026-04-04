# DeerFlow 精简配置使用指南

本指南说明如何使用精简后的 DeerFlow 配置，该配置移除了占用内存较多的功能，适合通过 MCP 调用外部服务的场景。

## 精简内容

### 已禁用的功能

1. **沙箱工具** - 文件操作功能（bash, ls, read_file, write_file, str_replace, glob, grep）
2. **网页抓取工具** - web_fetch, image_search
3. **网页抓取依赖** - readabilipy, markdownify, tavily-python, firecrawl-py

### 保留的功能

1. **MCP 服务器集成** - 完整保留
2. **网页搜索** - DuckDuckGo 搜索（无 API key 要求）
3. **记忆系统** - 跨会话记忆
4. **子代理系统** - 并行任务处理
5. **核心对话功能** - 意图识别和结果返回

## 配置文件

### 1. config.yaml

主配置文件已精简，禁用的工具已注释掉：

```yaml
# 禁用的工具
# - name: web_fetch
# - name: image_search
# - name: ls, read_file, glob, grep, write_file, str_replace, bash

# 保留的工具
- name: web_search  # DuckDuckGo 搜索
```

### 2. extensions_config.json

MCP 服务器和技能配置，已精简为最小配置：

```json
{
  "mcpServers": {
    "example-mcp-server": {
      "enabled": false
    }
  },
  "skills": {
    "bootstrap": { "enabled": true },
    "research": { "enabled": false },
    "report-generation": { "enabled": false }
    // ... 其他技能已禁用
  }
}
```

**重要**：请修改 `mcpServers` 部分，添加你实际使用的 MCP 服务器配置。

### 3. pyproject.toml

依赖已精简，注释掉了网页抓取相关的依赖：

```toml
# 已禁用的依赖
# "readabilipy>=0.3.0",
# "markdownify>=1.2.2",
# "tavily-python>=0.7.17",
# "firecrawl-py>=1.15.0",

# 保留的依赖
"ddgs>=9.10.0",  # DuckDuckGo 搜索
```

## 使用方式

### 方式 1：使用精简 Docker Compose 配置（推荐）

使用精简的 Docker Compose 配置，只启动必需的服务：

```bash
# 启动服务（无前端 UI，只有 API）
docker-compose -f docker/docker-compose-lite.yaml up --build

# 后台运行
docker-compose -f docker/docker-compose-lite.yaml up -d --build

# 停止服务
docker-compose -f docker/docker-compose-lite.yaml down
```

**访问地址**：
- 统一入口：http://localhost:2026（通过 nginx）
- Gateway API：http://localhost:8001（直接访问）
- LangGraph API：http://localhost:2024（直接访问）

### 方式 2：使用标准 Docker Compose 配置

使用标准的 Docker Compose 配置，但禁用不需要的服务：

```bash
# 启动服务（包括前端 UI）
docker-compose -f docker/docker-compose-dev.yaml up --build

# 后台运行
docker-compose -f docker/docker-compose-dev.yaml up -d --build

# 停止服务
docker-compose -f docker/docker-compose-dev.yaml down
```

**注意**：此配置包含前端服务，如果不需要 UI，可以使用方式 1。

### 方式 3：本地开发模式

在本地直接运行服务（不使用 Docker）：

```bash
# 1. 安装依赖
make install

# 2. 启动所有服务
make dev

# 或者单独启动各个服务
# 终端 1：LangGraph 服务器
cd backend && make dev

# 终端 2：Gateway API
cd backend && make gateway

# 终端 3：前端（可选）
cd frontend && pnpm dev
```

**访问地址**：http://localhost:2026

## 配置 MCP 服务器

在 `extensions_config.json` 中配置你的 MCP 服务器：

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "your-mcp-server-package"],
      "env": {
        "API_KEY": "$YOUR_API_KEY"
      },
      "description": "My custom MCP server"
    }
  },
  "skills": {}
}
```

## 内存占用优化效果

精简配置的预期内存占用：

| 组件 | 原配置 | 精简后 | 节省 |
|------|--------|--------|------|
| 沙箱系统 | ~300MB | ~50MB | ~250MB |
| 网页抓取 | ~100MB | ~0MB | ~100MB |
| 前端服务 | ~200MB | ~0MB | ~200MB |
| provisioner | ~100MB | ~0MB | ~100MB |
| **总计** | **~700MB** | **~250MB** | **~450MB** |

*实际占用可能因配置和使用情况而异*

## 恢复完整功能

如果需要恢复沙箱或网页抓取功能，按以下步骤操作：

### 1. 恢复沙箱工具

编辑 `config.yaml`，取消注释沙箱工具配置：

```yaml
# File operations tools
- name: ls
  group: file:read
  use: deerflow.sandbox.tools:ls_tool

# ... 其他沙箱工具
```

### 2. 恢复网页抓取工具

编辑 `config.yaml`，取消注释网页工具：

```yaml
# Web fetch tool
- name: web_fetch
  group: web
  use: deerflow.community.jina_ai.tools:web_fetch_tool
  timeout: 10

# Image search tool
- name: image_search
  group: web
  use: deerflow.community.image_search.tools:image_search_tool
  max_results: 5
```

### 3. 恢复依赖

编辑 `backend/packages/harness/pyproject.toml`，取消注释依赖：

```toml
dependencies = [
    # ...
    "markdownify>=1.2.2",
    "readabilipy>=0.3.0",
    "tavily-python>=0.7.17",
    "firecrawl-py>=1.15.0",
    # ...
]
```

然后重新安装依赖：

```bash
make install
```

### 4. 重启服务

```bash
# 如果使用 Docker
docker-compose -f docker/docker-compose-lite.yaml restart

# 如果使用本地开发
make stop && make dev
```

## 测试验证

启动服务后，验证功能是否正常：

### 1. 健康检查

```bash
# 检查 Gateway API
curl http://localhost:8001/health

# 检查 LangGraph API
curl http://localhost:2024/ok
```

### 2. 模型列表

```bash
curl http://localhost:8001/api/models
```

### 3. MCP 配置

```bash
curl http://localhost:8001/api/mcp/config
```

### 4. 创建对话测试

```bash
curl -X POST http://localhost:2024/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "lead_agent",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "Hello, can you help me?"
        }
      ]
    }
  }'
```

## 故障排查

### 问题 1：依赖安装失败

如果依赖安装失败，可能是因为某些依赖被注释掉了：

```bash
# 手动安装依赖
cd backend
uv sync
```

### 问题 2：MCP 服务器连接失败

检查 MCP 服务器配置是否正确：

```bash
# 查看 MCP 配置
curl http://localhost:8001/api/mcp/config

# 查看日志
docker-compose -f docker/docker-compose-lite.yaml logs gateway
```

### 问题 3：内存占用仍然很高

检查是否有其他容器在运行：

```bash
# 查看所有容器
docker ps -a

# 停止不需要的容器
docker stop <container_id>
```

## 进一步优化

如果还需要进一步减少内存占用，可以考虑：

1. **禁用记忆系统**：在 `config.yaml` 中设置 `memory.enabled: false`
2. **禁用子代理**：在运行时设置 `subagent_enabled: false`
3. **禁用 IM 渠道**：在 `config.yaml` 中设置所有 `channels.*.enabled: false`
4. **使用更小的模型**：配置更轻量的 LLM 模型

## 总结

精简配置适合以下场景：
- ✅ 通过 MCP 调用外部服务
- ✅ 只需 API，不需要前端 UI
- ✅ 内存资源受限的环境
- ✅ 不需要文件操作和网页抓取功能

如果需要这些功能，请参考"恢复完整功能"部分。
