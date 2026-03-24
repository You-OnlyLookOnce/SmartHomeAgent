from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain.llms import OpenAI
from typing import Dict, List, Optional, Any
import json
import os
import datetime
import hashlib

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
        # 消息重要性分级
        self.message_importance = []
        
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
        
        # 分析消息重要性
        importance = self._calculate_importance(user_message, assistant_message)
        # 存储消息重要性
        self.message_importance.append({
            "user_message": user_message,
            "assistant_message": assistant_message,
            "importance": importance,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # 限制重要性列表长度
        if len(self.message_importance) > 100:
            # 按照重要性排序，保留重要的消息
            self.message_importance.sort(key=lambda x: x["importance"], reverse=True)
            self.message_importance = self.message_importance[:100]
    
    def _calculate_importance(self, user_message: str, assistant_message: str) -> int:
        """计算消息重要性
        
        Args:
            user_message: 用户消息
            assistant_message: 助手消息
            
        Returns:
            重要性级别（0-10）
        """
        importance = 5  # 默认重要性
        
        # 关键词权重
        important_keywords = {
            "名字": 8,
            "姓名": 8,
            "职业": 7,
            "工作": 7,
            "爱好": 6,
            "喜欢": 6,
            "讨厌": 6,
            "需求": 9,
            "要求": 9,
            "问题": 8,
            "困难": 8,
            "计划": 7,
            "目标": 7,
            "时间": 6,
            "日期": 6,
            "地点": 6,
            "地址": 6
        }
        
        # 分析用户消息
        for keyword, weight in important_keywords.items():
            if keyword in user_message:
                importance = max(importance, weight)
        
        # 分析助手消息
        for keyword, weight in important_keywords.items():
            if keyword in assistant_message:
                importance = max(importance, weight)
        
        # 消息长度也是重要性的一个指标
        total_length = len(user_message) + len(assistant_message)
        if total_length > 100:
            importance += 1
        if total_length > 200:
            importance += 1
        
        # 确保重要性在0-10之间
        return min(max(importance, 0), 10)
    
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
        self.message_importance = []
    
    def to_dict(self) -> Dict:
        """将记忆转换为字典"""
        return {
            "memory_type": self.memory_type,
            "window_size": self.window_size,
            "messages": self._messages_to_dict(),
            "message_importance": self.message_importance,
            "checksum": self._calculate_checksum()
        }
    
    def from_dict(self, data: Dict):
        """从字典加载记忆"""
        # 验证数据完整性
        if not self._verify_checksum(data):
            print("警告: 记忆数据可能已损坏，尝试继续加载...")
        
        self.memory_type = data.get("memory_type", "buffer")
        self.window_size = data.get("window_size", 10)
        self.memory = self._create_memory()
        
        # 加载消息重要性
        self.message_importance = data.get("message_importance", [])
        
        # 加载消息
        messages = data.get("messages", [])
        # 处理不同格式的消息
        i = 0
        while i < len(messages):
            msg = messages[i]
            # 处理 {"user": "..."} 格式的消息
            if "user" in msg:
                user_content = msg.get("user", "")
                # 查找下一条消息作为助手消息
                if i + 1 < len(messages):
                    next_msg = messages[i + 1]
                    if "assistant" in next_msg:
                        assistant_content = next_msg.get("assistant", "")
                        self.memory.save_context(
                            {"input": user_content},
                            {"output": assistant_content}
                        )
                        i += 2
                        continue
            # 处理 {"type": "human"} 格式的消息
            elif msg.get("type") == "human":
                user_content = msg.get("content", "")
                # 查找下一条消息作为助手消息
                if i + 1 < len(messages):
                    next_msg = messages[i + 1]
                    if next_msg.get("type") == "ai":
                        assistant_content = next_msg.get("content", "")
                        self.memory.save_context(
                            {"input": user_content},
                            {"output": assistant_content}
                        )
                        i += 2
                        continue
            i += 1
    
    def _calculate_checksum(self) -> str:
        """计算数据校验和"""
        data = {
            "memory_type": self.memory_type,
            "window_size": self.window_size,
            "messages": self._messages_to_dict(),
            "message_importance": self.message_importance
        }
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _verify_checksum(self, data: Dict) -> bool:
        """验证数据校验和"""
        if "checksum" not in data:
            return False
        
        # 复制数据，移除校验和字段
        data_copy = data.copy()
        checksum = data_copy.pop("checksum")
        
        # 计算校验和
        data_str = json.dumps(data_copy, ensure_ascii=False, sort_keys=True)
        calculated_checksum = hashlib.md5(data_str.encode()).hexdigest()
        
        return checksum == calculated_checksum
    
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
                        result.append({"user": msg["user"]})
                    elif "assistant" in msg:
                        result.append({"assistant": msg["assistant"]})
                elif hasattr(msg, 'content'):
                    # 处理其他类型的消息
                    if hasattr(msg, 'type'):
                        result.append({"type": msg.type, "content": msg.content})
                    else:
                        result.append({"content": msg.content})
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