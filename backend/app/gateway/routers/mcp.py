import json
import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from deerflow.config.extensions_config import ExtensionsConfig, get_extensions_config, reload_extensions_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["mcp"])


class McpOAuthConfigResponse(BaseModel):
    """OAuth configuration for an MCP server."""

    enabled: bool = Field(default=True, description="是否启用 OAuth 令牌注入")
    token_url: str = Field(default="", description="OAuth 令牌端点 URL")
    grant_type: Literal["client_credentials", "refresh_token"] = Field(default="client_credentials", description="OAuth 授权类型")
    client_id: str | None = Field(default=None, description="OAuth 客户端 ID")
    client_secret: str | None = Field(default=None, description="OAuth 客户端密钥")
    refresh_token: str | None = Field(default=None, description="OAuth 刷新令牌")
    scope: str | None = Field(default=None, description="OAuth 作用域")
    audience: str | None = Field(default=None, description="OAuth 受众")
    token_field: str = Field(default="access_token", description="包含访问令牌的响应字段")
    token_type_field: str = Field(default="token_type", description="包含令牌类型的响应字段")
    expires_in_field: str = Field(default="expires_in", description="包含过期秒数的响应字段")
    default_token_type: str = Field(default="Bearer", description="响应省略 token_type 时的默认令牌类型")
    refresh_skew_seconds: int = Field(default=60, description="在过期前多少秒刷新")
    extra_token_params: dict[str, str] = Field(default_factory=dict, description="发送到令牌端点的其他表单参数")


class McpServerConfigResponse(BaseModel):
    """Response model for MCP server configuration."""

    enabled: bool = Field(default=True, description="是否启用此 MCP 服务器")
    type: str = Field(default="stdio", description="传输类型：'stdio'、'sse' 或 'http'")
    command: str | None = Field(default=None, description="启动 MCP 服务器的命令（用于 stdio 类型）")
    args: list[str] = Field(default_factory=list, description="传递给命令的参数（用于 stdio 类型）")
    env: dict[str, str] = Field(default_factory=dict, description="MCP 服务器的环境变量")
    url: str | None = Field(default=None, description="MCP 服务器的 URL（用于 sse 或 http 类型）")
    headers: dict[str, str] = Field(default_factory=dict, description="要发送的 HTTP 标头（用于 sse 或 http 类型）")
    oauth: McpOAuthConfigResponse | None = Field(default=None, description="MCP HTTP/SSE 服务器的 OAuth 配置")
    description: str = Field(default="", description="此 MCP 服务器所提供功能的人类可读描述")


class McpConfigResponse(BaseModel):
    """Response model for MCP configuration."""

    mcp_servers: dict[str, McpServerConfigResponse] = Field(
        default_factory=dict,
        description="MCP 服务器名称到配置的映射",
    )


class McpConfigUpdateRequest(BaseModel):
    """Request model for updating MCP configuration."""

    mcp_servers: dict[str, McpServerConfigResponse] = Field(
        ...,
        description="MCP 服务器名称到配置的映射",
    )


@router.get(
    "/mcp/config",
    response_model=McpConfigResponse,
    summary="获取 MCP 配置",
    description="检索当前的模型上下文协议 (MCP) 服务器配置。",
)
async def get_mcp_configuration() -> McpConfigResponse:
    """Get the current MCP configuration.

    Returns:
        The current MCP configuration with all servers.

    Example:
        ```json
        {
            "mcp_servers": {
                "github": {
                    "enabled": true,
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "ghp_xxx"},
                    "description": "GitHub MCP server for repository operations"
                }
            }
        }
        ```
    """
    config = get_extensions_config()

    return McpConfigResponse(mcp_servers={name: McpServerConfigResponse(**server.model_dump()) for name, server in config.mcp_servers.items()})


@router.put(
    "/mcp/config",
    response_model=McpConfigResponse,
    summary="更新 MCP 配置",
    description="更新模型上下文协议 (MCP) 服务器配置并保存到文件。",
)
async def update_mcp_configuration(request: McpConfigUpdateRequest) -> McpConfigResponse:
    """Update the MCP configuration.

    This will:
    1. Save the new configuration to the mcp_config.json file
    2. Reload the configuration cache
    3. Reset MCP tools cache to trigger reinitialization

    Args:
        request: The new MCP configuration to save.

    Returns:
        The updated MCP configuration.

    Raises:
        HTTPException: 500 if the configuration file cannot be written.

    Example Request:
        ```json
        {
            "mcp_servers": {
                "github": {
                    "enabled": true,
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "$GITHUB_TOKEN"},
                    "description": "GitHub MCP server for repository operations"
                }
            }
        }
        ```
    """
    try:
        # Get the current config path (or determine where to save it)
        config_path = ExtensionsConfig.resolve_config_path()

        # If no config file exists, create one in the parent directory (project root)
        if config_path is None:
            config_path = Path.cwd().parent / "extensions_config.json"
            logger.info(f"No existing extensions config found. Creating new config at: {config_path}")

        # Load current config to preserve skills configuration
        current_config = get_extensions_config()

        # Convert request to dict format for JSON serialization
        config_data = {
            "mcpServers": {name: server.model_dump() for name, server in request.mcp_servers.items()},
            "skills": {name: {"enabled": skill.enabled} for name, skill in current_config.skills.items()},
        }

        # Write the configuration to file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"MCP configuration updated and saved to: {config_path}")

        # NOTE: No need to reload/reset cache here - LangGraph Server (separate process)
        # will detect config file changes via mtime and reinitialize MCP tools automatically

        # Reload the configuration and update the global cache
        reloaded_config = reload_extensions_config()
        return McpConfigResponse(mcp_servers={name: McpServerConfigResponse(**server.model_dump()) for name, server in reloaded_config.mcp_servers.items()})

    except Exception as e:
        logger.error(f"Failed to update MCP configuration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update MCP configuration: {str(e)}")
