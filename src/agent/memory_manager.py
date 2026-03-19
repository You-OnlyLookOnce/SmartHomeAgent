import json
import os
from typing import Dict, Optional, Any

class MemoryManager:
    """记忆管理器 - 负责读取和管理记忆文件"""
    
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent_memory")
        self.soul_file = os.path.join(self.base_dir, "soul.json")
        self.profile_file = os.path.join(self.base_dir, "personality", "profile.json")
        self.long_term_memory_dir = os.path.join(self.base_dir, "long_term_memory")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "personality"), exist_ok=True)
        os.makedirs(self.long_term_memory_dir, exist_ok=True)
    
    def read_soul(self) -> Optional[Dict[str, Any]]:
        """读取灵魂文件"""
        try:
            if os.path.exists(self.soul_file):
                with open(self.soul_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            print(f"读取灵魂文件失败: {e}")
            return None
    
    def read_profile(self) -> Optional[Dict[str, Any]]:
        """读取个人资料文件"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            print(f"读取个人资料文件失败: {e}")
            return None
    
    def read_long_term_memory(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """读取长期记忆文件"""
        try:
            memory_file = os.path.join(self.long_term_memory_dir, f"{user_id}_memory.json")
            if os.path.exists(memory_file):
                with open(memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 如果文件不存在，返回默认记忆
                return {
                    "user_id": user_id,
                    "conversations": [],
                    "preferences": {},
                    "learned_information": []
                }
        except Exception as e:
            print(f"读取长期记忆文件失败: {e}")
            return None
    
    def write_long_term_memory(self, user_id: str, memory: Dict[str, Any]):
        """写入长期记忆文件"""
        try:
            memory_file = os.path.join(self.long_term_memory_dir, f"{user_id}_memory.json")
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入长期记忆文件失败: {e}")
    
    def update_long_term_memory(self, user_id: str, conversation: Dict[str, Any]):
        """更新长期记忆"""
        memory = self.read_long_term_memory(user_id)
        if memory:
            # 添加新的对话
            memory["conversations"].append(conversation)
            # 限制对话历史长度
            if len(memory["conversations"]) > 100:
                memory["conversations"] = memory["conversations"][-100:]
            # 写入更新后的记忆
            self.write_long_term_memory(user_id, memory)
    
    def get_agent_name(self) -> str:
        """获取智能代理名称"""
        soul = self.read_soul()
        if soul and "name" in soul:
            return soul["name"]
        return "悦悦"  # 默认名称
    
    def get_core_guidelines(self) -> Optional[Dict[str, Any]]:
        """获取核心指南"""
        soul = self.read_soul()
        if soul and "core_guidelines" in soul:
            return soul["core_guidelines"]
        return None
    
    def get_user_preferences(self) -> Optional[Dict[str, Any]]:
        """获取用户偏好"""
        profile = self.read_profile()
        if profile and "user_profile" in profile and "preferences" in profile["user_profile"]:
            return profile["user_profile"]["preferences"]
        return None
    
    def get_communication_preferences(self) -> Optional[Dict[str, Any]]:
        """获取沟通偏好"""
        profile = self.read_profile()
        if profile and "user_profile" in profile and "communication_preferences" in profile["user_profile"]:
            return profile["user_profile"]["communication_preferences"]
        return None
