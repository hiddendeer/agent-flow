# 外部MCP服务器开发指南

本文档介绍如何为DeerFlow系统开发外部MCP (Model Context Protocol) 服务器，以Home Assistant为例提供完整的实现指南。

## 目录

- [MCP协议概述](#mcp协议概述)
- [开发环境准备](#开发环境准备)
- [MCP服务器基础结构](#mcp服务器基础结构)
- [Home Assistant MCP服务器示例](#home-assistant-mcp服务器示例)
- [配置与集成](#配置与集成)
- [测试与调试](#测试与调试)
- [最佳实践](#最佳实践)

## MCP协议概述

MCP (Model Context Protocol) 是一个标准化协议，允许AI应用通过统一的接口访问外部工具和数据源。DeerFlow支持三种传输类型：

### 传输类型

1. **stdio** - 通过标准输入输出通信
   - 适用：本地进程、命令行工具
   - 配置：`command`, `args`, `env`

2. **SSE** - 通过Server-Sent Events通信
   - 适用：长连接、实时推送
   - 配置：`url`, `headers`, `oauth`

3. **HTTP** - 通过HTTP请求通信
   - 适用：REST API、Web服务
   - 配置：`url`, `headers`, `oauth`

## 开发环境准备

### 1. 安装依赖

```bash
# 创建Python虚拟环境
python -m venv mcp-server-env
source mcp-server-env/bin/activate  # Linux/Mac
# 或
mcp-server-env\Scripts\activate  # Windows

# 安装MCP SDK
pip install mcp
```

### 2. 开发工具

```bash
# 推荐安装
pip install pyright  # 类型检查
pip install pytest   # 单元测试
pip install black    # 代码格式化
```

## MCP服务器基础结构

### 最小化示例

```python
#!/usr/bin/env python3
"""简单的MCP服务器示例"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建服务器实例
server = Server("my-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="greet",
            description="向用户打招呼",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要打招呼的名字"
                    }
                },
                "required": ["name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    if name == "greet":
        user_name = arguments.get("name", "世界")
        return [TextContent(
            type="text",
            text=f"你好，{user_name}！"
        )]
    else:
        raise ValueError(f"未知工具: {name}")

async def main():
    """启动服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 关键组件说明

1. **Server实例** - MCP服务器的核心
2. **list_tools()** - 声明可用工具及其参数
3. **call_tool()** - 处理工具调用的逻辑
4. **stdio_server()** - 标准输入输出传输层

## Home Assistant MCP服务器示例

### 完整实现

```python
#!/usr/bin/env python3
"""Home Assistant MCP服务器

提供通过MCP协议访问Home Assistant实体的能力。
"""

import asyncio
import json
import os
from typing import Any
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Home Assistant配置
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

# 创建服务器实例
server = Server("home-assistant-mcp")

class HomeAssistantClient:
    """Home Assistant API客户端"""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def get_states(self) -> dict[str, Any]:
        """获取所有实体状态"""
        response = await self.client.get(
            f"{self.url}/api/states",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """获取单个实体状态"""
        response = await self.client.get(
            f"{self.url}/api/states/{entity_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """调用Home Assistant服务"""
        response = await self.client.post(
            f"{self.url}/api/services/{domain}/{service}",
            headers=self.headers,
            json=service_data or {}
        )
        response.raise_for_status()
        return response.json()

    async def get_history(
        self,
        entity_id: str,
        start_time: str | None = None,
        end_time: str | None = None
    ) -> list[dict[str, Any]]:
        """获取实体历史记录"""
        params = {}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        response = await self.client.get(
            f"{self.url}/api/history/period/{entity_id}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

# 全局HA客户端实例
ha_client: HomeAssistantClient | None = None

def get_ha_client() -> HomeAssistantClient:
    """获取HA客户端实例"""
    global ha_client
    if ha_client is None:
        if not HA_TOKEN:
            raise ValueError("HA_TOKEN环境变量未设置")
        ha_client = HomeAssistantClient(HA_URL, HA_TOKEN)
    return ha_client

@server.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """列出可用的资源（Home Assistant实体）"""
    try:
        client = get_ha_client()
        states = await client.get_states()

        resources = []
        for state in states:
            entity_id = state["entity_id"]
            friendly_name = state.get("attributes", {}).get(
                "friendly_name",
                entity_id
            )

            resources.append({
                "uri": f"ha://{entity_id}",
                "name": friendly_name,
                "description": f"Home Assistant实体: {entity_id}",
                "mimeType": "application/json"
            })

        return resources
    except Exception as e:
        return []

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="ha_get_state",
            description="获取Home Assistant实体的当前状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "实体ID，例如: light.living_room"
                    }
                },
                "required": ["entity_id"]
            }
        ),
        Tool(
            name="ha_call_service",
            description="调用Home Assistant服务控制设备",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "服务域，例如: light, switch, script"
                    },
                    "service": {
                        "type": "string",
                        "description": "服务名称，例如: turn_on, turn_off"
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "目标实体ID"
                    },
                    "service_data": {
                        "type": "object",
                        "description": "服务参数（可选）"
                    }
                },
                "required": ["domain", "service", "entity_id"]
            }
        ),
        Tool(
            name="ha_list_entities",
            description="列出所有可用的Home Assistant实体",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "过滤特定域的实体（可选）"
                    },
                    "state": {
                        "type": "string",
                        "description": "按状态过滤（可选）"
                    }
                }
            }
        ),
        Tool(
            name="ha_get_history",
            description="获取实体的历史状态记录",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "实体ID"
                    },
                    "hours": {
                        "type": "number",
                        "description": "查询最近多少小时的历史（默认24）"
                    }
                },
                "required": ["entity_id"]
            }
        ),
        Tool(
            name="ha_get_weather",
            description="获取Home Assistant天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "weather_entity": {
                        "type": "string",
                        "description": "天气实体ID（可选，默认查找第一个weather实体）"
                    }
                }
            )
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    try:
        client = get_ha_client()

        if name == "ha_get_state":
            entity_id = arguments["entity_id"]
            state = await client.get_state(entity_id)

            return [TextContent(
                type="text",
                text=json.dumps({
                    "entity_id": state["entity_id"],
                    "state": state["state"],
                    "attributes": state.get("attributes", {}),
                    "last_changed": state.get("last_changed"),
                    "last_updated": state.get("last_updated")
                }, indent=2, ensure_ascii=False)
            )]

        elif name == "ha_call_service":
            domain = arguments["domain"]
            service = arguments["service"]
            entity_id = arguments["entity_id"]

            service_data = arguments.get("service_data", {})
            service_data["entity_id"] = entity_id

            result = await client.call_service(domain, service, service_data)

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "service": f"{domain}.{service}",
                    "entity_id": entity_id,
                    "result": result
                }, indent=2, ensure_ascii=False)
            )]

        elif name == "ha_list_entities":
            states = await client.get_states()

            # 应用过滤条件
            domain_filter = arguments.get("domain")
            state_filter = arguments.get("state")

            filtered_states = states
            if domain_filter:
                filtered_states = [
                    s for s in filtered_states
                    if s["entity_id"].startswith(f"{domain_filter}.")
                ]
            if state_filter:
                filtered_states = [
                    s for s in filtered_states
                    if s["state"] == state_filter
                ]

            # 格式化输出
            entities_info = []
            for state in filtered_states:
                friendly_name = state.get("attributes", {}).get(
                    "friendly_name",
                    state["entity_id"]
                )
                entities_info.append({
                    "entity_id": state["entity_id"],
                    "friendly_name": friendly_name,
                    "state": state["state"],
                    "domain": state["entity_id"].split(".")[0]
                })

            return [TextContent(
                type="text",
                text=json.dumps({
                    "total_count": len(entities_info),
                    "entities": entities_info
                }, indent=2, ensure_ascii=False)
            )]

        elif name == "ha_get_history":
            entity_id = arguments["entity_id"]
            hours = arguments.get("hours", 24)

            # 计算时间范围
            end_time = datetime.utcnow()
            start_time = datetime.fromtimestamp(
                end_time.timestamp() - hours * 3600
            )

            history = await client.get_history(
                entity_id,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )

            return [TextContent(
                type="text",
                text=json.dumps({
                    "entity_id": entity_id,
                    "period_hours": hours,
                    "history_count": len(history[0]) if history else 0,
                    "history": history[0] if history else []
                }, indent=2, ensure_ascii=False)
            )]

        elif name == "ha_get_weather":
            # 获取天气实体
            states = await client.get_states()
            weather_entity = arguments.get("weather_entity")

            weather_states = [
                s for s in states
                if s["entity_id"].startswith("weather.")
            ]

            if not weather_states:
                return [TextContent(
                    type="text",
                    text="未找到天气实体"
                )]

            # 选择天气实体
            if weather_entity:
                weather_state = next(
                    (s for s in weather_states
                     if s["entity_id"] == weather_entity),
                    None
                )
            else:
                weather_state = weather_states[0]

            if not weather_state:
                return [TextContent(
                    type="text",
                    text=f"未找到指定的天气实体: {weather_entity}"
                )]

            return [TextContent(
                type="text",
                text=json.dumps({
                    "entity_id": weather_state["entity_id"],
                    "state": weather_state["state"],
                    "temperature": weather_state.get("attributes", {}).get("temperature"),
                    "humidity": weather_state.get("attributes", {}).get("humidity"),
                    "pressure": weather_state.get("attributes", {}).get("pressure"),
                    "wind_speed": weather_state.get("attributes", {}).get("wind_speed"),
                    "forecast": weather_state.get("attributes", {}).get("forecast", [])
                }, indent=2, ensure_ascii=False)
            )]

        else:
            raise ValueError(f"未知工具: {name}")

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"错误: {str(e)}"
        )]

async def main():
    """启动Home Assistant MCP服务器"""
    # 验证环境变量
    if not HA_URL:
        raise ValueError("HA_URL环境变量未设置")
    if not HA_TOKEN:
        raise ValueError("HA_TOKEN环境变量未设置")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 功能说明

这个Home Assistant MCP服务器提供以下功能：

1. **实体状态查询** - 获取设备当前状态
2. **服务调用** - 控制设备（开关灯、调节空调等）
3. **实体列表** - 浏览所有可用的设备和传感器
4. **历史记录** - 查询设备状态变化历史
5. **天气信息** - 获取当前天气和预报

## 配置与集成

### 1. 在DeerFlow中配置

编辑项目根目录的 `extensions_config.json`：

```json
{
  "mcpServers": {
    "home-assistant": {
      "enabled": true,
      "type": "stdio",
      "command": "python",
      "args": [
        "/path/to/ha_mcp_server.py"
      ],
      "env": {
        "HA_URL": "http://homeassistant.local:8123",
        "HA_TOKEN": "$HA_TOKEN"
      },
      "description": "Home Assistant智能家层控制"
    }
  },
  "skills": {}
}
```

### 2. 环境变量设置

在系统或项目根目录的 `.env` 文件中：

```bash
# Home Assistant配置
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6Ik1hZC3...
```

### 3. 重启服务

```bash
# 从项目根目录
make stop
make dev
```

## 测试与调试

### 本地测试MCP服务器

创建测试脚本 `test_ha_mcp.py`：

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_ha_mcp():
    """测试Home Assistant MCP服务器"""

    # 创建服务器连接参数
    server_params = StdioServerParameters(
        command="python",
        args=["ha_mcp_server.py"],
        env={
            "HA_URL": "http://localhost:8123",
            "HA_TOKEN": "your_token_here"
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # 测试实体列表
            result = await session.call_tool("ha_list_entities", {})
            print("\n实体列表:")
            print(result.content[0].text)

            # 测试获取状态
            result = await session.call_tool("ha_get_state", {
                "entity_id": "sun.sun"
            })
            print("\n太阳状态:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_ha_mcp())
```

### 在DeerFlow中测试

启动服务后，在Web界面中：

```
用户: 帮我查看家里所有灯的状态
AI: [使用 ha_list_entities 工具查询 light. 开头的实体]

用户: 打开客厅的灯
AI: [使用 ha_call_service 工具调用 light.turn_on 服务]
```

## 最佳实践

### 1. 错误处理

```python
try:
    result = await client.call_service(domain, service, data)
except httpx.HTTPStatusError as e:
    return [TextContent(
        type="text",
        text=f"HTTP错误: {e.response.status_code} - {e.response.text}"
    )]
except Exception as e:
    return [TextContent(
        type="text",
        text=f"错误: {str(e)}"
    )]
```

### 2. 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ha-mcp-server")

# 在关键操作处添加日志
logger.info(f"调用服务: {domain}.{service} on {entity_id}")
```

### 3. 配置验证

```python
def validate_config() -> None:
    """验证必需的配置"""
    if not HA_URL:
        raise ValueError("HA_URL环境变量未设置")
    if not HA_TOKEN:
        raise ValueError("HA_TOKEN环境变量未设置")

    # 验证URL格式
    if not HA_URL.startswith(("http://", "https://")):
        raise ValueError("HA_URL必须以http://或https://开头")
```

### 4. 性能优化

```python
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_cached_state(entity_id: str) -> dict:
    """缓存实体状态以提高性能"""
    return await client.get_state(entity_id)

# 或使用缓存装饰器
from cachetools import cached, TTLCache

cache = TTLCache(maxsize=100, ttl=60)

@cached(cache)
async def get_state_with_cache(entity_id: str):
    return await client.get_state(entity_id)
```

### 5. 类型注解

```python
from typing import TypedDict

class EntityState(TypedDict):
    entity_id: str
    state: str
    attributes: dict[str, Any]
    last_changed: str
    last_updated: str

async def get_entity_state(entity_id: str) -> EntityState:
    """获取实体状态（带类型注解）"""
    state = await client.get_state(entity_id)
    return EntityState(
        entity_id=state["entity_id"],
        state=state["state"],
        attributes=state.get("attributes", {}),
        last_changed=state["last_changed"],
        last_updated=state["last_updated"]
    )
```

### 6. 文档和注释

```python
def call_service(
    domain: str,
    service: str,
    service_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """调用Home Assistant服务

    Args:
        domain: 服务域（如：light, switch, climate）
        service: 服务名称（如：turn_on, turn_off）
        service_data: 服务参数（如：brightness, color_temp）

    Returns:
        服务调用结果字典

    Raises:
        httpx.HTTPStatusError: HTTP请求失败
        ValueError: 参数无效

    Examples:
        >>> await call_service("light", "turn_on", {
        ...     "entity_id": "light.living_room",
        ...     "brightness": 255
        ... })
    """
    pass
```

## HTTP/SSE MCP服务器

如果需要通过网络提供服务：

### HTTP服务器示例

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.fastmcp import FastMCP
import uvicorn

# 创建FastMCP实例（支持HTTP）
app = FastMCP("ha-http-server")

# 添加工具（与stdio版本相同）
@app.tool()
async def ha_get_state(entity_id: str) -> str:
    """获取实体状态"""
    # 实现逻辑...
    pass

# 启动HTTP服务器
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

### DeerFlow配置

```json
{
  "mcpServers": {
    "home-assistant-http": {
      "enabled": true,
      "type": "http",
      "url": "http://localhost:3000/mcp",
      "description": "Home Assistant HTTP MCP服务器"
    }
  }
}
```

## 安全考虑

1. **令牌安全** - 使用环境变量存储敏感信息
2. **输入验证** - 验证所有用户输入
3. **权限控制** - 限制MCP服务器可访问的实体
4. **日志脱敏** - 避免在日志中记录敏感信息
5. **HTTPS** - 生产环境使用HTTPS连接

## 扩展阅读

- [MCP协议规范](https://modelcontextprotocol.io)
- [Home Assistant API文档](https://developers.home-assistant.io/docs/api/rest/)
- [DeerFlow架构文档](ARCHITECTURE.md)
- [MCP服务器配置](MCP_SERVER.md)

## 社区资源

- [MCP官方示例](https://github.com/modelcontextprotocol)
- [Home Assistant集成](https://www.home-assistant.io/docs/api/)
- [DeerFlow文档](../README.md)

通过本指南，你应该能够为DeerFlow开发功能完整的MCP服务器，实现与各种外部系统的无缝集成。
