from typing import Dict, Optional, List
from ai.qiniu_llm import QiniuLLM

class SearchIntegration:
    """搜索结果处理和整合功能"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = QiniuLLM()
    
    async def integrate_search_results(self, query: str, search_results: str) -> str:
        """整合搜索结果到回答中
        
        Args:
            query: 用户查询
            search_results: 格式化后的搜索结果
            
        Returns:
            整合后的回答
        """
        # 构建提示词，让模型基于搜索结果生成自然的回答
        prompt = f"用户问: {query}\n\n根据以下搜索结果，生成一个自然、连贯的回答，不要直接复制搜索结果，而是将信息整合到回答中：\n\n{search_results}\n\n请用中文回答，回答要自然、友好，符合对话的语境。回答要准确反映搜索结果中的信息，不要添加搜索结果中没有的内容。"
        
        # 调用模型生成回答
        response = await self.llm.generate_text(prompt, stream=False)
        
        if response.get("success", False):
            return response.get("text", "")
        else:
            # 如果模型调用失败，直接返回搜索结果
            return f"根据搜索结果，{search_results}"
    
    async def process_tool_call(self, tool_calls: list, query: str) -> Dict:
        """处理工具调用
        
        Args:
            tool_calls: 工具调用列表
            query: 用户查询
            
        Returns:
            处理结果
        """
        from src.skills.search_skills.web_search import WebSearchSkill
        
        web_search = WebSearchSkill(self.api_key)
        
        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name", "")
            function_args = tool_call.get("function", {}).get("arguments", {})
            
            if function_name == "web_search":
                # 执行网络搜索
                search_query = function_args.get("query", query)
                search_type = function_args.get("search_type", "web")
                time_filter = function_args.get("time_filter", None)
                site_filter = function_args.get("site_filter", None)
                
                try:
                    search_result = web_search.execute(
                        search_query,
                        search_type=search_type,
                        time_filter=time_filter,
                        site_filter=site_filter
                    )
                    
                    if search_result.get("success", False):
                        # 整合搜索结果
                        integrated_answer = await self.integrate_search_results(query, search_result.get("result", ""))
                        return {
                            "success": True,
                            "answer": integrated_answer,
                            "search_result": search_result
                        }
                    else:
                        # 获取错误信息
                        error_code = search_result.get("error_code", "SEARCH_ERROR")
                        error_message = search_result.get("error_message", "搜索失败")
                        friendly_message = search_result.get("message", "搜索失败")
                        
                        return {
                            "success": False,
                            "error_code": error_code,
                            "error_message": error_message,
                            "message": friendly_message
                        }
                except Exception as e:
                    error_message = f"处理搜索工具调用失败: {str(e)}"
                    print(f"[搜索集成] 处理工具调用异常: {error_message}")
                    return {
                        "success": False,
                        "error_code": "TOOL_EXECUTION_ERROR",
                        "error_message": error_message,
                        "message": "抱歉，搜索工具执行失败"
                    }
        
        return {
            "success": False,
            "error_code": "INVALID_TOOL_CALL",
            "error_message": "未找到有效的工具调用",
            "message": "抱歉，未找到有效的搜索工具调用"
        }
    
    def extract_key_info(self, search_result: Dict) -> List[Dict]:
        """从搜索结果中提取关键信息
        
        Args:
            search_result: 搜索结果
            
        Returns:
            提取的关键信息列表
        """
        key_info = []
        
        if search_result.get("success", True):
            data = search_result.get("data", {})
            results = data.get("results", [])
            
            for result in results[:3]:  # 只处理前3个结果
                info = {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "source": result.get("source", ""),
                    "date": result.get("date", "")
                }
                if info["title"] or info["content"]:
                    key_info.append(info)
        
        return key_info
    
    def format_key_info(self, key_info: List[Dict]) -> str:
        """格式化关键信息
        
        Args:
            key_info: 关键信息列表
            
        Returns:
            格式化后的字符串
        """
        formatted = []
        
        for i, info in enumerate(key_info, 1):
            item = []
            if info["title"]:
                item.append(f"{i}. {info['title']}")
            if info["content"]:
                # 限制内容长度
                if len(info["content"]) > 150:
                    info["content"] = info["content"][:150] + "..."
                item.append(info["content"])
            if info["source"]:
                item.append(f"来源: {info['source']}")
            if info["date"]:
                item.append(f"时间: {info['date']}")
            if info["url"]:
                item.append(f"链接: {info['url']}")
            
            if item:
                formatted.append("\n".join(item) + "\n")
        
        return "\n".join(formatted)