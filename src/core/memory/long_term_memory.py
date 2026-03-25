from typing import Dict, Any, Optional
import json
import os
import time

class LongTermMemory:
    """长期记忆模块 - 作为个性化智能体的"用户档案+知识库"
    
    存储用户偏好、历史交互模式、设备信息及领域知识等长期数据，
    为LLM提供个性化决策支持。
    """
    
    def __init__(self, storage_dir: str = None):
        """初始化长期记忆模块
        
        Args:
            storage_dir: 存储目录
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "long_term_memory")
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.user_preferences_file = os.path.join(self.storage_dir, "user_preferences.json")
        self.device_info_file = os.path.join(self.storage_dir, "device_info.json")
        self.domain_knowledge_file = os.path.join(self.storage_dir, "domain_knowledge.json")
        
        # 初始化存储数据
        self.user_preferences = self._load_data(self.user_preferences_file, {})
        self.device_info = self._load_data(self.device_info_file, {})
        self.domain_knowledge = self._load_data(self.domain_knowledge_file, {})
        
        self.last_updated = time.time()
    
    def _load_data(self, file_path: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """加载数据从文件
        
        Args:
            file_path: 文件路径
            default: 默认数据
            
        Returns:
            加载的数据
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载文件 {file_path} 失败: {e}")
        return default
    
    def _save_data(self, file_path: str, data: Dict[str, Any]):
        """保存数据到文件
        
        Args:
            file_path: 文件路径
            data: 数据
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件 {file_path} 失败: {e}")
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """更新用户偏好
        
        Args:
            preferences: 用户偏好数据
        """
        self.user_preferences.update(preferences)
        self._save_data(self.user_preferences_file, self.user_preferences)
        self.last_updated = time.time()
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好
        
        Returns:
            用户偏好数据
        """
        return self.user_preferences
    
    def update_device_info(self, device_info: Dict[str, Any]):
        """更新设备信息
        
        Args:
            device_info: 设备信息数据
        """
        self.device_info.update(device_info)
        self._save_data(self.device_info_file, self.device_info)
        self.last_updated = time.time()
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息
        
        Returns:
            设备信息数据
        """
        return self.device_info
    
    def update_domain_knowledge(self, knowledge: Dict[str, Any]):
        """更新领域知识
        
        Args:
            knowledge: 领域知识数据
        """
        self.domain_knowledge.update(knowledge)
        self._save_data(self.domain_knowledge_file, self.domain_knowledge)
        self.last_updated = time.time()
    
    def get_domain_knowledge(self) -> Dict[str, Any]:
        """获取领域知识
        
        Returns:
            领域知识数据
        """
        return self.domain_knowledge
    
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有长期记忆数据
        
        Returns:
            所有长期记忆数据
        """
        return {
            "user_preferences": self.user_preferences,
            "device_info": self.device_info,
            "domain_knowledge": self.domain_knowledge
        }
    
    def clear(self):
        """清空长期记忆"""
        self.user_preferences = {}
        self.device_info = {}
        self.domain_knowledge = {}
        self._save_data(self.user_preferences_file, self.user_preferences)
        self._save_data(self.device_info_file, self.device_info)
        self._save_data(self.domain_knowledge_file, self.domain_knowledge)
        self.last_updated = time.time()
    
    def get_last_updated(self) -> float:
        """获取最后更新时间
        
        Returns:
            最后更新时间戳
        """
        return self.last_updated
