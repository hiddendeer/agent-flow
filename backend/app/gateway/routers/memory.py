"""Memory API router for retrieving and managing global memory data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from deerflow.agents.memory.updater import (
    clear_memory_data,
    create_memory_fact,
    delete_memory_fact,
    get_memory_data,
    import_memory_data,
    reload_memory_data,
    update_memory_fact,
)
from deerflow.config.memory_config import get_memory_config

router = APIRouter(prefix="/api", tags=["memory"])


class ContextSection(BaseModel):
    """Model for context sections (user and history)."""

    summary: str = Field(default="", description="摘要内容")
    updatedAt: str = Field(default="", description="最后更新时间戳")


class UserContext(BaseModel):
    """Model for user context."""

    workContext: ContextSection = Field(default_factory=ContextSection)
    personalContext: ContextSection = Field(default_factory=ContextSection)
    topOfMind: ContextSection = Field(default_factory=ContextSection)


class HistoryContext(BaseModel):
    """Model for history context."""

    recentMonths: ContextSection = Field(default_factory=ContextSection)
    earlierContext: ContextSection = Field(default_factory=ContextSection)
    longTermBackground: ContextSection = Field(default_factory=ContextSection)


class Fact(BaseModel):
    """Model for a memory fact."""

    id: str = Field(..., description="事实的唯一标识符")
    content: str = Field(..., description="事实内容")
    category: str = Field(default="context", description="事实类别")
    confidence: float = Field(default=0.5, description="置信度评分 (0-1)")
    createdAt: str = Field(default="", description="创建时间戳")
    source: str = Field(default="unknown", description="来源线程 ID")
    sourceError: str | None = Field(default=None, description="可选的先前错误或错误方法的描述")


class MemoryResponse(BaseModel):
    """Response model for memory data."""

    version: str = Field(default="1.0", description="记忆架构版本")
    lastUpdated: str = Field(default="", description="最后更新时间戳")
    user: UserContext = Field(default_factory=UserContext)
    history: HistoryContext = Field(default_factory=HistoryContext)
    facts: list[Fact] = Field(default_factory=list)


def _map_memory_fact_value_error(exc: ValueError) -> HTTPException:
    """Convert updater validation errors into stable API responses."""
    if exc.args and exc.args[0] == "confidence":
        detail = "Invalid confidence value; must be between 0 and 1."
    else:
        detail = "Memory fact content cannot be empty."
    return HTTPException(status_code=400, detail=detail)


class FactCreateRequest(BaseModel):
    """Request model for creating a memory fact."""

    content: str = Field(..., min_length=1, description="事实内容")
    category: str = Field(default="context", description="事实类别")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度评分 (0-1)")


class FactPatchRequest(BaseModel):
    """PATCH request model that preserves existing values for omitted fields."""

    content: str | None = Field(default=None, min_length=1, description="事实内容")
    category: str | None = Field(default=None, description="事实类别")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="置信度评分 (0-1)")


class MemoryConfigResponse(BaseModel):
    """Response model for memory configuration."""

    enabled: bool = Field(..., description="记忆是否已启用")
    storage_path: str = Field(..., description="记忆存储文件的路径")
    debounce_seconds: int = Field(..., description="记忆更新的防抖时间")
    max_facts: int = Field(..., description="要存储的最大事实数量")
    fact_confidence_threshold: float = Field(..., description="事实的最小置信度阈值")
    injection_enabled: bool = Field(..., description="是否启用记忆注入")
    max_injection_tokens: int = Field(..., description="记忆注入的最大 Token 数")


class MemoryStatusResponse(BaseModel):
    """Response model for memory status."""

    config: MemoryConfigResponse
    data: MemoryResponse


@router.get(
    "/memory",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="获取记忆数据",
    description="检索当前的全局记忆数据，包括用户上下文、历史记录和事实。",
)
async def get_memory() -> MemoryResponse:
    """Get the current global memory data.

    Returns:
        The current memory data with user context, history, and facts.

    Example Response:
        ```json
        {
            "version": "1.0",
            "lastUpdated": "2024-01-15T10:30:00Z",
            "user": {
                "workContext": {"summary": "Working on DeerFlow project", "updatedAt": "..."},
                "personalContext": {"summary": "Prefers concise responses", "updatedAt": "..."},
                "topOfMind": {"summary": "Building memory API", "updatedAt": "..."}
            },
            "history": {
                "recentMonths": {"summary": "Recent development activities", "updatedAt": "..."},
                "earlierContext": {"summary": "", "updatedAt": ""},
                "longTermBackground": {"summary": "", "updatedAt": ""}
            },
            "facts": [
                {
                    "id": "fact_abc123",
                    "content": "User prefers TypeScript over JavaScript",
                    "category": "preference",
                    "confidence": 0.9,
                    "createdAt": "2024-01-15T10:30:00Z",
                    "source": "thread_xyz"
                }
            ]
        }
        ```
    """
    memory_data = get_memory_data()
    return MemoryResponse(**memory_data)


@router.post(
    "/memory/reload",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="重新加载记忆数据",
    description="从存储文件重新加载记忆数据，刷新内存缓存。",
)
async def reload_memory() -> MemoryResponse:
    """Reload memory data from file.

    This forces a reload of the memory data from the storage file,
    useful when the file has been modified externally.

    Returns:
        The reloaded memory data.
    """
    memory_data = reload_memory_data()
    return MemoryResponse(**memory_data)


@router.delete(
    "/memory",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="清除所有记忆数据",
    description="删除所有保存的记忆数据，并将记忆结构重置为空状态。",
)
async def clear_memory() -> MemoryResponse:
    """Clear all persisted memory data."""
    try:
        memory_data = clear_memory_data()
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to clear memory data.") from exc

    return MemoryResponse(**memory_data)


@router.post(
    "/memory/facts",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="创建记忆事实",
    description="手动创建一个保存的记忆事实。",
)
async def create_memory_fact_endpoint(request: FactCreateRequest) -> MemoryResponse:
    """Create a single fact manually."""
    try:
        memory_data = create_memory_fact(
            content=request.content,
            category=request.category,
            confidence=request.confidence,
        )
    except ValueError as exc:
        raise _map_memory_fact_value_error(exc) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to create memory fact.") from exc

    return MemoryResponse(**memory_data)


@router.delete(
    "/memory/facts/{fact_id}",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="删除记忆事实",
    description="根据事实 ID 删除单个保存的记忆事实。",
)
async def delete_memory_fact_endpoint(fact_id: str) -> MemoryResponse:
    """Delete a single fact from memory by fact id."""
    try:
        memory_data = delete_memory_fact(fact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Memory fact '{fact_id}' not found.") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to delete memory fact.") from exc

    return MemoryResponse(**memory_data)


@router.patch(
    "/memory/facts/{fact_id}",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="更新记忆事实",
    description="根据事实 ID 部分更新单个保存的记忆事实，同时保留省略的字段。",
)
async def update_memory_fact_endpoint(fact_id: str, request: FactPatchRequest) -> MemoryResponse:
    """Partially update a single fact manually."""
    try:
        memory_data = update_memory_fact(
            fact_id=fact_id,
            content=request.content,
            category=request.category,
            confidence=request.confidence,
        )
    except ValueError as exc:
        raise _map_memory_fact_value_error(exc) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Memory fact '{fact_id}' not found.") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to update memory fact.") from exc

    return MemoryResponse(**memory_data)


@router.get(
    "/memory/export",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="导出记忆数据",
    description="将当前的全局记忆数据导出为 JSON，用于备份或传输。",
)
async def export_memory() -> MemoryResponse:
    """Export the current memory data."""
    memory_data = get_memory_data()
    return MemoryResponse(**memory_data)


@router.post(
    "/memory/import",
    response_model=MemoryResponse,
    response_model_exclude_none=True,
    summary="导入记忆数据",
    description="从 JSON 载荷中导入并覆盖当前的全局记忆数据。",
)
async def import_memory(request: MemoryResponse) -> MemoryResponse:
    """Import and persist memory data."""
    try:
        memory_data = import_memory_data(request.model_dump())
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to import memory data.") from exc

    return MemoryResponse(**memory_data)


@router.get(
    "/memory/config",
    response_model=MemoryConfigResponse,
    summary="获取记忆配置",
    description="检索当前记忆系统的配置。",
)
async def get_memory_config_endpoint() -> MemoryConfigResponse:
    """Get the memory system configuration.

    Returns:
        The current memory configuration settings.

    Example Response:
        ```json
        {
            "enabled": true,
            "storage_path": ".deer-flow/memory.json",
            "debounce_seconds": 30,
            "max_facts": 100,
            "fact_confidence_threshold": 0.7,
            "injection_enabled": true,
            "max_injection_tokens": 2000
        }
        ```
    """
    config = get_memory_config()
    return MemoryConfigResponse(
        enabled=config.enabled,
        storage_path=config.storage_path,
        debounce_seconds=config.debounce_seconds,
        max_facts=config.max_facts,
        fact_confidence_threshold=config.fact_confidence_threshold,
        injection_enabled=config.injection_enabled,
        max_injection_tokens=config.max_injection_tokens,
    )


@router.get(
    "/memory/status",
    response_model=MemoryStatusResponse,
    response_model_exclude_none=True,
    summary="获取记忆状态",
    description="在单个请求中检索记忆配置和当前数据。",
)
async def get_memory_status() -> MemoryStatusResponse:
    """Get the memory system status including configuration and data.

    Returns:
        Combined memory configuration and current data.
    """
    config = get_memory_config()
    memory_data = get_memory_data()

    return MemoryStatusResponse(
        config=MemoryConfigResponse(
            enabled=config.enabled,
            storage_path=config.storage_path,
            debounce_seconds=config.debounce_seconds,
            max_facts=config.max_facts,
            fact_confidence_threshold=config.fact_confidence_threshold,
            injection_enabled=config.injection_enabled,
            max_injection_tokens=config.max_injection_tokens,
        ),
        data=MemoryResponse(**memory_data),
    )
