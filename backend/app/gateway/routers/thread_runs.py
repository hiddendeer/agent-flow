"""Runs endpoints — create, stream, wait, cancel.

Implements the LangGraph Platform runs API on top of
:class:`deerflow.agents.runs.RunManager` and
:class:`deerflow.agents.stream_bridge.StreamBridge`.

SSE format is aligned with the LangGraph Platform protocol so that
the ``useStream`` React hook from ``@langchain/langgraph-sdk/react``
works without modification.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.gateway.deps import get_checkpointer, get_run_manager, get_stream_bridge
from app.gateway.services import sse_consumer, start_run
from deerflow.runtime import RunRecord, serialize_channel_values

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/threads", tags=["runs"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RunCreateRequest(BaseModel):
    assistant_id: str | None = Field(default=None, description="要使用的 Agent / 助手 ID")
    input: dict[str, Any] | None = Field(default=None, description="图输入（例如 {messages: [...]})")
    command: dict[str, Any] | None = Field(default=None, description="LangGraph 命令")
    metadata: dict[str, Any] | None = Field(default=None, description="运行元数据")
    config: dict[str, Any] | None = Field(default=None, description="RunnableConfig 覆盖配置")
    context: dict[str, Any] | None = Field(default=None, description="DeerFlow 上下文覆盖配置 (model_name, thinking_enabled 等)")
    webhook: str | None = Field(default=None, description="完成后的回调 URL")
    checkpoint_id: str | None = Field(default=None, description="从指定检查点恢复")
    checkpoint: dict[str, Any] | None = Field(default=None, description="完整的检查点对象")
    interrupt_before: list[str] | Literal["*"] | None = Field(default=None, description="在这些节点之前中断")
    interrupt_after: list[str] | Literal["*"] | None = Field(default=None, description="在这些节点之后中断")
    stream_mode: list[str] | str | None = Field(default=None, description="流模式")
    stream_subgraphs: bool = Field(default=False, description="是否包含子图事件")
    stream_resumable: bool | None = Field(default=None, description="SSE 可恢复模式")
    on_disconnect: Literal["cancel", "continue"] = Field(default="cancel", description="SSE 断开连接时的行为")
    on_completion: Literal["delete", "keep"] = Field(default="keep", description="完成后是否删除临时线程")
    multitask_strategy: Literal["reject", "rollback", "interrupt", "enqueue"] = Field(default="reject", description="并发策略")
    after_seconds: float | None = Field(default=None, description="延迟执行秒数")
    if_not_exists: Literal["reject", "create"] = Field(default="create", description="线程创建策略")
    feedback_keys: list[str] | None = Field(default=None, description="LangSmith 反馈键")


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    assistant_id: str | None = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    multitask_strategy: str = "reject"
    created_at: str = ""
    updated_at: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _record_to_response(record: RunRecord) -> RunResponse:
    return RunResponse(
        run_id=record.run_id,
        thread_id=record.thread_id,
        assistant_id=record.assistant_id,
        status=record.status.value,
        metadata=record.metadata,
        kwargs=record.kwargs,
        multitask_strategy=record.multitask_strategy,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{thread_id}/runs",
    response_model=RunResponse,
    summary="创建运行 (后台)",
    description="在后台创建一个运行并立即返回。",
)
async def create_run(thread_id: str, body: RunCreateRequest, request: Request) -> RunResponse:
    record = await start_run(body, thread_id, request)
    return _record_to_response(record)


@router.post(
    "/{thread_id}/runs/stream",
    summary="创建运行并流式输出",
    description="创建一个运行，并通过 SSE（Server-Sent Events）流式传输事件。响应包含 Content-Location 标头以匹配协议。",
)
async def stream_run(thread_id: str, body: RunCreateRequest, request: Request) -> StreamingResponse:
    bridge = get_stream_bridge(request)
    run_mgr = get_run_manager(request)
    record = await start_run(body, thread_id, request)

    return StreamingResponse(
        sse_consumer(bridge, record, request, run_mgr),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            # LangGraph Platform includes run metadata in this header.
            # The SDK's _get_run_metadata_from_response() parses it.
            "Content-Location": (f"/api/threads/{thread_id}/runs/{record.run_id}/stream?thread_id={thread_id}&run_id={record.run_id}"),
        },
    )


@router.post(
    "/{thread_id}/runs/wait",
    response_model=dict,
    summary="创建运行并等待完成",
    description="创建一个运行并阻塞直到其完成，返回最终状态。",
)
async def wait_run(thread_id: str, body: RunCreateRequest, request: Request) -> dict:
    record = await start_run(body, thread_id, request)

    if record.task is not None:
        try:
            await record.task
        except asyncio.CancelledError:
            pass

    checkpointer = get_checkpointer(request)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        checkpoint_tuple = await checkpointer.aget_tuple(config)
        if checkpoint_tuple is not None:
            checkpoint = getattr(checkpoint_tuple, "checkpoint", {}) or {}
            channel_values = checkpoint.get("channel_values", {})
            return serialize_channel_values(channel_values)
    except Exception:
        logger.exception("Failed to fetch final state for run %s", record.run_id)

    return {"status": record.status.value, "error": record.error}


@router.get(
    "/{thread_id}/runs",
    response_model=list[RunResponse],
    summary="获取运行列表",
    description="获取指定线程的所有运行记录。",
)
async def list_runs(thread_id: str, request: Request) -> list[RunResponse]:
    run_mgr = get_run_manager(request)
    records = await run_mgr.list_by_thread(thread_id)
    return [_record_to_response(r) for r in records]


@router.get(
    "/{thread_id}/runs/{run_id}",
    response_model=RunResponse,
    summary="获取运行详情",
    description="获取特定运行的详细信息。",
)
async def get_run(thread_id: str, run_id: str, request: Request) -> RunResponse:
    run_mgr = get_run_manager(request)
    record = run_mgr.get(run_id)
    if record is None or record.thread_id != thread_id:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return _record_to_response(record)


@router.post(
    "/{thread_id}/runs/{run_id}/cancel",
    summary="取消运行",
    description="取消正在运行或待处理的任务。action 参数控制是中断还是回滚，wait 参数控制是否同步等待任务停止。",
)
async def cancel_run(
    thread_id: str,
    run_id: str,
    request: Request,
    wait: bool = Query(default=False, description="Block until run completes after cancel"),
    action: Literal["interrupt", "rollback"] = Query(default="interrupt", description="Cancel action"),
) -> Response:
    run_mgr = get_run_manager(request)
    record = run_mgr.get(run_id)
    if record is None or record.thread_id != thread_id:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    cancelled = await run_mgr.cancel(run_id, action=action)
    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail=f"Run {run_id} is not cancellable (status: {record.status.value})",
        )

    if wait and record.task is not None:
        try:
            await record.task
        except asyncio.CancelledError:
            pass
        return Response(status_code=204)

    return Response(status_code=202)


@router.get(
    "/{thread_id}/runs/{run_id}/join",
    summary="加入现有运行流",
    description="加入现有运行的 SSE 消息流。",
)
async def join_run(thread_id: str, run_id: str, request: Request) -> StreamingResponse:
    bridge = get_stream_bridge(request)
    run_mgr = get_run_manager(request)
    record = run_mgr.get(run_id)
    if record is None or record.thread_id != thread_id:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return StreamingResponse(
        sse_consumer(bridge, record, request, run_mgr),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.api_route(
    "/{thread_id}/runs/{run_id}/stream",
    methods=["GET", "POST"],
    response_model=None,
    summary="获取现有运行流或取消并流式输出",
    description="GET 请求用于加入现有流。POST 请求可带 action 参数，用于先取消运行再流式输出剩余缓冲事件。",
)
async def stream_existing_run(
    thread_id: str,
    run_id: str,
    request: Request,
    action: Literal["interrupt", "rollback"] | None = Query(default=None, description="Cancel action"),
    wait: int = Query(default=0, description="Block until cancelled (1) or return immediately (0)"),
):
    run_mgr = get_run_manager(request)
    record = run_mgr.get(run_id)
    if record is None or record.thread_id != thread_id:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Cancel if an action was requested (stop-button / interrupt flow)
    if action is not None:
        cancelled = await run_mgr.cancel(run_id, action=action)
        if cancelled and wait and record.task is not None:
            try:
                await record.task
            except (asyncio.CancelledError, Exception):
                pass
            return Response(status_code=204)

    bridge = get_stream_bridge(request)
    return StreamingResponse(
        sse_consumer(bridge, record, request, run_mgr),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
