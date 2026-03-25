from typing import List, Dict, Any
import time
import uuid

class ConversationMemory:
    """对话记忆模块 - 作为上下文理解的"聊天记录册"
    
    负责完整存储用户与智能体的所有对话内容，为LLM提供完整上下文信息，
    确保准确理解用户意图及确认无额外要求。
    """
    
    def __init__(self):
        """初始化对话记忆模块"""
        self.conversations = {}
        self.last_updated = time.time()
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到对话记录
        
        Args:
            session_id: 会话ID
            role: 角色，如"user"或"assistant"
            content: 消息内容
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        self.conversations[session_id].append(message)
        self.last_updated = time.time()
        return message["message_id"]
    
    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有消息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话的所有消息
        """
        if session_id in self.conversations:
            return self.conversations[session_id]
        return []
    
    def get_last_n_messages(self, session_id: str, n: int) -> List[Dict[str, Any]]:
        """获取会话的最后n条消息
        
        Args:
            session_id: 会话ID
            n: 消息数量
            
        Returns:
            会话的最后n条消息
        """
        if session_id in self.conversations:
            return self.conversations[session_id][-n:]
        return []
    
    def delete_conversation(self, session_id: str):
        """删除会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            self.last_updated = time.time()
    
    def clear(self):
        """清空对话记忆"""
        self.conversations.clear()
        self.last_updated = time.time()
    
    def get_last_updated(self) -> float:
        """获取最后更新时间
        
        Returns:
            最后更新时间戳
        """
        return self.last_updated
    
    def get_session_ids(self) -> List[str]:
        """获取所有会话ID
        
        Returns:
            所有会话ID
        """
        return list(self.conversations.keys())
