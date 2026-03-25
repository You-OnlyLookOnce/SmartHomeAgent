# 架构 V2 文档

## 概述

架构 V2 是对原有系统的重大重构，将系统从"披着智能体外衣的规则系统"转变为真正的 AI 驱动架构。核心变更是移除所有人工编写的规则决策逻辑，完全由 LLM 通过 Function Calling 自主决策。

## 核心变更

### 1. 移除人工规则决策系统

**移除内容：**
- A/B/C/D/E 决策类型（使用现成资源/触发搜索/承认不知道/请求澄清/设备控制）
- 人工编写的 30+ 条决策规则
- MultiLayerDecision 多层决策类
- 复杂的决策提示词模板

**替代方案：**
- LLM 原生 Function Calling 能力
- 端到端的 AI 驱动决策

### 2. 新的决策架构

#### Function Calling 引擎 (`src/core/function_calling_engine.py`)

核心组件，负责：
- 管理 MCP 工具注册
- 生成工具描述（OpenAI 格式）
- 调用 LLM 进行 Function Calling 决策
- 执行工具并处理结果
- 生成最终回复

**工作流程：**
```
用户输入 → LLM Function Calling → 工具选择 → 工具执行 → 结果整合 → 生成回复
```

#### MCP 工具注册中心 (`src/core/mcp_tool_registry.py`)

统一管理所有 MCP 工具：
- 工具注册与注销
- 工具发现与分类
- 工具执行
- 自动生成工具描述

**特性：**
- 单例模式，全局唯一实例
- 支持装饰器注册
- 支持动态工具发现
- 支持工具分类和标签

### 3. MCP 工具模块

所有功能统一封装为 MCP 工具：

#### 设备控制工具 (`src/tools/mcp_tools/device_control_tool.py`)
- `control_device` - 控制智能家居设备
- `get_device_status` - 获取设备状态
- `list_devices` - 列出所有设备

#### 网络搜索工具 (`src/tools/mcp_tools/web_search_tool.py`)
- `web_search` - 网络搜索（集成七牛云搜索 API）
- `search_news` - 新闻搜索
- `get_current_time` - 获取当前时间
- `calculate` - 数学计算

#### 记忆管理工具 (`src/tools/mcp_tools/memory_tool.py`)
- `store_memory` - 存储记忆
- `retrieve_memory` - 检索记忆
- `get_all_memories` - 获取所有记忆
- `delete_memory` - 删除记忆

#### 文件操作工具 (`src/tools/mcp_tools/file_operations_tool.py`)
- `read_file` - 读取文件
- `write_file` - 写入文件
- `search_files` - 搜索文件
- `list_directory` - 列出目录

#### 定时任务工具 (`src/tools/mcp_tools/scheduler_tool.py`)
- `create_task` - 创建任务
- `get_tasks` - 获取任务列表
- `delete_task` - 删除任务

#### 备忘录工具 (`src/tools/mcp_tools/memo_tool.py`)
- `create_memo` - 创建备忘录
- `get_memos` - 获取备忘录列表
- `search_memos` - 搜索备忘录
- `update_memo` - 更新备忘录
- `delete_memo` - 删除备忘录

### 4. 七牛云 API 集成

#### 实时推理 API (`src/ai/qiniu_llm_v2.py`)

集成七牛云 AI 大模型推理 API：
- 聊天完成（流式/非流式）
- Function Calling 支持
- 多模型支持（kimi-k2.5, gpt-4o, claude-3-5-sonnet 等）

**API 端点：**
```
https://api.qnaigc.com/v1/chat/completions
```

#### 全网搜索 API

集成七牛云全网搜索 API：
- 网页搜索
- 时间过滤
- 结构化结果返回

**API 端点：**
```
https://api.qnaigc.com/v1/web-search
```

### 5. 保留的核心模块

#### Soul 模块
- 存在意义、使命、价值观
- 人格核心

#### Agent 模块
- 名字、性别、年龄感
- 职业、MBTI、语言风格
- 人格特质

#### Profile 模块
- 用户配置
- 个人偏好

这些模块通过 `PersonaManager` 统一管理，在系统提示词中传递给 LLM。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
│                   (Frontend - HTML/JS)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                        API 网关层                            │
│              (FastAPI - api_gateway.py)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  新的 Function Calling 处理流程                      │   │
│  │  1. 接收用户输入                                     │   │
│  │  2. 调用 MetaCognitionRouterV2.process()            │   │
│  │  3. 流式返回处理结果                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     决策引擎层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MetaCognitionRouterV2                              │   │
│  │  ├─ FunctionCallingEngine                           │   │
│  │  │   ├─ 工具注册管理                                  │   │
│  │  │   ├─ LLM Function Calling                        │   │
│  │  │   └─ 工具执行与结果处理                            │   │
│  │  └─ PersonaManager (soul/agent/profile)             │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP 工具层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 设备控制    │ │ 网络搜索    │ │ 记忆管理    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 文件操作    │ │ 定时任务    │ │ 备忘录      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 七牛云 LLM  │ │ 七牛云搜索  │ │ 设备管理器  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 记忆管理器  │ │ 任务调度器  │ │ 备忘录管理  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 优势

### 1. 智能化水平提升
- LLM 自主决策，无需人工编写规则
- 能够处理更复杂的场景
- 决策更加灵活和智能

### 2. 架构简化
- 移除复杂的规则系统
- 统一的 MCP 工具接口
- 更易于维护和扩展

### 3. 扩展性增强
- 动态工具注册
- 易于添加新功能
- 工具复用性强

### 4. 标准化
- 符合 MCP 规范
- 兼容 OpenAI Function Calling 格式
- 便于与其他系统集成

## 迁移指南

### 从旧架构迁移

1. **更新依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **环境变量配置**
   ```bash
   export QINIU_AI_API_KEY="your-api-key"
   ```

3. **启动服务**
   ```bash
   python app.py
   ```

### 添加新工具

```python
from src.core.mcp_tool_registry import mcp_tool

@mcp_tool(
    name="my_tool",
    description="我的工具描述",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"}
        },
        "required": ["param1"]
    },
    category="custom"
)
async def my_tool(param1: str):
    return {"success": True, "result": f"处理结果: {param1}"}
```

## API 文档

### 聊天接口

**端点：** `POST /api/chat`

**请求体：**
```json
{
  "message": "你好",
  "user_id": "default_user",
  "session_id": "optional_session_id",
  "stream": true,
  "message_id": "unique_message_id"
}
```

**响应（流式）：**
```
data: {"type": "session_id", "content": "session_xxx"}

data: {"type": "thinking", "content": "正在思考..."}

data: {"type": "tool_calls", "tool_calls": [...]}

data: {"type": "answer", "content": "你好！很高兴见到你..."}

data: {"type": "stream_end"}
```

## 测试

运行测试：
```bash
pytest tests/test_architecture_refactoring.py -v
```

## 注意事项

1. **API 密钥**：确保设置了 `QINIU_AI_API_KEY` 环境变量
2. **网络连接**：需要稳定的网络连接访问七牛云 API
3. **工具权限**：部分工具（如文件操作）有安全限制
4. **错误处理**：新架构有完善的错误处理和回退机制

## 未来规划

1. **多模态支持**：支持语音、图像输入
2. **更强大的工具**：集成更多外部服务
3. **智能体协作**：支持多智能体协作
4. **个性化学习**：根据用户反馈优化决策
