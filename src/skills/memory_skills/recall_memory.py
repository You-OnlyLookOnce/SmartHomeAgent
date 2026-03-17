from src.skills.skill_base import SkillBase
from typing import Dict
import json
import os

class RecallMemorySkill(SkillBase):
    """回忆记忆技能"""
    
    # 技能元信息
    SKILL_NAME = "recall_memory"
    SKILL_DESCRIPTION = "回忆用户记忆"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "user_id": {"type": "string", "required": True},
        "memory_key": {"type": "string", "required": False},
        "query": {"type": "string", "required": False}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "memories": "list"
    }
    
    def __init__(self):
        # 确保记忆存储目录存在
        self.memory_dir = "data/memories"
        os.makedirs(self.memory_dir, exist_ok=True)
        self.preference_dir = "data/preferences"
    
    async def execute(self, params: Dict) -> Dict:
        user_id = params["user_id"]
        memory_key = params.get("memory_key")
        query = params.get("query")
        
        memories = []
        
        # 从偏好中检索
        if memory_key:
            preference_file = os.path.join(self.preference_dir, f"{user_id}.json")
            if os.path.exists(preference_file):
                with open(preference_file, "r", encoding="utf-8") as f:
                    preferences = json.load(f)
                    if memory_key in preferences:
                        memories.append({
                            "type": "preference",
                            "key": memory_key,
                            "value": preferences[memory_key]
                        })
        
        # 从记忆库中检索
        memory_file = os.path.join(self.memory_dir, f"{user_id}.json")
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                all_memories = json.load(f)
                if query:
                    # 简单的关键词匹配
                    for memory in all_memories:
                        if query.lower() in str(memory).lower():
                            memories.append(memory)
                else:
                    # 返回所有记忆
                    memories.extend(all_memories)
        
        # 记录日志
        await self.log_operation(user_id, "recall_memory", {
            "memory_key": memory_key,
            "query": query,
            "count": len(memories)
        })
        
        return {
            "success": True,
            "message": f"成功回忆 {len(memories)} 条记忆",
            "memories": memories
        }
