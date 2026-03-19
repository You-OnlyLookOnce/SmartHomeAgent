from src.agent.agent_base import AgentBase
from typing import Dict, List, Optional
import time
import os
from dotenv import load_dotenv
from src.ai.qiniu_llm import QiniuLLM
from src.tools.tool_manager import ToolManager
from src.agent.memory_manager import MemoryManager

class ConversationAgent(AgentBase):
    """对话Agent - 专门处理通用对话和问答任务"""
    
    def __init__(self):
        super().__init__("conversation", "智能对话助手")
        self.capabilities = {
            "general_chat": True,
            "question_answering": True,
            "small_talk": True,
            "tool_calling": True,
            "memory_management": True
        }
        self.permissions = [
            "chat",
            "answer_questions",
            "use_tools",
            "access_memory"
        ]
        # 初始化大模型客户端
        self.llm = QiniuLLM()
        # 初始化工具管理器
        self.tool_manager = ToolManager()
        # 初始化记忆管理器
        self.memory_manager = MemoryManager()
        # 加载环境变量以获取API密钥
        load_dotenv()
        # 对话历史管理
        self.conversation_history = {}
    
    async def execute(self, task: str, user_id: str = "default_user") -> Dict:
        """执行对话任务"""
        # 更新状态
        self.context.append({"user": task, "user_id": user_id})
        
        # 获取对话历史
        history = self._get_conversation_history(user_id)
        
        # 执行对话
        result = await self._execute_conversation(task, history, user_id)
        
        # 记录日志
        self.execution_log.append({
            "task": task,
            "result": result,
            "user_id": user_id,
            "timestamp": time.time()
        })
        
        return result
    
    async def _execute_conversation(self, task: str, history: list, user_id: str) -> Dict:
        """执行对话逻辑"""
        print("="*50)
        print(f"_execute_conversation called with task: {task}")
        print(f"User ID: {user_id}")
        print(f"History length: {len(history)}")
        print(f"LLM instance: {self.llm}")
        print(f"LLM API key: {self.llm.api_key[:20]}...")
        # 预响应协议：首先查阅灵魂文件和个人资料文件
        soul = self.memory_manager.read_soul()
        profile = self.memory_manager.read_profile()
        
        # 获取核心指南和用户偏好
        core_guidelines = self.memory_manager.get_core_guidelines()
        user_preferences = self.memory_manager.get_user_preferences()
        communication_preferences = self.memory_manager.get_communication_preferences()
        
        # 构建上下文，包含灵魂文件和个人资料的信息
        enhanced_context = history.copy()
        
        # 添加灵魂文件信息到上下文
        if soul:
            # 从soul文件中获取完整的身份信息
            agent_name = self.memory_manager.get_agent_name()
            core_description = soul.get('core_identity', {}).get('description', '')
            core_purpose = soul.get('core_identity', {}).get('purpose', '')
            
            # 构建详细的系统提示
            system_prompt = f"我的名字是{agent_name}。{core_description}我的目的是：{core_purpose}"
            
            # 添加核心指南
            if core_guidelines:
                guidelines_text = []
                for key, value in core_guidelines.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            guidelines_text.append(f"{sub_key}：{sub_value}")
                    else:
                        guidelines_text.append(f"{key}：{value}")
                system_prompt += " 我的行为指南：" + "，".join(guidelines_text)
            
            enhanced_context.append({"system": system_prompt})
        
        # 添加用户偏好到上下文
        if user_preferences:
            enhanced_context.append({"system": f"用户偏好：{user_preferences.get('description', '')}"})
        if communication_preferences:
            enhanced_context.append({"system": f"沟通偏好：{communication_preferences.get('description', '')}"})
        
        # 使用大模型API生成回复，使用增强的上下文
        print("Calling llm.generate_text...")
        print(f"Enhanced context length: {len(enhanced_context)}")
        llm_result = await self.llm.generate_text(task, context=enhanced_context)
        print(f"llm.generate_text returned: {llm_result}")
        print("="*50)
        
        if llm_result["success"]:
            # 检查是否需要调用工具
            if llm_result.get("tool_call"):
                tool_call = llm_result["tool_call"]
                tool_name = tool_call["name"]
                tool_params = tool_call["params"]
                
                # 执行工具
                tool_result = await self._execute_tool(tool_name, tool_params)
                
                # 生成工具执行结果的回复
                response_message = self._format_tool_response(tool_result, tool_name, tool_params)
                
                # 更新对话历史
                self._update_conversation_history(user_id, task, response_message)
                
                # 更新记忆
                conversation = {
                    "timestamp": time.time(),
                    "user": task,
                    "assistant": response_message,
                    "tool_used": tool_name,
                    "tool_result": tool_result
                }
                self.memory_manager.update_memory(conversation)
                
                return {
                    "success": True,
                    "message": response_message,
                    "usage": llm_result.get("usage", {}),
                    "tool_used": tool_name,
                    "tool_result": tool_result
                }
            else:
                # 直接返回大模型的回复
                response_message = llm_result["text"]
                
                # 检查回复是否完整或有用
                if self._is_response_incomplete(response_message):
                    # 应用错误处理协议
                    error_response = self._handle_incomplete_response(task)
                    
                    # 更新对话历史
                    self._update_conversation_history(user_id, task, error_response)
                    
                    # 更新记忆
                    conversation = {
                        "timestamp": time.time(),
                        "user": task,
                        "assistant": error_response,
                        "error": "Incomplete response"
                    }
                    self.memory_manager.update_memory(conversation)
                    
                    return {
                        "success": False,
                        "message": error_response
                    }
                else:
                    # 正常回复
                    # 更新对话历史
                    self._update_conversation_history(user_id, task, response_message)
                    
                    # 更新记忆
                    conversation = {
                        "timestamp": time.time(),
                        "user": task,
                        "assistant": response_message
                    }
                    self.memory_manager.update_memory(conversation)
                    
                    return {
                        "success": True,
                        "message": response_message,
                        "usage": llm_result.get("usage", {})
                    }
        else:
            # 大模型调用失败，应用错误处理协议
            error_message = self._handle_llm_error(llm_result.get('error', '未知错误'), task)
            
            # 更新对话历史
            self._update_conversation_history(user_id, task, error_message)
            
            # 更新记忆
            conversation = {
                "timestamp": time.time(),
                "user": task,
                "assistant": error_message,
                "error": llm_result.get('error', '未知错误')
            }
            self.memory_manager.update_memory(conversation)
            
            return {
                "success": False,
                "message": error_message
            }
    
    async def _execute_tool(self, tool_name: str, tool_params: Dict) -> Dict:
        """执行工具"""
        tool = self.tool_manager.get_tool(tool_name)
        if tool:
            return await tool.execute(**tool_params)
        else:
            return {
                "success": False,
                "error": f"工具 {tool_name} 不存在"
            }
    
    def _format_tool_response(self, tool_result: Dict, tool_name: str, tool_params: Dict) -> str:
        """格式化工具执行结果"""
        if tool_result["success"]:
            result = tool_result["result"]
            
            if tool_name == "control_device":
                return result.get("message", f"已执行设备控制操作")
            elif tool_name == "create_reminder":
                return result.get("message", f"已创建提醒")
            elif tool_name == "get_weather":
                location = tool_params.get("location", "未知位置")
                temperature = result.get("temperature", "未知")
                condition = result.get("condition", "未知")
                return f"{location}的天气：{condition}，温度 {temperature}"
            elif tool_name == "get_time":
                current_time = result.get("time", "未知时间")
                return f"当前时间：{current_time}"
            else:
                return f"工具执行成功：{str(result)}"
        else:
            return f"工具执行失败：{tool_result.get('error', '未知错误')}"
    
    def _get_conversation_history(self, user_id: str) -> list:
        """获取对话历史"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # 限制对话历史长度，只保留最近的10轮对话
        history = self.conversation_history[user_id]
        if len(history) > 20:  # 10轮对话，每轮包含用户和助手的消息
            # 对对话历史进行压缩，保留最近的5轮完整对话，前面的对话进行摘要
            recent_history = history[-10:]  # 最近的5轮对话
            older_history = history[:-10]   # 更早的对话
            
            # 对更早的对话进行摘要
            if older_history:
                summary = self._summarize_conversation(older_history)
                # 用摘要替换更早的对话
                compressed_history = [{"summary": summary}] + recent_history
                self.conversation_history[user_id] = compressed_history
            else:
                self.conversation_history[user_id] = recent_history
        
        return self.conversation_history[user_id]
    
    def _update_conversation_history(self, user_id: str, user_message: str, assistant_message: str):
        """更新对话历史"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # 添加用户消息
        self.conversation_history[user_id].append({"user": user_message})
        # 添加助手消息
        self.conversation_history[user_id].append({"assistant": assistant_message})
        
        # 限制对话历史长度
        if len(self.conversation_history[user_id]) > 20:
            # 对对话历史进行压缩
            recent_history = self.conversation_history[user_id][-10:]
            older_history = self.conversation_history[user_id][:-10]
            
            if older_history:
                summary = self._summarize_conversation(older_history)
                compressed_history = [{"summary": summary}] + recent_history
                self.conversation_history[user_id] = compressed_history
            else:
                self.conversation_history[user_id] = recent_history
    
    def _summarize_conversation(self, history: list) -> str:
        """对对话历史进行摘要"""
        # 简单的摘要逻辑
        user_messages = []
        assistant_messages = []
        
        for msg in history:
            if "user" in msg:
                user_messages.append(msg["user"])
            elif "assistant" in msg:
                assistant_messages.append(msg["assistant"])
        
        # 生成摘要
        summary = f"用户问了{len(user_messages)}个问题，助手回答了{len(assistant_messages)}次。"
        
        # 添加最后一个问题和回答
        if user_messages:
            summary += f" 最后一个问题是：{user_messages[-1]}"
        if assistant_messages:
            summary += f" 最后一个回答是：{assistant_messages[-1]}"
        
        return summary
    
    def clear_conversation_history(self, user_id: str):
        """清除对话历史"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
    
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
        return self.execute(task.get("task", ""))
    
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
    
    def _is_response_incomplete(self, response: str) -> bool:
        """检查响应是否不完整或无用"""
        # 检查空响应
        if not response or response.strip() == "":
            return True
        
        # 检查通用的无用响应
        generic_responses = [
            "我不知道",
            "我不确定",
            "我无法回答",
            "请提供更多信息",
            "好问题！",
            "我很乐意帮忙！",
            "这是一个有趣的问题"
        ]
        
        for generic in generic_responses:
            if generic in response:
                return True
        
        # 检查响应是否过于简短
        if len(response) < 10:
            return True
        
        return False
    
    def _handle_incomplete_response(self, task: str) -> str:
        """处理不完整的响应，提供具体、可操作的请求"""
        # 根据任务类型生成具体的请求
        if "天气" in task:
            return "为了帮你查询天气，请告诉我你所在的城市或地区名称。"
        elif "时间" in task:
            return "为了告诉你准确的时间，请确认你所在的时区或城市。"
        elif "提醒" in task or "提醒我" in task:
            return "为了创建提醒，请告诉我提醒的内容、时间和日期。"
        elif "控制" in task or "打开" in task or "关闭" in task:
            return "为了帮你控制设备，请告诉我设备名称和你想要执行的操作。"
        elif "搜索" in task or "查找" in task:
            return "为了帮你搜索信息，请提供更具体的关键词或问题。"
        else:
            # 通用请求
            return "为了更好地帮助你，请提供更多关于你问题的具体信息。"
    
    def _handle_llm_error(self, error: str, task: str) -> str:
        """处理大模型错误，提供具体、可操作的请求"""
        # 根据错误类型和任务生成具体的响应
        if "API key format is incorrect" in error:
            return "API密钥格式不正确。请确保你使用的是有效的七牛云AI API密钥，而不是普通的Access Key或OpenAI格式的密钥。"
        elif "OpenAI format key" in error:
            return "你使用的是OpenAI格式的密钥，但七牛云AI API需要使用七牛云专用的API密钥。请在七牛云控制台创建正确的API密钥。"
        elif "Authentication failed" in error or "Unauthorized" in error:
            return "认证失败。请检查你的API密钥并确保它具有正确的权限。"
        elif "token" in error.lower() or "rate" in error.lower():
            return "当前系统负载较高，请稍后再试，或者尝试简化你的问题。"
        elif "context" in error.lower() or "length" in error.lower():
            return "你的问题可能包含过多信息，请尝试将问题拆分成更小的部分。"
        else:
            # 通用错误处理
            return "抱歉，我暂时无法处理你的请求。请稍后再试，或者尝试以不同的方式表达你的问题。"
