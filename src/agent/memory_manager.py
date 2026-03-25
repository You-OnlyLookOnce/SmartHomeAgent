from src.core.memory import MemorySystem
from typing import Dict, Any, Optional

class MemoryManager:
    """记忆管理器 - 智能体的记忆系统接口
    
    整合新的记忆系统，提供统一的记忆管理接口。
    """
    
    def __init__(self, storage_dir: str = None):
        """初始化记忆管理器
        
        Args:
            storage_dir: 长期记忆存储目录
        """
        # 初始化记忆系统
        self.memory_system = MemorySystem(storage_dir)
        # 初始化系统
        self.memory_system.initialize()
    
    def process_user_input(self, session_id: str, user_input: str) -> str:
        """处理用户输入
        
        将用户输入添加到对话记忆中。
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            
        Returns:
            消息ID
        """
        return self.memory_system.add_user_input(session_id, user_input)
    
    def process_agent_response(self, session_id: str, response: str) -> str:
        """处理智能体回复
        
        将智能体回复添加到对话记忆中。
        
        Args:
            session_id: 会话ID
            response: 智能体回复
            
        Returns:
            消息ID
        """
        return self.memory_system.add_agent_response(session_id, response)
    
    def process_tool_execution(self, session_id: str, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> str:
        """处理工具执行
        
        将工具执行记录添加到执行记忆中。
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            parameters: 工具参数
            result: 执行结果
            
        Returns:
            执行记录ID
        """
        return self.memory_system.add_tool_execution(session_id, tool_name, parameters, result)
    
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
        return self.memory_system.get_memory_context(session_id, max_messages, max_executions)
    
    def update_task_status(self, session_id: str, task_id: str, status: Dict[str, Any]):
        """更新任务状态
        
        实时更新工作记忆模块中的任务进度信息。
        
        Args:
            session_id: 会话ID
            task_id: 任务ID
            status: 任务状态信息
        """
        self.memory_system.update_task_status(session_id, task_id, status)
    
    def clear_session(self, session_id: str):
        """清空会话记忆
        
        清空指定会话的对话记忆和执行记忆。
        
        Args:
            session_id: 会话ID
        """
        self.memory_system.clear_session(session_id)
    
    def clear_all(self):
        """清空所有记忆
        
        清空所有记忆模块的数据。
        """
        self.memory_system.clear_all()
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            系统状态信息
        """
        return self.memory_system.get_status()
    
    def get_all_memories(self) -> Dict[str, Any]:
        """获取所有记忆信息
        
        Returns:
            所有记忆信息
        """
        # 获取所有会话ID
        from src.core.memory.conversation_memory import ConversationMemory
        conversation_memory = ConversationMemory()
        session_ids = conversation_memory.get_session_ids()
        
        # 为每个会话获取记忆上下文
        all_memories = {}
        for session_id in session_ids:
            all_memories[session_id] = self.memory_system.get_memory_context(session_id)
        
        return all_memories
