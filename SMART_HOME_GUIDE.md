# 🏠 智能家居智能体系统 - 完整使用指南

## 🎉 项目完成概览

恭喜！你已经成功创建了一个专业级的智能家居智能体系统！

### 系统架构

```
🦌 Smart Home Manager (主智能体)
    │
    ├── 📱 Device Controller (设备控制子智能体)
    │   ├── Home Assistant API 集成
    │   └── MQTT 设备管理
    │
    ├── 🎬 Scene Manager (场景管理子智能体)
    │   ├── 场景创建和编辑
    │   └── 自动化触发配置
    │
    ├── 🛡️ Security Monitor (安全监控子智能体)
    │   ├── 摄像头监控
    │   ├── 传感器网络
    │   └── 异常检测报警
    │
    └── ⚡ Energy Optimizer (能耗优化子智能体)
        ├── 实时能耗监测
        ├── 能耗模式分析
        └── 节能建议生成
```

### 核心组件

| 组件 | 类型 | 文件位置 | 状态 |
|------|------|----------|------|
| **Smart Home Manager** | 主智能体 | [backend/packages/harness/deerflow/agents/lead_agent/smart-home/](backend/packages/harness/deerflow/agents/lead_agent/smart-home/) | ✅ 已创建 |
| **Device Controller** | 子智能体 | [backend/packages/harness/deerflow/subagents/builtins/device_controller.py](backend/packages/harness/deerflow/subagents/builtins/device_controller.py) | ✅ 已创建 |
| **Scene Manager** | 子智能体 | [backend/packages/harness/deerflow/subagents/builtins/scene_manager.py](backend/packages/harness/deerflow/subagents/builtins/scene_manager.py) | ✅ 已创建 |
| **Security Monitor** | 子智能体 | [backend/packages/harness/deerflow/subagents/builtins/security_monitor.py](backend/packages/harness/deerflow/subagents/builtins/security_monitor.py) | ✅ 已创建 |
| **Energy Optimizer** | 子智能体 | [backend/packages/harness/deerflow/subagents/builtins/energy_optimizer.py](backend/packages/harness/deerflow/subagents/builtins/energy_optimizer.py) | ✅ 已创建 |
| **Home Assistant 集成技能** | 技能 | [skills/custom/home-assistant-integration/](skills/custom/home-assistant-integration/) | ✅ 已创建 |
| **场景自动化技能** | 技能 | [skills/custom/scene-automation/](skills/custom/scene-automation/) | ✅ 已创建 |
| **安全监控技能** | 技能 | [skills/custom/security-monitoring/](skills/custom/security-monitoring/) | ✅ 已创建 |
| **能源管理技能** | 技能 | [skills/custom/energy-management/](skills/custom/energy-management/) | ✅ 已创建 |
| **Home Assistant 工具** | 工具 | [backend/packages/harness/deerflow/community/homeassistant/](backend/packages/harness/deerflow/community/homeassistant/) | ✅ 已创建 |
| **MQTT 设备工具** | 工具 | [backend/packages/harness/deerflow/community/mqtt_devices/](backend/packages/harness/deerflow/community/mqtt_devices/) | ✅ 已创建 |
| **能耗监测工具** | 工具 | [backend/packages/harness/deerflow/community/energy_monitor/](backend/packages/harness/deerflow/community/energy_monitor/) | ✅ 已创建 |
| **场景执行工具** | 工具 | [backend/packages/harness/deerflow/community/scene_executor/](backend/packages/harness/deerflow/community/scene_executor/) | ✅ 已创建 |

---

## 🚀 快速开始

### 方式一：云端部署（推荐）

#### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.smarthome.example .env.smarthome

# 编辑 .env.smarthome，填写关键配置
nano .env.smarthome
```

**必需配置**：
```bash
# Home Assistant Token（必须）
HOMEASSISTANT_TOKEN=your_homeassistant_token_here

# LLM API Key（至少配置一个）
OPENAI_API_KEY=your_openai_api_key
# 或
ANTHROPIC_API_KEY=your_anthropic_api_key

# MQTT 配置（可选，如果使用 MQTT 设备）
MQTT_BROKER=your_mqtt_broker
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

**获取 Home Assistant Token**：
1. 打开 Home Assistant Web 界面（http://localhost:8123）
2. 左侧菜单 → 用户设置（最下方）→ 滚动到底部 → 长期访问令牌
3. 点击"创建令牌"，输入名称（如 "DeerFlow"）
4. 复制生成的 token 到 `.env.smarthome`

#### 2. 启动云端服务

```bash
# 启动所有服务
docker-compose -f docker/docker-compose-smarthome.yaml up -d

# 查看服务状态
docker-compose -f docker/docker-compose-smarthome.yaml ps

# 查看日志
docker-compose -f docker-compose-smarthome.yaml logs -f smart-home
```

#### 3. 访问智能体

- **统一入口**: http://your-server-ip:2026
- **Gateway API**: http://your-server-ip:8001
- **LangGraph API**: http://your-server-ip:2024
- **Home Assistant**: http://your-server-ip:8123

#### 4. 测试连接

```bash
# 测试 Gateway API
curl http://localhost:8001/health

# 测试 LangGraph API
curl http://localhost:2024/ok

# 测试模型列表
curl http://localhost:8001/api/models
```

### 方式二：本地开发模式

#### 1. 安装依赖

```bash
# 安装所有依赖（包括新增的智能家居依赖）
make install
```

这将自动安装：
- `paho-mqtt>=2.0.0` - MQTT 客户端
- `requests>=2.31.0` - HTTP 请求库
- 以及所有 DeerFlow 核心依赖

#### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# Home Assistant
HOMEASSISTANT_URL=http://localhost:8123
HOMEASSISTANT_TOKEN=your_token_here

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# LLM（选择一个）
OPENAI_API_KEY=your_key_here
```

#### 3. 启动服务

```bash
# 启动所有服务
make dev

# 或分别启动
# 终端 1: LangGraph 服务器
cd backend && make dev

# 终端 2: Gateway API
cd backend && make gateway
```

#### 4. 访问智能体

- **开发地址**: http://localhost:2026

---

## 📖 使用示例

### 示例 1：控制 Home Assistant 设备

```
用户: 打开客厅灯

智能体: 我来帮你打开客厅灯。

[调用 homeassistant_call_service]
- domain: light
- service: turn_on
- entity_id: light.living_room

✅ 客厅灯已打开，亮度设置为 100%。
```

### 示例 2：创建自动化场景

```
用户: 帮我创建一个回家场景

智能体: 我来帮你创建回家场景。

[调用 scene_manager 子智能体]
[子智能体使用 create_scene 工具]
- 场景名称: 回家模式
- 设备:
  - light.living_room (打开, 亮度 200)
  - climate.living_room (设置温度 22°C)
  - media_player.music (播放轻松音乐)

✅ 回家场景已创建完成！

场景包含以下操作：
1. 打开客厅灯（亮度 80%）
2. 设置温度到 22°C
3. 播放轻松音乐

触发方式：手动、GPS 到达、语音命令
```

### 示例 3：能耗分析和优化

```
用户: 分析我家今天的能耗情况

智能体: 我来为你分析今天的能耗情况。

[调用 energy_optimizer 子智能体]
[子智能体使用 get_energy_usage 工具]

今日能耗概览：
- 总用电量：18.5 kWh
- 电费成本：14.8 元
- 峰值功率：5.2 kW（18:30）

设备能耗排行：
1. 空调（客厅）- 8.5 kWh (46%)
2. 热水器 - 3.2 kWh (17%)
3. 冰箱 - 2.8 kWh (15%)
4. 照明 - 2.1 kWh (11%)
5. 其他 - 1.9 kWh (11%)

节能建议：
- 傍晚时段用电量较大（42%），建议在此时段适当降低空调功率
- 可以在谷电时段（23点后）运行洗衣机、热水器
- 使用自然光，人走灯灭

需要我帮你制定更详细的节能计划吗？
```

### 示例 4：安全监控

```
用户: 检查安全系统状态

智能体: 我来检查安全系统状态。

[调用 security_monitor 子智能体]
[子智能体使用 homeassistant_get_state 工具检查传感器]

安全系统状态概览：

🟢 安全级别：正常
- 所有系统运行正常
- 无异常活动
- 设备在线率：100%

传感器状态：
- 门窗传感器：✅ 正常
- 运动传感器：✅ 正常
- 烟雾传感器：✅ 正常
- 摄像头：✅ 在线

最近事件：
- 无异常事件
- 上次安全检查：2 小时前

系统运行良好，继续监控中！
```

### 示例 5：MQTT 设备控制

```
用户: 通过 MQTT 控制智能插座

智能体: 我来帮你通过 MQTT 控制智能插座。

[调用 device_controller 子智能体]
[子智能体使用 mqtt_publish 工具]

[发布 MQTT 消息]
- 主题: smartthings/plug1/command
- 消息: ON

✅ 智能插座已打开

如果你想控制其他 MQTT 设备，请告诉我设备的主题和命令。
```

---

## 🔧 配置详解

### 智能体配置

#### 主智能体配置文件

**文件**：[smart-home/config.yaml](backend/packages/harness/deerflow/agents/lead_agent/smart-home/config.yaml)

```yaml
name: smart-home
description: "智能家居管理专家"
model: gpt-4o

skills:
  - home-assistant-integration
  - scene-automation
  - security-monitoring
  - energy-management

tool_groups:
  - homeassistant
  - mqtt
  - scene
  - energy

subagents:
  enabled: true
  max_concurrent: 3
```

#### 子智能体配置

每个子智能体都有自己的配置，详见：
- [device_controller.py](backend/packages/harness/deerflow/subagents/builtins/device_controller.py)
- [scene_manager.py](backend/packages/harness/deerflow/subagents/builtins/scene_manager.py)
- [security_monitor.py](backend/packages/harness/deerflow/subagents/builtins/security_monitor.py)
- [energy_optimizer.py](backend/packages/harness/deerflow/subagents/builtins/energy_optimizer.py)

### 技能配置

**文件**：[extensions_config.json](extensions_config.json)

```json
{
  "skills": {
    "home-assistant-integration": {
      "enabled": true
    },
    "scene-automation": {
      "enabled": true
    },
    "security-monitoring": {
      "enabled": true
    },
    "energy-management": {
      "enabled": true
    }
  }
}
```

### 工具配置

**文件**：[config.yaml](config.yaml) 中的 `tools` 部分

已注册的工具：
- `homeassistant_call_service` - 调用 Home Assistant 服务
- `homeassistant_get_state` - 获取设备状态
- `homeassistant_get_entities` - 列出所有实体
- `mqtt_publish` - 发布 MQTT 消息
- `mqtt_subscribe` - 订阅 MQTT 主题
- `mqtt_discover` - 发现 MQTT 设备
- `get_energy_usage` - 获取能耗数据
- `analyze_energy_pattern` - 分析能耗模式
- `generate_energy_report` - 生成能耗报告
- `execute_scene` - 执行场景
- `create_scene` - 创建场景
- `list_scenes` - 列出场景

---

## 🎯 典型使用场景

### 场景 1：设备控制

```
用户: 打开客厅的灯，把温度调到 23 度

智能体: 好的，我来帮你控制客厅设备。

[调用 homeassistant_call_service x2]
1. 打开客厅灯
2. 设置温度到 23°C

✅ 完成！客厅灯已打开，温度设置为 23°C。
```

### 场景 2：场景创建

```
用户: 我想创建一个"睡眠模式"场景

智能体: 好的，我来帮你创建睡眠模式场景。

[调用 scene_manager 子智能体]
设计场景包含：
1. 关闭所有灯
2. 降低温度到 20°C
3. 开启夜间安防模式

✅ 睡眠模式场景已创建完成！

场景执行步骤：
1. 关闭所有灯泡
2. 设置空调温度为 20°C
3. 启用夜间安防监控
4. 静音所有媒体设备

你可以通过以下方式触发：
- 语音："嘿 Siri，睡眠模式"
- 手动：在 App 中点击
- 自动：每天晚上 23:00
```

### 场景 3：安全监控

```
用户: 查看一下家里的安全状况

智能体: 我来检查家里的安全状况。

[调用 security_monitor 子智能体]
检查所有传感器和摄像头...

🟢 安全系统状态：一切正常

监控状态：
- 客厅摄像头：✅ 在线
- 门窗传感器：✅ 全部关闭
- 运动传感器：✅ 无异常活动
- 烟雾传感器：✅ 正常
- 气体传感器：✅ 正常

最近 24 小时无异常事件，安全系统运行良好。
```

### 场景 4：能耗管理

```
用户: 这个月的电费有多少？

智能体: 我来查询本月的能耗数据。

[调用 energy_optimizer 子智能体]
[子智能体使用 get_energy_usage 和 analyze_energy_pattern]

📊 本月能耗报告：

用电量：550 kWh
电费：440 元
日均用电：18.33 kWh

对比分析：
- 同比去年：↓ 8%
- 环比上月：↓ 3%

节能建议：
1. 继续保持当前节能措施
2. 夏季即将到来，建议提前维护空调
3. 考虑增加光伏发电（如有条件）

需要详细的能耗分析报告吗？
```

---

## 🔌 API 使用指南

### Gateway API 端点

#### 1. 获取模型列表

```bash
curl http://localhost:8001/api/models
```

#### 2. 获取技能列表

```bash
curl http://localhost:8001/api/skills
```

#### 3. 获取能耗数据（通过智能体）

```bash
curl -X POST http://localhost:8001/api/langgraph/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "smart_home",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "获取今日能耗数据"
        }
      ]
    }
  }'
```

### LangGraph API 端点

#### 1. 创建新对话

```bash
curl -X POST http://localhost:2024/threads \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 2. 发送消息

```bash
curl -X POST http://localhost:2024/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "smart_home",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "帮我打开客厅的灯"
        }
      ]
    }
  }'
```

#### 3. 流式响应

```bash
curl -X POST http://localhost:2024/threads/{thread_id}/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "smart_home",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "帮我监控家里的安全状况"
        }
      ]
    }
  }'
```

---

## 🛠️ 自定义和扩展

### 添加新的 Home Assistant 服务

编辑 [config.yaml](config.yaml)，在工具配置中添加：

```yaml
# 添加自定义服务调用
- name: homeassistant_custom_service
  group: homeassistant
  use: deerflow.community.homeassistant.tools:homeassistant_call_service_tool
```

然后在智能体对话中：
```
用户: 调用 Home Assistant 的自定义服务

智能体: 我来调用自定义服务。

[使用 homeassistant_call_service 工具]
- domain: your_custom_domain
- service: your_custom_service
- entity_id: your_device
```

### 添加新的 MQTT 设备

1. 发现 MQTT 设备：
```
用户: 发现我的 MQTT 设备

智能体: [使用 mqtt_discover 工具]
发现到以下 MQTT 设备：
- zigbee2mqtt/bulb2
- zigbee2mqtt/switch3
- smartthings/outlet1
```

2. 控制设备：
```
用户: 打开 zigbee2mqtt/bulb2

智能体: [使用 mqtt_publish 工具]
✅ 设备已打开
```

### 创建自定义技能

1. 在 `skills/custom/` 创建新技能目录
2. 创建 `SKILL.md` 文件
3. 在 [extensions_config.json](extensions_config.json) 中启用技能

详见：[技能开发指南](#自定义技能开发)

---

## 🧪 测试和验证

### 1. 基础功能测试

```bash
# 测试 Home Assistant 连接
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/states

# 测试 MQTT 连接
mosquitto_pub -h localhost -t "test/topic" -m "test message"

# 测试智能体
curl http://localhost:8001/health
```

### 2. 工具功能测试

```python
# 测试 Home Assistant 工具
>>> from deerflow.community.homeassistant.tools import homeassistant_get_state_tool
>>> result = await homeassistant_get_state_tool.invoke({"entity_id": "light.living_room"})
>>> print(result)

# 测试 MQTT 工具
>>> from deerflow.community.mqtt_devices.tools import mqtt_publish_tool
>>> result = mqtt_publish_tool.invoke({
...     "topic": "test/topic",
...     "payload": "test message"
... })
>>> print(result)
```

### 3. 子智能体测试

通过主智能体调用子智能体：
```
用户: 使用设备控制子智能体帮我查看所有灯光状态

智能体: 我来调用设备控制子智能体帮你查看。

[调用 task 工具，subagent_type="device-controller"]
子智能体完成并返回结果...
```

---

## 🐛 故障排查

### 常见问题

#### 1. Home Assistant 连接失败

**问题**：`homeassistant_call_service` 返回连接错误

**解决方案**：
```bash
# 检查 Home Assistant 是否运行
docker ps | grep homeassistant

# 检查网络连接
curl http://localhost:8123/

# 验证 Token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/

# 检查环境变量
docker-compose -f docker/docker-compose-smarthome.yaml exec smart-home env | grep HOMEASSISTANT
```

#### 2. MQTT 连接失败

**问题**：`mqtt_publish` 返回连接错误

**解决方案**：
```bash
# 检查 MQTT broker 是否运行
docker ps | grep mqtt

# 测试 MQTT 连接
mosquitto_pub -h localhost -t "test" -m "test"

# 检查端口
netstat -tuln | grep 1883

# 查看 MQTT 日志
docker-compose -f docker/docker-compose-smarthome.yaml logs mqtt
```

#### 3. 子智能体不执行

**问题**：子智能体没有被调用

**解决方案**：
- 检查 `subagent_enabled` 是否为 `true`
- 确认子智能体已注册到 `BUILTIN_SUBAGENTS`
- 查看智能体日志是否有错误

#### 4. 技能未加载

**问题**：技能没有在系统提示中出现

**解决方案**：
```bash
# 检查技能配置
curl http://localhost:8001/api/skills

# 确保 extensions_config.json 中技能已启用
# 确保 SKILL.md 文件存在且格式正确

# 重启服务
docker-compose -f docker/docker-compose-smarthome.yaml restart smart-home
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker/docker-compose-smarthome.yaml logs -f

# 查看特定服务日志
docker-compose -f docker/docker-compose-smarthome.yaml logs -f smart-home
docker-compose -f docker/docker-compose-smarthome.yaml logs -f homeassistant
docker-compose -f docker-compose-smarthome.yaml logs -f mqtt

# 查看最近 100 行日志
docker-compose -f docker/docker-compose-smarthome.yaml logs --tail=100 smart-home
```

---

## 📊 性能优化

### 内存优化

当前配置已经禁用了沙箱功能，如需进一步优化：

1. **禁用不需要的技能**
   ```json
   {
     "skills": {
       "security-monitoring": {"enabled": false},
       "energy-management": {"enabled": false}
     }
   }
   ```

2. **减少子智能体并发数**
   ```yaml
   # config.yaml
   subagents:
     max_concurrent: 1  # 默认是 3
   ```

3. **使用更小的模型**
   ```yaml
   models:
     - name: smart-home-model
       model: gpt-4o-mini  # 使用更小的模型
   ```

### 性能监控

```bash
# 查看容器资源占用
docker stats

# 查看服务性能
docker-compose -f docker/docker-compose-smarthome.yaml top
```

---

## 🚀 部署到云端

### 前提条件

- 云服务器（推荐配置：2核4G，带宽 5Mbps）
- 域名和 SSL 证书（可选）
- Home Assistant 实例（可本地或云端）

### 部署步骤

#### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 部署代码

```bash
# 克隆代码
git clone https://github.com/your-username/deer-flow.git
cd deer-flow

# 配置环境
cp .env.smarthome.example .env.smarthome
nano .env.smarthome  # 填写配置

# 启动服务
docker-compose -f docker/docker-compose-smarthome.yaml up -d
```

#### 3. 配置域名（可选）

```bash
# 配置 Nginx 反向代理
sudo nano /etc/nginx/sites-available/smarthome
```

#### 4. 配置防火墙

```bash
# 开放必要端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 2026
sudo ufw allow 8123
sudo ufw enable
```

#### 5. 配置 SSL（推荐）

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📚 进阶开发

### 添加新的子智能体

1. 创建配置文件：
```python
# new_subagent.py
from deerflow.subagents.config import SubagentConfig

NEW_SUBAGENT_CONFIG = SubagentConfig(
    name="new-subagent",
    description="新子智能体描述",
    system_prompt="""系统提示内容""",
    tools=None,
    disallowed_tools=["task", "ask_clarification"],
    model="inherit",
    max_turns=30,
    timeout_seconds=900,
)
```

2. 注册到系统：
```python
# __init__.py
from .new_subagent import NEW_SUBAGENT_CONFIG

BUILTIN_SUBAGENTS["new-subagent"] = NEW_SUBAGENT_CONFIG
```

### 创建新的工具集

1. 创建工具目录：
```bash
mkdir -p backend/packages/harness/deerflow/community/my_tools
```

2. 实现工具：
```python
# tools.py
from langchain.tools import tool

@tool("my_custom_tool", parse_docstring=True)
def my_custom_tool(
    param: str,
) -> str:
    """我的自定义工具

    Args:
        param: 参数说明

    Returns:
        执行结果
    """
    # 实现逻辑
    return f"执行结果: {param}"
```

3. 注册到 [config.yaml](config.yaml)

### 创建新的技能

1. 创建技能目录：
```bash
mkdir -p skills/custom/my-skill
```

2. 编写 [SKILL.md](skills/custom/my-skill/SKILL.md)

3. 启用技能：
```bash
# 通过 API 或 extensions_config.json 启用
```

---

## 🔐 安全注意事项

### 安全配置

1. **使用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

2. **API 密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换密钥
   - 不要在代码中硬编码密钥

3. **网络隔离**
   - 使用防火墙
   - 限制访问 IP
   - VLAN 隔离

4. **用户认证**
   - 启用用户认证
   - 使用强密码
   - 定期审查访问权限

### 隐私保护

1. **数据加密**
   - 传输加密（HTTPS/TLS）
   - 存储加密

2. **数据最小化**
   - 只收集必要数据
   - 定期清理过期数据

3. **用户控制**
   - 提供数据删除功能
   - 允许用户导出数据

---

## 📞 支持和资源

### 官方文档

- [DeerFlow GitHub](https://github.com/bytedance/deer-flow)
- [Home Assistant 文档](https://www.home-assistant.io/docs/)
- [MQTT 协议](https://mqtt.org/)

### 社区资源

- [DeerFlow Discussions](https://github.com/bytedance/deer-flow/discussions)
- [Home Assistant Community](https://community.home-assistant.io/)
- [智能家居论坛](https://community.smart-home.com/)

### 常见问题

查看 [FAQ.md](docs/FAQ.md)

---

## 🎓 学习路径

### 初级用户

1. ✅ 阅读[快速开始](#快速开始)
2. ✅ 配置环境变量
3. ✅ 启动服务
4. ✅ 尝试基本对话

### 中级用户

1. ✅ 自定义技能
2. ✅ 添加新工具
3. ✅ 配置子智能体
4. ✅ 优化系统性能

### 高级用户

1. ✅ 深度定制架构
2. ✅ 开发新的集成
3. ✅ 贡献代码到社区
4. ✅ 部署生产环境

---

## 🎉 恭喜！

你现在拥有一个功能完整、架构专业的智能家居智能体系统！

开始探索你的智能家居之旅吧！
