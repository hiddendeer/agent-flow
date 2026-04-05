"""
DeerFlow Gateway /api/threads/{thread_id}/runs/stream 渐进式并发压力测试
从 1 用户 → 10 用户，验证接口稳定性和并发处理能力。
"""
import asyncio
import httpx
import time
import uuid
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"
# 已知可用的 thread_id（每次请求可带不同 thread_id 模拟多用户）
THREAD_ID = "f74c04e6-bb46-4021-aa77-1d13768d362d"

def make_url(thread_id: str) -> str:
    return f"{BASE_URL}/api/threads/{thread_id}/runs/stream"


async def single_request(client: httpx.AsyncClient, user_id: int, round_id: int):
    """发送单个流式请求并返回 (tag, http_status, duration, error_msg)."""
    # 每个用户用独立 thread_id，避免同一线程的并发冲突策略影响结果
    # 如需模拟"同一线程多用户"，将下行改为 thread_id = THREAD_ID
    thread_id = str(uuid.uuid4())
    url = make_url(thread_id)
    payload = {
        "stream_mode": ["messages"],
        "assistant_id": "lead_agent",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": f"用户{user_id}：验证并发"
                }
            ]
        }
    }

    tag = f"R{round_id}-U{user_id}"
    t0 = time.time()
    now = lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3]

    try:
        async with client.stream(
            "POST", url, json=payload,
            timeout=httpx.Timeout(180.0, connect=10.0),
        ) as resp:
            status = resp.status_code
            if status != 200:
                body = (await resp.aread()).decode(errors="replace")[:300]
                print(f"  [{now()}] {tag} 失败 HTTP {status}: headers={resp.headers} body={body}")
                return tag, status, time.time() - t0, f"HTTP {status}"

            has_error_event = False
            first_byte_logged = False
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if not first_byte_logged:
                    first_byte_logged = True
                    print(f"  [{now()}] {tag} 收到首个事件 (等待 {time.time()-t0:.1f}s)")
                if line.startswith("event:"):
                    evt = line.split(":", 1)[1].strip()
                    if evt == "error":
                        has_error_event = True

            dur = time.time() - t0
            if has_error_event:
                print(f"  [{now()}] {tag} 完成(含SSE error事件) 耗时 {dur:.1f}s")
                return tag, 200, dur, "SSE error event"
            else:
                print(f"  [{now()}] {tag} 成功完成 耗时 {dur:.1f}s")
                return tag, 200, dur, None

    except Exception as e:
        dur = time.time() - t0
        print(f"  [{now()}] {tag} 异常({dur:.1f}s): {e}")
        return tag, None, dur, str(e)


async def run_stage(concurrency: int, stage_no: int):
    """执行一个并发阶段."""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 阶段 {stage_no}：并发 {concurrency} 个用户")
    print(f"{'='*60}")

    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [single_request(client, i, concurrency) for i in range(concurrency)]
        results = await asyncio.gather(*tasks)

    ok     = sum(1 for _, s, _, e in results if s == 200 and e is None)
    sse_err= sum(1 for _, s, _, e in results if s == 200 and e == "SSE error event")
    http_fail = sum(1 for _, s, _, _ in results if s != 200)
    exc    = sum(1 for _, s, _, _ in results if s is None)
    total_dur = max(dur for _, _, dur, _ in results)

    print(f"\n  小结: 成功 {ok} | SSE错误 {sse_err} | HTTP失败 {http_fail} | 异常 {exc}  (最长等待 {total_dur:.1f}s)")
    return concurrency, ok, sse_err, http_fail, exc, total_dur


async def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] === DeerFlow 渐进式并发压力测试 ===")
    print(f"接口: {make_url(THREAD_ID)}")

    # 健康检查
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{BASE_URL}/health")
            print(f"健康检查: {r.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}，仍继续测试")

    stages = [1, 2, 3, 5, 10]
    all_results = []

    for idx, concurrency in enumerate(stages, 1):
        row = await run_stage(concurrency, stage_no=idx)
        all_results.append(row)
        
        c, ok, sse, hf, ex, dur = row
        if ok < concurrency:
            print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] 🚨 检测到请求失败，测试提前结束！")
            break

        if concurrency < stages[-1]:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] 等待 3s 后进入下一阶段...")
            await asyncio.sleep(3)

    # 最终汇总
    print(f"\n{'='*60}")
    print("=== 最终汇总 ===")
    print(f"{'并发':>4} | {'成功':>4} | {'SSE错':>5} | {'HTTP错':>5} | {'异常':>4} | {'最长耗时':>8}")
    print("-"*45)
    for c, ok, sse, hf, ex, dur in all_results:
        print(f"{c:>4} | {ok:>4} | {sse:>5} | {hf:>5} | {ex:>4} | {dur:>7.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
