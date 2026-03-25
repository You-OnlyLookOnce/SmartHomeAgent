from typing import Dict, Any, List
from .working_memory import WorkingMemory
from .conversation_memory import ConversationMemory
from .execution_memory import ExecutionMemory
from .long_term_memory import LongTermMemory
import time

class MemorySystem:
    """记忆系统 - 整合四个独立记忆模块的主接口
    
    实现包含工作记忆、对话记忆、执行记忆和长期记忆的完整记忆系统，
    支持ReAct循环的高效运行。
    """
    
    def __init__(self, storage_dir: str = None):
        """初始化记忆系统
        
        Args:
            storage_dir: 长期记忆存储目录
        """
        # 初始化四个记忆模块
        self.working_memory = WorkingMemory()
        self.conversation_memory = ConversationMemory()
        self.execution_memory = ExecutionMemory()
        self.long_term_memory = LongTermMemory(storage_dir)
        
        # 系统初始化时间
        self.initialized_at = time.time()
    
    def initialize(self):
        """系统启动初始化
        
        加载长期记忆模块中的用户偏好设置与设备库信息，
        初始化工作记忆、对话记忆及执行记忆模块为空状态。
        """
        # 加载长期记忆数据
        long_term_data = self.long_term_memory.get_all_data()
        
        # 初始化临时记忆模块
        self.working_memory.clear()
        self.conversation_memory.clear()
        self.execution_memory.clear()
        
        return long_term_data
    
    def add_user_input(self, session_id: str, content: str):
        """用户输入接收
        
        将用户输入内容完整写入对话记忆模块，确保时间戳与内容完整性。
        
        Args:
            session_id: 会话ID
            content: 用户输入内容
            
        Returns:
            消息ID
        """
        return self.conversation_memory.add_message(session_id, "user", content)
    
    def add_agent_response(self, session_id: str, content: str):
        """添加智能体回复
        
        将智能体回复内容写入对话记忆模块，确保对话历史的完整性。
        
        Args:
            session_id: 会话ID
            content: 智能体回复内容
            
        Returns:
            消息ID
        """
        return self.conversation_memory.add_message(session_id, "assistant", content)
    
    def add_tool_execution(self, session_id: str, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """添加工具执行记录
        
        详细记录MCP工具调用的完整信息，并实时反馈给LLM。
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            parameters: 工具调用参数
            result: 工具执行结果
            
        Returns:
            执行记录ID
        """
        return self.execution_memory.add_execution(session_id, tool_name, parameters, result)
    
    def update_task_status(self, session_id: str, task_id: str, status: Dict[str, Any]):
        """更新任务状态
        
        实时更新工作记忆模块中的任务进度信息。
        
        Args:
            session_id: 会话ID
            task_id: 任务ID
            status: 任务状态信息
        """
        # 这里可以根据需要将session_id作为任务ID的一部分，或者单独管理
        self.working_memory.update_task(task_id, status)
    
    def get_memory_context(self, session_id: str, max_messages: int = 10, max_executions: int = 5) -> Dict[str, Any]:
        """获取记忆上下文
        
        从四个记忆模块中读取全部相关信息，按照指定格式拼接后作为上下文提供给LLM。
        
        Args:
            session_id: 会话ID
            max_messages: 最大消息数量
            max_executions: 最大执行记录数量
            
        Returns:
            整合后的记忆上下文
        """
        # 获取对话记忆
        conversation = self.conversation_memory.get_last_n_messages(session_id, max_messages)
        
        # 获取执行记忆
        executions = self.execution_memory.get_last_n_executions(session_id, max_executions)
        
        # 获取工作记忆
        tasks = self.working_memory.get_all_tasks()
        
        # 获取长期记忆
        long_term_data = self.long_term_memory.get_all_data()
        
        # 整合上下文
        context = {
            "conversation": conversation,
            "executions": executions,
            "tasks": tasks,
            "long_term": long_term_data
        }
        
        return context
    
    def clear_session(self, session_id: str):
        """清空会话记忆
        
        清空指定会话的对话记忆和执行记忆。
        
        Args:
            session_id: 会话ID
        """
        self.conversation_memory.delete_conversation(session_id)
        self.execution_memory.delete_executions(session_id)
    
    def clear_all(self):
        """清空所有记忆
        
        清空所有记忆模块的数据。
        """
        self.working_memory.clear()
        self.conversation_memory.clear()
        self.execution_memory.clear()
        self.long_term_memory.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            系统状态信息
        """
        return {
            "initialized_at": self.initialized_at,
            "last_updated": {
                "working_memory": self.working_memory.get_last_updated(),
                "conversation_memory": self.conversation_memory.get_last_updated(),
                "execution_memory": self.execution_memory.get_last_updated(),
                "long_term_memory": self.long_term_memory.get_last_updated()
            },
            "session_count": {
                "conversation": len(self.conversation_memory.get_session_ids()),
                "execution": len(self.execution_memory.get_session_ids())
            }
        }
