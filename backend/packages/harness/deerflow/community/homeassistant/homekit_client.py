"""Home Assistant API 客户端

提供与 Home Assistant REST API 的通信接口
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Home Assistant API 客户端

    与 Home Assistant 的 REST API 进行通信，支持：
    - 调用服务 (call_service)
    - 获取状态 (get_state)
    - 获取实体 (get_entities)
    - 订阅事件 (subscribe_events)
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
    ):
        """初始化 Home Assistant 客户端

        Args:
            base_url: Home Assistant 基础 URL (如 http://localhost:8123)
            token: Home Assistant API 令牌 (长期访问令牌)
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

        # HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        # 同步客户端（用于某些场景）
        self.sync_client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """调用 Home Assistant 服务

        Args:
            domain: 服务域名 (如 light, switch, climate)
            service: 服务名称 (如 turn_on, turn_off, set_temperature)
            service_data: 服务参数
            entity_id: 目标实体 ID (可选)

        Returns:
            服务调用结果

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        # 构建服务 URL
        if entity_id:
            url = f"/api/services/{domain}/{service}"
            service_data["entity_id"] = entity_id
        else:
            url = f"/api/services/{domain}/{service}"

        try:
            response = await self.client.post(url, json=service_data)
            response.raise_for_status()

            result = response.json()

            logger.info(
                f"Home Assistant 服务调用成功: {domain}.{service} -> {entity_id or '批量'}"
            )

            return result

        except httpx.HTTPError as e:
            logger.error(f"Home Assistant 服务调用失败: {e}")
            raise

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """获取实体状态

        Args:
            entity_id: 实体 ID (如 light.living_room)

        Returns:
            实体状态字典

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        url = f"/api/states/{entity_id}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            state = response.json()

            logger.debug(f"Home Assistant 状态查询成功: {entity_id}")

            return state

        except httpx.HTTPError as e:
            logger.error(f"Home Assistant 状态查询失败: {e}")
            raise

    async def get_states(self) -> list[dict[str, Any]]:
        """获取所有实体状态

        Returns:
            所有实体的状态列表

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        url = "/api/states"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            states = response.json()

            logger.info(f"Home Assistant 状态查询成功: 共 {len(states)} 个实体")

            return states

        except httpx.HTTPError as e:
            logger.error(f"Home Assistant 状态查询失败: {e}")
            raise

    async def get_entities(
        self,
        domain: Optional[str] = None,
    ) -> list[str]:
        """获取实体列表

        Args:
            domain: 过滤域名（可选），如 light, switch 等

        Returns:
            实体 ID 列表
        """
        states = await self.get_states()

        if domain:
            entities = [
                state["entity_id"] for state in states
                if state["entity_id"].startswith(f"{domain}.")
            ]
        else:
            entities = [state["entity_id"] for state in states]

        logger.debug(f"Home Assistant 实体查询成功: {len(entities)} 个实体")

        return entities

    async def get_config(self) -> dict[str, Any]:
        """获取 Home Assistant 配置

        Returns:
            配置字典
        """
        url = "/api/config"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            config = response.json()

            return config

        except httpx.HTTPError as e:
            logger.error(f"Home Assistant 配置查询失败: {e}")
            raise

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
        self.sync_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 同步上下文管理器
        self.sync_client.close()


# 全局客户端实例（单例）
_ha_client: Optional[HomeAssistantClient] = None


def get_homeassistant_client() -> HomeAssistantClient:
    """获取 Home Assistant 客户端单例

    Returns:
        HomeAssistantClient 实例
    """
    global _ha_client

    if _ha_client is None:
        from deerflow.config.app_config import get_app_config

        config = get_app_config()

        # 从环境变量或配置获取 Home Assistant URL 和 Token
        import os

        ha_url = os.getenv("HOMEASSISTANT_URL", "http://localhost:8123")
        ha_token = os.getenv("HOMEASSISTANT_TOKEN", "")

        if not ha_token:
            raise ValueError(
                "HOMEASSISTANT_TOKEN 环境变量未设置。"
                "请在 .env 文件中配置 HOMEASSISTANT_TOKEN"
            )

        _ha_client = HomeAssistantClient(
            base_url=ha_url,
            token=ha_token,
        )

    return _ha_client
