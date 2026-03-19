# Smart Home Agent 技术规范书

> 版本: V3.0 (基于九智能体框架 + 前沿AI架构)
> 日期: 2026-03-09
> 项目: 智能家居智能体

---

## 一、核心设计原则

### 1.1 算力支撑
- **AI算力提供商**: 七牛云平台
- **模型分层策略**:
  - **决策层 (Coordinator)**: 采用**旗舰模型** (如Qwen-Max)，具备最强推理能力
  - **执行层 (Experts)**: 采用**普通模型** (如Qwen-Turbo)，专注特定任务，高效低成本

### 1.2 代码规范
```c
// ============================================
// 核心参数宏定义区 (Config.h)
// ============================================

// 硬件配置
#define HARDWARE_UART_BAUDRATE    115200
#define HARDWARE_LED_PIN          GPIO_Pin_13
#define HARDWARE_STM32_FREQ        72000000

// 模型配置
#define MODEL_DECISION_PROVIDER   "qiniu"
#define MODEL_DECISION_NAME        "qwen-max"
#define MODEL_EXPERT_PROVIDER     "qiniu"
#define MODEL_EXPERT_NAME          "qwen-turbo"
#define MODEL_TEMPERATURE         0.7
#define MODEL_MAX_TOKENS          2048

// Agent配置
#define AGENT_MAX_CONTEXT         10
#define AGENT_TIMEOUT_SECONDS     30
#define AGENT_RETRY_COUNT         3

// 检索配置
#define LANCEDB_DIMENSION         1536
#define HYBRID_SEARCH_TOP_K        5
#define MEMORY_DISTRILL_INTERVAL   "02:00"  // 每日凌晨2点

// 前端配置
#define UI_THEME_COLOR            "#FFF5E6"  // 晨光色
#define UI_THEME_WARMTH           0.85
```

---

## 二、Agent架构设计 (三层隔离系统)

### 2.1 三层隔离模型

```
┌─────────────────────────────────────────────────────────────┐
│                      整体系统架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    身份层 (Identity)                │   │
│   │   - Agent唯一标识 (UUID)                            │   │
│   │   - 角色定义与能力边界                               │   │
│   │   - 权限清单                                         │   │
│   │   - 知识库引用                                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    状态层 (State)                   │   │
│   │   - 当前对话上下文                                   │   │
│   │   - 会话历史摘要                                     │   │
│   │   - 临时变量与缓存                                   │   │
│   │   - 情感状态标记                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    工作层 (Work)                    │   │
│   │   - 原子化技能 (Skills)                             │   │
│   │   - 工具调用                                         │   │
│   │   - 执行日志                                         │   │
│   │   - 成果产出                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 三层隔离实现

```python
class AgentBase:
    """Agent基类 - 实现三层隔离"""
    
    def __init__(self, agent_id: str, role: str):
        # ========== 身份层 (Identity) ==========
        self.agent_id = agent_id
        self.role = role
        self.capabilities = self._load_capabilities()
        self.permissions = self._load_permissions()
        self.knowledge_base = self._init_knowledge_base()
        
        # ========== 状态层 (State) ==========
        self.context = []          # 对话上下文
        self.session_summary = ""  # 会话摘要
        self.temp_variables = {}   # 临时变量
        self.emotion_state = "neutral"  # 情感状态
        
        # ========== 工作层 (Work) ==========
        self.skills = []           # 原子化技能
        self.execution_log = []   # 执行日志
        self.output_buffer = []    # 输出缓冲
        
    def _load_capabilities(self) -> Dict:
        """加载角色能力定义"""
        # 从配置中读取该Agent能做什么
        
    def _load_permissions(self) -> List[str]:
        """加载权限清单"""
        # 明确列出可访问的资源和操作
        
    def _init_knowledge_base(self) -> Any:
        """初始化知识库引用"""
        # 关联该Agent的专业知识
        
    def execute(self, task: str) -> Dict:
        """执行任务 - 工作层"""
        # 1. 验证权限 (身份层)
        # 2. 更新状态 (状态层)
        # 3. 执行技能 (工作层)
        pass
```

---

## 三、原子化技能体系 (Skills)

### 3.1 设计原则
- **小而精**: 每个Skill只完成单一原子操作
- **可组合**: 多个Skills可以自由组合完成复杂任务
- **可复用**: Skills可以在不同Agent间共享

### 3.2 技能分类

```
Skills/
├── core_skills/           # 核心技能 (所有Agent可用)
│   ├── search_knowledge   # 知识检索
│   ├── call_llm          # 调用大模型
│   └── log_operation     # 操作日志
│
├── device_skills/         # 设备控制技能
│   ├── led_on            # 开灯
│   ├── led_off           # 关灯
│   └── led_brightness    # 调亮度
│
├── memory_skills/        # 记忆技能
│   ├── save_preference   # 保存偏好
│   ├── recall_memory     # 回忆记忆
│   └── distill_memory    # 记忆蒸馏
│
├── search_skills/        # 检索技能
│   ├── vector_search     # 向量检索
│   ├── keyword_search    # 关键词检索
│   └── hybrid_search     # 混合检索
│
└── task_skills/          # 任务技能
    ├── create_reminder   # 创建提醒
    ├── schedule_task     # 安排任务
    └── send_notification # 发送通知
```

### 3.3 技能定义示例

```python
# skill_led_on.py - 开灯技能 (原子化)
class LedOnSkill:
    """开灯 - 最小的原子化操作"""
    
    # 技能元信息
    SKILL_NAME = "led_on"
    SKILL_DESCRIPTION = "打开指定LED灯"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "device_id": {"type": "string", "required": True},
        "brightness": {"type": "int", "default": 100, "range": [0, 100]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "device_state": "dict"
    }
    
    async def execute(self, params: Dict) -> Dict:
        device_id = params["device_id"]
        brightness = params.get("brightness", 100)
        
        # 1. 调用串口控制器
        result = await serial_controller.send_command({
            "action": "led_on",
            "device_id": device_id,
            "brightness": brightness
        })
        
        # 2. 记录日志
        await self.log_operation(device_id, "led_on", result)
        
        # 3. 返回结果
        return {
            "success": result["status"] == "ok",
            "message": f"已打开灯 {device_id}",
            "device_state": result.get("state", {})
        }
```

---

## 四、决策层架构 (ReAct + 混合检索)

### 4.1 决策层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    决策层 (Coordinator)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐    ┌──────────────┐    ┌─────────────┐ │
│   │   用户输入   │───→│   ReAct引擎  │───→│  响应生成   │ │
│   └──────────────┘    └──────────────┘    └─────────────┘ │
│                              ↓                              │
│                    ┌──────────────────┐                    │
│                    │   混合检索引擎   │                    │
│                    ├──────────────────┤                    │
│                    │  LanceDB向量检索 │                    │
│                    │  + 关键词检索    │                    │
│                    │  + 规则匹配      │                    │
│                    └──────────────────┘                    │
│                              ↓                              │
│                    ┌──────────────────┐                    │
│                    │   记忆蒸馏系统   │                    │
│                    │  (每日凌晨自动) │                    │
│                    └──────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 LanceDB + 混合检索实现

```python
import lancedb
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document

class HybridSearchEngine:
    """混合检索引擎 - 向量 + 关键词"""
    
    def __init__(self):
        # 初始化LanceDB (向量数据库)
        self.db = lancedb.connect("./data/lancedb")
        self.table = self.db.open_table("agent_memory")
        
        # 初始化BM25 (关键词检索)
        self.bm25_index = None
        self.documents = []
        
    def add_documents(self, docs: List[Document]):
        """添加文档到检索库"""
        # 1. 添加到向量库
        self.table.add([
            {"id": doc.id, "content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ])
        
        # 2. 添加到BM25索引
        self.documents.extend(docs)
        self.bm25_index = BM25Retriever.from_documents(self.documents)
        
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索"""
        results = []
        
        # 1. 向量检索 (语义理解)
        vector_results = await self._vector_search(query, top_k)
        results.extend(vector_results)
        
        # 2. 关键词检索 (精确匹配)
        keyword_results = await self._keyword_search(query, top_k)
        results.extend(keyword_results)
        
        # 3. 规则匹配 (高优先级)
        rule_results = self._rule_match(query)
        results.extend(rule_results)
        
        # 4. 去重和排序
        results = self._deduplicate_and_rank(results, top_k)
        
        return results
    
    async def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """LanceDB向量检索"""
        # 使用嵌入模型将查询转为向量
        embedding = await get_embedding(query)
        
        # 向量相似度搜索
        results = self.table.search(embedding).limit(top_k).to_list()
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """BM25关键词检索"""
        return self.bm25_index.get_relevant_documents(query)[:top_k]
    
    def _rule_match(self, query: str) -> List[Dict]:
        """规则匹配 (高优先级)"""
        # 预设规则，如"开灯" -> 直接触发led_on技能
        rules = {
            "开灯": {"skill": "led_on", "priority": 100},
            "关灯": {"skill": "led_off", "priority": 100},
            "提醒": {"skill": "create_reminder", "priority": 100}
        }
        
        results = []
        for keyword, rule in rules.items():
            if keyword in query:
                results.append({"rule": rule, "score": rule["priority"]})
        return results
```

### 4.3 记忆蒸馏系统 (自主进化)

```python
class MemoryDistiller:
    """夜间记忆蒸馏 - 自主进化系统"""
    
    def __init__(self):
        self.distill_interval = "02:00"  # 每日凌晨2点
        self.embedding_model = "text-embedding-v3"
        
    async def nightly_distill(self):
        """执行夜间记忆蒸馏"""
        # 1. 收集今日交互数据
        interactions = await self._collect_daily_interactions()
        
        # 2. 提取有价值的信息
        valuable_insights = await self._extract_insights(interactions)
        
        # 3. 更新知识库
        await self._update_knowledge_base(valuable_insights)
        
        # 4. 优化决策策略
        await self._optimize_decision_strategy()
        
        # 5. 生成蒸馏报告
        report = await self._generate_distill_report()
        
        return report
    
    async def _extract_insights(self, interactions: List[Dict]) -> List[Dict]:
        """使用LLM提取有价值的见解"""
        prompt = f"""
        请分析以下交互记录，提取有价值的见解和模式：
        
        交互记录：{interactions}
        
        请提取：
        1. 用户习惯模式
        2. 成功的响应策略
        3. 需要改进的地方
        4. 新的知识要点
        
        以JSON格式返回。
        """
        
        response = await llm_call(prompt, model="qwen-turbo")
        return json.loads(response)
    
    async def _optimize_decision_strategy(self):
        """优化决策策略"""
        # 分析哪些决策路径效果最好
        # 更新ReAct引擎的决策权重
        pass
```

### 4.4 Gateway崩溃自修复机制

```python
import asyncio
import logging
from datetime import datetime, timedelta

class GatewayGuardian:
    """Gateway守护者 - 崩溃自修复机制"""
    
    def __init__(self):
        self.health_check_interval = 30  # 每30秒检查一次
        self.max_restart_attempts = 3
        self.self_healing_enabled = True
        
    async def start_health_monitor(self):
        """启动健康监控"""
        while self.self_healing_enabled:
            try:
                await self._health_check()
            except Exception as e:
                logging.error(f"健康检查异常: {e}")
                await self._trigger_self_healing()
            
            await asyncio.sleep(self.health_check_interval)
    
    async def _health_check(self) -> bool:
        """执行健康检查"""
        checks = {
            "gateway_process": self._check_process,
            "api_response_time": self._check_api_latency,
            "database_connection": self._check_db,
            "memory_usage": self._check_memory,
            "llm_service": self._check_llm_service
        }
        
        results = {}
        for name, check_func in checks.items():
            results[name] = await check_func()
        
        # 判断整体健康状态
        all_healthy = all(results.values())
        
        if not all_healthy:
            logging.warning(f"健康检查异常: {results}")
            
        return all_healthy
    
    async def _trigger_self_healing(self):
        """触发自修复"""
        logging.info("开始自修复流程...")
        
        # 1. 记录崩溃现场
        await self._capture_crash_context()
        
        # 2. 尝试重启Gateway进程
        for attempt in range(self.max_restart_attempts):
            try:
                logging.info(f"尝试重启 (第{attempt + 1}次)...")
                await self._restart_gateway()
                
                # 3. 验证重启是否成功
                if await self._verify_restart():
                    logging.info("自修复成功!")
                    await self._send_notification("Gateway已自动恢复")
                    return
                    
            except Exception as e:
                logging.error(f"重启失败: {e}")
                await asyncio.sleep(5)  # 等待5秒后重试
        
        # 4. 所有尝试都失败，发送告警
        logging.critical("自修复失败，需要人工介入")
        await self._send_alert("Gateway自修复失败，请立即处理!")
    
    async def _capture_crash_context(self):
        """记录崩溃现场信息"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent(),
            "active_connections": len(self.get_active_connections()),
            "recent_errors": self.get_recent_errors(10)
        }
        
        # 保存到日志
        logging.critical(f"崩溃上下文: {context}")
        
        # 可选：上传到监控系统
        # await self._upload_crash_context(context)
```

---

## 五、拟人化ReAct回复机制

### 5.1 拟人化设计

```python
class PersonaReActAgent:
    """拟人化ReAct Agent"""
    
    def __init__(self):
        self.personality = {
            "name": "小酷",
            "tone": "温暖、亲切、专业",
            "greeting": "你好呀！有什么我可以帮你的吗？",
            "thinking_phrase": "让我想想...",
            "action_phrase": "好，我现在帮你",
            "success_phrase": "已经帮你搞定啦！",
            "uncertain_phrase": "嗯...这个问题我需要再想想"
        }
        
    async def think(self, context: Dict) -> str:
        """思考过程 - 带有人类思考的节奏感"""
        # 输出思考提示（可选）
        yield self.personality["thinking_phrase"]
        
        # 执行推理
        reasoning_result = await self._do_reasoning(context)
        
        return reasoning_result
    
    async def act(self, plan: Dict) -> str:
        """执行过程 - 告知用户正在行动"""
        yield self.personality["action_phrase"]
        
        # 执行计划
        result = await self._execute_plan(plan)
        
        return result
    
    async def respond(self, context: Dict) -> str:
        """生成拟人化回复"""
        # 完整的ReAct流程
        thinking = await self.think(context)
        plan = await self._create_plan(thinking)
        result = await self.act(plan)
        
        # 生成最终回复
        response = self._format_response(result, context)
        
        return response
    
    def _format_response(self, result: Dict, context: Dict) -> str:
        """格式化回复 - 带有人类情感"""
        if result.get("success"):
            # 成功回复 - 带有关心
            base = self.personality["success_phrase"]
            detail = result.get("message", "")
            
            # 根据上下文添加关心语
            if context.get("time") == "morning":
                return f"早上好！{base} {detail} 祝你有美好的一天！"
            elif context.get("time") == "night":
                return f"晚安！{base} {detail} 好梦！"
            else:
                return f"{base} {detail}"
        else:
            # 失败回复 - 真诚道歉
            return f"抱歉，{result.get('error', '出了点问题')}。让我再试试看？"
```

### 5.2 回复风格配置

```python
RESPONSE_STYLES = {
    "morning": {
        "color": "#FFF8E7",  # 晨光黄
        "emoji": "☀️",
        "phrase": "早安！新的一天开始啦~"
    },
    "noon": {
        "color": "#FFFBF0",  # 阳光白
        "emoji": "🌤️",
        "phrase": "中午好！吃了吗？"
    },
    "evening": {
        "color": "#FFE4C4",  # 晚霞橙
        "emoji": "🌆",
        "phrase": "晚上好！今天过得怎么样？"
    },
    "night": {
        "color": "#E6E6FA",  # 星光淡紫
        "emoji": "🌙",
        "phrase": "夜深了，该休息啦~"
    }
}
```

---

## 六、前端UI设计 (晨光风格)

### 6.1 主题色彩

```css
/* 晨光主题 CSS Variables */
:root {
    /* 主色调 - 晨光 */
    --theme-primary: #FFB347;        /* 晨光橙 */
    --theme-secondary: #FFECD2;      /* 晨光白 */
    --theme-accent: #FFCC33;        /* 阳光黄 */
    
    /* 背景色 */
    --bg-main: linear-gradient(180deg, #FFF5E6 0%, #FFFBF0 50%, #FFECD2 100%);
    --bg-card: rgba(255, 255, 255, 0.85);
    --bg-glass: rgba(255, 255, 255, 0.6);
    
    /* 文字色 */
    --text-primary: #5D4E37;         /* 温暖深棕 */
    --text-secondary: #8B7355;       /* 柔和棕 */
    --text-muted: #B8A99A;           /* 淡棕 */
    
    /* 功能色 */
    --success: #7CB342;              /* 清新绿 */
    --warning: #FFB74D;              /* 温暖橙 */
    --error: #E57373;                 /* 柔和红 */
    --info: #64B5F6;                 /* 天空蓝 */
    
    /* 特效 */
    --shadow-warm: 0 4px 20px rgba(255, 179, 71, 0.15);
    --shadow-card: 0 8px 32px rgba(93, 78, 55, 0.08);
    --glow-subtle: 0 0 20px rgba(255, 204, 51, 0.2);
    
    /* 圆角 */
    --radius-small: 12px;
    --radius-medium: 20px;
    --radius-large: 32px;
    
    /* 动画 */
    --transition-smooth: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 6.2 界面布局

```html
<!-- 主界面结构 -->
<div class="app-container">
    <!-- 顶部晨光栏 -->
    <header class="sunrise-header">
        <div class="sunrise-glow"></div>
        <h1 class="app-title">🌤️ 小酷</h1>
        <p class="app-subtitle">你的智能家居伙伴</p>
    </header>
    
    <!-- 对话区域 -->
    <main class="chat-area">
        <div class="message received">
            <div class="avatar">🌟</div>
            <div class="bubble">你好呀！今天过得怎么样？</div>
        </div>
        <div class="message sent">
            <div class="bubble">我回来了</div>
        </div>
    </main>
    
    <!-- 输入区域 -->
    <footer class="input-area">
        <input type="text" placeholder="跟小酷说点什么..." />
        <button class="send-btn">发送</button>
    </footer>
</div>
```

---

## 七、模型分层策略

### 7.1 模型分配

| 层级 | Agent | 使用模型 | 用途 |
|------|-------|----------|------|
| 决策层 | Coordinator | **Qwen-Max** (旗舰) | 复杂推理、任务规划 |
| 执行层 | DeviceControl | Qwen-Turbo | 设备控制 |
| 执行层 | NoteKeeper | Qwen-Turbo | 笔记处理 |
| 执行层 | TaskManager | Qwen-Turbo | 任务管理 |
| 执行层 | Security | Qwen-Turbo | 安全检查 |
| 工具层 | 原子Skills | Qwen-Turbo | 简单工具调用 |

### 7.2 模型调用示例

```python
class ModelRouter:
    """模型路由器 - 根据任务选择合适模型"""
    
    MODELS = {
        "旗舰": {
            "provider": "qiniu",
            "name": "qwen-max",
            "strengths": ["复杂推理", "创意生成", "深度理解"],
            "cost_factor": 3.0  # 成本倍数
        },
        "普通": {
            "provider": "qiniu", 
            "name": "qwen-turbo",
            "strengths": ["快速响应", "简单任务", "工具调用"],
            "cost_factor": 1.0
        }
    }
    
    async def route(self, task: Dict) -> str:
        """根据任务类型选择模型"""
        task_type = task.get("type")
        
        if task_type in ["复杂推理", "创意生成", "深度理解"]:
            return self.MODELS["旗舰"]
        else:
            return self.MODELS["普通"]
    
    async def call(self, prompt: str, task: Dict) -> str:
        """调用模型"""
        model_info = await self.route(task)
        
        response = await qiniu_client.chat.completions.create(
            model=model_info["name"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
```

---

## 八、系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (前端)                           │
│         🌅 晨光主题 UI • 拟人化交互 • 温暖体验                  │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Gateway (API网关)                          │
│            崩溃自修复 • 负载均衡 • 限流保护                      │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      决策层 (Coordinator)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  旗舰模型    │  │  混合检索   │  │   记忆蒸馏系统       │ │
│  │  (Qwen-Max) │  │  (LanceDB)   │  │   (每日自动)         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Agent集群 (执行层)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 设备控制 │ │  AI笔记  │ │  待办管理 │ │ 安全守护 │         │
│  │ Agent   │ │  Agent   │ │  Agent   │ │  Agent   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                        (普通模型 Qwen-Turbo)                    │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      原子化技能层 (Skills)                       │
│  led_on | led_off | led_brightness | create_reminder | ...     │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      执行层 (硬件/服务)                         │
│        STM32 (LED) │ SQLite │ 七牛云LLM │ 定时任务             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 九、技术规范总结

| 特性 | 实现方案 |
|------|----------|
| **算力** | 七牛云平台 |
| **模型分层** | 决策层Qwen-Max + 执行层Qwen-Turbo |
| **Agent架构** | 身份层 + 状态层 + 工作层 (三层隔离) |
| **工具设计** | 原子化Skills (小而精) |
| **检索增强** | LanceDB向量 + BM25混合检索 |
| **自主进化** | 夜间记忆蒸馏系统 |
| **容错机制** | Gateway崩溃自修复 |
| **UI风格** | 晨光主题 (温暖、专业) |
| **交互方式** | 拟人化ReAct回复 |
| **代码规范** | 核心参数宏定义 |

---

**技术规范完成！V3.0版本融合了最前沿的AI Agent架构理念。** 🚀

> 提示：这份技术规范将作为 `SmartHomeAgent_Project` 的核心技术文档，指导后续开发工作。