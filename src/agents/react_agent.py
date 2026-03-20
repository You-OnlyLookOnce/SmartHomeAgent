from src.agent.agent_base import AgentBase
from typing import Dict, List, Optional, Any
import time
import os
from dotenv import load_dotenv
from src.ai.qiniu_llm import QiniuLLM
from src.tools.tool_manager import ToolManager
from src.agent.memory_manager import MemoryManager
from src.agent.session_manager import SessionManager

class ReActAgent(AgentBase):
    """ReAct Agent - 实现自主决策和工具调用"""
    
    def __init__(self):
        super().__init__("react", "智能决策助手")
        self.capabilities = {
            "general_chat": True,
            "question_answering": True,
            "tool_calling": True,
            "memory_management": True,
            "task_planning": True
        }
        self.permissions = [
            "chat",
            "answer_questions",
            "use_tools",
            "access_memory",
            "plan_tasks"
        ]
        # 初始化大模型客户端
        self.llm = QiniuLLM()
        # 初始化工具管理器
        self.tool_manager = ToolManager()
        # 初始化记忆管理器
        self.memory_manager = MemoryManager()
        # 初始化会话管理器
        self.session_manager = SessionManager()
        # 加载环境变量以获取API密钥
        load_dotenv()
        # 最大思考步数
        self.max_steps = 5
    
    async def execute(self, task: str, user_id: str = "default_user", session_id: str = None) -> Dict:
        """执行任务"""
        # 更新状态
        self.context.append({"user": task, "user_id": user_id, "session_id": session_id})
        
        # 如果没有提供session_id，创建一个新会话
        if not session_id:
            new_chat = self.session_manager.create_session(user_id=user_id)
            session_id = new_chat["session_id"]
        
        # 获取对话历史
        history = self.session_manager.get_conversation_history(session_id)
        
        # 执行ReAct循环
        result = await self._execute_react_loop(task, history, user_id, session_id)
        
        # 记录日志
        self.execution_log.append({
            "task": task,
            "result": result,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        return result
    
    async def _execute_react_loop(self, task: str, history: list, user_id: str, session_id: str) -> Dict:
        """执行ReAct思考循环"""
        print("="*50)
        print(f"_execute_react_loop called with task: {task}")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"History length: {len(history)}")
        
        # 初始化ReAct循环状态
        steps = []
        current_state = "IDLE"
        
        for step in range(self.max_steps):
            print(f"\nStep {step + 1}/{self.max_steps}")
            
            # 1. 思考阶段
            thought = await self._think(task, steps, history, user_id, session_id)
            steps.append({"type": "thought", "content": thought})
            print(f"Thought: {thought}")
            
            # 2. 行动选择阶段
            action = await self._select_action(thought, steps, task)
            steps.append({"type": "action", "content": action})
            print(f"Action: {action}")
            
            # 3. 行动执行阶段
            if action["type"] == "tool":
                # 调用工具
                tool_result = await self._execute_tool(action["tool"], action["params"])
                steps.append({"type": "observation", "content": tool_result})
                print(f"Observation: {tool_result}")
            elif action["type"] == "finish":
                # 完成任务
                response_message = action["content"]
                break
            else:
                # 未知行动类型
                response_message = "抱歉，我无法处理这个任务。"
                break
        
        # 更新对话历史
        self.session_manager.update_conversation_history(session_id, task, response_message)
        
        # 更新记忆
        conversation = {
            "timestamp": time.time(),
            "user": task,
            "assistant": response_message,
            "steps": steps
        }
        self.memory_manager.update_memory(conversation)
        
        return {
            "success": True,
            "message": response_message,
            "steps": steps
        }
    
    async def _think(self, task: str, steps: list, history: list, user_id: str, session_id: str) -> str:
        """思考阶段"""
        # 构建上下文
        context = history.copy()
        
        # 添加灵魂文件和个人资料信息
        soul = self.memory_manager.read_soul()
        profile = self.memory_manager.read_profile()
        
        if soul:
            agent_name = self.memory_manager.get_agent_name()
            core_description = soul.get('core_identity', {}).get('description', '')
            core_purpose = soul.get('core_identity', {}).get('purpose', '')
            system_prompt = f"我的名字是{agent_name}。{core_description}我的目的是：{core_purpose}"
            context.append({"system": system_prompt})
        
        # 添加用户偏好
        user_preferences = self.memory_manager.get_user_preferences()
        if user_preferences:
            context.append({"system": f"用户偏好：{user_preferences.get('description', '')}"})
        
        # 添加ReAct步骤
        if steps:
            steps_str = "\n".join([f"{s['type']}: {s['content']}" for s in steps])
            context.append({"system": f"ReAct步骤：\n{steps_str}"})
        
        # 构建思考提示
        think_prompt = f"""你是一个智能助手，正在处理用户的任务：{task}。

请根据当前情况，思考下一步应该做什么。

思考过程应该包括：
1. 分析当前任务和已有的信息
2. 确定需要执行的操作
3. 如果需要使用工具，请说明使用什么工具以及为什么使用它
4. 如果已经有足够的信息可以回答用户，请说明最终答案

请以"我需要"开头，清晰表达你的思考过程。"""
        
        # 调用大模型生成思考
        llm_result = await self.llm.generate_text(think_prompt, context=context)
        if llm_result["success"]:
            return llm_result["text"]
        else:
            return "我需要分析用户的任务，确定下一步操作。"
    
    async def _select_action(self, thought: str, steps: list, task: str) -> Dict:
        """行动选择阶段"""
        # 构建行动选择提示
        action_prompt = f"""基于以下思考过程，确定下一步行动：

思考：{thought}

请从以下选项中选择一个行动：
1. 使用工具：请指定工具名称和参数
2. 直接回答：请提供最终答案

如果选择使用工具，请以JSON格式返回：
{{"type": "tool", "tool": "工具名称", "params": {{"参数1": "值1", "参数2": "值2"}}}}

如果选择直接回答，请以JSON格式返回：
{{"type": "finish", "content": "最终答案"}}"""
        
        # 调用大模型生成行动
        llm_result = await self.llm.generate_text(action_prompt)
        if llm_result["success"]:
            try:
                # 解析JSON响应
                import json
                action = json.loads(llm_result["text"])
                return action
            except Exception:
                # 如果解析失败，默认直接回答
                return {"type": "finish", "content": llm_result["text"]}
        else:
            # 如果大模型调用失败，默认直接回答
            return {"type": "finish", "content": "抱歉，我无法处理这个任务。"}
    
    async def _execute_tool(self, tool_name: str, tool_params: Dict) -> Dict:
        """执行工具"""
        # 检查是否是内置工具
        if tool_name == "schedule_task":
            # 创建定时任务
            from src.scheduler.task_scheduler import TaskScheduler
            scheduler = TaskScheduler()
            task_name = tool_params.get("name", "")
            cron_expr = tool_params.get("cron_expr", "0 0 * * *")
            command = tool_params.get("command", "")
            result = await scheduler.create_windows_task(task_name, cron_expr, command)
            return result
        elif tool_name == "distill_memory":
            # 执行记忆蒸馏
            from src.agent.memory_manager import MemoryManager
            memory_manager = MemoryManager()
            days = tool_params.get("days", 7)
            result = memory_manager.distill_memory(days)
            return result
        else:
            # 调用工具管理器中的工具
            tool = self.tool_manager.get_tool(tool_name)
            if tool:
                return await tool.execute(**tool_params)
            else:
                return {
                    "success": False,
                    "error": f"工具 {tool_name} 不存在"
                }
    
    def handle_message(self, message: Dict) -> Dict:
        """处理来自其他Agent的消息"""
        message_type = message.get("type")
        content = message.get("content", {})
        
        # 更新状态
        self.context.append({
            "type": "message",
            "from": message.get("from"),
            "content": content,
            "timestamp": message.get("timestamp")
        })
        
        # 根据消息类型处理
        if message_type == "task_request":
            return self._handle_task_request(content)
        elif message_type == "status_request":
            return self._handle_status_request()
        elif message_type == "capability_query":
            return self._handle_capability_query()
        else:
            return {"status": "unknown_message_type"}
    
    def _handle_task_request(self, task: Dict) -> Dict:
        """处理任务请求"""
        # 由于execute是异步方法，这里返回一个同步响应
        return {"status": "task_accepted", "task_id": "async_task"}
    
    def _handle_status_request(self) -> Dict:
        """处理状态请求"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "context_length": len(self.context),
            "emotion_state": self.emotion_state
        }
    
    def _handle_capability_query(self) -> Dict:
        """处理能力查询"""
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "permissions": self.permissions
        }
