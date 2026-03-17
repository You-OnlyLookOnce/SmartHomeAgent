from src.skills.skill_base import SkillBase
from typing import Dict
import json
import os

class SavePreferenceSkill(SkillBase):
    """保存偏好技能"""
    
    # 技能元信息
    SKILL_NAME = "save_preference"
    SKILL_DESCRIPTION = "保存用户偏好"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "preference_key": {"type": "string", "required": True},
        "preference_value": {"type": "any", "required": True}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "preference": "dict"
    }
    
    def __init__(self):
        # 确保偏好存储目录存在
        self.preference_dir = "data/preferences"
        os.makedirs(self.preference_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        preference_key = params["preference_key"]
        preference_value = params["preference_value"]
        
        # 加载用户偏好
        preference_file = os.path.join(self.preference_dir, f"{user_id}.json")
        if os.path.exists(preference_file):
            with open(preference_file, "r", encoding="utf-8") as f:
                preferences = json.load(f)
        else:
            preferences = {}
        
        # 更新偏好
        preferences[preference_key] = preference_value
        
        # 保存偏好
        with open(preference_file, "w", encoding="utf-8") as f:
            json.dump(preferences, f, ensure_ascii=False, indent=2)
        
        # 记录日志
        await self.log_operation(user_id, "save_preference", {
            "key": preference_key,
            "value": preference_value
        })
        
        return {
            "success": True,
            "message": f"成功保存偏好: {preference_key}",
            "preference": {
                "key": preference_key,
                "value": preference_value
            }
        }
