from typing import Dict, AsyncGenerator
import time
from src.agent.prompt_tree import PromptTree
from src.agent.model_router import ModelRouter

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
        
        # 回复风格配置
        self.response_styles = {
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
        
        # SAGE风格：动态LLM提示树
        self.prompt_tree = PromptTree()
        self.model_router = ModelRouter()
    
    async def think(self, context: Dict) -> str:
        """思考过程 - 带有人类思考的节奏感"""
        # 输出思考提示（可选）
        print(self.personality["thinking_phrase"])
        
        # 模拟思考时间
        await asyncio.sleep(1)
        
        # 执行推理
        reasoning_result = await self._do_reasoning(context)
        
        return reasoning_result
    
    async def act(self, plan: Dict) -> str:
        """执行过程 - 告知用户正在行动"""
        print(self.personality["action_phrase"])
        
        # 模拟执行时间
        await asyncio.sleep(1)
        
        # 执行计划
        result = await self._execute_plan(plan)
        
        return result
    
    async def respond(self, context: Dict) -> str:
        """生成拟人化回复"""
        # SAGE风格：动态提示树构建和决策
        result = await self._sage_react_loop(context)
        
        # 生成最终回复
        response = self._format_response(result, context)
        
        return response
    
    async def _sage_react_loop(self, context: Dict) -> Dict:
        """SAGE风格的ReAct循环"""
        query = context.get("query", "")
        
        # 构建初始提示树
        self.prompt_tree.build(query)
        
        max_steps = 5
        current_step = 0
        
        while current_step < max_steps:
            # 获取当前提示
            current_prompt = self.prompt_tree.get_current_prompt()
            
            # LLM决策下一步
            action = await self._llm_decide(current_prompt)
            
            # 执行动作
            result = await self._execute_action(action)
            
            # 评估结果
            if self._is_success(result):
                # 添加成功节点
                child_id = self.prompt_tree.add_child(
                    self.prompt_tree.current_node,
                    f"执行 {action} 成功: {result['message']}",
                    action
                )
                self.prompt_tree.move_to_child(child_id)
                return result
            else:
                # 添加失败节点，继续决策
                child_id = self.prompt_tree.add_child(
                    self.prompt_tree.current_node,
                    f"执行 {action} 失败: {result.get('error', '未知错误')}",
                    action
                )
                self.prompt_tree.move_to_child(child_id)
                current_step += 1
        
        # 达到最大步数，返回失败结果
        return {
            "success": False,
            "error": "任务执行超时"
        }
    
    async def _llm_decide(self, prompt: str) -> str:
        """LLM决策下一步动作"""
        # 直接根据prompt内容进行决策，模拟LLM的决策逻辑
        if "打开" in prompt or "开灯" in prompt:
            return "led_on"
        elif "关闭" in prompt or "关灯" in prompt:
            return "led_off"
        elif "亮度" in prompt:
            return "led_brightness"
        elif "提醒" in prompt:
            return "create_reminder"
        else:
            return "call_llm"
    
    async def _execute_action(self, action: str) -> Dict:
        """执行动作"""
        # 根据动作类型构建执行计划
        if action == "led_on":
            plan = {
                "skill": "led_on",
                "params": {
                    "device_id": "led_1",
                    "brightness": 100
                }
            }
        elif action == "led_off":
            plan = {
                "skill": "led_off",
                "params": {
                    "device_id": "led_1"
                }
            }
        elif action == "led_brightness":
            plan = {
                "skill": "led_brightness",
                "params": {
                    "device_id": "led_1",
                    "brightness": 50
                }
            }
        elif action == "create_reminder":
            plan = {
                "skill": "create_reminder",
                "params": {
                    "user_id": "test_user",
                    "title": "提醒",
                    "time": "2026-03-17 09:00",
                    "description": "用户的提醒"
                }
            }
        else:
            plan = {
                "skill": "call_llm",
                "params": {
                    "prompt": "回答用户问题",
                    "task_type": "简单任务"
                }
            }
        
        return await self._execute_plan(plan)
    
    def _is_success(self, result: Dict) -> bool:
        """评估执行结果"""
        return result.get("success", False)
    
    async def _do_reasoning(self, context: Dict) -> str:
        """执行推理"""
        query = context.get("query", "")
        
        # Lares风格：第一步 - 意图识别
        if "开灯" in query or "打开" in query:
            return "决定调用led_on技能，原因: 用户需要打开灯"
        elif "关灯" in query or "关闭" in query:
            return "决定调用led_off技能，原因: 用户需要关闭灯"
        elif "亮度" in query:
            return "决定调用led_brightness技能，原因: 用户需要调节灯光亮度"
        elif "提醒" in query:
            return "决定调用create_reminder技能，原因: 用户需要创建提醒"
        else:
            return "决定调用call_llm技能，原因: 用户的问题需要进一步分析"
    
    async def _create_plan(self, thinking: str) -> Dict:
        """创建执行计划"""
        # Lares风格：第二步 - 参数确定
        if "led_on" in thinking:
            return {
                "skill": "led_on",
                "params": {
                    "device_id": "led_1",
                    "brightness": 100
                }
            }
        elif "led_off" in thinking:
            return {
                "skill": "led_off",
                "params": {
                    "device_id": "led_1"
                }
            }
        elif "led_brightness" in thinking:
            return {
                "skill": "led_brightness",
                "params": {
                    "device_id": "led_1",
                    "brightness": 50
                }
            }
        elif "create_reminder" in thinking:
            return {
                "skill": "create_reminder",
                "params": {
                    "user_id": "test_user",
                    "title": "提醒",
                    "time": "2026-03-17 09:00",
                    "description": "用户的提醒"
                }
            }
        else:
            return {
                "skill": "call_llm",
                "params": {
                    "prompt": f"回答用户问题: {thinking}",
                    "task_type": "简单任务"
                }
            }
    
    async def _execute_plan(self, plan: Dict) -> Dict:
        """执行计划"""
        # 这里应该调用技能管理器执行技能
        # 暂时返回模拟结果
        return {
            "success": True,
            "message": f"已执行 {plan['skill']} 技能",
            "result": "操作成功"
        }
    
    def _format_response(self, result: Dict, context: Dict) -> str:
        """格式化回复 - 带有人类情感"""
        # 获取当前时间
        hour = time.localtime().tm_hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "noon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        style = self.response_styles.get(time_of_day, self.response_styles["noon"])
        
        if result.get("success"):
            # 成功回复 - 带有关心
            base = self.personality["success_phrase"]
            detail = result.get("message", "")
            
            return f"{style['emoji']} {style['phrase']} {base} {detail}"
        else:
            # 失败回复 - 真诚道歉
            return f"{style['emoji']} {style['phrase']} 抱歉，{result.get('error', '出了点问题')}。让我再试试看？"

# 导入asyncio
import asyncio
