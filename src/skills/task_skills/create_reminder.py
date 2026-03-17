from src.skills.skill_base import SkillBase
from typing import Dict
import json
import os
import time

class CreateReminderSkill(SkillBase):
    """创建提醒技能"""
    
    # 技能元信息
    SKILL_NAME = "create_reminder"
    SKILL_DESCRIPTION = "创建提醒"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "title": {"type": "string", "required": True},
        "time": {"type": "string", "required": True},
        "description": {"type": "string", "default": ""},
        "repeat": {"type": "string", "default": "once", "enum": ["once", "daily", "weekly", "monthly"]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "reminder": "dict"
    }
    
    def __init__(self):
        # 确保提醒存储目录存在
        self.reminder_dir = "data/reminders"
        os.makedirs(self.reminder_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        title = params["title"]
        time_str = params["time"]
        description = params.get("description", "")
        repeat = params.get("repeat", "once")
        
        # 生成提醒ID
        reminder_id = f"reminder_{int(time.time())}_{user_id}"
        
        # 构建提醒对象
        reminder = {
            "id": reminder_id,
            "user_id": user_id,
            "title": title,
            "time": time_str,
            "description": description,
            "repeat": repeat,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }
        
        # 保存提醒
        reminder_file = os.path.join(self.reminder_dir, f"{user_id}.json")
        if os.path.exists(reminder_file):
            with open(reminder_file, "r", encoding="utf-8") as f:
                reminders = json.load(f)
        else:
            reminders = []
        
        reminders.append(reminder)
        
        with open(reminder_file, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
        
        # 记录日志
        await self.log_operation(user_id, "create_reminder", reminder)
        
        return {
            "success": True,
            "message": f"成功创建提醒: {title}",
            "reminder": reminder
        }
