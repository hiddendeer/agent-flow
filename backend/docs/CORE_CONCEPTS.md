# 宅力觉醒智能体 Backend 核心知识点

## 📋 目录

- [架构概览](#架构概览)
- [核心设计思想](#核心设计思想)
- [技术栈](#技术栈)
- [核心组件](#核心组件)
- [记忆系统详解](#记忆系统详解)
- [关键技术点](#关键技术点)
- [项目结构](#项目结构)

---

## 架构概览

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Port 2026)                        │
│                   统一反向代理入口                           │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
    /api/langgraph/*                     │  /api/* (其他)
                │                         │
                ▼                         ▼
    ┌─────────────────────┐   ┌──────────────────────┐
    │  LangGraph Server   │   │   Gateway API         │
    │    (Port 2024)      │   │   FastAPI REST       │
    │                     │   │   (Port 8001)        │
    │ ┌─────────────────┐ │   │                      │
    │ │   Lead Agent    │ │   │  Models, MCP, Skills │
    │ │  ┌───────────┐  │ │   │  Memory, Uploads    │
    │ │  │Middleware │  │ │   │  Artifacts, Threads │
    │ │  │  Chain    │  │ │   └──────────────────────┘
    │ │  └───────────┘  │ │
    │ │  ┌───────────┐  │ │
    │ │  │  Tools    │  │ │
    │ │  └───────────┘  │ │
    │ │  ┌───────────┐  │ │
    │ │  │Subagents  │  │ │
    │ │  └───────────┘  │ │
    │ └─────────────────┘ │
    └─────────────────────┘
```

### 服务划分

1. **LangGraph Server** (2024端口)
   - Agent交互、会话管理、流式响应
   - 状态机执行、工具调用
   - 子Agent协调

2. **Gateway API** (8001端口)
   - 模型管理、MCP配置
   - 技能管理、记忆操作
   - 文件上传、制品服务
   - 线程清理

3. **Nginx** (2026端口)
   - 统一入口、路由分发
   - 静态文件服务
   - 负载均衡

---

## 核心设计思想

### 1. 分层架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    App Layer (app/)                     │
│                  FastAPI Gateway API                    │
│              • REST接口  • IM频道集成                   │
└────────────────────┬────────────────────────────────────┘
                     │ 只允许App→Harness
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Harness Layer (deerflow/)                │
│              可发布的Agent框架包                         │
│  • Agent系统  • 工具系统  • 沙盒  • 配置管理            │
└─────────────────────────────────────────────────────────┘
```

**关键设计原则**：
- **单向依赖**：App依赖Harness，Harness绝不依赖App
- **可发布性**：Harness可以独立打包和分发
- **边界测试**：`test_harness_boundary.py`确保边界不被破坏

### 2. 隔离性设计

#### 线程级隔离
```python
# 每个线程有独立的文件系统
.deer-flow/
└── threads/
    └── {thread_id}/
        ├── user-data/
        │   ├── workspace/    # 工作空间
        │   ├── uploads/      # 上传文件
        │   └── outputs/      # 输出制品
        └── acp-workspace/    # ACP工作区
```

#### 虚拟路径映射
```python
# Agent看到的路径 vs 实际路径
"/mnt/user-data/workspace" → ".deer-flow/threads/{id}/user-data/workspace"
"/mnt/skills"               → "deer-flow/skills/"
"/mnt/acp-workspace"        → ".deer-flow/threads/{id}/acp-workspace"
```

### 3. 中间件链模式

**执行顺序**（严格顺序）：
```python
1. ThreadDataMiddleware      # 创建线程隔离环境
2. UploadsMiddleware         # 注入上传文件信息
3. SandboxMiddleware         # 获取沙盒执行环境
4. DanglingToolCallMiddleware # 处理中断的工具调用
5. GuardrailMiddleware       # 工具调用授权检查（可选）
6. SummarizationMiddleware   # 上下文压缩（可选）
7. TodoListMiddleware        # 任务跟踪（可选）
8. TitleMiddleware           # 自动生成标题
9. MemoryMiddleware          # 记忆更新排队
10. ViewImageMiddleware      # 图像数据注入（条件）
11. SubagentLimitMiddleware  # 子Agent数量限制（可选）
12. ClarificationMiddleware  # 澄清请求拦截（必须最后）
```

**设计优势**：
- **单一职责**：每个中间件只处理一个特定问题
- **可组合性**：可选中间件支持功能开关
- **可测试性**：每个中间件可独立测试
- **可扩展性**：新功能可作为新中间件插入

### 4. 异步处理模式

#### 记忆更新队列
```python
# 对话不阻塞，异步更新记忆
对话 → MemoryMiddleware → 队列 → [防抖30s] → 后台处理
```

#### 子Agent执行
```python
# 双线程池：调度池 + 执行池
task()工具 → 调度池(3) → 执行池(3) → 轮询完成 → 返回结果
```

---

## 技术栈

### 核心框架
- **LangGraph** (1.0.6+) - Agent框架和多Agent编排
- **LangChain** (1.2.3+) - LLM抽象和工具系统
- **FastAPI** (0.115.0+) - 高性能REST API

### 关键库
- **langchain-mcp-adapters** - Model Context Protocol支持
- **agent-sandbox** - 沙盒代码执行
- **markitdown** - 多格式文档转换
- **tavily-python** / **firecrawl-py** - 网络搜索和爬取

### 开发工具
- **ruff** - 代码检查和格式化
- **pytest** - 测试框架
- **uv** - 包管理器

---

## 核心组件

### 1. Lead Agent系统

**工厂模式**：`make_lead_agent(config)`

```python
# 核心组成部分
Lead Agent = 动态模型选择 + 中间件链 + 工具系统 + 子Agent + 系统提示
```

**特点**：
- **模型动态选择**：支持thinking和vision能力
- **工具动态加载**：根据配置加载不同工具集
- **提示词模板**：技能注入、记忆注入、子Agent指令

### 2. 沙盒系统

**抽象接口**：
```python
class Sandbox(ABC):
    @abstractmethod
    def execute_command(self, command: str) -> dict:
        pass

    @abstractmethod
    def read_file(self, path: str) -> str:
        pass
```

**提供者模式**：
- **LocalSandboxProvider**：本地文件系统执行
- **AioSandboxProvider**：Docker隔离执行（社区版）

**安全特性**：
- 路径映射：虚拟路径→物理路径
- 并发控制：`str_replace`的序列化
- 隔离性：每线程独立工作目录

### 3. 工具系统

**工具加载**：`get_available_tools()`

```python
# 工具来源优先级
1. 配置定义的工具 (config.yaml)
2. MCP工具 (动态加载)
3. 内置工具 (present_files, ask_clarification, view_image)
4. 子Agent工具 (task)
5. 社区工具 (tavily, jina_ai, firecrawl)
```

### 4. 子Agent系统

**内置Agent**：
- **general-purpose**：全工具集（除task外）
- **bash**：命令行专家

**执行机制**：
```
并发限制：最多3个
超时时间：15分钟
执行模式：双线程池（调度+执行）
状态同步：SSE事件流
```

---

## 记忆系统详解

### 🎯 设计理念

记忆系统通过**LLM驱动的智能提取**和**持久化存储**，实现跨对话的上下文保留。核心设计目标是让AI Agent能够：

1. **记住用户信息**：工作背景、个人偏好、当前关注点
2. **积累历史知识**：最近活动、长期背景、技术专长
3. **学习事实知识**：具体的偏好、技能、目标和修正记录
4. **持续优化**：通过对话不断更新和精炼记忆

### 📦 存储设计

#### 存储位置
```
默认路径：
  .deer-flow/memory.json

配置路径：
  config.yaml → memory.storage_path

Per-Agent路径：
  .deer-flow/agents/{agent_name}/memory.json
```

#### 数据结构
```json
{
  "version": "1.0",
  "lastUpdated": "2025-04-05T12:00:00Z",
  "user": {
    "workContext": {
      "summary": "核心贡献者，主要项目有16k+ stars，技术栈包括Python和AI框架",
      "updatedAt": "2025-04-05T12:00:00Z"
    },
    "personalContext": {
      "summary": "双语能力，专注于AI Agent开发和分布式系统",
      "updatedAt": "2025-04-05T12:00:00Z"
    },
    "topOfMind": {
      "summary": "主要工作：宅力觉醒智能体的后端开发；副线：LangGraph集成研究；学习：最新LLM模型特性跟踪",
      "updatedAt": "2025-04-05T12:00:00Z"
    }
  },
  "history": {
    "recentMonths": {
      "summary": "最近几个月专注于构建基于LangGraph的AI Agent系统，实现了中间件链、沙盒执行、记忆系统等核心功能。深入研究了子Agent协作和工具扩展机制。",
      "updatedAt": "2025-04-05T12:00:00Z"
    },
    "earlierContext": {
      "summary": "较早时期主要在探索不同的AI Agent框架，最终选择了LangGraph作为基础，并开始构建可扩展的Agent系统。",
      "updatedAt": "2025-04-05T12:00:00Z"
    },
    "longTermBackground": {
      "summary": "具有扎实的软件工程背景，长期专注于分布式系统和AI应用开发，擅长Python和现代AI框架。",
      "updatedAt": "2025-04-05T12:00:00Z"
    }
  },
  "facts": [
    {
      "id": "fact_abc123",
      "content": "用户主要使用Python进行开发，偏好使用类型提示",
      "category": "preference",
      "confidence": 0.95,
      "createdAt": "2025-04-05T12:00:00Z",
      "source": "thread_123"
    },
    {
      "id": "fact_def456",
      "content": "用户在LangGraph集成中遇到了流式响应的问题，正确的做法是使用runs.stream()方法",
      "category": "correction",
      "confidence": 0.98,
      "createdAt": "2025-04-05T12:00:00Z",
      "source": "thread_456",
      "sourceError": "之前使用了runs.wait()导致无法实现流式响应"
    }
  ]
}
```

#### 分类体系

**事实类别** (category)：
- **preference**：用户偏好（工具、风格、方法）
- **knowledge**：专业知识或技能
- **context**：背景信息（职位、项目、位置）
- **behavior**：行为模式
- **goal**：目标或目的
- **correction**：错误修正记录

**置信度** (confidence)：
- **0.9-1.0**：明确陈述的事实
- **0.7-0.8**：强烈暗示的信息
- **0.5-0.6**：推断的模式（谨慎使用）

### 🔄 更新机制

#### 工作流程
```
对话发生
    ↓
MemoryMiddleware过滤
    ↓
加入更新队列
    ↓
[防抖等待 30s]
    ↓
后台线程处理
    ↓
LLM提取新信息
    ↓
合并到现有记忆
    ↓
原子性保存文件
```

#### 关键组件

**1. MemoryMiddleware**
```python
# 只处理用户消息和最终AI回复
过滤规则：
  - 包含用户输入（human消息）
  - 包含最终AI响应（ai消息）
  - 过滤中间工具调用结果
```

**2. MemoryUpdateQueue**
```python
# 防抖队列机制
特性：
  - 同一线程的多次更新会合并
  - 防抖时间：默认30秒（可配置）
  - 批量处理：一次处理多个队列项
  - 线程安全：使用锁保护
```

**3. MemoryUpdater**
```python
# LLM驱动的记忆更新
流程：
  1. 加载当前记忆
  2. 格式化对话历史
  3. 构建更新提示词
  4. 调用LLM提取更新
  5. 应用变更到记忆
  6. 清理上传文件提及
  7. 原子性保存
```

#### 去重机制

**事实去重**：
```python
# 基于内容去重
fact_content_key = content.strip()

# 已存在相同内容则跳过
if fact_key in existing_fact_keys:
    continue
```

**上传事件过滤**：
```python
# 移除文件上传相关的句子
_UPLOAD_SENTENCE_RE = re.compile(
    r"[^.!?]*\b(?:upload(?:ed|ing)?|/mnt/user-data/uploads/)[^.!?]*[.!?]?\s*"
)
```

### 💉 注入机制

#### 系统提示注入
```python
# 在Agent系统提示中注入记忆
<memory>
User Context:
- Work: {workContext.summary}
- Personal: {personalContext.summary}
- Current Focus: {topOfMind.summary}

History:
- Recent: {recentMonths.summary}
- Earlier: {earlierContext.summary}
- Background: {longTermBackground.summary}

Facts:
- [preference | 0.95] 用户主要使用Python进行开发
- [correction | 0.98] LangGraph集成应使用runs.stream()方法
</memory>
```

#### Token控制
```python
# 准确的token计数
1. 使用tiktoken库精确计算token数
2. 限制：默认2000 tokens（可配置）
3. 优先级：按置信度排序，高置信度优先
4. 截断策略：超出时按字符比例截断
```

#### 格式化优化
```python
# 智能格式化
- 修正事实：包含错误原因
  [correction | 0.98] 正确做法 (避免: 错误做法)

- 普通事实：
  [preference | 0.95] 偏好描述
```

### 🗂️ 存储抽象

#### 存储提供者接口
```python
class MemoryStorage(ABC):
    @abstractmethod
    def load(self, agent_name: str | None = None) -> dict:
        """加载记忆数据"""
        pass

    @abstractmethod
    def reload(self, agent_name: str | None = None) -> dict:
        """强制重新加载"""
        pass

    @abstractmethod
    def save(self, memory_data: dict, agent_name: str | None = None) -> bool:
        """保存记忆数据"""
        pass
```

#### FileMemoryStorage特性
```python
# 缓存机制
cache = {
    agent_name: (memory_data, file_mtime)
}

# 缓存失效
if cached_mtime != current_mtime:
    return load_from_file()

# 原子性保存
1. 写入临时文件 (.tmp)
2. 重命名到目标文件
3. 更新缓存
```

### ⚙️ 配置选项

```yaml
memory:
  # 总开关
  enabled: true

  # 存储配置
  storage_path: ""  # 空=使用默认路径
  storage_class: "deerflow.agents.memory.storage.FileMemoryStorage"

  # 更新配置
  debounce_seconds: 30      # 防抖等待时间
  model_name: null          # 使用的模型（null=默认模型）

  # 存储限制
  max_facts: 100                     # 最大事实数量
  fact_confidence_threshold: 0.7     # 最低置信度阈值

  # 注入配置
  injection_enabled: true
  max_injection_tokens: 2000         # 注入token限制
```

### 🔧 API接口

#### Gateway API端点
```python
# 获取记忆数据
GET /api/memory
→ {user: {...}, history: {...}, facts: [...]}

# 强制重新加载
POST /api/memory/reload
→ {success: true}

# 获取配置
GET /api/memory/config
→ {enabled: true, max_facts: 100, ...}

# 获取状态（配置+数据）
GET /api/memory/status
→ {config: {...}, data: {...}}
```

#### 嵌入式客户端
```python
from deerflow import DeerFlowClient

client = DeerFlowClient()

# 获取记忆
memory = client.get_memory()

# 重新加载
memory = client.reload_memory()

# 手动创建事实
memory = client.create_memory_fact(
    content="用户偏好使用Python类型提示",
    category="preference",
    confidence=0.95
)
```

### 🎨 设计亮点

1. **Per-Agent记忆**：支持每个Agent独立记忆
2. **原子性操作**：使用临时文件+重命名确保数据一致性
3. **缓存优化**：mtime检测避免重复读取
4. **防抖机制**：避免频繁的LLM调用
5. **Token精确控制**：使用tiktoken准确计算
6. **错误修正学习**：专门的correction类别记录错误
7. **清理上传事件**：避免临时文件信息污染长期记忆

### 📊 数据流图

```
对话消息
    ↓
MemoryMiddleware（过滤）
    ↓
MemoryUpdateQueue（排队+防抖）
    ↓
MemoryUpdater（LLM提取）
    ↓
FileMemoryStorage（原子保存）
    ↓
下次对话注入（系统提示）
```

---

## 关键技术点

### 1. 配置系统

**配置优先级**：
```
1. 显式参数 config_path
2. 环境变量 DEER_FLOW_CONFIG_PATH
3. 当前目录的 config.yaml
4. 父目录的 config.yaml（推荐）
```

**配置缓存**：
- 自动检测文件mtime变化
- 无需重启即可加载新配置

### 2. 反射系统

**动态类加载**：
```python
# resolve_variable()
"module.path:variable_name" → variable_value

# resolve_class()
"module.path:ClassName" → class_object
```

### 3. 模型工厂

**thinking模式**：
```python
# 扩展思考模式
create_chat_model(name="gpt-4", thinking_enabled=True)
```

**vision模式**：
```python
# 视觉能力
ViewImageMiddleware只在supports_vision=True时启用
```

### 4. IM频道系统

**支持平台**：
- **飞书**：流式响应，卡片更新
- **Slack**：等待完整响应
- **Telegram**：等待完整响应

**消息总线**：
```python
InboundMessage → MessageBus → ChannelManager → LangGraph
OutboundMessage → MessageBus → Channel → Platform
```

### 5. 测试策略

**TDD要求**：
- 每个功能必须有单元测试
- 边界测试确保架构完整性
- 回归测试防止破坏性变更

---

## 项目结构

```
backend/
├── packages/harness/deerflow/    # 核心框架包
│   ├── agents/                   # Agent系统
│   │   ├── lead_agent/          # 主Agent
│   │   ├── middlewares/         # 12个中间件
│   │   ├── memory/              # 记忆系统
│   │   │   ├── storage.py       # 存储抽象
│   │   │   ├── updater.py       # LLM更新
│   │   │   ├── queue.py         # 更新队列
│   │   │   └── prompt.py        # 提示词模板
│   │   └── thread_state.py      # 线程状态
│   ├── sandbox/                  # 沙盒系统
│   ├── subagents/               # 子Agent
│   ├── tools/                   # 工具系统
│   ├── mcp/                     # MCP集成
│   ├── models/                  # 模型工厂
│   ├── skills/                  # 技能系统
│   ├── config/                  # 配置管理
│   └── client.py                # 嵌入式客户端
├── app/                          # 应用层
│   ├── gateway/                 # Gateway API
│   │   └── routers/            # 6个路由模块
│   └── channels/                # IM频道集成
├── tests/                       # 测试套件
├── docs/                        # 文档
└── langgraph.json              # LangGraph配置
```

---

## 🎯 总结

宅力觉醒智能体的Backend采用了**现代Agent架构**，核心特点：

1. **分层设计**：清晰的App/Harness边界，可发布性
2. **中间件模式**：灵活的横切关注点处理
3. **隔离执行**：线程级沙盒隔离，安全可控
4. **智能记忆**：LLM驱动的上下文学习和持久化
5. **异步优先**：队列化处理，不阻塞主流程
6. **可扩展性**：工具、技能、MCP、子Agent都可扩展

**记忆系统**是整个系统的"大脑"，通过：
- 结构化存储（用户上下文、历史、事实）
- 智能更新（LLM提取、防抖队列）
- 精准注入（Token控制、优先级排序）
实现了真正的"越用越懂你"的智能体验。
