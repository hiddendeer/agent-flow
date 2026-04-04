"""MQTT 客户端

提供 MQTT 协议通信的客户端实现
"""

import json
import logging
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT 客户端

    提供发布/订阅功能，用于与 MQTT 智能家居设备通信
    """

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        qos: int = 1,
    ):
        """初始化 MQTT 客户端

        Args:
            broker: MQTT broker 地址
            port: MQTT broker 端口（默认 1883）
            username: 用户名（可选）
            password: 密码（可选）
            client_id: 客户端 ID（可选，自动生成）
            qos: 服务质量等级（默认 1）
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.qos = qos

        # 生成客户端 ID
        if not client_id:
            import uuid
            client_id = f"deerflow-mqtt-{uuid.uuid4().hex[:8]}"

        # 创建 MQTT 客户端
        self.client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_disconnect = self._on_disconnect

        # 消息存储
        self.messages: list[dict[str, Any]] = []
        self.message_callback: Optional[Callable[[str, str], None]] = None

        # 连接状态
        self.connected = False

        # 设置用户名和密码
        if username and password:
            self.client.username_pw_set(username, password)

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            logger.info(f"MQTT 客户端连接成功: {self.broker}:{self.port}")
            self.connected = True
        else:
            logger.error(f"MQTT 客户端连接失败: {rc}")
            self.connected = False

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        message = {
            "topic": msg.topic,
            "payload": msg.payload.decode("utf-8"),
            "qos": msg.qos,
            "retain": msg.retain,
        }

        self.messages.append(message)

        # 调用回调函数（如果设置）
        if self.message_callback:
            self.message_callback(msg.topic, message["payload"])

        logger.debug(f"MQTT 消息接收: {msg.topic} -> {message['payload'][:100]}")

    def _on_publish(self, client, userdata, mid):
        """发布确认回调"""
        logger.debug(f"MQTT 消息发布确认: {mid}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        logger.warning(f"MQTT 客户端断开连接: {rc}")
        self.connected = False

    def connect(self) -> bool:
        """连接到 MQTT broker

        Returns:
            连接是否成功
        """
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()

            # 等待连接建立
            import time
            time.sleep(1)

            return self.connected

        except Exception as e:
            logger.error(f"MQTT 连接失败: {e}")
            return False

    def disconnect(self):
        """断开 MQTT 连接"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False

    def publish(
        self,
        topic: str,
        payload: str,
        qos: Optional[int] = None,
        retain: bool = False,
    ) -> bool:
        """发布 MQTT 消息

        Args:
            topic: 主题
            payload: 消息内容
            qos: 服务质量等级（默认使用客户端设置）
            retain: 是否保留消息

        Returns:
            发布是否成功
        """
        if not self.connected:
            logger.error("MQTT 客户端未连接")
            return False

        try:
            qos = qos if qos is not None else self.qos

            info = self.client.publish(
                topic,
                payload=payload,
                qos=qos,
                retain=retain,
            )

            info.wait_for_publish()

            logger.info(f"MQTT 消息发布: {topic} -> {payload[:100]}")

            return True

        except Exception as e:
            logger.error(f"MQTT 消息发布失败: {e}")
            return False

    def subscribe(
        self,
        topic: str,
        qos: int = 1,
        callback: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """订阅 MQTT 主题

        Args:
            topic: 主题（支持通配符 + 和 #）
            qos: 服务质量等级
            callback: 消息回调函数

        Returns:
            订阅是否成功
        """
        if not self.connected:
            logger.error("MQTT 客户端未连接")
            return False

        try:
            self.message_callback = callback

            result, mid = self.client.subscribe(topic, qos=qos)

            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"MQTT 主题订阅成功: {topic}")
                return True
            else:
                logger.error(f"MQTT 主题订阅失败: {topic}")
                return False

        except Exception as e:
            logger.error(f"MQTT 主题订阅异常: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """取消订阅 MQTT 主题

        Args:
            topic: 主题

        Returns:
            取消订阅是否成功
        """
        if not self.connected:
            logger.error("MQTT 客户端未连接")
            return False

        try:
            result, mid = self.client.unsubscribe(topic)

            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"MQTT 主题取消订阅: {topic}")
                return True
            else:
                logger.error(f"MQTT 主题取消订阅失败: {topic}")
                return False

        except Exception as e:
            logger.error(f"MQTT 主题取消订阅异常: {e}")
            return False

    def get_messages(self, clear: bool = True) -> list[dict[str, Any]]:
        """获取接收到的消息

        Args:
            clear: 是否清除已获取的消息

        Returns:
            消息列表
        """
        messages = self.messages.copy()

        if clear:
            self.messages.clear()

        return messages


# 全局 MQTT 客户端实例（单例）
_mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """获取 MQTT 客户端单例

    Returns:
        MQTTClient 实例
    """
    global _mqtt_client

    if _mqtt_client is None:
        from deerflow.config.app_config import get_app_config

        config = get_app_config()

        # 从环境变量或配置获取 MQTT 参数
        import os

        mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        mqtt_username = os.getenv("MQTT_USERNAME")
        mqtt_password = os.getenv("MQTT_PASSWORD")

        _mqtt_client = MQTTClient(
            broker=mqtt_broker,
            port=mqtt_port,
            username=mqtt_username,
            password=mqtt_password,
        )

        # 连接到 broker
        _mqtt_client.connect()

    return _mqtt_client
