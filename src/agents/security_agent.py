from src.agent.agent_base import AgentBase
from src.skills.skill_manager import SkillManager
from typing import Dict, List, Optional
import time

class SecurityAgent(AgentBase):
    """安全守护Agent - 专门处理安全监控"""
    
    def __init__(self):
        super().__init__("security", "安全守护专家")
        self.capabilities = {
            "monitor_security": True,
            "detect_anomaly": True,
            "send_alert": True
        }
        self.permissions = [
            "monitor_system",
            "detect_threat",
            "send_security_alert"
        ]
        self.skill_manager = SkillManager()
        self._load_security_skills()
    
    def _load_security_skills(self):
        """加载安全相关技能"""
        try:
            self.skills = [
                self.skill_manager.get_skill("sensor_read"),
                self.skill_manager.get_skill("send_notification")
            ]
        except Exception as e:
            print(f"加载安全技能失败: {e}")
            self.skills = []
    
    async def execute(self, task: str) -> Dict:
        """执行安全监控任务"""
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
        if "安全" in task or "监控" in task:
            # 检查传感器数据
            skill_instance = self.skills[0]()
            sensor_result = await skill_instance.execute({
                "device_id": "security_sensor",
                "sensor_type": "motion"
            })
            
            # 如果检测到异常，发送告警
            sensor_value = sensor_result.get("data", {}).get("value")
            if sensor_result.get("success") and sensor_value is not None and sensor_value > 0:
                skill_instance = self.skills[1]()
                return await skill_instance.execute({
                    "user_id": "default_user",
                    "title": "安全告警",
                    "message": "检测到异常活动"
                })
            else:
                return {"success": True, "message": "安全状态正常"}
        elif "告警" in task or "通知" in task:
            skill_instance = self.skills[1]()
            return await skill_instance.execute({
                "user_id": "default_user",
                "title": "安全通知",
                "message": task
            })
        else:
            return {"success": False, "message": "无法识别的安全命令"}
    
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