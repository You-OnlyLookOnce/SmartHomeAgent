# 智能家居智能体API文档

## 1. 基础信息

- **API Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content-Type**: `application/json`
- **Authentication**: 无（开发环境）

## 2. 定时任务API

### 2.1 创建定时任务

**Endpoint**: `POST /api/tasks`

**Request Body**:
```json
{
  "name": "任务名称",
  "cron_expr": "CRON表达式",
  "command": "执行命令"
}
```

**Response**:
```json
{
  "success": true,
  "message": "任务创建成功",
  "task_id": "任务ID"
}
```

### 2.2 获取所有任务

**Endpoint**: `GET /api/tasks`

**Response**:
```json
{
  "tasks": [
    {
      "id": "任务ID",
      "name": "任务名称",
      "type": "任务类型",
      "cron_expr": "CRON表达式",
      "command": "执行命令",
      "last_run": "上次执行时间",
      "enabled": true
    }
  ]
}
```

### 2.3 删除任务

**Endpoint**: `DELETE /api/tasks/{task_id}`

**Response**:
```json
{
  "success": true,
  "message": "任务删除成功"
}
```

## 3. 记忆蒸馏API

### 3.1 执行记忆蒸馏

**Endpoint**: `POST /api/memory/distill`

**Request Body**:
```json
{
  "days": 7
}
```

**Response**:
```json
{
  "success": true,
  "message": "记忆蒸馏完成"
}
```

### 3.2 获取长期记忆

**Endpoint**: `GET /api/memory/long-term`

**Response**:
```json
{
  "memory": "长期记忆内容"
}
```

### 3.3 获取记忆版本

**Endpoint**: `GET /api/memory/versions`

**Response**:
```json
{
  "versions": [
    "版本1",
    "版本2"
  ]
}
```

### 3.4 获取特定版本记忆

**Endpoint**: `GET /api/memory/versions/{version}`

**Response**:
```json
{
  "memory": "版本记忆内容"
}
```

## 4. Agent智能核心API

### 4.1 执行任务

**Endpoint**: `POST /api/agent/execute`

**Request Body**:
```json
{
  "task": "任务描述",
  "user_id": "用户ID",
  "session_id": "会话ID"
}
```

**Response**:
```json
{
  "success": true,
  "message": "任务执行结果",
  "steps": [
    {
      "type": "thought",
      "content": "思考内容"
    },
    {
      "type": "action",
      "content": "行动内容"
    },
    {
      "type": "observation",
      "content": "观察结果"
    }
  ]
}
```

### 4.2 获取Agent状态

**Endpoint**: `GET /api/agent/status`

**Response**:
```json
{
  "agent_id": "agent ID",
  "role": "智能助手",
  "context_length": 10,
  "emotion_state": "neutral"
}
```

### 4.3 获取Agent能力

**Endpoint**: `GET /api/agent/capabilities`

**Response**:
```json
{
  "agent_id": "agent ID",
  "capabilities": {
    "general_chat": true,
    "question_answering": true,
    "tool_calling": true,
    "memory_management": true,
    "task_planning": true
  },
  "permissions": [
    "chat",
    "answer_questions",
    "use_tools",
    "access_memory",
    "plan_tasks"
  ]
}
```

## 5. 会话管理API

### 5.1 创建会话

**Endpoint**: `POST /api/sessions`

**Request Body**:
```json
{
  "user_id": "用户ID"
}
```

**Response**:
```json
{
  "session_id": "会话ID",
  "user_id": "用户ID",
  "created_at": "创建时间"
}
```

### 5.2 获取会话历史

**Endpoint**: `GET /api/sessions/{session_id}/history`

**Response**:
```json
{
  "history": [
    {
      "role": "user",
      "content": "用户消息",
      "timestamp": "时间戳"
    },
    {
      "role": "assistant",
      "content": "助手回复",
      "timestamp": "时间戳"
    }
  ]
}
```

### 5.3 删除会话

**Endpoint**: `DELETE /api/sessions/{session_id}`

**Response**:
```json
{
  "success": true,
  "message": "会话删除成功"
}
```

## 6. 错误处理

所有API接口都可能返回以下错误响应：

```json
{
  "success": false,
  "error": "错误信息"
}
```

常见错误码：
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

## 7. 示例请求

### 创建定时任务

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日备份",
    "cron_expr": "0 0 * * *",
    "command": "python backup.py"
  }'
```

### 执行记忆蒸馏

```bash
curl -X POST http://localhost:8000/api/memory/distill \
  -H "Content-Type: application/json" \
  -d '{
    "days": 7
  }'
```

### 执行Agent任务

```bash
curl -X POST http://localhost:8000/api/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "帮我查询明天的天气",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```
