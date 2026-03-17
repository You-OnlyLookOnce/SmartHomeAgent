from src.skills.skill_base import SkillBase
from typing import Dict, List

class VectorSearchSkill(SkillBase):
    """向量检索技能"""
    
    # 技能元信息
    SKILL_NAME = "vector_search"
    SKILL_DESCRIPTION = "向量检索（语义理解）"
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
    
    def __init__(self):
        # 初始化示例文档
        self.documents = [
            {"id": "1", "content": "智能家居系统可以控制灯光、风扇等设备", "category": "智能家居"},
            {"id": "2", "content": "LED灯可以调节亮度和颜色", "category": "灯光控制"},
            {"id": "3", "content": "风扇可以调节速度和模式", "category": "风扇控制"},
            {"id": "4", "content": "传感器可以监测温度、湿度等环境数据", "category": "传感器"},
            {"id": "5", "content": "智能提醒可以帮助用户管理时间", "category": "提醒"}
        ]
    
    async def execute(self, params: Dict) -> Dict:
        query = params["query"]
        top_k = params.get("top_k", 5)
        
        # 执行向量检索
        results = await self._vector_search(query, top_k)
        
        return {
            "success": True,
            "message": f"成功检索到 {len(results)} 条结果",
            "results": results
        }
    
    async def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """向量检索 - 模拟"""
        # 简单的语义相似度模拟
        results = []
        for doc in self.documents:
            # 简单的关键词匹配作为相似度
            score = sum(1 for word in query.split() if word in doc["content"])
            if score > 0:
                results.append({
                    "id": f"vector_{doc['id']}",
                    "content": doc["content"],
                    "score": score * 0.2,
                    "type": "vector",
                    "category": doc["category"]
                })
        
        # 排序并取前top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
