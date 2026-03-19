import json
import os
import datetime
from typing import Dict, Optional, Any, List

class MemoryManager:
    """记忆管理器 - 负责读取和管理记忆文件"""
    
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent_memory")
        self.soul_file = os.path.join(self.base_dir, "soul.json")
        self.profile_file = os.path.join(self.base_dir, "personality", "profile.json")
        self.long_term_memory_file = os.path.join(self.base_dir, "MEMORY.md")
        self.daily_notes_dir = os.path.join(self.base_dir, "memory")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "personality"), exist_ok=True)
        os.makedirs(self.daily_notes_dir, exist_ok=True)
        
        # 初始化短期记忆
        self.short_term_memory = []
    
    def read_soul(self) -> Optional[Dict[str, Any]]:
        """读取灵魂文件"""
        try:
            if os.path.exists(self.soul_file):
                with open(self.soul_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            print(f"读取灵魂文件失败: {e}")
            return None
    
    def read_profile(self) -> Optional[Dict[str, Any]]:
        """读取个人资料文件"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            print(f"读取个人资料文件失败: {e}")
            return None
    
    def read_long_term_memory(self) -> str:
        """读取长期记忆文件"""
        try:
            if os.path.exists(self.long_term_memory_file):
                with open(self.long_term_memory_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                # 如果文件不存在，返回默认内容
                default_content = "# MEMORY.md - 长期记忆库\n\n## 技术偏好\n- **编程语言**：Python 为主，C++ 为辅\n- **正在学习**：ROS2、YOLO、嵌入式开发\n- **学习方式**：项目驱动学习（先做成功再思考问题）\n\n## 工具设置\n- **浏览器工具**：browser_use（Playwright 后端）\n- **定时任务**：Copaw cron（每周三、六 21:00 执行周报）\n- **Python 环境**：E:\Anaconda\envs\copaw_env\python.exe\n- **系统编码**：GBK（代码页 936）\n"
                self.write_long_term_memory(default_content)
                return default_content
        except Exception as e:
            print(f"读取长期记忆文件失败: {e}")
            return ""
    
    def write_long_term_memory(self, content: str):
        """写入长期记忆文件"""
        try:
            with open(self.long_term_memory_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"写入长期记忆文件失败: {e}")
    
    def append_daily_note(self, content: str):
        """追加每日笔记"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            note_file = os.path.join(self.daily_notes_dir, f"{today}.md")
            
            # 检查文件是否存在
            if not os.path.exists(note_file):
                # 创建新文件
                with open(note_file, "w", encoding="utf-8") as f:
                    f.write(f"# {today}.md\n\n")
            
            # 追加内容
            current_time = datetime.datetime.now().strftime("%H:%M")
            with open(note_file, "a", encoding="utf-8") as f:
                f.write(f"## {current_time}\n{content}\n\n")
        except Exception as e:
            print(f"追加每日笔记失败: {e}")
    
    def read_daily_note(self, date: str = None) -> str:
        """读取指定日期的每日笔记"""
        try:
            if date is None:
                date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            note_file = os.path.join(self.daily_notes_dir, f"{date}.md")
            if os.path.exists(note_file):
                with open(note_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return f"# {date}.md\n\n"  # 返回空的笔记模板
        except Exception as e:
            print(f"读取每日笔记失败: {e}")
            return ""
    
    def add_to_short_term_memory(self, item: Dict[str, Any]):
        """添加到短期记忆"""
        self.short_term_memory.append(item)
        # 限制短期记忆长度
        if len(self.short_term_memory) > 100:
            self.short_term_memory = self.short_term_memory[-100:]
    
    def get_short_term_memory(self) -> List[Dict[str, Any]]:
        """获取短期记忆"""
        return self.short_term_memory
    
    def clear_short_term_memory(self):
        """清空短期记忆"""
        self.short_term_memory = []
    
    def memory_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """语义搜索记忆"""
        try:
            # 读取所有记忆文件
            memories = []
            
            # 读取长期记忆
            long_term_content = self.read_long_term_memory()
            memories.append({"source": "MEMORY.md", "content": long_term_content})
            
            # 读取最近7天的每日笔记
            for i in range(7):
                date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                note_content = self.read_daily_note(date)
                if note_content:
                    memories.append({"source": f"memory/{date}.md", "content": note_content})
            
            # 模拟语义搜索（实际项目中应该使用向量嵌入和余弦相似度）
            results = []
            for memory in memories:
                if query in memory["content"]:
                    results.append({
                        "source": memory["source"],
                        "content": memory["content"][:200] + "..." if len(memory["content"]) > 200 else memory["content"],
                        "score": 0.9  # 模拟相似度分数
                    })
            
            # 按分数排序并返回前max_results个结果
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:max_results]
        except Exception as e:
            print(f"记忆搜索失败: {e}")
            return []
    
    def update_memory(self, conversation: Dict[str, Any]):
        """更新记忆"""
        # 添加到短期记忆
        self.add_to_short_term_memory(conversation)
        
        # 追加到每日笔记
        user_input = conversation.get("user", "")
        assistant_response = conversation.get("assistant", "")
        note_content = f"- 用户: {user_input}\n- 助手: {assistant_response}"
        self.append_daily_note(note_content)
    
    def get_agent_name(self) -> str:
        """获取智能代理名称"""
        soul = self.read_soul()
        if soul and "name" in soul:
            return soul["name"]
        return "悦悦"  # 默认名称
    
    def get_core_guidelines(self) -> Optional[Dict[str, Any]]:
        """获取核心指南"""
        soul = self.read_soul()
        if soul and "core_guidelines" in soul:
            return soul["core_guidelines"]
        return None
    
    def get_user_preferences(self) -> Optional[Dict[str, Any]]:
        """获取用户偏好"""
        profile = self.read_profile()
        if profile and "user_profile" in profile and "preferences" in profile["user_profile"]:
            return profile["user_profile"]["preferences"]
        return None
    
    def get_communication_preferences(self) -> Optional[Dict[str, Any]]:
        """获取沟通偏好"""
        profile = self.read_profile()
        if profile and "user_profile" in profile and "communication_preferences" in profile["user_profile"]:
            return profile["user_profile"]["communication_preferences"]
        return None

