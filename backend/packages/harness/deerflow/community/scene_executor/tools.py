"""场景执行工具

提供场景的创建、执行和管理功能
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool("execute_scene", parse_docstring=True)
def execute_scene_tool(
    scene_name: str,
    devices: str | None = None,
    wait_time: int = 5,
) -> str:
    """执行智能家居场景

    Args:
        scene_name: 场景名称（如 "回家模式", "睡眠模式", "观影模式"）
        devices: 设备列表的 JSON 字符串（可选，格式见示例）
        wait_time: 等待所有设备完成的超时时间（秒）

    Returns:
        场景执行结果

    Examples:
        # 执行预设场景
        execute_scene(scene_name="回家模式")

        # 执行自定义场景
        execute_scene(
            scene_name="晚间放松",
            devices=json.dumps([
                {"entity_id": "light.living_room", "state": "on", "brightness": 150},
                {"entity_id": "climate.living_room", "state": "on", "temperature": 23},
                {"entity_id": "media_player.tv", "state": "on"}
            ])
        )
    """
    try:
        # 这里是示例实现，实际应该调用 Home Assistant 或执行具体的场景
        result = {
            "success": True,
            "scene_name": scene_name,
            "executed_at": datetime.now().isoformat(),
            "devices_executed": [],
        }

        # 如果提供了设备列表，执行每个设备
        if devices:
            device_list = json.loads(devices)

            for device in device_list:
                entity_id = device.get("entity_id")
                state = device.get("state")
                attributes = device.get("attributes", {})

                # 模拟设备控制
                result["devices_executed"].append({
                    "entity_id": entity_id,
                    "state": state,
                    "attributes": attributes,
                    "status": "success",
                })

            result["device_count"] = len(device_list)

        # 记录场景执行历史
        scene_history_path = Path("/mnt/user-data/workspace/scenes/history.json")

        try:
            scene_history_path.parent.mkdir(parents=True, exist_ok=True)

            if scene_history_path.exists():
                with open(scene_history_path, "r") as f:
                    history = json.load(f)
            else:
                history = []

            history.append({
                "scene": scene_name,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            })

            with open(scene_history_path, "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.warning(f"场景历史记录失败: {e}")

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.exception(f"场景执行失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "scene_name": scene_name,
            },
            indent=2,
        )


@tool("create_scene", parse_docstring=True)
def create_scene_tool(
    scene_name: str,
    description: str,
    devices: str,
    triggers: str | None = None,
) -> str:
    """创建新的智能家居场景

    Args:
        scene_name: 场景名称（唯一）
        description: 场景描述
        devices: 设备列表的 JSON 字符串
        triggers: 触发器配置的 JSON 字符串（可选）

    Returns:
        场景创建结果

    Examples:
        # 创建回家场景
        create_scene(
            scene_name="回家模式",
            description="回家时自动执行，打开灯光、调温、播放音乐",
            devices=json.dumps([
                {"entity_id": "light.living_room", "state": "on", "brightness": 200},
                {"entity_id": "climate.living_room", "state": "on", "temperature": 22},
                {"entity_id": "media_player.music", "state": "on"}
            ]),
            triggers=json.dumps([
                {"type": "geo", "condition": "arriving", "radius": 500}
            ])
        )
    """
    try:
        device_list = json.loads(devices)
        trigger_list = json.loads(triggers) if triggers else []

        # 创建场景配置
        scene_config = {
            "name": scene_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "devices": device_list,
            "triggers": trigger_list,
        }

        # 保存场景配置
        scene_file_path = Path(f"/mnt/user-data/workspace/scenes/{scene_name}.json")
        scene_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(scene_file_path, "w") as f:
            json.dump(scene_config, f, indent=2)

        return json.dumps(
            {
                "success": True,
                "scene_name": scene_name,
                "scene_file": str(scene_file_path),
                "device_count": len(device_list),
                "trigger_count": len(trigger_list),
            },
            indent=2,
        )

    except Exception as e:
        logger.exception(f"场景创建失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "scene_name": scene_name,
            },
            indent=2,
        )


@tool("list_scenes", parse_docstring=True)
def list_scenes_tool(
    category: str | None = None,
) -> str:
    """列出所有可用的场景

    Args:
        category: 场景类别过滤（可选）

    Returns:
        场景列表

    Examples:
        # 列出所有场景
        list_scenes()

        # 列出特定类别的场景
        list_scenes(category="自动化")
    """
    try:
        # 预定义场景模板
        predefined_scenes = {
            "回家模式": {
                "description": "回家时自动执行",
                "category": "预设",
                "devices": [
                    "light.living_room",
                    "climate.living_room",
                    "media_player.music",
                ],
            },
            "离家模式": {
                "description": "离家时自动执行",
                "category": "预设",
                "devices": [
                    "light.all",
                    "climate.off",
                    "security.on",
                ],
            },
            "睡眠模式": {
                "description": "睡前自动执行",
                "category": "预设",
                "devices": [
                    "light.all",
                    "climate.sleep",
                    "security.night",
                ],
            },
            "观影模式": {
                "description": "观看电影时执行",
                "category": "预设",
                "devices": [
                    "cover.living_room",
                    "light.living_room.dim",
                    "media_player.tv",
                ],
            },
        }

        # 查看自定义场景
        scenes_dir = Path("/mnt/user-data/workspace/scenes")

        if scenes_dir.exists():
            custom_scenes = {}
            for scene_file in scenes_dir.glob("*.json"):
                try:
                    with open(scene_file, "r") as f:
                        scene_config = json.load(f)
                        scene_name = scene_config.get("name", scene_file.stem)
                        custom_scenes[scene_name] = scene_config
                except Exception as e:
                    logger.warning(f"加载场景失败 {scene_file}: {e}")

            predefined_scenes.update(custom_scenes)

        # 过滤场景
        if category:
            filtered_scenes = {
                name: scene for name, scene in predefined_scenes.items()
                if scene.get("category") == category
            }
        else:
            filtered_scenes = predefined_scenes

        return json.dumps(
            {
                "success": True,
                "total_count": len(filtered_scenes),
                "scenes": filtered_scenes,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception(f"场景列表获取失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
            },
            indent=2,
        )
