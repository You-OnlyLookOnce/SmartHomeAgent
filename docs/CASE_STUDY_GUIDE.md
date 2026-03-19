# AI智能家居案例创新点借鉴指南

> 版本: V1.0
> 日期: 2026-03-09
> 用途: 智能家居AI智能体项目技术参考

---

## 一、案例概览

| 案例 | 来源 | 核心贡献 | 成功率 |
|------|------|----------|--------|
| **SAGE** | 三星蒙特利尔AI中心 | LLM提示树 + 工具链 | 76% |
| **Lares** | Matt Webb | 意图/行动分离 | - |
| **Energy Agent** | GitHub | 多Agent协调 | - |

---

## 二、SAGE 核心创新点

### 2.1 动态LLM提示树

**创新描述**: 用户请求触发LLM控制的离散动作序列，动态构建提示树来决定下一步操作。

```
用户请求 → LLM决策 → 动作执行 → 结果评估 → 继续/终止
```

**可借鉴程度**: ⭐⭐⭐⭐⭐

**实施建议**:
```python
class SAGEAgent:
    def __init__(self):
        self.prompt_tree = PromptTree()
    
    def process_request(self, user_request):
        # 构建动态提示树
        current_prompt = self.prompt_tree.build(user_request)
        
        # LLM决策下一步
        action = self.llm.decide(current_prompt)
        
        # 执行并评估
        result = self.executor.execute(action)
        
        if self.evaluator.is_success(result):
            return result
        else:
            # 构建反馈提示，继续决策
            return self.process_request(user_request + f" 上次失败: {result}")
```

### 2.2 层级用户画像

**创新描述**: 
- 每日偏好摘要 → 全局用户画像 → 个性化工具

```
┌─────────────────────────────────────┐
│         用户长期记忆                │
│   (每日 utterance 累积存储)         │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│       Daily Preference Summary      │
│        (每日偏好摘要)               │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│        Global User Profile          │
│         (全局用户画像)              │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Personalization Tool           │
│        (个性化工具)                 │
└─────────────────────────────────────┘
```

**可借鉴程度**: ⭐⭐⭐⭐⭐

**实施建议**:
```python
class UserProfileManager:
    """层级用户画像管理器"""
    
    def __init__(self):
        self.long_term_memory = []      # 长期记忆
        self.daily_summaries = {}       # 每日摘要 {date: summary}
        self.global_profile = {}        # 全局画像
    
    def add_interaction(self, utterance: str):
        """添加用户交互记录"""
        self.long_term_memory.append({
            'timestamp': datetime.now(),
            'utterance': utterance
        })
    
    def distill_daily(self):
        """夜间记忆蒸馏 - 生成每日摘要"""
        today = date.today().isoformat()
        today_memories = [m for m in self.long_term_memory 
                         if m['timestamp'].date() == date.today()]
        
        # 调用LLM生成摘要
        summary = self.llm.summarize(today_memories)
        self.daily_summaries[today] = summary
    
    def update_global_profile(self):
        """更新全局用户画像"""
        # 汇总所有每日摘要
        all_summaries = list(self.daily_summaries.values())
        
        # 调用LLM生成全局画像
        self.global_profile = self.llm.generate_profile(all_summaries)
    
    def personalize_response(self, query: str) -> str:
        """生成个性化响应"""
        context = {
            'global_profile': self.global_profile,
            'recent_summaries': list(self.daily_summaries.values())[-7:]
        }
        return self.llm.generate(query, context=context)
```

### 2.3 API无代码控制

**创新描述**: LLM直接读取在线API文档，动态生成调用代码。

**实现流程**:
```
1. API Planner (设备与能力选择)
     ↓
2. Documentation Retrieval (文档检索)
     ↓
3. Get Attribute (读取状态)
     ↓
4. Execution (发送命令)
```

**可借鉴程度**: ⭐⭐⭐

**实施建议**: 可用于未来扩展更多智能设备

### 2.4 设备消歧 (VLM)

**创新描述**: 使用视觉语言模型(CLIP)匹配用户自然语言描述与实际设备。

```
用户说: "打开钢琴旁边的灯"
     ↓
房间照片 + CLIP模型
     ↓
识别"钢琴"位置 + 旁边设备
     ↓
定位目标设备
```

**可借鉴程度**: ⭐⭐ (可选功能)

---

## 三、Lares 核心创新点

### 3.1 意图与行动分离

**创新描述**: 将"决定调用哪个函数"和"确定函数参数"分成两步。

```
传统方式:
LLM直接输出: toggleLight(lightId="lounge")

Lares方式:
Step 1: decideBestFunction() → 决定调用 toggleLight
Step 2: toggleLight(lightId="lounge") → 确定参数并执行
```

**可借鉴程度**: ⭐⭐⭐⭐⭐

**核心价值**:
- 支持Chain-of-Thought推理
- 提高Agent可靠性
- 便于调试和追踪

**实施建议**:
```python
class LaresAgent:
    """Lares风格的Agent - 意图行动分离"""
    
    def __init__(self):
        self.functions = self._register_functions()
    
    def process(self, user_request: str) -> str:
        transcript = self._build_transcript(user_request)
        
        # ========== 第一步: 意图识别 ==========
        intent_result = self.llm.call(
            function="decideBestFunction",
            transcript=transcript,
            available_functions=self.functions
        )
        
        chosen_function = intent_result['bestFunction']
        reasoning = intent_result['reasoning']
        
        # 添加意图总结到transcript
        transcript.add_summary(
            f"决定调用 {chosen_function}，原因: {reasoning}"
        )
        
        # ========== 第二步: 参数确定 ==========
        action_result = self.llm.call(
            function=chosen_function,
            transcript=transcript,
            params_schema=self.functions[chosen_function]['params']
        )
        
        # 执行函数
        return self.executor.execute(chosen_function, action_result)
    
    def _register_functions(self) -> dict:
        """注册可用函数"""
        return {
            "toggleLight": {
                "description": "开关灯光",
                "params": {
                    "lightId": "灯光ID"
                }
            },
            "moveRobot": {
                "description": "移动机器人",
                "params": {
                    "destinationRoomId": "目标房间ID"
                }
            },
            "askUser": {
                "description": "询问用户",
                "params": {
                    "question": "问题内容"
                }
            },
            "halt": {
                "description": "完成任务",
                "params": {
                    "messageToUser": "回复消息"
                }
            }
        }
```

### 3.2 世界知识管理

**创新描述**: 动态供给最新世界状态，区分"隐藏状态"与"公开状态"。

```
┌────────────────────────────────────────────┐
│           真实世界状态 (Hidden)             │
│   - 宠物位置 🐕                            │
│   - 人员位置                               │
│   - 可移动物品                             │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         Agent世界知识 (Public)             │
│   - 设备状态 (灯/门/温度)                  │
│   - 房间布局                               │
│   - 已知信息                               │
└────────────────────────────────────────────┘
```

**可借鉴程度**: ⭐⭐⭐⭐⭐

**实施建议**:
```python
class WorldKnowledgeManager:
    """世界知识管理器 - Lares风格"""
    
    def __init__(self):
        # 隐藏的真实世界状态
        self.hidden_state = {
            'pets': {},
            'people': {},
            'movable_items': {}
        }
        
        # Agent可知的公开状态
        self.public_state = {
            'devices': {},
            'rooms': {},
            'known_info': []
        }
    
    def get_agent_knowledge(self) -> dict:
        """获取Agent视角的世界知识"""
        return {
            'devices': self.public_state['devices'],
            'rooms': self.public_state['rooms'],
            'known_info': self.public_state['known_info']
        }
    
    def update_from_action(self, action: str, result: dict):
        """从动作结果更新世界知识"""
        if action == 'moveRobot':
            # 机器人可以发现隐藏状态
            if result.get('found_items'):
                self.public_state['known_info'].extend(result['found_items'])
        
        # 设备状态始终公开
        if 'device_state' in result:
            self.public_state['devices'].update(result['device_state'])
    
    def add_hidden_discovery(self, category: str, item: str, location: str):
        """添加新发现的隐藏物体"""
        if category in self.hidden_state:
            self.hidden_state[category][item] = location
```

### 3.3 Agent-Facing API 设计原则

**创新描述**: Lares总结的Agent专用API设计准则。

| 原则 | 说明 | 我们的应用 |
|------|------|-----------|
| **高层函数** | 常用任务一个调用完成 | 设备控制用高层函数 |
| **自然语言反馈** | 成功/失败消息用自然语言 | "灯已打开" 而非 "OK" |
| **一致性命名** | 函数名是Agent提示的一部分 | 统一设备命名规范 |
| **错误提示** | 错误消息提示解决方案 | 详细错误处理 |

**可借鉴程度**: ⭐⭐⭐⭐⭐

---

## 四、多Agent协调 (Energy Agent)

### 4.1 专业化Agent分工

**创新描述**: 多个专业Agent协调工作，各司其职。

```
┌─────────────────────────────────────────────┐
│              协调层 (Coordinator)            │
│         意图理解 → 任务分解 → 结果汇总       │
└─────────────────────────────────────────────┘
                      ↓
    ┌─────────────────┼─────────────────┐
    ↓                 ↓                 ↓
┌─────────┐     ┌─────────┐     ┌─────────┐
│ 能源    │     │ 设备    │     │ 用户    │
│ 管理    │     │ 控制    │     │ 交互    │
│ Agent   │     │ Agent   │     │ Agent   │
└─────────┘     └─────────┘     └─────────┘
```

**可借鉴程度**: ⭐⭐⭐⭐⭐

**与我们的9智能体框架对应**:

| Energy Agent角色 | 我们的对应Agent |
|------------------|-----------------|
| 能源管理 | 能源优化Agent |
| 设备控制 | 设备控制Agent |
| 用户交互 | 对话管理Agent |

---

## 五、整合实施路线图

### 5.1 第一阶段: 核心架构 (Week 1-2)

- [ ] 实现Lares风格的**意图/行动分离**ReAct
- [ ] 实现**世界知识管理器**
- [ ] 配置七牛云模型调用

```python
# 第一阶段代码结构
SmartHomeAgent/
├── core/
│   ├── react_engine.py      # Lares风格ReAct
│   ├── world_knowledge.py   # 世界知识管理
│   └── function_registry.py # 函数注册
├── agents/
│   ├── coordinator.py       # 协调Agent
│   └── device_control.py    # 设备控制Agent
└── config.py                # 核心参数宏定义
```

### 5.2 第二阶段: 个性化 (Week 3-4)

- [ ] 实现SAGE风格的**层级用户画像**
- [ ] 添加**夜间记忆蒸馏**功能
- [ ] 完善用户偏好学习

```python
# 第二阶段代码结构
agents/
├── user_profile.py          # 层级用户画像
├── memory_distiller.py      # 夜间记忆蒸馏
└── personalization.py       # 个性化响应
```

### 5.3 第三阶段: 扩展功能 (Week 5-6)

- [ ] 添加更多设备支持
- [ ] 实现持久命令功能
- [ ] (可选) 设备消歧功能

---

## 六、关键代码片段汇总

### 6.1 意图/行动分离 - ReAct引擎

```python
async def react_loop(user_request: str) -> str:
    """Lares风格的ReAct循环"""
    
    # 构建初始transcript
    transcript = Transcript()
    transcript.add_system("你是智能家居助手...")
    transcript.add_user(user_request)
    
    while True:
        # Step 1: 意图识别
        intent_prompt = build_intent_prompt(transcript, available_functions)
        intent_result = await llm.function_call("decideBestFunction", intent_prompt)
        
        chosen_func = intent_result['bestFunction']
        reasoning = intent_result['reasoning']
        
        transcript.add_assistant(f"决定调用 {chosen_func}，原因: {reasoning}")
        
        # Step 2: 参数确定
        action_prompt = build_action_prompt(transcript, chosen_func)
        action_result = await llm.function_call(chosen_func, action_prompt)
        
        # Step 3: 执行
        exec_result = await executor.execute(chosen_func, action_result)
        
        transcript.add_tool_result(exec_result)
        
        # 检查是否完成
        if chosen_func == "halt":
            return exec_result['messageToUser']
```

### 6.2 世界知识同步

```python
def sync_world_knowledge(devices: list, rooms: list) -> dict:
    """同步设备状态到世界知识"""
    
    return {
        "rooms": {r.id: r.to_dict() for r in rooms},
        "devices": {d.id: {
            "type": d.type,
            "state": d.state,
            "room": d.room_id
        } for d in devices},
        "timestamp": datetime.now().isoformat()
    }
```

---

## 七、参考资料

1. **SAGE: Smart Home Agent with Grounded Execution**
   - 论文: https://arxiv.org/abs/2311.00772
   - 代码: https://github.com/SAIC-MONTREAL/SAGE
   - 官网: https://saic-montreal.github.io/

2. **Lares: Smart Home AI Agent**
   - 代码: https://github.com/genmon/lares
   - 文档: https://interconnected.org/more/2024/lares/

3. **Smart Home Energy System Agent**
   - 代码: https://github.com/asimunit/smart_home_energy_system_agent

4. **All Agentic Architectures**
   - 代码: https://github.com/FareedKhan-dev/all-agentic-architectures

---

## 八、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| V1.0 | 2026-03-09 | 初始版本，整合4个案例的创新点 |

---

*本指南将作为智能家居AI智能体项目的核心技术参考文档。*