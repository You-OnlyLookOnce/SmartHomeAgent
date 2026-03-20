# 智能家居智能体架构文档

## 1. 系统架构概览

智能家居智能体采用模块化、分层的架构设计，主要包含以下核心模块：

- **API Gateway**: 系统的入口点，处理所有外部请求
- **Agent Cluster**: 智能体集群，包含多种专业智能体
- **Core Features**: 三大核心功能模块
  - 定时任务模块
  - 记忆蒸馏系统
  - Agent智能核心
- **Tools & Services**: 工具和服务层
- **Storage**: 存储层

## 2. 三大核心功能模块

### 2.1 定时任务模块

**功能概述**：
- 实现任务的创建、调度、执行与监控
- 支持CRON表达式和Windows Task Scheduler集成
- 提供任务状态管理和执行结果追踪

**架构设计**：
- `TaskScheduler` 类：核心调度器，负责任务的管理和执行
- 支持三种任务类型：
  - 每日任务：指定时间点执行
  - 间隔任务：按固定时间间隔执行
  - CRON任务：支持复杂的CRON表达式
- 任务存储：使用JSON文件存储任务配置
- 任务历史：记录任务执行结果和状态

**关键接口**：
- `schedule_daily_task()`: 调度每日任务
- `schedule_interval_task()`: 调度间隔任务
- `schedule_cron_task()`: 调度CRON任务
- `create_windows_task()`: 创建Windows计划任务
- `get_all_tasks()`: 获取所有任务
- `delete_task()`: 删除任务
- `disable_task()`: 禁用任务
- `enable_task()`: 启用任务

### 2.2 记忆蒸馏系统

**功能概述**：
- 实现智能体经验的提取、压缩、存储与应用
- 从对话历史中提取重要信息
- 生成和管理长期记忆
- 实现记忆版本管理和老化机制

**架构设计**：
- `MemoryManager` 类：核心记忆管理器
- 记忆层次：
  - 短期记忆：对话历史
  - 每日笔记：按日期存储的对话摘要
  - 长期记忆：经过蒸馏的重要信息
- 记忆版本：定期保存记忆快照，支持版本回滚
- 记忆老化：自动清理过期或不重要的记忆

**关键接口**：
- `update_memory()`: 更新记忆
- `distill_memory()`: 执行记忆蒸馏
- `read_long_term_memory()`: 读取长期记忆
- `write_long_term_memory()`: 写入长期记忆
- `memory_search()`: 搜索记忆
- `get_memory_versions()`: 获取记忆版本
- `get_memory_version_content()`: 获取记忆版本内容

### 2.3 Agent智能核心

**功能概述**：
- 实现自主决策、环境交互与任务规划能力
- 基于ReAct（Reasoning + Action）思考循环
- 支持工具发现和调用
- 集成七牛大模型进行智能决策

**架构设计**：
- `ReActAgent` 类：核心智能体，实现ReAct思考循环
- 思考循环包含三个阶段：
  - 思考阶段：分析任务和上下文
  - 行动选择阶段：决定执行的操作
  - 行动执行阶段：执行选定的操作
- 工具调用：支持调用内置工具和外部工具
- 记忆注入：将长期记忆注入到思考过程中

**关键接口**：
- `execute()`: 执行任务
- `_execute_react_loop()`: 执行ReAct思考循环
- `_think()`: 思考阶段
- `_select_action()`: 行动选择阶段
- `_execute_tool()`: 执行工具
- `handle_message()`: 处理来自其他Agent的消息

## 3. 系统集成

### 3.1 模块间交互

- **API Gateway** ↔ **Agent Cluster**: 通过消息传递进行通信
- **Agent Cluster** ↔ **Core Features**: Agent可以调用核心功能模块
- **Core Features** ↔ **Storage**: 核心功能模块读写存储

### 3.2 数据流向

1. 外部请求 → API Gateway
2. API Gateway → Agent Cluster
3. Agent Cluster → 核心功能模块
4. 核心功能模块 → 存储
5. 存储 → 核心功能模块
6. 核心功能模块 → Agent Cluster
7. Agent Cluster → API Gateway
8. API Gateway → 外部响应

## 4. 技术栈

- **编程语言**: Python 3.11
- **Web框架**: FastAPI
- **大模型**: 七牛云大模型API
- **存储**: 文件系统（JSON、Markdown）
- **任务调度**: Windows Task Scheduler
- **测试**: unittest

## 5. 扩展性设计

- **模块化设计**: 各模块职责明确，易于扩展
- **插件机制**: 支持添加新的工具和Agent
- **配置驱动**: 通过配置文件调整系统行为
- **版本管理**: 支持记忆和任务的版本管理

## 6. 性能优化

- **异步处理**: 使用asyncio处理并发请求
- **缓存机制**: 缓存频繁访问的记忆和任务
- **批处理**: 批量处理记忆蒸馏和任务执行
- **资源管理**: 合理分配系统资源，避免资源竞争

## 7. 安全考虑

- **权限管理**: 控制对核心功能的访问权限
- **数据加密**: 保护敏感记忆和任务信息
- **输入验证**: 验证所有外部输入，防止注入攻击
- **错误处理**: 妥善处理异常，避免系统崩溃
