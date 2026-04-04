#!/bin/bash
# DeerFlow 简单对话脚本

echo "=== 宅力觉醒智能体 对话 ==="

# 1. 创建对话线程
echo "1. 创建对话线程..."
THREAD_RESPONSE=$(curl -s -X POST "http://localhost:2024/threads" \
  -H "Content-Type: application/json" \
  -d '{}')

echo $THREAD_RESPONSE | python -c "
import sys, json
data = json.load(sys.stdin)
thread_id = data['thread_id']
print(f'   线程ID: {thread_id}')
print(f'   创建时间: {data[\"created_at\"]}')
"

THREAD_ID=$(echo $THREAD_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['thread_id'])")

# 2. 发送消息
echo ""
echo "2. 发送消息..."
echo "   用户: 你好，请简单介绍一下你自己"

RESPONSE=$(curl -s -X POST "http://localhost:2024/threads/$THREAD_ID/runs" \
  -H "Content-Type: application/json" \
  -d "{
    \"assistant_id\": \"lead_agent\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"你好，请简单介绍一下你自己\"
        }
      ]
    }
  }")

echo ""
echo "3. AI 响应:"
echo $RESPONSE | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # 检查是否有消息内容
    if 'values' in data and 'messages' in data['values']:
        messages = data['values']['messages']
        for msg in messages:
            if msg.get('role') == 'ai':
                content = msg.get('content', '')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            print(f'   AI: {item[\"text\"]}')
                        elif isinstance(item, str):
                            print(f'   AI: {item}')
                else:
                    print(f'   AI: {content}')
    else:
        print('   (响应处理中，请稍候...)')
        print(f'   完整响应: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}')
except Exception as e:
    print(f'   解析响应时出错: {e}')
    print(f'   原始响应: {sys.stdin.read()[:200]}')
"

echo ""
echo "4. 查看对话历史"
curl -s "http://localhost:2024/threads/$THREAD_ID/history?limit=5" | python -c "
import sys, json
data = json.load(sys.stdin)
messages = data.get('messages', [])
for i, msg in enumerate(messages[-5:]):
    role = msg.get('role', 'unknown')
    content = msg.get('content', '')
    if isinstance(content, str):
        print(f'{i+1}. {role}: {content[:100]}...')
    else:
        print(f'{i+1}. {role}: [复杂内容]')
"

echo ""
echo "=== 对话完成 ==="
echo "线程ID: $THREAD_ID"
echo "你可以继续使用这个线程ID进行更多对话"