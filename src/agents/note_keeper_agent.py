from src.agent.agent_base import AgentBase
from src.skills.skill_manager import SkillManager
from typing import Dict, List, Optional
import time

class NoteKeeperAgent(AgentBase):
    """AI笔记Agent - 专门处理笔记任务"""
    
    def __init__(self):
        super().__init__("note_keeper", "AI笔记专家")
        self.capabilities = {
            "create_note": True,
            "search_note": True,
            "organize_note": True
        }
        self.permissions = [
            "create_note",
            "read_note",
            "update_note",
            "delete_note"
        ]
        self.skill_manager = SkillManager()
        self._load_note_skills()
    
    def _load_note_skills(self):
        """加载笔记相关技能"""
        try:
            self.skills = [
                self.skill_manager.get_skill("save_preference"),
                self.skill_manager.get_skill("recall_memory"),
                self.skill_manager.get_skill("search_knowledge")
            ]
        except Exception as e:
            print(f"加载笔记技能失败: {e}")
            self.skills = []
    
    async def execute(self, task: str) -> Dict:
        """执行笔记任务"""
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
        if "记笔记" in task or "保存" in task:
            # 提取笔记内容
            note_content = task.replace("记笔记", "").replace("保存", "").strip()
            skill_instance = self.skills[0]()
            return await skill_instance.execute({
                "user_id": "default_user",
                "preference_key": f"note_{int(time.time())}",
                "preference_value": note_content
            })
        elif "回忆" in task or "查看" in task:
            skill_instance = self.skills[1]()
            return await skill_instance.execute({
                "user_id": "default_user"
            })
        elif "搜索" in task:
            skill_instance = self.skills[2]()
            return await skill_instance.execute({
                "query": task
            })
        else:
            return {"success": False, "message": "无法识别的笔记命令"}
    
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