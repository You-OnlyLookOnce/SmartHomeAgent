from src.skills.skill_base import SkillBase
from typing import Dict
import json
import os
import time

class ScheduleTaskSkill(SkillBase):
    """安排任务技能"""
    
    # 技能元信息
    SKILL_NAME = "schedule_task"
    SKILL_DESCRIPTION = "安排任务"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "title": {"type": "string", "required": True},
        "due_date": {"type": "string", "required": True},
        "priority": {"type": "string", "default": "medium", "enum": ["low", "medium", "high"]},
        "description": {"type": "string", "default": ""},
        "status": {"type": "string", "default": "pending", "enum": ["pending", "in_progress", "completed"]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "task": "dict"
    }
    
    def __init__(self):
        # 确保任务存储目录存在
        self.task_dir = "data/tasks"
        os.makedirs(self.task_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        title = params["title"]
        due_date = params["due_date"]
        priority = params.get("priority", "medium")
        description = params.get("description", "")
        status = params.get("status", "pending")
        
        # 生成任务ID
        task_id = f"task_{int(time.time())}_{user_id}"
        
        # 构建任务对象
        task = {
            "id": task_id,
            "user_id": user_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "description": description,
            "status": status,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存任务
        task_file = os.path.join(self.task_dir, f"{user_id}.json")
        if os.path.exists(task_file):
            with open(task_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        else:
            tasks = []
        
        tasks.append(task)
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        # 记录日志
        await self.log_operation(user_id, "schedule_task", task)
        
        return {
            "success": True,
            "message": f"成功安排任务: {title}",
            "task": task
        }
