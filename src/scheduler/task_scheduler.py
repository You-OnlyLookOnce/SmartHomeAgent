import asyncio
from datetime import datetime, time
from typing import Callable, Dict, List
import json
import os

class TaskScheduler:
    """任务调度器 - 定时任务执行"""
    
    def __init__(self):
        self.scheduled_tasks = []
        self.running = False
        self.task_history = []
    
    async def schedule_daily_task(self, task_id: str, time_str: str, callback: Callable):
        """安排每日定时任务"""
        hour, minute = map(int, time_str.split(':'))
        self.scheduled_tasks.append({
            "id": task_id,
            "type": "daily",
            "time": (hour, minute),
            "callback": callback,
            "last_run": None,
            "enabled": True
        })
    
    async def schedule_interval_task(self, task_id: str, interval_seconds: int, callback: Callable):
        """安排间隔任务"""
        self.scheduled_tasks.append({
            "id": task_id,
            "type": "interval",
            "interval": interval_seconds,
            "callback": callback,
            "last_run": None,
            "enabled": True
        })
    
    async def start(self):
        """启动调度器"""
        self.running = True
        print("任务调度器启动")
        
        while self.running:
            now = datetime.now()
            current_time = (now.hour, now.minute)
            current_timestamp = now.timestamp()
            
            for task in self.scheduled_tasks:
                if not task["enabled"]:
                    continue
                
                try:
                    if task["type"] == "daily":
                        if task["time"] == current_time:
                            if self._should_run(task, current_timestamp):
                                await self._execute_task(task)
                                task["last_run"] = current_timestamp
                    
                    elif task["type"] == "interval":
                        if self._should_run(task, current_timestamp):
                            await self._execute_task(task)
                            task["last_run"] = current_timestamp
                except Exception as e:
                    print(f"任务执行失败: {task['id']} - {e}")
                    self.task_history.append({
                        "task_id": task["id"],
                        "timestamp": current_timestamp,
                        "status": "failed",
                        "error": str(e)
                    })
            
            await asyncio.sleep(60)  # 每分钟检查一次
    
    def _should_run(self, task: Dict, current_timestamp: float) -> bool:
        """检查任务是否应该执行"""
        if task["last_run"] is None:
            return True
        
        if task["type"] == "daily":
            # 每日任务：检查是否在同一天内执行过
            last_run_date = datetime.fromtimestamp(task["last_run"]).date()
            current_date = datetime.fromtimestamp(current_timestamp).date()
            return last_run_date != current_date
        
        elif task["type"] == "interval":
            # 间隔任务：检查是否超过间隔时间
            return (current_timestamp - task["last_run"]) >= task["interval"]
        
        return False
    
    async def _execute_task(self, task: Dict):
        """执行任务"""
        print(f"执行任务: {task['id']}")
        
        try:
            result = await task["callback"]()
            
            self.task_history.append({
                "task_id": task["id"],
                "timestamp": time.time(),
                "status": "success",
                "result": str(result)
            })
            
            return result
        except Exception as e:
            raise e
    
    def stop(self):
        """停止调度器"""
        self.running = False
        print("任务调度器停止")
    
    def get_task_status(self) -> List[Dict]:
        """获取任务状态"""
        status = []
        for task in self.scheduled_tasks:
            status.append({
                "id": task["id"],
                "type": task["type"],
                "enabled": task["enabled"],
                "last_run": task["last_run"]
            })
        return status
    
    def get_task_history(self, limit: int = 100) -> List[Dict]:
        """获取任务执行历史"""
        return self.task_history[-limit:]
    
    def disable_task(self, task_id: str):
        """禁用任务"""
        for task in self.scheduled_tasks:
            if task["id"] == task_id:
                task["enabled"] = False
                return {"success": True, "message": f"任务 {task_id} 已禁用"}
        return {"success": False, "message": f"任务 {task_id} 不存在"}
    
    def enable_task(self, task_id: str):
        """启用任务"""
        for task in self.scheduled_tasks:
            if task["id"] == task_id:
                task["enabled"] = True
                return {"success": True, "message": f"任务 {task_id} 已启用"}
        return {"success": False, "message": f"任务 {task_id} 不存在"}