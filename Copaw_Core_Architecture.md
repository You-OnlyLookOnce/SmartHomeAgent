# Copaw 核心系统架构
> 描述定时任务、记忆蒸馏、Agent 智能三大核心功能的技术实现原理

---

## 📋 目录

1. [定时任务系统](#1-定时任务系统)
2. [记忆蒸馏系统](#2-记忆蒸馏系统)
3. [Agent 智能系统](#3-agent-智能系统)
4. [系统协同工作流程](#4-系统协同工作流程)
5. [附录：关键数据格式](#附录关键数据格式)

---

## 1. 定时任务系统

### 1.1 功能概述

定时任务系统允许 Agent 自我调度，周期性执行预设任务（如周报生成、状态检查等）。

```
┌─────────────────────────────────────────────────────────┐
│                    Cron 任务管理器                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  创建    │  │  查询    │  │  删除    │  ← 用户指令   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       ▼             ▼              ▼                    │
│  ┌─────────────────────────────────────────┐           │
│  │         Windows Task Scheduler          │           │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │           │
│  │  │ Task 1  │  │ Task 2  │  │ Task 3  │ │           │
│  │  │ UUID... │  │ UUID... │  │ UUID... │ │           │
│  │  └────┬────┘  └────┬────┘  └────┬────┘ │           │
│  └───────┼────────────┼────────────┼──────┘           │
│          ▼            ▼            ▼                   │
│  ┌─────────────────────────────────────────┐           │
│  │      copaw_task_runner.bat (触发器)      │           │
│  └──────────────────┬──────────────────────┘           │
└─────────────────────┼──────────────────────────────────┘
                      ▼
          会话恢复 → Agent 执行任务 → 输出文件
```

### 1.2 任务创建流程

#### 步骤 1：解析用户指令

用户输入示例：
```
帮我创建一个每周三和周六晚上9点执行的任务，生成AI领域周报
```

**解析逻辑：**
```
触发时间: "每周三和周六晚上9点" 
    → Cron表达式: "0 21 * * 3,6"
任务内容: "生成AI领域周报"
    → 命令脚本: browser_use + write_file 组合操作
任务名称: "AI周报生成"
    → 用于标识的友好名称
```

#### 步骤 2：构建任务命令

将任务内容封装为可执行命令：
```batch
# copaw_task_{UUID}.bat
cd C:\Users\Administrator\.copaw
python -c "
from browser_use import browser_use
# 执行具体的网页抓取和内容生成逻辑
browser_service.generate_weekly_report()
"
```

#### 步骤 3：注册到 Windows Task Scheduler

使用 `schtasks` 命令或 Python 的 `win32com.client`：

```python
# 伪代码展示注册逻辑
def create_cron_task(name, cron_expr, command):
    """
    name: 任务名称（如 'AI周报生成'）
    cron_expr: CRON 表达式（如 '0 21 * * 3,6'）
    command: 要执行的命令路径
    """
    
    # 转换为 Windows 计划任务格式
    # Windows 使用 XML 定义或通过 schtasks 命令行
    
    task_command = f"""
    schtasks /Create /tn "{name}_{uuid}" \
             /tr "{command}" \
             /sc WEEKLY /d WED,SAT /st 21:00 \
             /ru SYSTEM
    """
    
    # 执行注册
    execute_shell_command(task_command)
    
    # 记录到 chats.json 追踪
    save_to_registry(uuid, {
        'name': name,
        'cron': cron_expr,
        'status': 'active',
        'created': datetime.now().isoformat()
    })
```

### 1.3 CRON 表达式映射表

| CRON 格式 | 含义 | 转换为 Windows |
|-----------|------|---------------|
| `0 21 * * 3,6` | 每周三、六 21:00 | `/sc WEEKLY /d WED,SAT /st 21:00` |
| `0 12 * * *` | 每天 12:00 | `/sc DAILY /st 12:00` |
| `0 9 * * 1` | 每周一 09:00 | `/sc WEEKLY /d MON /st 09:00` |
| `*/30 * * * *` | 每30分钟 | 需特殊处理（Windows 不支持分频）|

### 1.4 任务生命周期管理

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  CREATED│────▶│  ACTIVE │────▶│ RUNNING │────▶│ SUCCESS/│
└─────────┘     └─────────┘     └─────────┘     │ FAILURE │
     ▲                                              │
     │                                              ▼
     └────────────────────────────────────────────┘
                    暂停/恢复/删除
```

**状态变更操作：**

| 操作 | 命令示例 | 效果 |
|------|----------|------|
| 暂停 | `chtasks /change /disable {task_id}` | 保留任务但不执行 |
| 恢复 | `schtasks /change /enable {task_id}` | 重新激活任务 |
| 删除 | `schtasks /delete /tn {task_id} /f` | 完全移除 |

### 1.5 关键技术难点

1. **CRON 与 Windows 任务调度器的表达差异**
   - Linux CRON 更灵活，Windows 需要用 `schtasks` 参数化
   
2. **会话保持问题**
   - 定时任务触发时，需要自动恢复与 Agent 的连接
   - 通过 `chats.json` 注册表管理活跃的会话上下文

3. **错误重试机制**
   - 任务失败后记录日志并可选重试 N 次
   - 重试间隔指数退避（30s → 2m → 5m）

---

## 2. 记忆蒸馏系统

### 2.1 功能概述

记忆蒸馏是将日常对话中产生的碎片信息提炼为长期知识的自动化过程。

```
┌─────────────────────────────────────────────────────────────┐
│                       记忆蒸馏流水线                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐        │
│   │ Daily Log │────▶│  Filter   │────▶│  Extract  │        │
│   │ (原始记录)│     │ (重要性)  │     │ (关键点)  │        │
│   └───────────┘     └───────────┘     └────┬──────┘        │
│                                            │                │
│          ┌─────────────────────────────────┘               │
│          ▼                                                  │
│   ┌─────────────────────────────────────────┐              │
│   │         LLM 摘要 + 结构化                 │              │
│   │  - 识别决策、教训、偏好                  │              │
│   │  - 去除冗余和临时信息                    │              │
│   │  - 按类别组织到 MEMORY.md                │              │
│   └─────────────────────────────────────────┘              │
│                          │                                  │
│                          ▼                                  │
│   ┌─────────────────────────────────────────┐              │
│   │           MEMORY.md (长期记忆)           │              │
│   └─────────────────────────────────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 蒸馏触发机制

#### 方式一：Heartbeat 定期触发

```python
# Heartbeat 配置
HEARTBEAT_INTERVAL = 1800  # 30 分钟

def heartbeat_handler():
    """每次心跳时检查是否需要记忆蒸馏"""
    
    # 1. 检查是否有新的每日笔记
    daily_files = list_memory_files(pattern="YYYY-MM-DD.md")
    
    # 2. 找到未处理的文件
    unprocessed = [f for f in daily_files if not is_distilled(f)]
    
    # 3. 超过 2 天的文件优先处理
    stale_files = filter_by_age(unprocessed, days=2)
    
    if stale_files or len(unprocessed) > 5:
        start_memorial_distillation(stale_files or unprocessed[:3])
```

#### 方式二：手动触发

用户在对话中输入：
```
"帮我整理一下这周的记忆"
→ 触发 memory_distill(week_range=True)
```

### 2.3 蒸馏算法流程

#### 步骤 1：内容采集

读取所有待处理文件：
```python
daily_notes = []
for file in daily_files:
    content = read_file(file)
    daily_notes.append({
        'path': file,
        'date': parse_date(file),
        'content': content,
        'tokens_estimate': count_tokens(content)
    })
```

#### 步骤 2：重要性过滤

使用轻量级分类器判断每条记录的优先级：

```python
importance_scores = {
    'decision': 0.9,      # 决策类
    'lesson': 0.85,       # 教训类
    'preference': 0.7,    # 用户偏好
    'project': 0.75,      # 项目进展
    'casual': 0.2,        # 闲聊
    'error_log': 0.6      # 错误记录
}

# 使用关键词匹配初步分类
def classify_entry(text):
    keywords = {
        'decision': ['决定', '选择', '确定', '最终方案'],
        'lesson': ['学会', '发现', '避免', '下次注意'],
        'preference': ['喜欢', '希望', '偏好', '建议'],
    }
    # ... 简化的关键词计数逻辑
    return category
```

#### 步骤 3：LLM 摘要提取

对高价值内容调用 LLM 进行结构化总结：

```
系统提示词:
你是记忆专家。请从以下日常记录中提取有价值的内容，
按以下结构组织：

【重要决策】
- 决策内容 + 理由

【经验教训】  
- 遇到的问题 + 解决方案

【用户偏好】
- 用户明确表达的喜好和要求

【项目里程碑】
- 完成的重大节点

要求：简洁、准确、保留原始意图。
```

```python
distilled_content = llm_generate(
    system="你是记忆整理专家...",
    user=f"原始记录:\n{selected_entries}",
    max_tokens=2000
)
```

#### 步骤 4：冲突检测与合并

```python
def merge_to_memory(new_content, existing_memory):
    """
    检测新旧记忆之间的冲突或重复
    """
    
    # 按类别分组
    new_items = parse_sections(new_content)
    
    for section in ['重要决策', '经验教训', '用户偏好']:
        new_entries = new_items.get(section, [])
        old_entries = extract_section(existing_memory, section)
        
        # 语义相似度检查
        for new_entry in new_entries:
            similar = find_similar_in(new_entry, old_entries, threshold=0.8)
            
            if similar:
                # 发现冲突 -> 询问用户或标记
                if has_conflict(new_entry, similar):
                    flag_for_review(new_entry)
                else:
                    continue  # 重复，跳过
            
            # 无冲突，添加到对应章节
            append_to_section(existing_memory, section, new_entry)
```

### 2.4 记忆版本追踪

每次蒸馏更新MEMORY.md时保存历史版本：

```
memory/versions/
├── MEMORY_2026-03-15_v1.md
├── MEMORY_2026-03-18_v2.md
└── MEMORY_2026-03-20_v3.md
```

**版本 diff 对比：**
```bash
diff MEMORY_2026-03-15_v1.md MEMORY_2026-03-18_v2.md
```

### 2.5 记忆老化机制

随着时间推移，部分记忆可能不再适用：

```python
# 自动老化规则
AGING_RULES = {
    'user_preference': {'max_age_days': 180, 'action': 'review'},
    'project_milestone': {'max_age_days': 365, 'action': 'archive'},
    'decision': {'max_age_days': None, 'action': 'keep'},  # 永久保留
    'lesson': {'max_age_days': 365, 'action': 'summarize'}
}

def age_check(memory_entry):
    entry_age = today - memory_entry.created_date
    rule = AGING_RULES.get(entry_entry.type)
    
    if entry_age.days > rule.max_age_days:
        return rule.action  # review/archive/summarize
    return 'keep'
```

### 2.6 关键技术要点

| 挑战 | 解决方案 |
|------|----------|
| 信息过载 | 分级过滤 + 重要性评分 |
| 语义去重 | 向量相似度匹配（cosine similarity > 0.8）|
| 冲突解决 | 标记待审 + 用户确认 |
| Token 限制 | 分批处理，每批 ≤ 4k tokens |
| 增量更新 | 只在内存中标记变更段落，整文件重写 |

---

## 3. Agent 智能系统

### 3.1 功能概述

Agent 通过大语言模型实现自主规划、工具调用和多轮思考能力。

```
┌─────────────────────────────────────────────────────────────────┐
│                           Agent Core                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │   用户输入    │───▶│   思考引擎    │───▶│   工具调用    │   │
│  │  (User Msg)   │    │  (ReAct Loop) │    │  (Tool Exec)  │   │
│  └───────────────┘    └───────┬───────┘    └───────▲───────┘   │
│                                │                    │           │
│  ┌─────────────────────────────┴────────────────────┴───────┐  │
│  │                     记忆知识库                            │  │
│  │  - PROFILE.md (用户画像)                                 │  │
│  │  - MEMORY.md (长期记忆)                                   │  │
│  │  - HEARTBEAT.md (任务清单)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      工具注册中心                          │  │
│  │  可用工具列表 → 动态加载 SKILL.md → 绑定函数接口           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 ReAct 思考循环

**ReAct（Reason + Act）** 是 Agent 的核心推理框架：

```
循环开始
    │
    ▼
┌─────────────────────────┐
│ Step 1: Thought         │ ◀── 分析当前情况和下一步目标
│   "我需要做什么？"       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Step 2: Action Selection│ ◀── 选择合适的工具
│   "我应该用什么工具？"    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Step 3: Action Execution│ ◀── 调用工具
│   tool_name(args)       │
└────────────┬────────────┘
             │
             ▼
    观察工具返回结果
             │
             ▼
    ┌──────────────────┐
    │ 需要更多步骤吗？   │
    └────┬─────────────┘
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    │         ▼
    │   ┌───────────────┐
    │   │ Step 4: Final │ ◀── 生成最终回答
    │   │   Answer      │
    │   └───────────────┘
    │         │
    └─────────┘
        循环结束
```

#### 思考链示例

用户输入：
```
帮我看看今天有没有关于 AI 教育的重要新闻
```

**ReAct 循环展开：**

```
[Thought]
用户想要了解 AI 教育相关新闻。
我有 news 技能可以获取新闻，但根据技能描述 news 函数不可用。
我可以使用 browser_use 手动访问几个权威科技新闻网站。

[Action] browser_use
action = "open"
url = "https://www.stdaily.com/"

[Observation]
页面打开成功，快照显示有首页标题列表。

[Thought]
我需要查看科技日报上是否有 AI 教育相关内容。
现在抓取页面快照，搜索关键词"AI"、"教育"、"人工智能"等。

[Action] browser_use
action = "snapshot"

[Observation]
快照中包含以下标题：
- "教育部发布新一代人工智能发展规划..."
- "某高校开设 AI+ 教育学专业..."
- ...

[Thought]
找到了几篇相关报道。继续访问其他新闻源获取更多样化信息。
接下来访问人民网和教育部门户网站。

[Action] browser_use
action = "navigate"
url = "https://edu.people.com.cn/"

... (继续循环)

[Final Answer]
今天我找到以下关于 AI 教育的重要新闻：
1. 教育部发布新一代人工智能发展规划...
2. 某高校开设 AI+ 教育学专业...
（详细摘要见下方）
```

### 3.3 工具发现机制

#### 工具注册表

```json
// tools_registry.json
{
  "available_tools": [
    {
      "name": "execute_shell_command",
      "description": "执行 Shell 命令",
      "parameters": ["command", "cwd", "timeout"],
      "skill_file": null
    },
    {
      "name": "browser_use",
      "description": "控制浏览器",
      "parameters": ["action", "url", "ref", "selector", ...],
      "skill_file": null
    },
    {
      "name": "cron_manage",
      "description": "管理定时任务",
      "parameters": ["action", "task_id", "expression"],
      "skill_file": "C:/Users/Administrator/.copaw/active_skills/cron/SKILL.md"
    },
    {
      "name": "news",
      "description": "获取新闻内容",
      "status": "unavailable",
      "reason": "依赖外部服务，当前禁用"
    }
  ]
}
```

#### 技能文档加载

当 Agent 需要了解某个工具的详细用法时：

```python
def load_skill_documentation(tool_name):
    """
    从 SKILL.md 加载工具的完整使用说明
    """
    skill_map = {
        'cron_manage': 'active_skills/cron/SKILL.md',
        'dingtalk_channel_connect': 'active_skills/dingtalk_channel/SKILL.md',
        'pdf': 'active_skills/pdf/SKILL.md',
        # ...
    }
    
    skill_path = skill_map.get(tool_name)
    if skill_path and os.path.exists(skill_path):
        return read_file(skill_path)
    return None
```

#### 工具选择决策树

```
收到用户请求
    │
    ▼
┌─────────────────────┐
│ 分析请求意图类型    │
│ - 文件操作?         │
│ - 网络浏览?         │
│ - 系统命令?         │
│ - 定时调度?         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 列出候选工具        │
│ (基于描述匹配)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 检查工具可用性      │
│ (是否启用/受限)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 评估工具成本        │
│ - Token 消耗?        │
│ - 时间消耗?         │
│ - 风险等级?         │
└──────────┬──────────┘
           │
           ▼
    选择最优工具
```

### 3.4 上下文管理与记忆注入

#### Prompt 组装策略

每次调用 LLM 前组装完整的上下文：

```python
def build_prompt(user_message):
    prompt_parts = [
        # 1. 系统角色定义
        """你叫小酷，是一个 AI 学习伙伴和智能助手。
        风格：轻松随意、亲切友好、带点小幽默。
        """,
        
        # 2. 用户画像（来自 PROFILE.md）
        f"""【用户资料】
        {read_profile()}
        """,
        
        # 3. 相关记忆（来自 MEMORY.md，截取最近相关的 3-5 条）
        f"""【近期记忆】
        {fetch_recent_memory(top_k=5)}
        """,
        
        # 4. 当前任务的 heartBeat 提示（如有）
        heartbeat = read_file("HEARTBEAT.md")
        if heartbeat:
            f"""【待办事项】
            {heartbeat}
            """,
        
        # 5. 可用工具列表
        f"""【可用工具】
        {render_tools_list()}
        """,
        
        # 6. 对话历史（最近 10 轮）
        f"""【对话历史】
        {format_chat_history(max_turns=10)}
        """,
        
        # 7. 当前用户消息
        f"""【当前输入】
        {user_message}
        """
    ]
    
    return "\n\n".join(prompt_parts)
```

#### 记忆检索增强

使用语义搜索查找与当前任务最相关的记忆片段：

```python
def fetch_context_relevant_memory(query, top_k=5):
    """
    从 MEMORY.md 和 memory/*.md 中检索相关片段
    """
    results = memory_search(
        query=query,
        max_results=top_k,
        min_score=0.2  # 最低相似度阈值
    )
    
    # 格式化输出供 LLM 阅读
    formatted = []
    for r in results:
        formatted.append(f"""
来源：{r.file_path}:{r.line_number}
内容：{r.content_snippet}
相似度：{r.score}
        """)
    
    return "\n".join(formatted)
```

### 3.5 多轮对话状态追踪

#### 状态机设计

```
IDLE
  │ 用户输入
  ▼
RECOGNIZING  ←── 识别用户意图和目标
  │
  ├─明确目标──▶ PLANNING  → 制定执行计划
  │                   │
  │                   ▼
  │              EXECUTING  → 逐 step 执行
  │                   │
  │                   ▼
  │              COMPLETING  → 汇总结果
  │                   │
  │                   ▼
  └─需求模糊──▶ CLARIFYING  → 询问澄清问题
                        │
                        ▼
                   (回到 RECOGNIZING)
```

#### 状态持久化

每个会话的状态保存在 `chats.json`：

```json
{
  "session_id": "1773304047625",
  "state": "EXECUTING",
  "current_plan": {
    "step": 3,
    "total_steps": 5,
    "completed": ["调研背景", "分析需求", "设计方案"],
    "pending": ["创新点提炼", "场景拓展"]
  },
  "tool_calls": [
    {"timestamp": "...", "tool": "browser_use", "status": "success"},
    {"timestamp": "...", "tool": "write_file", "status": "success"}
  ],
  "last_activity": "2026-03-20T21:05:00+08:00"
}
```

### 3.6 关键技术要点

| 能力 | 实现方式 | 优化技巧 |
|------|----------|----------|
| 自主思考 | ReAct 循环 + Chain-of-Thought | 限制最大步数防止无限循环 |
| 工具选择 | 语义匹配 + 成本评估 | 缓存热门工具的决策结果 |
| 记忆利用 | 向量检索 + 关键词过滤 | 设定记忆有效期限 |
| 上下文窗口 | 滑动窗口 + 摘要压缩 | 超出限制时压缩早期对话 |
| 错误恢复 | Try-Catch 包装 + 回退策略 | 记录错误模式优化未来选择 |

---

## 4. 系统协同工作流程

### 4.1 典型日工作流

```
08:00 ──▶ 系统启动
              │
              ▼
        加载配置与记忆
              │
              ▼
        读取 HEARTBEAT.md
              │
              ▼
    ┌─────────────────┐
    │ 检查定时任务     │── 如果有待执行任务
    │ (cron 触发)      │
    └────────┬────────┘
             │
             ▼
        Agent 准备就绪
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
Heartbeat 轮询     等待用户输入
(30 分钟周期)       
    │                 │
    ▼                 ▼
检查待办事项      接收用户请求
    │                 │
    ▼                 ▼
触发记忆蒸馏    →  ReAct 思考循环
(如果需要)              │
    │                   ▼
    └──────────▶ 执行工具调用
                        │
                        ▼
                   更新记忆
                        │
                        ▼
                   输出结果
```

### 4.2 三个核心模块的交互关系

```
                    ┌──────────────┐
                    │   User       │
                    │  (驱动源)    │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │ 定时任务     │ │  记忆蒸馏   │ │  Agent 智能  │
   │ (被动触发)  │ │ (主动维护)  │ │ (响应式)    │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   MEMORY.md  │
                   │ (共享存储)   │
                   └──────────────┘
```

### 4.3 数据流转图

```
┌─────────────┐
│  用户输入   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────┐
│              Agent Core                   │
│                                          │
│   ┌─────────┐    ┌─────────┐            │
│   │ Profile │    │ Memory  │◀────────────┤ 读取记忆
│   │  注入   │    │  检索   │            │
│   └────┬────┘    └────┬────┘            │
│        │              │                  │
│        ▼              ▼                  │
│   ┌─────────────────────────┐           │
│   │    ReAct 思考引擎        │           │
│   │  Thought → Action       │           │
│   └───────────┬─────────────┘           │
│               │                          │
│               ▼                          │
│   ┌─────────────────────────┐           │
│   │      工具执行器          │           │
│   │  - shell_command        │           │
│   │  - browser_use          │           │
│   │  - cron_manage          │           │
│   │  - file_operations      │           │
│   └───────────┬─────────────┘           │
│               │                          │
│               ▼                          │
│   ┌─────────────────────────┐           │
│   │      结果聚合与输出      │           │
│   └───────────┬─────────────┘           │
└───────────────┼─────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│              输出层                       │
│                                          │
│   ┌─────────────┐  ┌─────────────┐      │
│   │  对话回复   │  │  文件写入   │      │
│   │  (控制台)   │  │ (周报/报告) │      │
│   └─────────────┘  └─────────────┘      │
│                                          │
│   ┌─────────────┐  ┌─────────────┐      │
│   │  记忆更新   │  │  任务调度   │      │
│   │ (蒸馏归档)  │  │ (new cron)  │      │
│   └─────────────┘  └─────────────┘      │
└──────────────────────────────────────────┘
```

---

## 附录：关键数据格式

### A. chats.json 注册表示例

```json
{
  "sessions": {
    "1773304047625": {
      "session_id": "1773304047625",
      "user_id": "default",
      "channel": "console",
      "working_dir": "C:\\Users\\Administrator\\.copaw",
      "created_at": "2026-03-20T20:00:00+08:00",
      "last_active": "2026-03-20T21:30:00+08:00",
      "status": "active",
      "context_summary": "反向宠物机器人项目五步法讨论"
    }
  },
  "scheduled_tasks": {
    "1b3824d7-d7b2-4b11-abd6-82e2378bcf49": {
      "name": "GitHub 热门项目周报",
      "cron": "0 21 * * 3,6",
      "command": "...",
      "status": "active",
      "next_run": "2026-03-22T21:00:00+08:00"
    }
  }
}
```

### B. Cron 任务 ID 管理

```json
{
  "tasks": {
    "github_weekly": {
      "id": "1b3824d7-d7b2-4b11-abd6-82e2378bcf49",
      "schedule": "0 21 * * 3,6",
      "output_dir": "D:\\CoWorks\\weekly_reports\\",
      "last_success": "2026-03-19T21:05:00+08:00"
    },
    "bili_ai_weekly": {
      "id": "b91e8a9e-60f5-477f-9f8d-c20a6d21ccb5",
      "schedule": "0 21 * * 3,6",
      "output_dir": "D:\\CoWorks\\weekly_reports\\",
      "last_success": "2026-03-19T21:05:00+08:00"
    },
    "bili_robotics_weekly": {
      "id": "0ab413d0-1967-428c-bda6-6af2f7a3ac4e",
      "schedule": "0 21 * * 3,6",
      "output_dir": "D:\\CoWorks\\weekly_reports\\",
      "last_success": "2026-03-19T21:05:00+08:00"
    }
  }
}
```

### C. MEMORY.md 结构模板

```markdown
# MEMORY.md - 长期记忆库

## 🧠 重要决策
- [日期] 决策内容 + 理由

## 📚 经验教训
- [日期] 遇到的问题和解决方案

## 👤 用户偏好
- [类别] 具体偏好描述

## 🏆 项目里程碑
- [项目名称] 完成的关键节点

## 🔧 工具设置
- [工具名] 配置信息和注意事项

## 📊 会话历史
- [会话 ID] 主要讨论主题和时间
```

---

**文档版本**: v1.0  
**最后更新**: 2026-03-20  
**维护者**: 小酷 (AI Agent)
