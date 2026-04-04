#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宅力觉醒智能体 简单对话客户端
"""

import requests
import json
import time

LANGGRAPH_URL = "http://localhost:2024"

def create_thread():
    """创建对话线程"""
    response = requests.post(f"{LANGGRAPH_URL}/threads", json={})
    result = response.json()
    print(f"[OK] 创建线程成功: {result['thread_id']}")
    return result['thread_id']

def send_message(thread_id, message):
    """发送消息"""
    print(f"[USER] {message}")

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

    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/threads/{thread_id}/runs",
            json=payload,
            timeout=120
        )

        result = response.json()
        print("[AI] 处理中...")

        # 等待AI处理
        time.sleep(15)

        # 获取对话历史
        history = get_history(thread_id)
        return history

    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return None

def get_history(thread_id):
    """获取对话历史"""
    try:
        response = requests.get(f"{LANGGRAPH_URL}/threads/{thread_id}/history")
        data = response.json()

        messages = data.get('messages', [])
        ai_messages = [msg for msg in messages if msg.get('role') == 'ai']

        if ai_messages:
            last_ai = ai_messages[-1]
            content = last_ai.get('content', '')

            # 处理不同类型的内容
            if isinstance(content, str):
                print(f"[AI] {content}")
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if 'text' in item:
                            print(f"[AI] {item['text']}")
                    elif isinstance(item, str):
                        print(f"[AI] {item}")
                    else:
                        print(f"[AI] [复杂内容]")
                return content
            return content
        else:
            print("[AI] (处理中...)")
            return None

    except Exception as e:
        print(f"[ERROR] 获取历史失败: {e}")
        return None

def main():
    print("=== DeerFlow 对话 ===\n")

    # 创建线程
    thread_id = create_thread()
    print()

    # 发送测试消息
    send_message(thread_id, "你好，请简单介绍一下你自己")
    print()

    print(f"[INFO] 你的线程ID是: {thread_id}")
    print(f"[INFO] 继续对话: POST {LANGGRAPH_URL}/threads/{thread_id}/runs")
    print("[INFO] API文档: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
