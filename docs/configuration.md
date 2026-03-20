# 智能家居智能体配置指南

## 1. 系统要求

- **操作系统**: Windows 11
- **Python版本**: Python 3.11+
- **依赖库**: 见`requirements.txt`
- **硬件要求**: 至少4GB RAM，500MB存储空间

## 2. 环境配置

### 2.1 安装依赖

```bash
pip install -r requirements.txt
```

### 2.2 配置环境变量

创建`.env`文件，添加以下环境变量：

```env
# 七牛云大模型API密钥
QINIU_API_KEY=your_qiniu_api_key

# 七牛云大模型模型名称
QINIU_MODEL=kimi-k2.5

# 七牛云大模型API URL
QINIU_API_URL=https://api.qnaigc.com/v1/chat/completions

# 系统日志级别
LOG_LEVEL=INFO

# 数据存储路径（可选，默认使用用户目录下的.copaw文件夹）
# DATA_DIR=path/to/data
```

### 2.3 目录结构

系统会自动创建以下目录结构：

```
.copaw/
├── data/
│   └── scheduled_tasks.json  # 定时任务配置
├── agent_memory/
│   ├── MEMORY.md             # 长期记忆
│   ├── memory/               # 每日笔记
│   │   └── 2024-01-01.md     # 按日期存储的笔记
│   ├── versions/             # 记忆版本
│   └── personality/          # 个性配置
└── chats.json                # 对话历史
```

## 3. 定时任务配置

### 3.1 任务类型

- **每日任务**: 在指定时间点执行，格式为"HH:MM"
- **间隔任务**: 按固定时间间隔执行，单位为秒
- **CRON任务**: 支持复杂的CRON表达式，格式为"分 时 日 月 周"

### 3.2 任务配置示例

#### 每日任务

```python
from src.scheduler.task_scheduler import TaskScheduler

async def test_task():
    print("执行测试任务")

async def main():
    scheduler = TaskScheduler()
    # 每天12:00执行
    await scheduler.schedule_daily_task("test_daily", "12:00", test_task)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### 间隔任务

```python
from src.scheduler.task_scheduler import TaskScheduler

async def test_task():
    print("执行测试任务")

async def main():
    scheduler = TaskScheduler()
    # 每3600秒（1小时）执行一次
    await scheduler.schedule_interval_task("test_interval", 3600, test_task)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### CRON任务

```python
from src.scheduler.task_scheduler import TaskScheduler

async def test_task():
    print("执行测试任务")

async def main():
    scheduler = TaskScheduler()
    # 每天12:00执行
    await scheduler.schedule_cron_task("test_cron", "0 12 * * *", test_task)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 3.3 Windows计划任务

系统会自动创建Windows计划任务，需要管理员权限。创建的任务会在Windows任务计划程序中显示，名称格式为`Copaw_{task_name}`。

## 4. 记忆蒸馏配置

### 4.1 记忆蒸馏频率

建议每天执行一次记忆蒸馏，将最近7天的对话历史蒸馏为长期记忆。

### 4.2 记忆蒸馏示例

```python
from src.agent.memory_manager import MemoryManager

# 执行记忆蒸馏，处理最近7天的对话
memory_manager = MemoryManager()
result = memory_manager.distill_memory(days=7)
print(result)
```

### 4.3 记忆版本管理

系统会自动保存记忆版本，默认保留最近10个版本。可以通过API或代码获取和恢复记忆版本。

```python
from src.agent.memory_manager import MemoryManager

memory_manager = MemoryManager()

# 获取所有记忆版本
versions = memory_manager.get_memory_versions()
print(versions)

# 获取特定版本的记忆内容
if versions:
    version_content = memory_manager.get_memory_version_content(versions[0])
    print(version_content)
```

## 5. Agent智能核心配置

### 5.1 大模型配置

在`.env`文件中配置七牛云大模型API密钥和模型名称：

```env
QINIU_API_KEY=your_qiniu_api_key
QINIU_MODEL=kimi-k2.5
QINIU_API_URL=https://api.qnaigc.com/v1/chat/completions
```

### 5.2 Agent参数配置

可以在`ReActAgent`类的初始化方法中调整以下参数：

- `max_steps`: 最大思考步数，默认5
- `capabilities`: Agent能力配置
- `permissions`: Agent权限配置

### 5.3 Agent使用示例

```python
from src.agents.react_agent import ReActAgent

async def main():
    agent = ReActAgent()
    # 执行任务
    result = await agent.execute("帮我查询明天的天气")
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 6. API配置

### 6.1 启动API服务

```bash
python src/gateway/api_gateway.py
```

服务默认运行在`http://localhost:8000`，可以通过环境变量`PORT`修改端口。

### 6.2 API文档访问

启动服务后，可以访问以下地址查看API文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 7. 日志配置

### 7.1 日志级别

在`.env`文件中配置日志级别：

```env
LOG_LEVEL=INFO  # 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 7.2 日志输出

日志默认输出到控制台，也可以配置为输出到文件。

## 8. 安全配置

### 8.1 权限管理

- **Windows计划任务**: 需要管理员权限创建和管理
- **文件系统**: 需要读写权限到数据存储目录

### 8.2 数据保护

- 敏感信息（如API密钥）应存储在`.env`文件中，不要提交到版本控制系统
- 定期备份数据存储目录，防止数据丢失

## 9. 性能优化

### 9.1 内存管理

- 定期执行记忆蒸馏，减少短期记忆的大小
- 调整记忆老化参数，自动清理过期记忆

### 9.2 任务调度

- 合理设置任务执行频率，避免频繁执行占用系统资源
- 使用CRON表达式精确控制任务执行时间

### 9.3 API性能

- 使用异步API处理并发请求
- 缓存频繁访问的数据，减少重复计算

## 10. 故障排除

### 10.1 常见问题

#### 10.1.1 Windows计划任务创建失败

**原因**: 缺少管理员权限
**解决方案**: 以管理员身份运行命令行或Python脚本

#### 10.1.2 记忆蒸馏失败

**原因**: 缺少对话历史或权限不足
**解决方案**: 确保有对话历史数据，并且有读写权限

#### 10.1.3 Agent执行失败

**原因**: 大模型API密钥错误或网络问题
**解决方案**: 检查API密钥配置，确保网络连接正常

### 10.2 日志查看

查看系统日志，了解详细的错误信息：

```bash
# 查看控制台日志
python src/gateway/api_gateway.py

# 查看任务执行日志
# 任务执行结果会记录在任务历史中
```

## 11. 最佳实践

### 11.1 定时任务最佳实践

- 使用描述性的任务名称，便于识别
- 合理设置任务执行频率，避免过度占用系统资源
- 定期检查任务执行状态，确保任务正常运行

### 11.2 记忆管理最佳实践

- 每天执行一次记忆蒸馏，保持长期记忆的更新
- 定期查看和清理长期记忆，移除不需要的信息
- 使用记忆版本管理，在重要变更前创建记忆快照

### 11.3 Agent使用最佳实践

- 提供清晰、具体的任务描述，帮助Agent更好地理解需求
- 利用Agent的工具调用能力，处理复杂任务
- 定期更新Agent的个性配置，保持Agent的响应风格一致

## 12. 升级和维护

### 12.1 系统升级

- 定期更新依赖库，确保系统安全性
- 关注七牛云大模型API的更新，及时调整配置

### 12.2 数据备份

- 定期备份数据存储目录，包括：
  - 定时任务配置
  - 长期记忆
  - 记忆版本
  - 对话历史

### 12.3 系统监控

- 监控定时任务的执行状态
- 监控记忆蒸馏的执行结果
- 监控API服务的运行状态
