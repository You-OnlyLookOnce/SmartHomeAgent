from src.agent.agent_base import AgentBase
from src.skills.skill_manager import SkillManager
from typing import Dict, List, Optional
import time

class DeviceControlAgent(AgentBase):
    """设备控制Agent - 专门处理设备控制任务"""
    
    def __init__(self):
        super().__init__("device_control", "设备控制专家")
        self.capabilities = {
            "led_control": True
        }
        self.permissions = [
            "control_led"
        ]
        self.skill_manager = SkillManager()
        self._load_device_skills()
    
    def _load_device_skills(self):
        """加载设备控制相关技能"""
        try:
            self.skills = [
                self.skill_manager.get_skill("led_on"),
                self.skill_manager.get_skill("led_off"),
                self.skill_manager.get_skill("led_brightness")
            ]
        except Exception as e:
            print(f"加载设备技能失败: {e}")
            self.skills = []
    
    async def execute(self, task: str) -> Dict:
        """执行设备控制任务"""
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
        # 简单的权限检查逻辑
        return True
    
    async def _execute_task(self, task: str) -> Dict:
        """执行任务"""
        # 任务匹配逻辑
        task_lower = task.lower()
        
        # 开灯指令
        if any(keyword in task_lower for keyword in ["开", "open", "turn on"]) and any(keyword in task_lower for keyword in ["灯", "led"]):
            skill_instance = self.skills[0]()
            return await skill_instance.execute({"device_id": "led_1"})
        # 关灯指令
        elif any(keyword in task_lower for keyword in ["关", "close", "turn off"]) and any(keyword in task_lower for keyword in ["灯", "led"]):
            skill_instance = self.skills[1]()
            return await skill_instance.execute({"device_id": "led_1"})
        # 调节亮度指令
        elif "亮度" in task or "brightness" in task_lower:
            skill_instance = self.skills[2]()
            return await skill_instance.execute({"device_id": "led_1", "brightness": 50})
        else:
            return {"success": False, "message": "无法识别的设备控制命令"}
    
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