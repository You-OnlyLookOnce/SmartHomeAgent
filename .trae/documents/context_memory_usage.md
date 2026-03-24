# 上下文记忆功能使用说明

## 1. 概述

上下文记忆功能是智能体的核心功能之一，它允许智能体在对话过程中保留和引用历史交互信息，从而提供更加连贯、个性化的对话体验。经过修复后，智能体现在能够准确、完整地保留并引用整个对话过程中的关键信息。

## 2. 实现原理

上下文记忆功能的实现基于以下几个核心组件：

- **会话管理器**：负责对话的创建、管理和持久化
- **记忆管理器**：负责对话历史的存储和检索
- **持久化机制**：确保对话历史能够被可靠地保存和加载

## 3. 核心功能

### 3.1 会话管理

- **创建会话**：创建新的对话会话
- **获取会话**：获取指定会话的信息
- **更新会话**：更新会话的名称和其他信息
- **删除会话**：删除指定的会话

### 3.2 对话历史管理

- **保存对话历史**：保存用户和助手的对话内容
- **获取对话历史**：获取指定会话的对话历史
- **更新对话历史**：更新对话历史内容
- **清空对话历史**：清空指定会话的对话历史

### 3.3 记忆管理

- **添加记忆**：将对话内容添加到记忆中
- **获取记忆**：获取记忆内容
- **保存记忆**：将记忆保存到文件
- **加载记忆**：从文件加载记忆

### 3.4 会话备份和恢复

- **备份会话**：创建会话状态的备份
- **恢复会话**：从备份恢复会话状态
- **列出备份**：列出会话的所有备份

## 4. 使用方法

### 4.1 会话管理

```python
from src.agent.independent_session_manager import IndependentSessionManager

# 创建会话管理器实例
session_manager = IndependentSessionManager()

# 创建新会话
session = session_manager.create_session(name="测试会话")
session_id = session["session_id"]

# 获取会话信息
session_info = session_manager.get_session(session_id)

# 更新会话名称
session_manager.update_session_name(session_id, "新的会话名称")

# 删除会话
session_manager.delete_session(session_id)
```

### 4.2 对话历史管理

```python
# 保存对话历史
session_manager.save_conversation_history(session_id, "用户消息", "助手回复")

# 获取对话历史
history = session_manager.get_conversation_history(session_id)

# 更新对话历史
session_manager.update_conversation_history(session_id, "用户消息", "助手回复")

# 清空对话历史
session_manager.clear_conversation_history(session_id)
```

### 4.3 会话备份和恢复

```python
# 备份会话
session_manager.backup_session(session_id)

# 列出会话备份
backups = session_manager.list_session_backups(session_id)

# 从备份恢复会话
if backups:
    session_manager.restore_session(session_id, backups[0])
```

## 5. 技术细节

### 5.1 会话存储

- **会话信息**：存储在 `data/conversations/chats.json` 文件中
- **会话上下文**：存储在 `data/conversations/sessions/` 目录下的 JSON 文件中
- **记忆数据**：存储在 `data/conversations/sessions/` 目录下的 `{session_id}_memory.json` 文件中
- **会话备份**：存储在 `data/conversations/backups/` 目录下

### 5.2 错误处理

系统具有完善的错误处理机制，能够处理各种异常情况：

- **IO错误**：处理文件读写错误
- **类型错误**：处理JSON序列化问题
- **权限错误**：处理文件权限问题
- **其他错误**：捕获并记录其他未知错误

### 5.3 性能优化

- **内存管理**：限制对话历史长度，避免内存溢出
- **文件操作**：使用原子性文件操作，确保数据安全
- **错误处理**：优化错误处理逻辑，提高系统稳定性

## 6. 测试验证

系统已经通过以下测试：

- **多轮对话测试**：验证智能体能够正确保留和引用历史对话信息
- **会话管理测试**：验证会话的创建、更新和删除功能
- **对话历史测试**：验证对话历史的保存、获取和更新功能
- **记忆管理测试**：验证记忆的保存和加载功能
- **备份恢复测试**：验证会话备份和恢复功能

## 7. 注意事项

- **内存限制**：对话历史长度限制为20轮（40条消息），超过后会自动截断
- **文件权限**：确保系统具有对 `data/conversations/` 目录的读写权限
- **错误处理**：系统会自动处理各种错误情况，但仍需确保输入数据的有效性

## 8. 总结

修复后的上下文记忆功能具有以下特点：

- **可靠性**：能够可靠地保存和加载对话历史
- **完整性**：能够完整地保留整个对话过程中的关键信息
- **稳定性**：在各种情况下都能稳定工作
- **易用性**：提供简单易用的API接口

通过使用这些功能，智能体现在能够提供更加连贯、个性化的对话体验，更好地满足用户的需求。