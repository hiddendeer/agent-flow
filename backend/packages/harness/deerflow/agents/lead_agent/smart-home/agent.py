"""Smart Home Agent 工厂函数

实现智能家居管理专家智能体的创建逻辑
"""

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from deerflow.agents.lead_agent.prompt import apply_prompt_template
from deerflow.agents.thread_state import ThreadState
from deerflow.config.agents_config import load_agent_config
from deerflow.models import create_chat_model
from deerflow.tools import get_available_tools
from deerflow.agents.middlewares.tool_error_handling_middleware import build_lead_runtime_middlewares


def make_smart_home_agent(config: RunnableConfig):
    """创建智能家居管理专家智能体

    这是智能家居系统的主智能体，负责协调各个专业子智能体：
    - device_controller: 设备控制子智能体
    - scene_manager: 场景管理子智能体
    - security_monitor: 安全监控子智能体
    - energy_optimizer: 能耗优化子智能体

    Args:
        config: 运行时配置，包含以下可选参数：
            - configurable.subagent_enabled: 是否启用子智能体（默认：True）
            - configurable.max_concurrent_subagents: 最大并发子智能体数量（默认：3）
            - configurable.thinking_enabled: 是否启用扩展思考模式（默认：True）
            - configurable.model_name: 模型名称（默认：使用配置文件第一个模型）
            - configurable.is_plan_mode: 是否启用计划模式（默认：True）

    Returns:
        编译后的 Agent 图
    """
    # 解析运行时配置
    cfg = config.get("configurable", {})

    # 加载智能体配置
    agent_config = load_agent_config("smart-home")

    # 模型配置
    thinking_enabled = cfg.get("thinking_enabled", True)
    model_name = cfg.get("model_name") or agent_config.model

    # 子智能体配置
    subagent_enabled = cfg.get("subagent_enabled", True)
    max_concurrent_subagents = cfg.get("max_concurrent_subagents", 3)

    # 计划模式
    is_plan_mode = cfg.get("is_plan_mode", True)

    # 创建模型
    model = create_chat_model(
        name=model_name,
        thinking_enabled=thinking_enabled
    )

    # 获取可用工具
    tools = get_available_tools(
        model_name=model_name,
        subagent_enabled=subagent_enabled
    )

    # 构建中间件链
    middlewares = build_lead_runtime_middlewares(
        lazy_init=True
    )

    # 生成系统提示
    # 加载智能体特定的 SOUL.md
    from deerflow.agents.lead_agent.prompt import load_agent_soul

    custom_soul = load_agent_soul("smart-home")

    system_prompt = apply_prompt_template(
        subagent_enabled=subagent_enabled,
        max_concurrent_subagents=max_concurrent_subagents,
        agent_name="smart-home",
        custom_soul=custom_soul
    )

    # 创建 agent
    agent = create_agent(
        model=model,
        tools=tools,
        middleware=middlewares,
        system_prompt=system_prompt,
        state_schema=ThreadState,
    )

    # 添加记忆保存器
    checkpointer = MemorySaver()

    # 编译 agent
    compiled_agent = agent.compile(checkpointer=checkpointer)

    return compiled_agent


# 导出配置类
from pydantic import BaseModel
from typing import Optional, List


class SmartHomeConfig(BaseModel):
    """智能家居智能体配置"""

    name: str = "smart-home"
    description: str = "智能家居管理专家"
    model: str = "gpt-4o"

    skills: List[str] = [
        "homekit-integration",
        "scene-automation",
        "security-monitoring",
        "energy-management"
    ]

    tool_groups: List[str] = [
        "homekit",
        "mqtt",
        "scene",
        "energy",
        "web"
    ]


__all__ = ["make_smart_home_agent", "SmartHomeConfig"]
