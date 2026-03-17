from src.agent.agent_base import AgentBase
from src.skills.skill_manager import SkillManager
from typing import Dict, List, Optional
import time

class TaskManagerAgent(AgentBase):
    """待办管理Agent - 专门处理任务管理"""
    
    def __init__(self):
        super().__init__("task_manager", "待办管理专家")
        self.capabilities = {
            "create_reminder": True,
            "schedule_task": True,
            "send_notification": True
        }
        self.permissions = [
            "create_reminder",
            "read_reminder",
            "update_reminder",
            "delete_reminder"
        ]
        self.skill_manager = SkillManager()
        self._load_task_skills()
    
    def _load_task_skills(self):
        """加载任务管理相关技能"""
        try:
            self.skills = [
                self.skill_manager.get_skill("create_reminder"),
                self.skill_manager.get_skill("schedule_task"),
                self.skill_manager.get_skill("send_notification")
            ]
        except Exception as e:
            print(f"加载任务技能失败: {e}")
            self.skills = []
    
    async def execute(self, task: str) -> Dict:
        """执行任务管理任务"""
        # 验证权限
        if not self._check_permission(task):
            return {"success": False, "message": "权限不足"}
        
        # 更新状态
        self.context.append({"user": task})
        
        # 执行技能
        result = await self._execute_task(task)
        
        # 记录日志
        self.execution_log.append({
            "task": task,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def _check_permission(self, task: str) -> bool:
        """检查权限"""
        return True
    
    async def _execute_task(self, task: str) -> Dict:
        """执行任务"""
        if "提醒" in task or "提醒我" in task:
            # 提取提醒内容和时间
            skill_instance = self.skills[0]()
            return await skill_instance.execute({
                "user_id": "default_user",
                "title": task,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 3600)),
                "description": task
            })
        elif "任务" in task or "安排" in task:
            skill_instance = self.skills[1]()
            return await skill_instance.execute({
                "user_id": "default_user",
                "title": task,
                "due_date": time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))
            })
        elif "通知" in task or "发送" in task:
            skill_instance = self.skills[2]()
            return await skill_instance.execute({
                "user_id": "default_user",
                "title": "通知",
                "message": task
            })
        else:
            return {"success": False, "message": "无法识别的任务管理命令"}
    
    def handle_message(self, message: Dict) -> Dict:
        """处理来自其他Agent的消息"""
        message_type = message.get("type")
        content = message.get("content", {})
        
        # 更新状态
        self.context.append({
            "type": "message",
            "from": message.get("from"),
            "content": content,
            "timestamp": message.get("timestamp")
        })
        
        # 根据消息类型处理
        if message_type == "task_request":
            return self._handle_task_request(content)
        elif message_type == "status_request":
            return self._handle_status_request()
        elif message_type == "capability_query":
            return self._handle_capability_query()
        else:
            return {"status": "unknown_message_type"}
    
    def _handle_task_request(self, task: Dict) -> Dict:
        """处理任务请求"""
        return self.execute(task.get("task", ""))
    
    def _handle_status_request(self) -> Dict:
        """处理状态请求"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "context_length": len(self.context),
            "emotion_state": self.emotion_state
        }
    
    def _handle_capability_query(self) -> Dict:
        """处理能力查询"""
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "permissions": self.permissions
        }