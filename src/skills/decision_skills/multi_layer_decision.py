from typing import Optional, Dict, Any
from src.skills.search_skills.search_judgment import SearchJudgment
from src.skills.knowledge_skills.built_in_knowledge import BuiltInKnowledge

class MultiLayerDecision:
    """多层决策系统，分析用户查询并决定如何处理"""
    
    def __init__(self):
        # 初始化内置知识库
        self.knowledge_base = BuiltInKnowledge()
        # 初始化搜索判断器
        self.search_judgment = SearchJudgment()
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析用户查询并返回决策结果
        
        Args:
            query: 用户查询
            
        Returns:
            决策结果，包含以下字段：
            - type: 处理类型 (knowledge, search, llm)
            - answer: 预定义回答（如果是简单问题）
            - need_search: 是否需要搜索（如果是复杂问题）
            - search_type: 搜索类型（如果需要搜索）
            - time_filter: 时间过滤参数（如果需要搜索）
        """
        print(f"[多层决策] 分析查询: {query}")
        
        # 1. 首先检查是否是简单问题（可以从知识库中直接回答）
        knowledge_answer = self.knowledge_base.search(query)
        if knowledge_answer:
            print(f"[多层决策] 识别为简单问题，从知识库获取回答")
            return {
                "type": "knowledge",
                "answer": knowledge_answer,
                "need_search": False
            }
        
        # 2. 如果是复杂问题，检查是否需要搜索
        need_search = self.search_judgment.is_search_needed(query)
        search_type = self.search_judgment.get_search_type(query)
        time_filter = self.search_judgment.get_time_filter(query)
        
        if need_search:
            print(f"[多层决策] 识别为复杂问题，需要搜索")
            return {
                "type": "search",
                "need_search": True,
                "search_type": search_type,
                "time_filter": time_filter
            }
        
        # 3. 如果不需要搜索，使用LLM直接回答
        print(f"[多层决策] 识别为复杂问题，使用LLM回答")
        return {
            "type": "llm",
            "need_search": False
        }
    
    def get_knowledge_answer(self, query: str) -> Optional[str]:
        """从知识库获取回答
        
        Args:
            query: 用户查询
            
        Returns:
            知识库中的回答，如果没有匹配则返回None
        """
        return self.knowledge_base.search(query)
    
    def is_simple_question(self, query: str) -> bool:
        """判断是否是简单问题
        
        Args:
            query: 用户查询
            
        Returns:
            是否是简单问题
        """
        return self.knowledge_base.is_simple_question(query)
    
    def is_search_needed(self, query: str) -> bool:
        """判断是否需要搜索
        
        Args:
            query: 用户查询
            
        Returns:
            是否需要搜索
        """
        # 如果是简单问题，不需要搜索
        if self.is_simple_question(query):
            return False
        # 否则使用搜索判断器
        return self.search_judgment.is_search_needed(query)
