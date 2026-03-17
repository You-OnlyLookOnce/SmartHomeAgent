from src.skills.skill_base import SkillBase
from typing import Dict

class SearchKnowledgeSkill(SkillBase):
    """知识检索技能"""
    
    # 技能元信息
    SKILL_NAME = "search_knowledge"
    SKILL_DESCRIPTION = "搜索知识库"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "query": {"type": "string", "required": True},
        "top_k": {"type": "int", "default": 5, "range": [1, 20]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "results": "list"
    }
    
    async def execute(self, params: Dict) -> Dict:
        query = params["query"]
        top_k = params.get("top_k", 5)
        
        # 模拟知识库搜索
        # 实际实现时需要连接到真实的知识库
        results = [
            {"id": "1", "content": f"关于'{query}'的信息1", "score": 0.9},
            {"id": "2", "content": f"关于'{query}'的信息2", "score": 0.8},
            {"id": "3", "content": f"关于'{query}'的信息3", "score": 0.7}
        ][:top_k]
        
        return {
            "success": True,
            "message": f"成功搜索到{len(results)}条结果",
            "results": results
        }
