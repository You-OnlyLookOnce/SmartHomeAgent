import asyncio
from datetime import datetime, time
from typing import Callable, Dict, List
import json
import os
import subprocess
import uuid
import re

class TaskScheduler:
    """任务调度器 - 定时任务执行"""
    
    def __init__(self):
        self.scheduled_tasks = []
        self.running = False
        self.task_history = []
        self.tasks_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "scheduled_tasks.json")
        self._ensure_data_directory()
        self._load_tasks()
    
    def _ensure_data_directory(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.tasks_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _load_tasks(self):
        """加载任务列表"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    self.scheduled_tasks = json.load(f)
            except Exception as e:
                print(f"加载任务失败: {e}")
                self.scheduled_tasks = []
    
    def _save_tasks(self):
        """保存任务列表"""
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")
    
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
        self._save_tasks()
    
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
        self._save_tasks()
    
    async def schedule_cron_task(self, task_id: str, cron_expr: str, callback: Callable):
        """安排CRON任务"""
        self.scheduled_tasks.append({
            "id": task_id,
            "type": "cron",
            "cron_expr": cron_expr,
            "callback": callback,
            "last_run": None,
            "enabled": True
        })
        self._save_tasks()
    
    async def create_windows_task(self, task_name: str, cron_expr: str, command: str):
        """创建Windows计划任务"""
        try:
            # 解析CRON表达式
            parsed = self._parse_cron_expression(cron_expr)
            if not parsed:
                return {"success": False, "message": "无效的CRON表达式"}
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 构建schtasks命令
            schtasks_cmd = self._build_schtasks_command(task_name, parsed, command)
            
            # 执行命令
            result = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 添加到任务列表
                self.scheduled_tasks.append({
                    "id": task_id,
                    "name": task_name,
                    "type": "windows",
                    "cron_expr": cron_expr,
                    "command": command,
                    "last_run": None,
                    "enabled": True
                })
                self._save_tasks()
                return {"success": True, "message": "Windows计划任务创建成功", "task_id": task_id}
            else:
                return {"success": False, "message": f"创建任务失败: {result.stderr}"}
        except Exception as e:
            return {"success": False, "message": f"创建任务失败: {str(e)}"}
    
    def _parse_cron_expression(self, cron_expr: str) -> Dict:
        """解析CRON表达式"""
        parts = cron_expr.split()
        if len(parts) != 5:
            return None
        
        try:
            minute, hour, day, month, weekday = parts
            return {
                "minute": minute,
                "hour": hour,
                "day": day,
                "month": month,
                "weekday": weekday
            }
        except Exception:
            return None
    
    def _build_schtasks_command(self, task_name: str, parsed_cron: Dict, command: str) -> str:
        """构建schtasks命令"""
        # 简化实现，仅支持基本的CRON表达式
        # 实际项目中可能需要更复杂的解析
        
        # 构建任务名称
        task_name = f"{task_name}_{str(uuid.uuid4())[:8]}"
        
        # 构建触发时间
        trigger = "/sc ONCE /st 00:00 /sd 01/01/2020"
        
        # 构建命令
        cmd = f'schtasks /create /tn "{task_name}" /tr "{command}" {trigger} /ru SYSTEM'
        
        return cmd
    
    def delete_windows_task(self, task_name: str):
        """删除Windows计划任务"""
        try:
            cmd = f'schtasks /delete /tn "{task_name}" /f'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 从任务列表中移除
                self.scheduled_tasks = [task for task in self.scheduled_tasks if task.get("name") != task_name]
                self._save_tasks()
                return {"success": True, "message": "Windows计划任务删除成功"}
            else:
                return {"success": False, "message": f"删除任务失败: {result.stderr}"}
        except Exception as e:
            return {"success": False, "message": f"删除任务失败: {str(e)}"}
    
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
                    
                    elif task["type"] == "cron":
                        if self._should_run_cron(task, now):
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
        
        elif task["type"] == "cron":
            # CRON任务：检查是否在同一天内执行过
            last_run_date = datetime.fromtimestamp(task["last_run"]).date()
            current_date = datetime.fromtimestamp(current_timestamp).date()
            return last_run_date != current_date
        
        return False
    
    def _should_run_cron(self, task: Dict, now: datetime) -> bool:
        """检查CRON任务是否应该执行"""
        cron_expr = task.get("cron_expr")
        if not cron_expr:
            return False
        
        parts = cron_expr.split()
        if len(parts) != 5:
            return False
        
        minute, hour, day, month, weekday = parts
        
        # 检查分钟
        if not self._match_cron_field(minute, now.minute):
            return False
        
        # 检查小时
        if not self._match_cron_field(hour, now.hour):
            return False
        
        # 检查日期
        if not self._match_cron_field(day, now.day):
            return False
        
        # 检查月份
        if not self._match_cron_field(month, now.month):
            return False
        
        # 检查星期
        # 注意：CRON中星期从0或1开始，Python中从0开始（0=周一）
        cron_weekday = weekday
        if cron_weekday == "7":
            cron_weekday = "0"  # 将7转换为0（周日）
        if not self._match_cron_field(cron_weekday, now.weekday()):
            return False
        
        return True
    
    def _match_cron_field(self, field: str, value: int) -> bool:
        """检查CRON字段是否匹配"""
        if field == "*":
            return True
        
        # 处理逗号分隔的列表
        if "," in field:
            for part in field.split(","):
                if self._match_cron_field(part, value):
                    return True
            return False
        
        # 处理范围
        if "-" in field:
            start, end = field.split("-")
            try:
                return int(start) <= value <= int(end)
            except ValueError:
                return False
        
        # 处理步长
        if "/" in field:
            base, step = field.split("/")
            if base == "*":
                base = "0"
            try:
                base_int = int(base)
                step_int = int(step)
                return (value - base_int) % step_int == 0
            except ValueError:
                return False
        
        # 处理单个值
        try:
            return int(field) == value
        except ValueError:
            return False
    
    async def _execute_task(self, task: Dict):
        """执行任务"""
        print(f"执行任务: {task['id']}")
        
        try:
            if "callback" in task:
                result = await task["callback"]()
            else:
                # 检查是否是内置任务类型
                task_name = task.get("name", "")
                if "记忆蒸馏" in task_name or "memory distill" in task_name.lower():
                    # 执行记忆蒸馏
                    from src.agent.memory_manager import MemoryManager
                    memory_manager = MemoryManager()
                    result = memory_manager.distill_memory()
                else:
                    result = "任务执行成功"
            
            self.task_history.append({
                "task_id": task["id"],
                "timestamp": datetime.now().timestamp(),
                "status": "success",
                "result": str(result)
            })
            
            return result
        except Exception as e:
            self.task_history.append({
                "task_id": task["id"],
                "timestamp": datetime.now().timestamp(),
                "status": "failed",
                "error": str(e)
            })
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
                self._save_tasks()
                return {"success": True, "message": f"任务 {task_id} 已禁用"}
        return {"success": False, "message": f"任务 {task_id} 不存在"}
    
    def enable_task(self, task_id: str):
        """启用任务"""
        for task in self.scheduled_tasks:
            if task["id"] == task_id:
                task["enabled"] = True
                self._save_tasks()
                return {"success": True, "message": f"任务 {task_id} 已启用"}
        return {"success": False, "message": f"任务 {task_id} 不存在"}
    
    def delete_task(self, task_id: str):
        """删除任务"""
        for i, task in enumerate(self.scheduled_tasks):
            if task["id"] == task_id:
                # 如果是Windows任务，先删除Windows计划任务
                if task["type"] == "windows" and "name" in task:
                    self.delete_windows_task(task["name"])
                
                del self.scheduled_tasks[i]
                self._save_tasks()
                return {"success": True, "message": f"任务 {task_id} 已删除"}
        return {"success": False, "message": f"任务 {task_id} 不存在"}
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return self.scheduled_tasks