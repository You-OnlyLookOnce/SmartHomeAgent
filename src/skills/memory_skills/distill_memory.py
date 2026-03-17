from src.skills.skill_base import SkillBase
from typing import Dict, List
import json
import os
import time

class DistillMemorySkill(SkillBase):
    """记忆蒸馏技能"""
    
    # 技能元信息
    SKILL_NAME = "distill_memory"
    SKILL_DESCRIPTION = "记忆蒸馏"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "force": {"type": "bool", "default": False}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "distilled_insights": "list",
        "report": "dict"
    }
    
    def __init__(self):
        # 确保记忆存储目录存在
        self.memory_dir = "data/memories"
        self.distilled_dir = "data/distilled"
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.distilled_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        force = params.get("force", False)
        
        # 检查是否需要蒸馏
        last_distill_file = os.path.join(self.distilled_dir, f"{user_id}_last_distill.json")
        if not force and os.path.exists(last_distill_file):
            with open(last_distill_file, "r", encoding="utf-8") as f:
                last_distill = json.load(f)
            last_time = last_distill.get("timestamp", 0)
            # 如果距离上次蒸馏不足24小时，跳过
            if time.time() - last_time < 24 * 3600:
                return {
                    "success": False,
                    "message": "距离上次蒸馏不足24小时",
                    "distilled_insights": [],
                    "report": {}
                }
        
        # 收集交互数据
        interactions = await self._collect_interactions(user_id)
        
        # 提取有价值的见解
        valuable_insights = await self._extract_insights(interactions)
        
        # 更新知识库
        await self._update_knowledge_base(user_id, valuable_insights)
        
        # 生成蒸馏报告
        report = {
            "timestamp": time.time(),
            "user_id": user_id,
            "interactions_count": len(interactions),
            "insights_count": len(valuable_insights),
            "summary": f"从 {len(interactions)} 条交互中提取了 {len(valuable_insights)} 条有价值的见解"
        }
        
        # 保存上次蒸馏时间
        with open(last_distill_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time()}, f)
        
        # 记录日志
        await self.log_operation(user_id, "distill_memory", report)
        
        return {
            "success": True,
            "message": "记忆蒸馏完成",
            "distilled_insights": valuable_insights,
            "report": report
        }
    
    async def _collect_interactions(self, user_id: str) -> List[Dict]:
        """收集交互数据"""
        # 这里应该从日志或数据库中收集交互数据
        # 暂时返回模拟数据
        return [
            {"timestamp": time.time() - 3600, "type": "device_control", "content": "打开客厅灯"},
            {"timestamp": time.time() - 7200, "type": "query", "content": "今天天气怎么样"},
            {"timestamp": time.time() - 10800, "type": "task", "content": "明天早上8点提醒我开会"}
        ]
    
    async def _extract_insights(self, interactions: List[Dict]) -> List[Dict]:
        """提取有价值的见解"""
        # 这里应该使用LLM提取见解
        # 暂时返回模拟结果
        return [
            {"type": "user_habit", "content": "用户喜欢在晚上开灯"},
            {"type": "user_interest", "content": "用户关注天气信息"},
            {"type": "task_pattern", "content": "用户经常设置会议提醒"}
        ]
    
    async def _update_knowledge_base(self, user_id: str, insights: List[Dict]):
        """更新知识库"""
        # 保存蒸馏后的见解到知识库
        knowledge_file = os.path.join(self.distilled_dir, f"{user_id}_knowledge.json")
        if os.path.exists(knowledge_file):
            with open(knowledge_file, "r", encoding="utf-8") as f:
                knowledge = json.load(f)
        else:
            knowledge = []
        
        knowledge.extend(insights)
        
        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
