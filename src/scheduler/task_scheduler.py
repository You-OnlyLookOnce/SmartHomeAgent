import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.agent.independent_session_manager import IndependentSessionManager
from src.ai.qiniu_llm import QiniuLLM

class TaskScheduler:
    def __init__(self, data_dir: str = "data/scheduler"):
        self.data_dir = data_dir
        self.tasks_file = os.path.join(data_dir, "tasks.json")
        self.backup_file = os.path.join(data_dir, "tasks_backup.json")
        os.makedirs(self.data_dir, exist_ok=True)
        self._load_tasks()
        self._backup_tasks()
    
    def _load_tasks(self):
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print(f"Error loading tasks: {e}")
                self.tasks = []
        else:
            self.tasks = []
    
    def _save_tasks(self):
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            self._backup_tasks()
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def _backup_tasks(self):
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = f.read()
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    f.write(tasks_data)
        except Exception as e:
            print(f"Error backing up tasks: {e}")
    
    def create_task(self, title: str, content: str, reminder_time: str, repeat_type: str = "once"):
        task_id = str(int(time.time() * 1000))
        task = {
            "id": task_id,
            "title": title,
            "content": content,
            "reminder_time": reminder_time,
            "repeat_type": repeat_type,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self._save_tasks()
        return task
    
    def get_tasks(self):
        return self.tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None
    
    def update_task_status(self, task_id: str, status: str):
        for task in self.tasks:
            if task["id"] == task_id:
                if status == "completed":
                    if task["repeat_type"] == "once":
                        task["status"] = "completed"
                    else:
                        # 对于循环任务，先标记为completed，等待下次检查时再重置为pending
                        task["status"] = "completed"
                        # 更新下次提醒时间
                        task["reminder_time"] = self._calculate_next_reminder_time(task["reminder_time"], task["repeat_type"])
                else:
                    task["status"] = status
                self._save_tasks()
                return True
        return False
    
    def _calculate_next_reminder_time(self, current_time: str, repeat_type: str) -> str:
        dt = datetime.fromisoformat(current_time)
        if repeat_type == "daily":
            next_dt = dt + timedelta(days=1)
        elif repeat_type == "weekly":
            next_dt = dt + timedelta(weeks=1)
        elif repeat_type == "monthly":
            next_dt = dt + timedelta(days=30)
        else:
            next_dt = dt + timedelta(days=1)
        return next_dt.isoformat()
    
    def check_tasks(self):
        current_time = datetime.now()
        due_tasks = []
        for task in self.tasks:
            if task["status"] == "pending":
                reminder_dt = datetime.fromisoformat(task["reminder_time"])
                if current_time >= reminder_dt:
                    task["status"] = "active"
                    due_tasks.append(task)
                    # 触发智能体响应
                    self._trigger_agent_response(task)
            elif task["status"] == "completed" and task["repeat_type"] != "once":
                # 对于循环任务，检查是否到达下次提醒时间
                reminder_dt = datetime.fromisoformat(task["reminder_time"])
                if current_time >= reminder_dt:
                    task["status"] = "active"
                    due_tasks.append(task)
                    # 触发智能体响应
                    self._trigger_agent_response(task)
        if due_tasks:
            self._save_tasks()
        return due_tasks
    
    def _trigger_agent_response(self, task):
        """触发智能体响应"""
        try:
            # 初始化会话管理器
            session_manager = IndependentSessionManager()
            # 创建新会话
            session = session_manager.create_session(name=f"定时提醒: {task['title']}", user_id="system")
            session_id = session["session_id"]
            
            # 构建任务消息
            task_message = f"提醒: {task['title']}\n\n{task['content']}"
            
            # 初始化LLM
            llm = QiniuLLM()
            
            # 生成响应
            result = llm.generate_text(task_message, stream=False)
            
            if result.get("success", False):
                # 保存对话历史
                session_manager.save_conversation_history(
                    session_id,
                    task_message,
                    result.get("text", "")
                )
                print(f"定时任务响应已记录，会话ID: {session_id}")
        except Exception as e:
            print(f"触发智能体响应失败: {e}")
    
    def delete_task(self, task_id: str):
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        self._save_tasks()
    
    def get_pending_tasks_count(self):
        count = 0
        for task in self.tasks:
            if task["status"] in ["pending", "active"]:
                count += 1
        return count