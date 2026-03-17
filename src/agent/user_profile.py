from typing import Dict, List, Any
from datetime import datetime, date
import json
import os

class UserProfileManager:
    """层级用户画像管理器 - SAGE风格"""
    
    def __init__(self):
        # 长期记忆
        self.long_term_memory = []
        # 每日摘要
        self.daily_summaries = {}
        # 全局画像
        self.global_profile = {}
        # 存储路径
        self.data_dir = "data/user_profiles"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def add_interaction(self, utterance: str):
        """添加用户交互记录"""
        self.long_term_memory.append({
            'timestamp': datetime.now().isoformat(),
            'utterance': utterance
        })
    
    def distill_daily(self, user_id: str):
        """夜间记忆蒸馏 - 生成每日摘要"""
        today = date.today().isoformat()
        today_memories = [m for m in self.long_term_memory 
                         if m['timestamp'].split('T')[0] == today]
        
        if not today_memories:
            return {"message": "今天没有交互记录"}
        
        # 生成每日摘要（模拟）
        summary = {
            "date": today,
            "interactions_count": len(today_memories),
            "key_patterns": ["灯光控制", "提醒设置"],
            "preferences": ["喜欢在晚上开灯"]
        }
        
        self.daily_summaries[today] = summary
        
        # 保存每日摘要
        self._save_daily_summary(user_id, summary)
        
        return summary
    
    def update_global_profile(self, user_id: str):
        """更新全局用户画像"""
        # 汇总所有每日摘要
        all_summaries = list(self.daily_summaries.values())
        
        if not all_summaries:
            return {"message": "没有足够的历史数据"}
        
        # 生成全局画像（模拟）
        self.global_profile = {
            "user_id": user_id,
            "updated_at": datetime.now().isoformat(),
            "personality": "温暖、友好",
            "habits": ["晚上开灯", "设置会议提醒"],
            "preferences": {
                "light_brightness": 70,
                "reminder_time": "09:00"
            },
            "interests": ["智能家居", "效率工具"]
        }
        
        # 保存全局画像
        self._save_global_profile(user_id, self.global_profile)
        
        return self.global_profile
    
    def personalize_response(self, query: str, user_id: str) -> str:
        """生成个性化响应"""
        # 加载用户画像
        self._load_global_profile(user_id)
        
        # 基于用户画像生成个性化响应（模拟）
        if "开灯" in query:
            brightness = self.global_profile.get("preferences", {}).get("light_brightness", 100)
            return f"已为您打开灯，亮度设置为 {brightness}%"
        elif "提醒" in query:
            reminder_time = self.global_profile.get("preferences", {}).get("reminder_time", "09:00")
            return f"已为您创建提醒，时间设置为 {reminder_time}"
        else:
            return f"您好！我是您的智能家居助手，有什么可以帮您的吗？"
    
    def _save_daily_summary(self, user_id: str, summary: Dict):
        """保存每日摘要"""
        summary_file = os.path.join(self.data_dir, f"{user_id}_daily_summaries.json")
        
        # 加载现有摘要
        existing_summaries = {}
        if os.path.exists(summary_file):
            with open(summary_file, "r", encoding="utf-8") as f:
                existing_summaries = json.load(f)
        
        # 更新摘要
        existing_summaries[summary["date"]] = summary
        
        # 保存更新后的摘要
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(existing_summaries, f, ensure_ascii=False, indent=2)
    
    def _save_global_profile(self, user_id: str, profile: Dict):
        """保存全局画像"""
        profile_file = os.path.join(self.data_dir, f"{user_id}_global_profile.json")
        
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    
    def _load_global_profile(self, user_id: str):
        """加载全局画像"""
        profile_file = os.path.join(self.data_dir, f"{user_id}_global_profile.json")
        
        if os.path.exists(profile_file):
            with open(profile_file, "r", encoding="utf-8") as f:
                self.global_profile = json.load(f)
    
    def get_user_profile(self, user_id: str) -> Dict:
        """获取用户画像"""
        self._load_global_profile(user_id)
        return self.global_profile
