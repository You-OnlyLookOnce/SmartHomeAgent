import sqlite3
import json
from typing import Dict, List, Optional
from contextlib import contextmanager

class DatabaseManager:
    """数据库管理器 - SQLite集成"""
    
    def __init__(self, db_path: str = "data/smarthome.db"):
        self.db_path = db_path
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 提醒表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    time TEXT NOT NULL,
                    description TEXT,
                    repeat TEXT DEFAULT 'once',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    due_date TEXT,
                    priority TEXT DEFAULT 'medium',
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 偏好表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, preference_key)
                )
            """)
            
            # 通知表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info',
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'unread',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_user ON preferences(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
            
            conn.commit()
    
    async def create_reminder(self, user_id: str, reminder: Dict) -> Dict:
        """创建提醒"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (user_id, title, time, description, repeat)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, reminder["title"], reminder["time"], 
                  reminder.get("description", ""), reminder.get("repeat", "once")))
            conn.commit()
            
            return {
                "success": True,
                "reminder_id": cursor.lastrowid
            }
    
    async def get_reminders(self, user_id: str) -> List[Dict]:
        """获取用户提醒"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders WHERE user_id = ? ORDER BY time ASC
            """, (user_id,))
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append(dict(row))
            
            return reminders
    
    async def save_preference(self, user_id: str, key: str, value: str) -> Dict:
        """保存用户偏好"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (user_id, preference_key, preference_value)
                VALUES (?, ?, ?)
            """, (user_id, key, json.dumps(value)))
            conn.commit()
            
            return {"success": True}
    
    async def get_preferences(self, user_id: str) -> Dict:
        """获取用户偏好"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preference_key, preference_value FROM preferences WHERE user_id = ?
            """, (user_id,))
            
            preferences = {}
            for row in cursor.fetchall():
                try:
                    preferences[row["preference_key"]] = json.loads(row["preference_value"])
                except:
                    preferences[row["preference_key"]] = row["preference_value"]
            
            return preferences
    
    async def create_task(self, user_id: str, task: Dict) -> Dict:
        """创建任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, title, due_date, priority, description)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, task["title"], task.get("due_date"),
                  task.get("priority", "medium"), task.get("description", "")))
            conn.commit()
            
            return {
                "success": True,
                "task_id": cursor.lastrowid
            }
    
    async def get_tasks(self, user_id: str) -> List[Dict]:
        """获取用户任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC
            """, (user_id,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append(dict(row))
            
            return tasks
    
    async def create_notification(self, user_id: str, notification: Dict) -> Dict:
        """创建通知"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, notification["title"], notification["message"],
                  notification.get("type", "info"), notification.get("priority", "medium")))
            conn.commit()
            
            return {
                "success": True,
                "notification_id": cursor.lastrowid
            }
    
    async def get_notifications(self, user_id: str) -> List[Dict]:
        """获取用户通知"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append(dict(row))
            
            return notifications
    
    async def save_memory(self, user_id: str, content: str, memory_type: str = "general") -> Dict:
        """保存记忆"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (user_id, content, memory_type)
                VALUES (?, ?, ?)
            """, (user_id, content, memory_type))
            conn.commit()
            
            return {
                "success": True,
                "memory_id": cursor.lastrowid
            }
    
    async def get_memories(self, user_id: str) -> List[Dict]:
        """获取用户记忆"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            
            memories = []
            for row in cursor.fetchall():
                memories.append(dict(row))
            
            return memories