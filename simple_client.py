#!/usr/bin/env python3
"""
宅力觉醒智能体 简单交互客户端
使用方法: python simple_client.py
"""

import requests
import json
import sys

GATEWAY_URL = "http://localhost:8001"
LANGGRAPH_URL = "http://localhost:2024"

def create_thread():
    """创建新的对话线程"""
    response = requests.post(f"{LANGGRAPH_URL}/threads", json={})
    return response.json()['thread_id']

def send_message(thread_id, message):
    """发送消息到对话线程"""
    payload = {
        "assistant_id": "lead_agent",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }
    }

    print(f"发送消息: {message}")
    print("等待回复...")

    response = requests.post(
        f"{LANGGRAPH_URL}/threads/{thread_id}/runs/stream",
        json=payload,
        stream=True
    )

    # 处理流式响应
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                if data.get('event') == 'messages/tuple':
                    print("收到回复更新")
                elif data.get('event') == 'end':
                    print("\n对话完成")
            except:
                pass

def get_thread_state(thread_id):
    """获取对话状态"""
    response = requests.get(f"{LANGGRAPH_URL}/threads/{thread_id}/state")
    return response.json()

def main():
    print("=== DeerFlow 简单交互客户端 ===\n")

    # 创建新线程
    print("1. 创建对话线程...")
    thread_id = create_thread()
    print(f"   线程ID: {thread_id}\n")

    # 发送测试消息
    print("2. 发送测试消息...")
    send_message(thread_id, "你好，请简单介绍一下你自己，你能做什么？")

    # 获取对话状态
    print("\n3. 获取对话状态...")
    state = get_thread_state(thread_id)
    if 'values' in state and state['values']:
        messages = state['values'].get('messages', [])
        print(f"   消息数量: {len(messages)}")
        for msg in messages[-3:]:  # 显示最后3条消息
            if msg.get('role') == 'ai':
                print(f"   AI: {msg.get('content', '')[:100]}...")
            elif msg.get('role') == 'user':
                print(f"   用户: {msg.get('content', '')}")

    print(f"\n你可以使用这个线程ID继续对话: {thread_id}")
    print(f"API文档: {GATEWAY_URL}/docs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已退出")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
