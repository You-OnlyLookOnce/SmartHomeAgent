# 智能家居智能体 - 接口使用文档

## 1. 接口概览

智能家居智能体提供了一系列RESTful API接口，用于实现对话管理、设备控制、任务管理、记忆管理等功能。所有接口均以`/api`为前缀，返回标准的JSON格式响应。

| 接口类别 | 接口数量 | 功能描述 |
|---------|---------|---------|
| 对话管理 | 6 | 创建、获取、更新、删除对话，获取对话历史 |
| 设备控制 | 2 | 控制设备，获取设备状态 |
| 任务管理 | 2 | 创建提醒，获取提醒列表 |
| 记忆管理 | 5 | 获取和保存人格文件，获取和保存长期记忆，执行记忆蒸馏 |
| 定时任务 | 3 | 获取定时任务列表，创建定时任务，删除定时任务 |
| 系统状态 | 2 | 获取智能体状态，健康检查 |

## 2. 接口详细说明

### 2.1 对话管理接口

#### 2.1.1 获取所有对话列表

**接口**：`GET /api/chats`

**功能**：获取所有对话的列表信息

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "chats": [
    {
      "channel": "Yueyue",
      "created_at": "2026-03-09T04:40:39.488955Z",
      "id": "d9608b90-6846-4aab-a480-74ea52e02eb0",
      "meta": {},
      "name": "新对话",
      "session_id": "1773031120918",
      "updated_at": "2026-03-19T14:32:46.706218Z",
      "user_id": "default"
    },
    ...
  ],
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/chats
```

#### 2.1.2 创建新对话

**接口**：`POST /api/chats`

**功能**：创建一个新的对话

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| name | string | 否 | 对话名称，默认值为"New Chat" |
| user_id | string | 否 | 用户ID，默认值为"default" |

**返回数据结构**：

```json
{
  "success": true,
  "chat": {
    "channel": "Yueyue",
    "created_at": "2026-03-20T10:00:00.000000Z",
    "id": "uuid",
    "meta": {},
    "name": "新对话",
    "session_id": "1773400000000",
    "updated_at": "2026-03-20T10:00:00.000000Z",
    "user_id": "default"
  },
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"name": "新对话", "user_id": "default"}'
```

#### 2.1.3 获取单个对话信息

**接口**：`GET /api/chats/{session_id}`

**功能**：获取指定对话的详细信息

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| session_id | string | 是 | 对话的会话ID |

**返回数据结构**：

```json
{
  "success": true,
  "chat": {
    "channel": "Yueyue",
    "created_at": "2026-03-09T04:40:39.488955Z",
    "id": "d9608b90-6846-4aab-a480-74ea52e02eb0",
    "meta": {},
    "name": "新对话",
    "session_id": "1773031120918",
    "updated_at": "2026-03-19T14:32:46.706218Z",
    "user_id": "default"
  },
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `404`：对话不存在
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/chats/1773031120918
```

#### 2.1.4 更新对话信息

**接口**：`PUT /api/chats/{session_id}`

**功能**：更新指定对话的名称

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| session_id | string | 是 | 对话的会话ID |
| name | string | 是 | 新的对话名称 |

**返回数据结构**：

```json
{
  "success": true,
  "chat": {
    "channel": "Yueyue",
    "created_at": "2026-03-09T04:40:39.488955Z",
    "id": "d9608b90-6846-4aab-a480-74ea52e02eb0",
    "meta": {},
    "name": "更新后的对话名称",
    "session_id": "1773031120918",
    "updated_at": "2026-03-20T10:00:00.000000Z",
    "user_id": "default"
  },
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `400`：缺少对话名称
- `404`：对话不存在
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X PUT http://localhost:8000/api/chats/1773031120918 \
  -H "Content-Type: application/json" \
  -d '{"name": "更新后的对话名称"}'
```

#### 2.1.5 删除对话

**接口**：`DELETE /api/chats/{session_id}`

**功能**：删除指定的对话

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| session_id | string | 是 | 对话的会话ID |

**返回数据结构**：

```json
{
  "success": true,
  "message": "对话删除成功",
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `404`：对话不存在
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X DELETE http://localhost:8000/api/chats/1773031120918
```

#### 2.1.6 获取对话历史

**接口**：`GET /api/chats/{session_id}/history`

**功能**：获取指定对话的历史消息

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| session_id | string | 是 | 对话的会话ID |

**返回数据结构**：

```json
{
  "success": true,
  "history": [
    {"user": "你好"},
    {"assistant": "你好！我是你的智能家居助手，有什么可以帮你的吗？"},
    {"user": "打开客厅灯"},
    {"assistant": "好的，已经为你打开客厅灯"}
  ],
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `404`：对话不存在
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/chats/1773031120918/history
```

### 2.2 聊天接口

#### 2.2.1 发送消息

**接口**：`POST /api/chat`

**功能**：发送消息并获取智能体的回复

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| message | string | 是 | 用户发送的消息内容 |
| user_id | string | 否 | 用户ID，默认值为"default_user" |
| session_id | string | 否 | 会话ID，如果不提供则创建新会话 |

**返回数据结构**：

```json
{
  "success": true,
  "response": {
    "message": "你好！我是你的智能家居助手，有什么可以帮你的吗？"
  },
  "agent": "conversation_agent",
  "session_id": "1773400000000",
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "user_id": "default_user", "session_id": "1773031120918"}'
```

### 2.3 设备控制接口

#### 2.3.1 控制设备

**接口**：`POST /api/device/control`

**功能**：控制指定的设备

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| device_id | string | 是 | 设备ID |
| action | string | 是 | 操作类型（如on、off、brightness等） |
| params | object | 否 | 操作参数，如亮度值等 |

**返回数据结构**：

```json
{
  "success": true,
  "message": "设备已打开"
}
```

**错误码说明**：
- `200`：成功
- `400`：参数错误
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/device/control \
  -H "Content-Type: application/json" \
  -d '{"device_id": "living_room_light", "action": "on"}'
```

#### 2.3.2 获取设备状态

**接口**：`GET /api/device/status/{device_id}`

**功能**：获取指定设备的状态

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| device_id | string | 是 | 设备ID |

**返回数据结构**：

```json
{
  "success": true,
  "status": "on",
  "brightness": 80
}
```

**错误码说明**：
- `200`：成功
- `404`：设备不存在
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/device/status/living_room_light
```

### 2.4 任务管理接口

#### 2.4.1 创建提醒

**接口**：`POST /api/reminder/create`

**功能**：创建一个新的提醒

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| title | string | 是 | 提醒标题 |

**返回数据结构**：

```json
{
  "success": true,
  "message": "提醒创建成功"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/reminder/create \
  -H "Content-Type: application/json" \
  -d '{"title": "下午3点开会"}'
```

#### 2.4.2 获取提醒列表

**接口**：`GET /api/reminder/list/{user_id}`

**功能**：获取指定用户的提醒列表

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| user_id | string | 是 | 用户ID |

**返回数据结构**：

```json
{
  "success": true,
  "reminders": [
    {"title": "下午3点开会", "status": "pending"},
    {"title": "明天早上8点起床", "status": "pending"}
  ]
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/reminder/list/default_user
```

### 2.5 记忆管理接口

#### 2.5.1 获取人格文件

**接口**：`GET /api/memory/soul`

**功能**：获取智能体的人格文件内容

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "data": "{\"name\": \"Yueyue\", \"personality\": \"友好、乐于助人\", ...}"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/memory/soul
```

#### 2.5.2 保存人格文件

**接口**：`POST /api/memory/soul`

**功能**：保存智能体的人格文件内容

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| content | string | 是 | 人格文件内容 |

**返回数据结构**：

```json
{
  "success": true,
  "message": "人格文件保存成功"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/memory/soul \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"name\": \"Yueyue\", \"personality\": \"友好、乐于助人\", ...}"}'
```

#### 2.5.3 获取长期记忆文件

**接口**：`GET /api/memory/long-term`

**功能**：获取智能体的长期记忆文件内容

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "data": "# 长期记忆\n\n## 用户偏好\n- 喜欢喝咖啡\n- 喜欢听古典音乐\n..."
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/memory/long-term
```

#### 2.5.4 保存长期记忆文件

**接口**：`POST /api/memory/long-term`

**功能**：保存智能体的长期记忆文件内容

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| content | string | 是 | 长期记忆文件内容 |

**返回数据结构**：

```json
{
  "success": true,
  "message": "记忆文件保存成功"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/memory/long-term \
  -H "Content-Type: application/json" \
  -d '{"content": "# 长期记忆\n\n## 用户偏好\n- 喜欢喝咖啡\n- 喜欢听古典音乐\n..."}'
```

#### 2.5.5 执行记忆蒸馏

**接口**：`POST /api/memory/distill`

**功能**：执行记忆蒸馏，将短期记忆转化为长期记忆

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "message": "记忆蒸馏完成"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/memory/distill
```

### 2.6 定时任务接口

#### 2.6.1 获取定时任务列表

**接口**：`GET /api/scheduler/list`

**功能**：获取所有定时任务的列表

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "schedules": [
    {"title": "每天早上7点提醒", "time": "07:00", "status": "active"},
    {"title": "每周一开会", "time": "09:00", "status": "active"}
  ]
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/scheduler/list
```

#### 2.6.2 创建定时任务

**接口**：`POST /api/scheduler/create`

**功能**：创建一个新的定时任务

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| title | string | 是 | 任务标题 |
| time | string | 是 | 任务执行时间 |

**返回数据结构**：

```json
{
  "success": true,
  "message": "定时任务创建成功"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X POST http://localhost:8000/api/scheduler/create \
  -H "Content-Type: application/json" \
  -d '{"title": "每天早上7点提醒", "time": "07:00"}'
```

#### 2.6.3 删除定时任务

**接口**：`DELETE /api/scheduler/{schedule_id}`

**功能**：删除指定的定时任务

**请求参数**：

| 参数名 | 类型 | 是否必填 | 说明 |
|-------|------|---------|------|
| schedule_id | string | 是 | 定时任务ID |

**返回数据结构**：

```json
{
  "success": true,
  "message": "定时任务删除成功"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X DELETE http://localhost:8000/api/scheduler/12345
```

### 2.7 系统状态接口

#### 2.7.1 获取智能体状态

**接口**：`GET /api/agent/status`

**功能**：获取所有智能体的状态信息

**请求参数**：无

**返回数据结构**：

```json
{
  "success": true,
  "agents": {
    "conversation_agent": "active",
    "device_control_agent": "active",
    "task_manager_agent": "active",
    "security_agent": "active",
    "memory_agent": "active"
  },
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/agent/status
```

#### 2.7.2 健康检查

**接口**：`GET /api/health`

**功能**：检查系统健康状态

**请求参数**：无

**返回数据结构**：

```json
{
  "status": "healthy",
  "timestamp": "2026-03-20T10:00:00.000000Z",
  "services": {
    "gateway": "ok",
    "agents": "ok",
    "database": "ok",
    "llm": "ok"
  }
}
```

**错误码说明**：
- `200`：成功
- `500`：服务器内部错误

**调用示例**：

```bash
curl -X GET http://localhost:8000/api/health
```

## 3. 通用响应格式

所有API接口返回的响应格式遵循以下通用结构：

### 成功响应

```json
{
  "success": true,
  "[data_key]": [data_value],
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

### 失败响应

```json
{
  "success": false,
  "message": "错误信息",
  "timestamp": "2026-03-20T10:00:00.000000Z"
}
```

## 4. 错误码说明

| 状态码 | 含义 | 说明 |
|-------|------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 参数错误 | 请求参数不正确或缺失 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 500 | 服务器内部错误 | 服务器处理请求时发生错误 |

## 5. 接口调用最佳实践

### 5.1 会话管理

1. **创建会话**：在开始对话前，先调用`POST /api/chats`创建一个新会话，获取session_id
2. **发送消息**：使用获取到的session_id调用`POST /api/chat`发送消息
3. **切换会话**：调用`GET /api/chats/{session_id}/history`获取历史消息，然后继续发送消息
4. **管理会话**：使用`PUT /api/chats/{session_id}`更新会话名称，使用`DELETE /api/chats/{session_id}`删除会话

### 5.2 设备控制

1. **控制设备**：调用`POST /api/device/control`发送控制命令
2. **查询状态**：调用`GET /api/device/status/{device_id}`获取设备状态

### 5.3 任务管理

1. **创建提醒**：调用`POST /api/reminder/create`创建提醒
2. **获取提醒列表**：调用`GET /api/reminder/list/{user_id}`获取提醒列表

### 5.4 记忆管理

1. **查看记忆**：调用`GET /api/memory/long-term`和`GET /api/memory/soul`查看记忆内容
2. **更新记忆**：调用`POST /api/memory/long-term`和`POST /api/memory/soul`更新记忆内容
3. **执行记忆蒸馏**：定期调用`POST /api/memory/distill`执行记忆蒸馏

### 5.5 定时任务

1. **创建定时任务**：调用`POST /api/scheduler/create`创建定时任务
2. **获取定时任务列表**：调用`GET /api/scheduler/list`获取定时任务列表
3. **删除定时任务**：调用`DELETE /api/scheduler/{schedule_id}`删除定时任务

## 6. 权限要求

当前系统采用简化的权限模型，所有接口均无需认证即可访问。在生产环境中，建议添加以下权限控制：

1. **API密钥认证**：为每个客户端分配唯一的API密钥
2. **用户认证**：实现用户登录和会话管理
3. **权限控制**：基于角色的访问控制（RBAC）
4. **速率限制**：限制API调用频率，防止滥用

## 7. 接口版本控制

当前系统使用API版本1.0.0，版本号体现在API网关的初始化中。未来版本更新时，将通过URL路径或请求头进行版本控制。

## 8. 总结

智能家居智能体提供了全面的API接口，支持对话管理、设备控制、任务管理、记忆管理等功能。这些接口设计遵循RESTful规范，返回标准的JSON格式响应，便于前端和其他系统集成。

通过这些接口，开发者可以：
- 构建自定义的前端界面
- 与其他智能家居系统集成
- 开发自动化脚本和工作流
- 扩展系统功能

系统的API设计注重简洁性和一致性，同时保持了足够的灵活性和可扩展性，为未来的功能扩展和系统升级奠定了基础。

---

**文档版本**：1.0.0
**最后更新**：2026-03-20
**适用系统**：智能家居智能体 v1.0.0