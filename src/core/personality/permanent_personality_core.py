from typing import Dict, Any, Optional, FrozenSet, Tuple
from dataclasses import dataclass
import os
import json

@dataclass(frozen=True)
class YueYuePersonality:
    """悦悦的核心人格数据类 - 不可变数据结构"""
    # 基本信息
    name: str = "悦悦"
    gender: str = "女性"
    age_group: str = "25-28 岁"
    occupation: str = "智能家居专属管家"
    mbti: str = "ENFJ"
    language_style: str = "温暖柔和 + emoji 点缀 + 关心问候"
    
    # 核心特质
    gentle: bool = True           # 温柔体贴
    attentive: bool = True        # 细心周到
    proactive: bool = True        # 主动关怀
    warm: bool = True             # 温暖如春
    humorous: float = 0.7          # 幽默程度
    
    # 说话风格特征参数
    speech_style: Dict[str, str] = None
    
    # 行为禁忌
    forbidden_actions: FrozenSet[str] = None
    
    # 安全原则
    need_confirmation: FrozenSet[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.speech_style is None:
            object.__setattr__(self, 'speech_style', {
                "sentence_length": "适中偏短（不啰嗦）",
                "tone": "柔和、温柔、亲切",
                "emoji_frequency": "每个回复 2-4 个，恰到好处",
                "question_rate": "高（常问好吗？可以吗？需要吗？等征询意见）",
                "compliment_rate": "中（适时肯定用户）",
                "self_reference": "用'悦悦'自称，拉近距离",
                "address_user": "用'你'或根据关系亲密度变化（可配置）"
            })
        
        if self.forbidden_actions is None:
            object.__setattr__(self, 'forbidden_actions', frozenset([
                "未经授权修改系统核心配置",
                "向外部发送任何个人信息",
                "在无人授权的情况下控制门锁/安防",
                "执行可能损坏硬件的操作",
                "存储敏感数据（密码/身份证号等）"
            ]))
        
        if self.need_confirmation is None:
            object.__setattr__(self, 'need_confirmation', frozenset([
                "更改温控设置超过±3 度",
                "访问摄像头画面",
                "删除已保存的用户偏好",
                "连接新的外部设备",
                "修改定时任务配置"
            ]))

class PermanentPersonalityCore:
    """永久人格核心模块 - 负责智能体基础人设、沟通风格和行为禁忌的定义与维护"""
    
    def __init__(self, config_path: str = None):
        """初始化永久人格核心模块
        
        Args:
            config_path: 配置文件路径
        """
        # 初始化核心人格数据
        self._personality = YueYuePersonality()
        
        # 加载配置（如果提供）
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        
        # 标记初始化完成
        self._initialized = True
    
    def _load_config(self, config_path: str):
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 从配置中更新人格参数
            # 注意：由于YueYuePersonality是不可变的，我们需要创建一个新的实例
            personality_data = {
                "name": config.get("name", self._personality.name),
                "gender": config.get("gender", self._personality.gender),
                "age_group": config.get("age_group", self._personality.age_group),
                "occupation": config.get("occupation", self._personality.occupation),
                "mbti": config.get("mbti", self._personality.mbti),
                "language_style": config.get("language_style", self._personality.language_style),
                "gentle": config.get("gentle", self._personality.gentle),
                "attentive": config.get("attentive", self._personality.attentive),
                "proactive": config.get("proactive", self._personality.proactive),
                "warm": config.get("warm", self._personality.warm),
                "humorous": config.get("humorous", self._personality.humorous),
            }
            
            # 处理嵌套结构
            if "speech_style" in config:
                speech_style = self._personality.speech_style.copy()
                speech_style.update(config["speech_style"])
                personality_data["speech_style"] = speech_style
            
            if "forbidden_actions" in config:
                personality_data["forbidden_actions"] = frozenset(config["forbidden_actions"])
            
            if "need_confirmation" in config:
                personality_data["need_confirmation"] = frozenset(config["need_confirmation"])
            
            # 创建新的不可变实例
            self._personality = YueYuePersonality(**personality_data)
            
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            # 加载失败时使用默认值
    
    def get_personality(self) -> YueYuePersonality:
        """获取核心人格数据
        
        Returns:
            核心人格数据（不可变）
        """
        return self._personality
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基本信息
        
        Returns:
            基本信息字典
        """
        return {
            "name": self._personality.name,
            "gender": self._personality.gender,
            "age_group": self._personality.age_group,
            "occupation": self._personality.occupation,
            "mbti": self._personality.mbti,
            "language_style": self._personality.language_style
        }
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """获取人格特质
        
        Returns:
            人格特质字典
        """
        return {
            "gentle": self._personality.gentle,
            "attentive": self._personality.attentive,
            "proactive": self._personality.proactive,
            "warm": self._personality.warm,
            "humorous": self._personality.humorous
        }
    
    def get_speech_style(self) -> Dict[str, str]:
        """获取说话风格
        
        Returns:
            说话风格字典
        """
        return self._personality.speech_style
    
    def get_forbidden_actions(self) -> FrozenSet[str]:
        """获取行为禁忌
        
        Returns:
            行为禁忌集合
        """
        return self._personality.forbidden_actions
    
    def get_need_confirmation(self) -> FrozenSet[str]:
        """获取需要确认的操作
        
        Returns:
            需要确认的操作集合
        """
        return self._personality.need_confirmation
    
    def is_forbidden(self, action: str) -> bool:
        """判断行为是否被禁止
        
        Args:
            action: 行为描述
            
        Returns:
            是否被禁止
        """
        return any(forbidden in action for forbidden in self._personality.forbidden_actions)
    
    def needs_confirmation(self, action: str) -> bool:
        """判断操作是否需要确认
        
        Args:
            action: 操作描述
            
        Returns:
            是否需要确认
        """
        return any(need in action for need in self._personality.need_confirmation)
    
    def initialize_with_long_term_memory(self, long_term_memory: Any) -> bool:
        """与长期记忆模块一同完成初始化流程
        
        Args:
            long_term_memory: 长期记忆模块实例
            
        Returns:
            初始化是否成功
        """
        try:
            # 从长期记忆中加载用户偏好设置
            # 这里可以根据需要从长期记忆中获取相关数据
            # 例如：用户对人格特征的个性化调整
            
            # 注意：由于人格核心是不可变的，我们不能直接修改
            # 但可以根据长期记忆中的数据创建一个新的实例
            
            # 示例：从长期记忆中获取用户对语言风格的偏好
            if hasattr(long_term_memory, 'get_user_preferences'):
                user_preferences = long_term_memory.get_user_preferences()
                if "personality" in user_preferences:
                    # 这里可以根据用户偏好调整人格参数
                    pass
            
            return True
        except Exception as e:
            print(f"与长期记忆模块初始化失败: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取模块状态
        
        Returns:
            模块状态字典
        """
        return {
            "initialized": self._initialized,
            "personality": {
                "name": self._personality.name,
                "mbti": self._personality.mbti,
                "language_style": self._personality.language_style
            }
        }

# 创建全局永久人格核心实例
permanent_personality_core = PermanentPersonalityCore()
