import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.gateway.config import get_gateway_config
from app.gateway.deps import langgraph_runtime
from app.gateway.routers import (
    agents,
    artifacts,
    assistants_compat,
    channels,
    mcp,
    memory,
    models,
    runs,
    skills,
    suggestions,
    thread_runs,
    threads,
    uploads,
)
from deerflow.config.app_config import get_app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""

    # Load config and check necessary environment variables at startup
    try:
        get_app_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        error_msg = f"Failed to load configuration during gateway startup: {e}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg) from e
    config = get_gateway_config()
    logger.info(f"Starting API Gateway on {config.host}:{config.port}")

    # Initialize LangGraph runtime components (StreamBridge, RunManager, checkpointer, store)
    async with langgraph_runtime(app):
        logger.info("LangGraph runtime initialised")

        # Start IM channel service if any channels are configured
        try:
            from app.channels.service import start_channel_service

            channel_service = await start_channel_service()
            logger.info("Channel service started: %s", channel_service.get_status())
        except Exception:
            logger.exception("No IM channels configured or channel service failed to start")

        yield

        # Stop channel service on shutdown
        try:
            from app.channels.service import stop_channel_service

            await stop_channel_service()
        except Exception:
            logger.exception("Failed to stop channel service")

    logger.info("Shutting down API Gateway")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    config = get_gateway_config()

    app = FastAPI(
        title="DeerFlow API 网关",
        description="""
## DeerFlow API 网关

DeerFlow 的 API 网关 - 基于 LangGraph 的 AI Agent 后端，具备沙箱执行能力。

### 主要功能

- **模型管理**：查询和检索可用的 AI 模型
- **MCP 配置**：管理模型上下文协议 (MCP) 服务器配置
- **记忆管理**：访问和管理全局记忆数据，用于个性化对话
- **技能管理**：查询和管理技能及其启用状态
- **产物管理**：访问线程产物和生成的文件
- **健康监测**：系统健康检查接口

### 架构说明

LangGraph 请求由 nginx 反向代理处理。
此网关为模型、MCP 配置、技能和产物提供自定义接口。
        """,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if config.docs_enabled else None,
        redoc_url="/redoc" if config.docs_enabled else None,
        openapi_url="/openapi.json" if config.docs_enabled else None,
        openapi_tags=[
            {
                "name": "models",
                "description": "查询可用 AI 模型及其配置的操作",
            },
            {
                "name": "mcp",
                "description": "管理模型上下文协议 (MCP) 服务器配置",
            },
            {
                "name": "memory",
                "description": "访问和管理用于个性化对话的全局记忆数据",
            },
            {
                "name": "skills",
                "description": "管理技能及其配置",
            },
            {
                "name": "artifacts",
                "description": "访问和下载线程产物及生成的文件",
            },
            {
                "name": "uploads",
                "description": "上传和管理用于线程的用户文件",
            },
            {
                "name": "threads",
                "description": "管理 DeerFlow 线程本地文件系统数据",
            },
            {
                "name": "agents",
                "description": "创建和管理具有特定配置和提示词的自定义 Agent",
            },
            {
                "name": "suggestions",
                "description": "为对话生成后续问题建议",
            },
            {
                "name": "channels",
                "description": "管理 IM 通道集成（飞书、Slack、Telegram）",
            },
            {
                "name": "assistants-compat",
                "description": "兼容 LangGraph Platform 的助手 API (桩接口)",
            },
            {
                "name": "runs",
                "description": "兼容 LangGraph Platform 的运行生命周期（创建、流式传输、取消）",
            },
            {
                "name": "health",
                "description": "健康检查和系统状态接口",
            },
        ],
    )

    # CORS is handled by nginx - no need for FastAPI middleware

    # Include routers
    # Models API is mounted at /api/models
    app.include_router(models.router)

    # MCP API is mounted at /api/mcp
    app.include_router(mcp.router)

    # Memory API is mounted at /api/memory
    app.include_router(memory.router)

    # Skills API is mounted at /api/skills
    app.include_router(skills.router)

    # Artifacts API is mounted at /api/threads/{thread_id}/artifacts
    app.include_router(artifacts.router)

    # Uploads API is mounted at /api/threads/{thread_id}/uploads
    app.include_router(uploads.router)

    # Thread cleanup API is mounted at /api/threads/{thread_id}
    app.include_router(threads.router)

    # Agents API is mounted at /api/agents
    app.include_router(agents.router)

    # Suggestions API is mounted at /api/threads/{thread_id}/suggestions
    app.include_router(suggestions.router)

    # Channels API is mounted at /api/channels
    app.include_router(channels.router)

    # Assistants compatibility API (LangGraph Platform stub)
    app.include_router(assistants_compat.router)

    # Thread Runs API (LangGraph Platform-compatible runs lifecycle)
    app.include_router(thread_runs.router)

    # Stateless Runs API (stream/wait without a pre-existing thread)
    app.include_router(runs.router)

    @app.get("/health", tags=["health"], summary="健康检查", description="检查服务的运行状态。")
    async def health_check() -> dict:
        """Health check endpoint.

        Returns:
            Service health status information.
        """
        return {"status": "healthy", "service": "deer-flow-gateway"}

    return app


# Create app instance for uvicorn
app = create_app()
