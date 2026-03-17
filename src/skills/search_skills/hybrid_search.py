from src.skills.skill_base import SkillBase
from typing import Dict, List
import os

class HybridSearchSkill(SkillBase):
    """混合检索技能"""
    
    # 技能元信息
    SKILL_NAME = "hybrid_search"
    SKILL_DESCRIPTION = "混合检索（向量 + 关键词 + 规则）"
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
        
        # 执行混合检索
        results = await self.search(query, top_k)
        
        return {
            "success": True,
            "message": f"成功检索到 {len(results)} 条结果",
            "results": results
        }
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索"""
        results = []
        
        # 1. 向量检索 (语义理解) - 模拟
        vector_results = await self._vector_search(query, top_k)
        results.extend(vector_results)
        
        # 2. 关键词检索 (精确匹配) - 模拟
        keyword_results = await self._keyword_search(query, top_k)
        results.extend(keyword_results)
        
        # 3. 规则匹配 (高优先级)
        rule_results = self._rule_match(query)
        results.extend(rule_results)
        
        # 4. 去重和排序
        results = self._deduplicate_and_rank(results, top_k)
        
        return results
    
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
    
    async def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """关键词检索 - 模拟"""
        # 简单的关键词匹配
        results = []
        for doc in self.documents:
            if query in doc["content"]:
                results.append({
                    "id": f"keyword_{doc['id']}",
                    "content": doc["content"],
                    "score": 0.5,
                    "type": "keyword",
                    "category": doc["category"]
                })
        
        return results[:top_k]
    
    def _rule_match(self, query: str) -> List[Dict]:
        """规则匹配 (高优先级)"""
        # 预设规则，如"开灯" -> 直接触发led_on技能
        rules = {
            "开灯": {"skill": "led_on", "priority": 100},
            "关灯": {"skill": "led_off", "priority": 100},
            "提醒": {"skill": "create_reminder", "priority": 100},
            "任务": {"skill": "schedule_task", "priority": 100},
            "温度": {"skill": "sensor_read", "priority": 90},
            "湿度": {"skill": "sensor_read", "priority": 90}
        }
        
        results = []
        for keyword, rule in rules.items():
            if keyword in query:
                results.append({
                    "id": f"rule_{keyword}",
                    "content": f"规则匹配: {keyword}",
                    "score": rule["priority"],
                    "type": "rule",
                    "skill": rule["skill"]
                })
        return results
    
    def _deduplicate_and_rank(self, results: List[Dict], top_k: int) -> List[Dict]:
        """去重和排序"""
        # 去重
        seen_ids = set()
        unique_results = []
        for result in results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 取前top_k个
        return unique_results[:top_k]
