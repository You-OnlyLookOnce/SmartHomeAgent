# 智能体架构文档

## 1. 项目概述

智能家居智能体（Home AI Agent）是一个基于大模型的智能助手系统，旨在为用户提供智能的家居管理和交互体验。该系统集成了大语言模型、技能系统、安全机制等多种功能，能够理解用户的需求并提供相应的服务。

## 2. 目录结构

项目采用模块化设计，各个模块职责明确，相互独立。以下是项目的目录结构及其作用：

### 2.1 根目录

- **.trae/**: 存储项目的文档和计划文件
- **YUEYUE/**: 存储悦悦智能体的相关配置和文档
- **config/**: 存储项目的配置文件
- **src/**: 存储项目的源代码
- **.gitignore**: Git版本控制的忽略文件配置
- **README.md**: 项目的说明文档
- **app.py**: 项目的主入口文件
- **requirements.txt**: 项目的依赖项配置

### 2.2 src目录

**src/** 目录是项目的核心代码目录，包含了智能体的各个模块：

#### 2.2.1 agent/ - 智能体核心模块
- **agent_base.py**: 智能体的基类，定义了智能体的基本接口和功能
- **gateway_guardian.py**: 网关守护者，负责保护API网关的安全
- **independent_session_manager.py**: 独立会话管理器，负责管理用户会话和聊天历史
- **memory_manager.py**: 记忆管理器，负责管理智能体的记忆和知识
- **model_router.py**: 模型路由器，负责路由不同的模型请求
- **persona_react.py**: 人格反应模块，负责智能体的人格表现
- **prompt_tree.py**: 提示树模块，负责管理和生成提示
- **reasoning_engine.py**: 推理引擎，负责智能体的推理和决策
- **user_profile.py**: 用户画像模块，负责管理用户的个人信息和偏好
- **world_knowledge.py**: 世界知识模块，负责管理智能体的世界知识

#### 2.2.2 agents/ - 具体智能体实现
- **agent_cluster.py**: 智能体集群，负责管理多个智能体
- **yueyue_agent.py**: 悦悦智能体的具体实现，是系统的核心智能体

#### 2.2.3 ai/ - 大模型集成
- **qiniu_llm.py**: 七牛云大模型的集成实现，负责与大模型的交互

#### 2.2.4 communication/ - 通信模块
- **agent_protocol.py**: 智能体通信协议，定义了智能体间的通信规范
- **communication_manager.py**: 通信管理器，负责管理智能体间的通信
- **mcp_client.py**: MCP客户端，负责与MCP（Master Control Program）的通信

#### 2.2.5 config/ - 配置模块
- **config.py**: 配置管理模块，负责加载和管理项目的配置

#### 2.2.6 database/ - 数据库模块
- **database_manager.py**: 数据库管理器，负责管理数据库的连接和操作

#### 2.2.7 frontend/ - 前端实现
- **static/**: 静态资源目录
  - **css/**: CSS样式文件
  - **js/**: JavaScript脚本文件
- **templates/**: 模板文件目录
  - **index.html**: 前端主页面

#### 2.2.8 gateway/ - API网关
- **api_gateway.py**: API网关，负责处理前端的API请求
- **load_balancer.py**: 负载均衡器，负责平衡API请求的负载
- **rate_limiter.py**: 速率限制器，负责限制API请求的速率

#### 2.2.9 scheduler/ - 调度器
- **task_scheduler.py**: 任务调度器，负责调度和执行定时任务

#### 2.2.10 security/ - 安全系统
- **audit_logger.py**: 审计日志记录器，负责记录系统的操作日志
- **auth_manager.py**: 认证管理器，负责用户的认证和授权
- **crypto_manager.py**: 加密管理器，负责数据的加密和解密
- **permission_manager.py**: 权限管理器，负责管理用户的权限
- **sensitive_detector.py**: 敏感信息检测器，负责检测和处理敏感信息

#### 2.2.11 skills/ - 技能系统
- **core_skills/**: 核心技能
  - **call_llm.py**: 调用大模型的技能
  - **log_operation.py**: 日志操作技能
  - **search_knowledge.py**: 知识搜索技能
- **device_skills/**: 设备控制技能
  - **led_brightness.py**: LED亮度控制技能
  - **led_off.py**: LED关闭技能
  - **led_on.py**: LED打开技能
- **mcp_skills/**: MCP技能
  - **netease_cloud_music.py**: 网易云音乐技能
- **memory_skills/**: 记忆技能
  - **distill_memory.py**: 记忆蒸馏技能
  - **recall_memory.py**: 记忆回忆技能
  - **save_preference.py**: 保存偏好技能
- **search_skills/**: 搜索技能
  - **hybrid_search.py**: 混合搜索技能
  - **keyword_search.py**: 关键词搜索技能
  - **vector_search.py**: 向量搜索技能
  - **web_search.py**: 网络搜索技能
- **task_skills/**: 任务技能
  - **create_reminder.py**: 创建提醒技能
  - **schedule_task.py**: 调度任务技能
  - **send_notification.py**: 发送通知技能
- **skill_base.py**: 技能基类，定义了技能的基本接口和功能
- **skill_manager.py**: 技能管理器，负责管理和执行技能

#### 2.2.12 tools/ - 工具模块
- **tool_manager.py**: 工具管理器，负责管理和执行工具

## 3. 智能体核心模块

智能体核心模块是系统的基础，提供了智能体的基本功能和接口。

### 3.1 AgentBase

`AgentBase`是所有智能体的基类，定义了智能体的基本接口和功能，包括：
- 执行任务的接口
- 状态管理
- 日志记录

### 3.2 IndependentSessionManager

`IndependentSessionManager`负责管理用户会话和聊天历史，包括：
- 创建和管理会话
- 存储和获取聊天历史
- 保存会话上下文

### 3.3 MemoryManager

`MemoryManager`负责管理智能体的记忆和知识，包括：
- 读取和写入灵魂文件
- 读取和写入个人资料文件
- 管理核心指南和用户偏好
- 更新和检索记忆

### 3.4 ReasoningEngine

`ReasoningEngine`负责智能体的推理和决策，包括：
- 逻辑推理
- 决策制定
- 问题解决

## 4. 具体智能体实现

### 4.1 YueYueAgent

`YueYueAgent`是系统的核心智能体，基于`AgentBase`实现，具有以下功能：
- 自然语言交互
- 大模型调用
- 技能执行
- 记忆管理
- 网络搜索
- 智能体协调
- MCP使用
- 推理能力

### 4.2 AgentCluster

`AgentCluster`负责管理多个智能体，包括：
- 智能体的注册和管理
- 任务的分配和执行
- 智能体间的协作

## 5. 大模型集成

### 5.1 QiniuLLM

`QiniuLLM`负责与七牛云大模型的交互，包括：
- 生成文本
- 流式响应
- 聊天完成
- API错误处理

## 6. 前端实现

前端实现基于HTML、CSS和JavaScript，提供了用户与智能体交互的界面，包括：
- 聊天界面
- 设备控制界面
- 任务管理界面
- 记忆管理界面
- 定时任务界面
- 记忆蒸馏界面
- 系统状态界面

## 7. API网关和通信

### 7.1 APIGateway

`APIGateway`负责处理前端的API请求，包括：
- 聊天接口
- 对话管理接口
- 设备控制接口
- 设备状态接口

### 7.2 CommunicationManager

`CommunicationManager`负责管理智能体间的通信，包括：
- 智能体间的消息传递
- 通信协议的实现
- 通信状态的管理

### 7.3 MCPClient

`MCPClient`负责与MCP（Master Control Program）的通信，包括：
- MCP服务的调用
- MCP消息的处理
- MCP状态的管理

## 8. 技能系统

技能系统是智能体的核心功能之一，提供了各种能力和服务，包括：

### 8.1 核心技能
- **call_llm**: 调用大模型生成文本
- **log_operation**: 记录系统操作日志
- **search_knowledge**: 搜索系统知识

### 8.2 设备控制技能
- **led_brightness**: 控制LED亮度
- **led_off**: 关闭LED
- **led_on**: 打开LED

### 8.3 MCP技能
- **netease_cloud_music**: 控制网易云音乐

### 8.4 记忆技能
- **distill_memory**: 蒸馏记忆，提取重要信息
- **recall_memory**: 回忆记忆，检索历史信息
- **save_preference**: 保存用户偏好

### 8.5 搜索技能
- **hybrid_search**: 混合搜索，结合多种搜索方法
- **keyword_search**: 关键词搜索
- **vector_search**: 向量搜索，基于语义相似度
- **web_search**: 网络搜索，获取外部信息

### 8.6 任务技能
- **create_reminder**: 创建提醒
- **schedule_task**: 调度任务
- **send_notification**: 发送通知

## 9. 安全系统

安全系统确保系统的安全性和可靠性，包括：

### 9.1 AuditLogger

`AuditLogger`负责记录系统的操作日志，包括：
- 用户操作日志
- 系统操作日志
- 安全事件日志

### 9.2 AuthManager

`AuthManager`负责用户的认证和授权，包括：
- 用户认证
- 权限验证
- 会话管理

### 9.3 CryptoManager

`CryptoManager`负责数据的加密和解密，包括：
- 敏感数据加密
- 数据传输加密
- 密钥管理

### 9.4 PermissionManager

`PermissionManager`负责管理用户的权限，包括：
- 权限定义
- 权限分配
- 权限检查

### 9.5 SensitiveDetector

`SensitiveDetector`负责检测和处理敏感信息，包括：
- 敏感信息识别
- 敏感信息过滤
- 敏感信息处理

## 10. 模块间的关系

智能体系统的各个模块之间存在着密切的关系，形成了一个完整的生态系统：

1. **前端**与**API网关**通过HTTP请求进行交互，前端发送请求，API网关处理请求并返回响应。
2. **API网关**与**智能体集群**通过函数调用进行交互，API网关将请求转发给智能体集群，智能体集群执行任务并返回结果。
3. **智能体集群**与**具体智能体**通过函数调用进行交互，智能体集群将任务分配给具体智能体，具体智能体执行任务并返回结果。
4. **具体智能体**与**大模型**通过API调用进行交互，具体智能体向大模型发送请求，大模型生成响应并返回结果。
5. **具体智能体**与**技能系统**通过函数调用进行交互，具体智能体调用技能系统的技能，技能系统执行技能并返回结果。
6. **具体智能体**与**记忆系统**通过函数调用进行交互，具体智能体读取和写入记忆，记忆系统存储和管理记忆。
7. **具体智能体**与**安全系统**通过函数调用进行交互，具体智能体使用安全系统的功能，安全系统提供安全保障。

## 11. 技术栈

智能体系统使用了以下技术栈：

- **后端**: Python 3.11
- **前端**: HTML, CSS, JavaScript
- **Web框架**: FastAPI
- **大模型**: 七牛云大模型
- **存储**: JSON文件
- **通信**: HTTP, WebSocket
- **安全**: JWT, 加密算法

## 12. 总结

智能家居智能体系统是一个功能强大、架构清晰的智能助手系统，它集成了大语言模型、技能系统、安全机制等多种功能，能够为用户提供智能的家居管理和交互体验。系统采用模块化设计，各个模块职责明确，相互独立，便于维护和扩展。

通过本文档，您可以了解智能体系统的整体架构、各个模块的功能和作用，以及模块间的关系。这将有助于您理解系统的设计理念和实现方式，为系统的使用和扩展提供参考。