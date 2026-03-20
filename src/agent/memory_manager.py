import json
import os
import datetime
from typing import Dict, Optional, Any, List
import uuid

class MemoryManager:
    """记忆管理器 - 负责读取和管理记忆文件"""
    
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent_memory")
        self.soul_file = os.path.join(self.base_dir, "soul.json")
        self.profile_file = os.path.join(self.base_dir, "personality", "profile.json")
        self.long_term_memory_file = os.path.join(self.base_dir, "MEMORY.md")
        self.daily_notes_dir = os.path.join(self.base_dir, "memory")
        self.memory_versions_dir = os.path.join(self.base_dir, "versions")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "personality"), exist_ok=True)
        os.makedirs(self.daily_notes_dir, exist_ok=True)
        os.makedirs(self.memory_versions_dir, exist_ok=True)
        
        # 初始化短期记忆
        self.short_term_memory = []
        
        # 记忆老化规则
        self.aging_rules = {
            'user_preference': {'max_age_days': 180, 'action': 'review'},
            'project_milestone': {'max_age_days': 365, 'action': 'archive'},
            'decision': {'max_age_days': None, 'action': 'keep'},
            'lesson': {'max_age_days': 365, 'action': 'summarize'}
        }
    
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
    
    def distill_memory(self, days: int = 7):
        """执行记忆蒸馏
        
        Args:
            days: 要处理的天数
        """
        try:
            # 1. 收集待处理的每日笔记
            daily_notes = []
            for i in range(days):
                date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                note_file = os.path.join(self.daily_notes_dir, f"{date}.md")
                if os.path.exists(note_file):
                    with open(note_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        daily_notes.append({
                            "date": date,
                            "content": content
                        })
            
            if not daily_notes:
                return {"success": False, "message": "没有找到待处理的每日笔记"}
            
            # 2. 提取重要信息
            important_info = self._extract_important_info(daily_notes)
            
            if not important_info:
                return {"success": False, "message": "未提取到重要信息"}
            
            # 3. 读取现有长期记忆
            existing_memory = self.read_long_term_memory()
            
            # 4. 检测并解决冲突
            resolved_memory = self._resolve_conflicts(important_info, existing_memory)
            
            # 5. 保存记忆版本
            self._save_memory_version()
            
            # 6. 更新长期记忆
            self.write_long_term_memory(resolved_memory)
            
            # 7. 执行记忆老化
            self._age_memory()
            
            return {"success": True, "message": "记忆蒸馏完成"}
        except Exception as e:
            print(f"记忆蒸馏失败: {e}")
            return {"success": False, "message": str(e)}
    
    def _extract_important_info(self, daily_notes: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """提取重要信息
        
        Args:
            daily_notes: 每日笔记列表
            
        Returns:
            提取的重要信息，按类别分组
        """
        # 重要性评分
        importance_scores = {
            'decision': 0.9,      # 决策类
            'lesson': 0.85,       # 教训类
            'preference': 0.7,    # 用户偏好
            'project': 0.75,      # 项目进展
            'casual': 0.2,        # 闲聊
            'error_log': 0.6      # 错误记录
        }
        
        # 关键词匹配
        keywords = {
            'decision': ['决定', '选择', '确定', '最终方案', '同意', '批准', '否决'],
            'lesson': ['学会', '发现', '避免', '下次注意', '问题', '解决方案', '教训'],
            'preference': ['喜欢', '希望', '偏好', '建议', '想要', '需要', '不要'],
            'project': ['项目', '进展', '完成', '里程碑', '阶段', '计划'],
            'error_log': ['错误', '失败', '异常', '崩溃', '问题']
        }
        
        extracted_info = {
            '重要决策': [],
            '经验教训': [],
            '用户偏好': [],
            '项目里程碑': []
        }
        
        for note in daily_notes:
            content = note['content']
            date = note['date']
            
            # 按类别提取
            for category, category_keywords in keywords.items():
                for keyword in category_keywords:
                    if keyword in content:
                        # 提取包含关键词的句子
                        sentences = content.split('\n')
                        for sentence in sentences:
                            if keyword in sentence:
                                if category == 'decision':
                                    extracted_info['重要决策'].append(f"[{date}] {sentence.strip()}")
                                elif category == 'lesson':
                                    extracted_info['经验教训'].append(f"[{date}] {sentence.strip()}")
                                elif category == 'preference':
                                    extracted_info['用户偏好'].append(f"[{date}] {sentence.strip()}")
                                elif category == 'project':
                                    extracted_info['项目里程碑'].append(f"[{date}] {sentence.strip()}")
                                break
        
        return extracted_info
    
    def _resolve_conflicts(self, new_info: Dict[str, List[str]], existing_memory: str) -> str:
        """检测并解决记忆冲突
        
        Args:
            new_info: 新提取的信息
            existing_memory: 现有长期记忆
            
        Returns:
            解决冲突后的记忆内容
        """
        # 解析现有记忆
        existing_sections = {}
        lines = existing_memory.split('\n')
        current_section = None
        
        for line in lines:
            if line.startswith('## '):
                current_section = line[3:].strip()
                existing_sections[current_section] = []
            elif current_section:
                existing_sections[current_section].append(line)
        
        # 合并新信息
        for section, items in new_info.items():
            if section not in existing_sections:
                existing_sections[section] = []
            
            for item in items:
                # 检查是否重复
                is_duplicate = False
                for existing_item in existing_sections[section]:
                    if item in existing_item:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    existing_sections[section].append(item)
        
        # 重新构建记忆内容
        new_memory = "# MEMORY.md - 长期记忆库\n\n"
        
        for section, items in existing_sections.items():
            new_memory += f"## {section}\n"
            for item in items:
                if item.strip():
                    new_memory += f"- {item}\n"
            new_memory += "\n"
        
        return new_memory
    
    def _save_memory_version(self):
        """保存记忆版本"""
        try:
            if os.path.exists(self.long_term_memory_file):
                # 生成版本号
                version_id = len(os.listdir(self.memory_versions_dir)) + 1
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
                version_file = os.path.join(self.memory_versions_dir, f"MEMORY_{timestamp}_v{version_id}.md")
                
                # 复制当前记忆到版本文件
                with open(self.long_term_memory_file, "r", encoding="utf-8") as src:
                    content = src.read()
                
                with open(version_file, "w", encoding="utf-8") as dst:
                    dst.write(content)
        except Exception as e:
            print(f"保存记忆版本失败: {e}")
    
    def _age_memory(self):
        """执行记忆老化"""
        try:
            # 读取当前记忆
            memory_content = self.read_long_term_memory()
            
            # 解析记忆内容
            sections = {}
            lines = memory_content.split('\n')
            current_section = None
            
            for line in lines:
                if line.startswith('## '):
                    current_section = line[3:].strip()
                    sections[current_section] = []
                elif current_section:
                    sections[current_section].append(line)
            
            # 处理每个部分
            for section, items in sections.items():
                aged_items = []
                for item in items:
                    if item.strip().startswith('- ['):
                        # 提取日期
                        date_str = item.strip()[2:12]
                        try:
                            item_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            today = datetime.date.today()
                            age_days = (today - item_date).days
                            
                            # 根据老化规则处理
                            if section == '用户偏好':
                                rule = self.aging_rules['user_preference']
                            elif section == '项目里程碑':
                                rule = self.aging_rules['project_milestone']
                            elif section == '重要决策':
                                rule = self.aging_rules['decision']
                            elif section == '经验教训':
                                rule = self.aging_rules['lesson']
                            else:
                                rule = {'max_age_days': None, 'action': 'keep'}
                            
                            # 检查是否需要老化
                            if rule['max_age_days'] is None or age_days <= rule['max_age_days']:
                                aged_items.append(item)
                            elif rule['action'] == 'review':
                                # 标记为需要审查
                                aged_items.append(f"{item} (需要审查)")
                            elif rule['action'] == 'summarize':
                                # 标记为需要总结
                                aged_items.append(f"{item} (需要总结)")
                            # archive 操作暂时不处理
                        except Exception:
                            # 无法解析日期，保留原样
                            aged_items.append(item)
                    else:
                        aged_items.append(item)
                
                sections[section] = aged_items
            
            # 重新构建记忆内容
            new_memory = "# MEMORY.md - 长期记忆库\n\n"
            
            for section, items in sections.items():
                new_memory += f"## {section}\n"
                for item in items:
                    new_memory += f"{item}\n"
                new_memory += "\n"
            
            # 保存老化后的记忆
            self.write_long_term_memory(new_memory)
        except Exception as e:
            print(f"记忆老化失败: {e}")
    
    def get_memory_versions(self) -> List[str]:
        """获取记忆版本列表"""
        try:
            versions = []
            for filename in os.listdir(self.memory_versions_dir):
                if filename.startswith('MEMORY_') and filename.endswith('.md'):
                    versions.append(filename)
            versions.sort(reverse=True)
            return versions
        except Exception as e:
            print(f"获取记忆版本失败: {e}")
            return []
    
    def get_memory_version_content(self, version_filename: str) -> str:
        """获取指定版本的记忆内容"""
        try:
            version_file = os.path.join(self.memory_versions_dir, version_filename)
            if os.path.exists(version_file):
                with open(version_file, "r", encoding="utf-8") as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"获取记忆版本内容失败: {e}")
            return ""

