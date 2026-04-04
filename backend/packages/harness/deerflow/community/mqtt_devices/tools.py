"""MQTT 工具实现

使用 LangChain 的 @tool 装饰器定义 MQTT 集成工具
"""

import json
import logging
from typing import Annotated

from langchain.tools import tool

from deerflow.community.mqtt_devices.mqtt_client import get_mqtt_client

logger = logging.getLogger(__name__)


@tool("mqtt_publish", parse_docstring=True)
def mqtt_publish_tool(
    topic: str,
    payload: str,
    qos: int = 1,
    retain: bool = False,
) -> str:
    """发布 MQTT 消息到智能家居设备

    Args:
        topic: MQTT 主题（如 smartthings/livingroom/main/light）
        payload: 消息内容（如 "ON", "OFF", 或 JSON 数据）
        qos: 服务质量等级（0=最多一次, 1=至少一次, 2=恰好一次）
        retain: 是否保留消息（true/false）

    Returns:
        发布结果

    Examples:
        # 控制智能灯
        mqtt_publish(
            topic="zigbee2mqtt/livingroom/light/set",
            payload='{"state": "ON", "brightness": 255}'
        )

        # 控制开关
        mqtt_publish(
            topic="smartthings/plug1/command",
            payload="on"
        )

        # 设置恒温器
        mqtt_publish(
            topic="home/livingroom/climate/set",
            payload='{"temperature": 22, "mode": "heat"}'
        )
    """
    try:
        # 获取 MQTT 客户端
        client = get_mqtt_client()

        # 发布消息
        success = client.publish(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
        )

        if success:
            return json.dumps(
                {
                    "success": True,
                    "topic": topic,
                    "payload": payload,
                    "qos": qos,
                    "retain": retain,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "success": False,
                    "error": "消息发布失败",
                    "topic": topic,
                },
                indent=2,
            )

    except Exception as e:
        logger.exception(f"MQTT 消息发布失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "topic": topic,
            },
            indent=2,
        )


@tool("mqtt_subscribe", parse_docstring=True)
def mqtt_subscribe_tool(
    topic: str,
    duration: int = 60,
) -> str:
    """订阅 MQTT 主题以接收设备消息

    Args:
        topic: MQTT 主题（支持通配符 + 和 #，如 smartthings/+/status）
        duration: 订阅持续时间（秒），默认 60 秒

    Returns:
        订阅期间接收到的消息

    Examples:
        # 订阅设备状态
        mqtt_subscribe(
            topic="zigbee2mqtt/+/availability",
            duration=30
        )

        # 订阅所有传感器数据
        mqtt_subscribe(
            topic="home/sensors/#",
            duration=120
        )
    """
    try:
        # 获取 MQTT 客户端
        client = get_mqtt_client()

        # 订阅主题
        success = client.subscribe(topic)

        if not success:
            return json.dumps(
                {
                    "success": False,
                    "error": "订阅失败",
                    "topic": topic,
                },
                indent=2,
            )

        # 等待接收消息
        import time

        messages = []
        end_time = time.time() + duration

        while time.time() < end_time:
            time.sleep(1)
            new_messages = client.get_messages(clear=True)
            messages.extend(new_messages)

            # 如果接收到消息，可以提前结束
            if messages and len(messages) >= 10:
                break

        return json.dumps(
            {
                "success": True,
                "topic": topic,
                "duration": duration,
                "message_count": len(messages),
                "messages": messages,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception(f"MQTT 订阅失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "topic": topic,
            },
            indent=2,
        )


@tool("mqtt_discover", parse_docstring=True)
def mqtt_discover_tool(
    base_topic: str = "home",
    timeout: int = 10,
) -> str:
    """发现 MQTT 智能家居设备

    Args:
        base_topic: 基础主题（如 home, smartthings, zigbee2mqtt）
        timeout: 发现超时时间（秒）

    Returns:
        发现的设备和主题列表

    Examples:
        # 发现所有家居设备
        mqtt_discover(base_topic="home")

        # 发现 Zigbee 设备
        mqtt_discover(base_topic="zigbee2mqtt")

        # 发现 SmartThings 设备
        mqtt_discover(base_topic="smartthings")
    """
    try:
        # 获取 MQTT 客户端
        client = get_mqtt_client()

        # 订阅基础主题及其子主题
        wildcard_topic = f"{base_topic}/#"

        success = client.subscribe(wildcard_topic)

        if not success:
            return json.dumps(
                {
                    "success": False,
                    "error": "订阅失败",
                    "topic": wildcard_topic,
                },
                indent=2,
            )

        # 等待接收消息
        import time

        discovered = {}  # {topic: [payloads]}
        end_time = time.time() + timeout

        while time.time() < end_time:
            time.sleep(1)
            messages = client.get_messages(clear=True)

            for msg in messages:
                topic = msg["topic"]
                payload = msg["payload"]

                if topic not in discovered:
                    discovered[topic] = []

                discovered[topic].append(payload)

            # 如果发现了足够的设备，可以提前结束
            if len(discovered) >= 20:
                break

        # 取消订阅
        client.unsubscribe(wildcard_topic)

        # 分析发现的设备
        devices = []
        for topic, payloads in discovered.items():
            # 尝试解析设备信息
            device_info = {
                "topic": topic,
                "message_count": len(payloads),
                "last_payload": payloads[-1] if payloads else None,
            }

            # 尝试解析 JSON
            try:
                parsed = json.loads(payloads[-1])
                device_info["parsed_data"] = parsed
            except:
                pass

            devices.append(device_info)

        return json.dumps(
            {
                "success": True,
                "base_topic": base_topic,
                "device_count": len(devices),
                "devices": devices,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception(f"MQTT 设备发现失败: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "base_topic": base_topic,
            },
            indent=2,
        )
