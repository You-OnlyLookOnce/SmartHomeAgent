import os
import json
from typing import Dict, Any, Optional

class PersonaConfig:
    """人设配置管理模块 - 负责加载和管理人设相关的配置"""
    
    def __init__(self, config_path: str = None):
        """初始化人设配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "..", "..", "config", "persona_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典
        """
        default_config = {
            "persona": {
                "weight": 0.8,  # 人设影响的权重 (0-1)
                "scope": {
                    "language_style": True,  # 语言风格
                    "emoji_usage": True,  # Emoji使用
                    "personality_traits": True,  # 性格特征
                    "emotional_expression": True,  # 情感表达
                    "interaction_mode": True  # 交互模式
                },
                "validation": {
                    "enabled": True,  # 是否启用验证
                    "strictness": "medium",  # 验证严格程度: low, medium, high
                    "auto_correct": True  # 是否自动修正
                }
            },
            "file_paths": {
                "agent_file": "YUEYUE/AGENT.md",
                "soul_file": "YUEYUE/Soul.md",
                "profile_file": "YUEYUE/Profile.md"
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    return self._merge_configs(default_config, user_config)
            except Exception as e:
                print(f"加载配置文件失败: {str(e)}")
                return default_config
        else:
            # 配置文件不存在，返回默认配置
            return default_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            合并后的配置
        """
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
            
        Returns:
            是否设置成功
        """
        keys = key.split('.')
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return True
    
    def get_persona_weight(self) -> float:
        """获取人设影响的权重
        
        Returns:
            权重值 (0-1)
        """
        return self.get("persona.weight", 0.8)
    
    def set_persona_weight(self, weight: float) -> bool:
        """设置人设影响的权重
        
        Args:
            weight: 权重值 (0-1)
            
        Returns:
            是否设置成功
        """
        if 0 <= weight <= 1:
            return self.set("persona.weight", weight)
        else:
            return False
    
    def get_scope(self, scope_name: str) -> bool:
        """获取特定范围的启用状态
        
        Args:
            scope_name: 范围名称
            
        Returns:
            是否启用
        """
        return self.get(f"persona.scope.{scope_name}", True)
    
    def set_scope(self, scope_name: str, enabled: bool) -> bool:
        """设置特定范围的启用状态
        
        Args:
            scope_name: 范围名称
            enabled: 是否启用
            
        Returns:
            是否设置成功
        """
        return self.set(f"persona.scope.{scope_name}", enabled)
    
    def get_validation_enabled(self) -> bool:
        """获取是否启用验证
        
        Returns:
            是否启用
        """
        return self.get("persona.validation.enabled", True)
    
    def set_validation_enabled(self, enabled: bool) -> bool:
        """设置是否启用验证
        
        Args:
            enabled: 是否启用
            
        Returns:
            是否设置成功
        """
        return self.set("persona.validation.enabled", enabled)
    
    def get_validation_strictness(self) -> str:
        """获取验证严格程度
        
        Returns:
            严格程度: low, medium, high
        """
        return self.get("persona.validation.strictness", "medium")
    
    def set_validation_strictness(self, strictness: str) -> bool:
        """设置验证严格程度
        
        Args:
            strictness: 严格程度: low, medium, high
            
        Returns:
            是否设置成功
        """
        if strictness in ["low", "medium", "high"]:
            return self.set("persona.validation.strictness", strictness)
        else:
            return False
    
    def get_auto_correct(self) -> bool:
        """获取是否自动修正
        
        Returns:
            是否自动修正
        """
        return self.get("persona.validation.auto_correct", True)
    
    def set_auto_correct(self, auto_correct: bool) -> bool:
        """设置是否自动修正
        
        Args:
            auto_correct: 是否自动修正
            
        Returns:
            是否设置成功
        """
        return self.set("persona.validation.auto_correct", auto_correct)
    
    def get_file_path(self, file_type: str) -> str:
        """获取人设文件路径
        
        Args:
            file_type: 文件类型: agent_file, soul_file, profile_file
            
        Returns:
            文件路径
        """
        return self.get(f"file_paths.{file_type}", f"YUEYUE/{file_type.replace('_file', '.md')}")
    
    def set_file_path(self, file_type: str, path: str) -> bool:
        """设置人设文件路径
        
        Args:
            file_type: 文件类型: agent_file, soul_file, profile_file
            path: 文件路径
            
        Returns:
            是否设置成功
        """
        return self.set(f"file_paths.{file_type}", path)
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self.config

# 创建全局配置实例
persona_config = PersonaConfig()
