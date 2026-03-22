from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain.llms import OpenAI
from typing import Dict, List, Optional, Any
import json
import os
import datetime

class LangChainMemoryManager:
    """LangChain记忆管理器 - 封装LangChain的记忆功能"""
    
    def __init__(self, memory_type: str = "buffer", window_size: int = 10):
        """初始化记忆管理器
        
        Args:
            memory_type: 记忆类型，可选值: buffer, summary, window
            window_size: 窗口大小，仅在使用window类型时有效
        """
        self.memory_type = memory_type
        self.window_size = window_size
        self.memory = self._create_memory()
        
    def _create_memory(self):
        """创建记忆模块"""
        if self.memory_type == "buffer":
            return ConversationBufferMemory(return_messages=True)
        elif self.memory_type == "window":
            return ConversationBufferWindowMemory(k=self.window_size, return_messages=True)
        else:
            # 默认使用buffer类型
            return ConversationBufferMemory(return_messages=True)
    
    def add_message(self, user_message: str, assistant_message: str):
        """添加对话消息到记忆"""
        # 使用正确的方法添加消息
        self.memory.save_context({"input": user_message}, {"output": assistant_message})
    
    def get_memory(self) -> Dict[str, Any]:
        """获取记忆内容"""
        return self.memory.load_memory_variables({})
    
    def get_messages(self) -> List:
        """获取消息列表"""
        memory_vars = self.get_memory()
        return memory_vars.get("history", [])
    
    def clear(self):
        """清空记忆"""
        self.memory.clear()
    
    def to_dict(self) -> Dict:
        """将记忆转换为字典"""
        return {
            "memory_type": self.memory_type,
            "window_size": self.window_size,
            "messages": self._messages_to_dict()
        }
    
    def from_dict(self, data: Dict):
        """从字典加载记忆"""
        self.memory_type = data.get("memory_type", "buffer")
        self.window_size = data.get("window_size", 10)
        self.memory = self._create_memory()
        
        # 加载消息
        messages = data.get("messages", [])
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i]
                ai_msg = messages[i + 1]
                if user_msg.get("type") == "human" and ai_msg.get("type") == "ai":
                    self.memory.save_context(
                        {"input": user_msg.get("content", "")},
                        {"output": ai_msg.get("content", "")}
                    )
    
    def _messages_to_dict(self) -> List[Dict]:
        """将消息转换为字典列表"""
        messages = self.get_messages()
        result = []
        # 处理不同格式的消息
        if isinstance(messages, list):
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    result.append({"type": msg.type, "content": msg.content})
                elif isinstance(msg, dict):
                    if "user" in msg:
                        result.append({"type": "human", "content": msg["user"]})
                    elif "assistant" in msg:
                        result.append({"type": "ai", "content": msg["assistant"]})
        return result
    
    def save_to_file(self, file_path: str):
        """保存记忆到文件"""
        try:
            data = self.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存记忆失败: {e}")
            return False
    
    def load_from_file(self, file_path: str):
        """从文件加载记忆"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.from_dict(data)
                return True
            return False
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return False