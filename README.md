# 智能家居智能体使用指南

## 项目简介

智能家居智能体是一个基于九智能体框架和前沿AI架构的智能家居控制系统，能够控制设备、管理任务、提供个性化服务，具有拟人化交互能力。

## 系统架构

- **AI Agent集群**：设备控制Agent、AI笔记Agent、待办管理Agent、安全守护Agent
- **后端服务**：API网关、负载均衡、数据库集成、定时任务系统
- **安全模块**：认证授权、权限控制、数据加密、敏感信息检测
- **前端界面**：晨光主题UI，温暖专业的用户界面

## 环境搭建

### 1. 创建隔离环境

```bash
# 使用conda创建虚拟环境
conda create -n Home_Agent python=3.11

# 激活虚拟环境
# Windows
conda activate Home_Agent
# Linux/Mac
conda activate Home_Agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

在项目根目录创建 `.env` 文件，添加以下配置：

```env
# 七牛云API密钥
QINIU_ACCESS_KEY=your_access_key
QINIU_SECRET_KEY=your_secret_key

# 其他配置
SECRET_KEY=your_secret_key_for_encryption
```

### 3. 启动后端服务

```bash
# 启动API网关
python app.py

# 服务将在 http://localhost:8000 运行
# 注意：启动时可能会显示 http://0.0.0.0:8000，这是服务器绑定地址，客户端访问时请使用 http://localhost:8000
```

### 4. 打开前端网页

```bash
# 启动前端服务器
cd src/frontend
python -m http.server 8080

# 或直接在浏览器中打开
# file:///path/to/Home-AI-Agent/src/frontend/templates/index.html
```

## 功能使用

### 1. 设备控制

**支持的设备控制命令**：
- 开灯："打开客厅灯"
- 关灯："关闭卧室灯"
- 调亮度："调整厨房灯亮度为50%"
- 控制风扇："打开客厅风扇"
- 读取传感器："读取温度传感器"

**API接口**：
- POST `/api/device/control`：控制设备
- GET `/api/device/status/{device_id}`：获取设备状态

### 2. 任务管理

**支持的任务管理命令**：
- 创建提醒："明天早上8点提醒我开会"
- 安排任务："安排下周三天的购物任务"
- 发送通知："发送通知给家人"

**API接口**：
- POST `/api/reminder/create`：创建提醒
- GET `/api/reminder/list/{user_id}`：获取提醒列表

### 3. AI笔记

**支持的笔记命令**：
- 记笔记："记笔记：今天买了牛奶"
- 查看记忆："查看我之前的笔记"
- 搜索："搜索关于购物的笔记"

### 4. 安全监控

**支持的安全命令**：
- 安全检查："检查家里的安全状态"
- 监控："开始监控"
- 告警："发送安全告警"

### 5. 系统管理

**API接口**：
- GET `/api/agent/status`：获取Agent状态
- GET `/api/health`：健康检查
- POST `/api/chat`：通用聊天接口

## 核心功能

### Agent集群
- **DeviceControlAgent**：专门处理设备控制任务
- **NoteKeeperAgent**：专门处理笔记和记忆管理
- **TaskManagerAgent**：专门处理任务和提醒管理
- **SecurityAgent**：专门处理安全监控和告警

### 安全特性
- **认证授权**：用户登录和权限管理
- **数据加密**：敏感数据加密存储
- **敏感信息检测**：自动检测和脱敏敏感信息
- **安全审计**：记录所有操作日志

### 智能特性
- **拟人化交互**：自然语言理解和情感化回复
- **混合检索**：向量检索 + 关键词检索 + 规则匹配
- **记忆蒸馏**：自动学习和优化知识库
- **Gateway崩溃自修复**：系统高可用性
- **Self-Reflection机制**：对系统行为进行反思和改进
- **幻觉检测**：检测和处理大模型的幻觉
- **Workflow Engine**：编排和执行复杂工作流
- **SAGE风格用户画像**：分层用户画像管理
- **Lares风格意图/动作分离**：提高任务处理可靠性

## 技术栈

- **后端**：Python 3.11, FastAPI, SQLite
- **AI**：七牛云LLM服务
- **前端**：HTML, CSS, JavaScript
- **安全**：JWT认证, 数据加密

## 项目结构

```
Home-AI-Agent/
├── src/
│   ├── agent/          # Agent基础架构
│   ├── agents/         # 具体Agent实现
│   ├── gateway/        # API网关和负载均衡
│   ├── database/       # 数据库集成
│   ├── scheduler/      # 定时任务系统
│   ├── security/       # 安全模块
│   ├── skills/         # 原子化技能
│   └── frontend/       # 前端界面
├── data/               # 数据存储
├── app.py              # 主应用入口
├── requirements.txt    # 依赖项
└── README.md           # 使用指南
```

## 常见问题

### 1. 服务启动失败
- 检查端口是否被占用
- 检查依赖是否安装正确
- 检查API密钥配置

### 2. 设备控制无响应
- 检查设备是否在线
- 检查设备ID是否正确
- 检查网络连接

### 3. 前端页面无法访问
- 检查前端服务器是否启动
- 检查浏览器缓存
- 检查网络连接

## 开发和扩展

### 添加新设备
1. 在 `src/skills/device_skills/` 目录创建新的设备控制技能
2. 在 `DeviceControlAgent` 中注册新技能
3. 测试设备控制功能

### 添加新功能
1. 创建新的技能或Agent
2. 在API网关中添加对应的路由
3. 测试新功能

## 维护和更新

- **定期更新依赖**：`pip update -r requirements.txt`
- **备份数据**：定期备份 `data/` 目录
- **监控系统**：使用 `api/health` 接口监控系统状态

## 联系方式

如有问题或建议，请联系项目维护者。

---

**智能家居智能体 - 让生活更智能，更便捷！** 🚀