import asyncio
import httpx
import time
import uuid

BASE_URL = "http://127.0.0.1:8001"

async def make_request(client, user_id):
    thread_id = str(uuid.uuid4())
    url = f"{BASE_URL}/api/threads/{thread_id}/runs/stream"
    payload = {
        "stream_mode": ["messages"],
        "assistant_id": "lead_agent",
        "input": {"messages": [{"role": "user", "content": f"User {user_id} prompt"}]}
    }
    
    try:
        async with client.stream("POST", url, json=payload, timeout=60.0) as resp:
            if resp.status_code != 200:
                print(f"User {user_id} failed with HTTP {resp.status_code}")
                return False
                
            has_error = False
            async for line in resp.aiter_lines():
                if line.startswith("event: error"):
                    has_error = True
            
            if has_error:
                print(f"User {user_id} received SSE error (likely Rate Limit)")
                return False
            else:
                print(f"User {user_id} completed successfully")
                return True
    except Exception as e:
        print(f"User {user_id} exception: {e}")
        return False

async def main():
    print("Testing 5 concurrent requests...")
    async with httpx.AsyncClient() as client:
        tasks = [make_request(client, i) for i in range(5)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    print(f"\nResult: {success_count}/5 requests succeeded.")
    
    if success_count < 5:
        print("Conclusion: The system hit the LLM provider's concurrency limit or another error occurred.")
    else:
        print("Conclusion: The system (and LLM provider) successfully handled 5 concurrent requests.")

if __name__ == "__main__":
    asyncio.run(main())
