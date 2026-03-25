from typing import Dict, Any, Optional
import time
import uuid

class WorkingMemory:
    """工作记忆模块 - 作为ReAct循环的"大脑临时记事本"
    
    专门用于记录当前任务目标、实时更新执行进度及中间状态信息，
    支持动态修改与实时查询。
    """
    
    def __init__(self):
        """初始化工作记忆模块"""
        self.memory = {}
        self.last_updated = time.time()
    
    def set_task(self, task_id: str, task_data: Dict[str, Any]):
        """设置任务信息
        
        Args:
            task_id: 任务ID
            task_data: 任务数据，包含目标、进度、状态等
        """
        self.memory[task_id] = {
            "task_id": task_id,
            "data": task_data,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self.last_updated = time.time()
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]):
        """更新任务信息
        
        Args:
            task_id: 任务ID
            task_data: 任务数据，包含目标、进度、状态等
        """
        if task_id in self.memory:
            self.memory[task_id]["data"].update(task_data)
            self.memory[task_id]["updated_at"] = time.time()
            self.last_updated = time.time()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务数据，如果任务不存在则返回None
        """
        if task_id in self.memory:
            return self.memory[task_id]["data"]
        return None
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务信息
        
        Returns:
            所有任务数据
        """
        return {task_id: task_data["data"] for task_id, task_data in self.memory.items()}
    
    def delete_task(self, task_id: str):
        """删除任务信息
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.memory:
            del self.memory[task_id]
            self.last_updated = time.time()
    
    def clear(self):
        """清空工作记忆"""
        self.memory.clear()
        self.last_updated = time.time()
    
    def get_last_updated(self) -> float:
        """获取最后更新时间
        
        Returns:
            最后更新时间戳
        """
        return self.last_updated
    
    def generate_task_id(self) -> str:
        """生成任务ID
        
        Returns:
            任务ID
        """
        return f"task_{uuid.uuid4().hex[:8]}"
