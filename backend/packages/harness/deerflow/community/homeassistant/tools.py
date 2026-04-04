"""Home Assistant 工具实现

使用 LangChain 的 @tool 装饰器定义 Home Assistant 集成工具
"""

import json
import logging
from typing import Annotated, Any

from langchain.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.community.homeassistant.homekit_client import get_homeassistant_client

logger = logging.getLogger(__name__)


@tool("homeassistant_call_service", parse_docstring=True)
async def homeassistant_call_service_tool(
    domain: str,
    service: str,
    tool_call_id: Annotated[str, "tool_call_id"],  # type: ignore
    entity_id: str | None = None,
    service_data: str | None = None,
) -> str:
    """调用 Home Assistant 服务来控制设备

    Args:
        domain: 服务域名（如 light, switch, climate, scene）
        service: 服务名称（如 turn_on, turn_off, set_temperature, turn_on）
        entity_id: 目标实体 ID（如 light.living_room, climate.bedroom）。如果是批量操作，可以为空
        service_data: 服务参数的 JSON 字符串（可选，如 {"brightness": 255, "color_temp": 400}）

    Returns:
        服务调用结果

    Examples:
        # 打开客厅灯
        homeassistant_call_service(
            domain="light",
            service="turn_on",
            entity_id="light.living_room",
            service_data='{"brightness": 255}'
        )

        # 关闭所有灯
        homeassistant_call_service(
            domain="light",
            service="turn_off",
            entity_id="light.all"
        )

        # 执行回家场景
        homeassistant_call_service(
            domain="scene",
            service="turn_on",
            entity_id="scene.home_arrival"
        )
    """
    try:
        # 获取 Home Assistant 客户端
        client = get_homeassistant_client()

        # 解析服务数据
        data: dict[str, Any] = {}
        if service_data:
            try:
                data = json.loads(service_data)
            except json.JSONDecodeError as e:
                return f"错误: service_data 不是有效的 JSON: {e}"

        # 调用服务
        result = await client.call_service(
            domain=domain,
            service=service,
            service_data=data,
            entity_id=entity_id,
        )

        # 格式化返回结果
        return json.dumps(
            {
                "success": True,
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
                "result": result,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception(f"Home Assistant 服务调用失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
            },
            indent=2,
        )


@tool("homeassistant_get_state", parse_docstring=True)
async def homeassistant_get_state_tool(
    entity_id: str,
    tool_call_id: Annotated[str, "tool_call_id"],  # type: ignore
) -> str:
    """获取 Home Assistant 实体的当前状态

    Args:
        entity_id: 实体 ID（如 light.living_room, sensor.temperature, switch.bedroom_fan）

    Returns:
        实体状态信息

    Examples:
        # 查询客厅灯状态
        homeassistant_get_state(entity_id="light.living_room")

        # 查询温度传感器
        homeassistant_get_state(entity_id="sensor.kitchen_temperature")
    """
    try:
        # 获取 Home Assistant 客户端
        client = get_homeassistant_client()

        # 获取状态
        state = await client.get_state(entity_id=entity_id)

        # 提取关键信息
        result = {
            "success": True,
            "entity_id": entity_id,
            "state": state.get("state"),
            "attributes": state.get("attributes", {}),
            "last_changed": state.get("last_changed"),
            "last_updated": state.get("last_updated"),
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.exception(f"Home Assistant 状态查询失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "entity_id": entity_id,
            },
            indent=2,
        )


@tool("homeassistant_get_entities", parse_docstring=True)
async def homeassistant_get_entities_tool(
    tool_call_id: Annotated[str, "tool_call_id"],  # type: ignore
    domain: str | None = None,
) -> str:
    """获取 Home Assistant 中的实体列表

    Args:
        domain: 过滤域名（可选），如 light, switch, sensor, climate 等。如果不指定，返回所有实体

    Returns:
        实体列表

    Examples:
        # 获取所有灯光实体
        homeassistant_get_entities(domain="light")

        # 获取所有实体
        homeassistant_get_entities()
    """
    try:
        # 获取 Home Assistant 客户端
        client = get_homeassistant_client()

        # 获取实体列表
        entities = await client.get_entities(domain=domain)

        # 按域名分组
        if domain:
            grouped = {domain: entities}
        else:
            grouped = {}
            for entity_id in entities:
                entity_domain = entity_id.split(".")[0]
                if entity_domain not in grouped:
                    grouped[entity_domain] = []
                grouped[entity_domain].append(entity_id)

        return json.dumps(
            {
                "success": True,
                "total_count": len(entities),
                "filtered_domain": domain,
                "entities": grouped,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception(f"Home Assistant 实体查询失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "domain": domain,
            },
            indent=2,
        )
