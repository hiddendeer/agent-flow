"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .general_purpose import GENERAL_PURPOSE_CONFIG

# 智能家居专业子智能体
from .device_controller import DEVICE_CONTROLLER_CONFIG
from .scene_manager import SCENE_MANAGER_CONFIG
from .security_monitor import SECURITY_MONITOR_CONFIG
from .energy_optimizer import ENERGY_OPTIMIZER_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "DEVICE_CONTROLLER_CONFIG",
    "SCENE_MANAGER_CONFIG",
    "SECURITY_MONITOR_CONFIG",
    "ENERGY_OPTIMIZER_CONFIG",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    # 智能家居专业子智能体
    "device-controller": DEVICE_CONTROLLER_CONFIG,
    "scene-manager": SCENE_MANAGER_CONFIG,
    "security-monitor": SECURITY_MONITOR_CONFIG,
    "energy-optimizer": ENERGY_OPTIMIZER_CONFIG,
}
