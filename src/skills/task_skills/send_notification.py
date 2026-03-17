from src.skills.skill_base import SkillBase
from typing import Dict
import json
import os
import time

class SendNotificationSkill(SkillBase):
    """发送通知技能"""
    
    # 技能元信息
    SKILL_NAME = "send_notification"
    SKILL_DESCRIPTION = "发送通知"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "title": {"type": "string", "required": True},
        "message": {"type": "string", "required": True},
        "type": {"type": "string", "default": "info", "enum": ["info", "warning", "error", "success"]},
        "priority": {"type": "string", "default": "medium", "enum": ["low", "medium", "high"]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "notification": "dict"
    }
    
    def __init__(self):
        # 确保通知存储目录存在
        self.notification_dir = "data/notifications"
        os.makedirs(self.notification_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        title = params["title"]
        message = params["message"]
        type_ = params.get("type", "info")
        priority = params.get("priority", "medium")
        
        # 生成通知ID
        notification_id = f"notification_{int(time.time())}_{user_id}"
        
        # 构建通知对象
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type_,
            "priority": priority,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "unread"
        }
        
        # 保存通知
        notification_file = os.path.join(self.notification_dir, f"{user_id}.json")
        if os.path.exists(notification_file):
            with open(notification_file, "r", encoding="utf-8") as f:
                notifications = json.load(f)
        else:
            notifications = []
        
        notifications.append(notification)
        
        with open(notification_file, "w", encoding="utf-8") as f:
            json.dump(notifications, f, ensure_ascii=False, indent=2)
        
        # 记录日志
        await self.log_operation(user_id, "send_notification", notification)
        
        # 这里可以添加实际的通知发送逻辑，如推送通知、邮件等
        
        return {
            "success": True,
            "message": f"成功发送通知: {title}",
            "notification": notification
        }
