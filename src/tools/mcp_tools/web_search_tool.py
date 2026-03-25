"""
网络搜索 MCP 工具

集成七牛云全网搜索 API，提供网络搜索功能。
API 文档：https://developer.qiniu.com/aitokenapi/13192/web-search-api
"""

from typing import Dict, Any, Optional
import logging
from src.core.mcp_tool_registry import mcp_tool
from src.ai.qiniu_llm_v2 import QiniuLLMV2

logger = logging.getLogger(__name__)

# 初始化搜索客户端
_search_client: Optional[QiniuLLMV2] = None


def _get_search_client() -> QiniuLLMV2:
    """获取搜索客户端（懒加载）"""
    global _search_client
    if _search_client is None:
        _search_client = QiniuLLMV2()
    return _search_client


@mcp_tool(
    name="web_search",
    description="搜索互联网上的信息，支持网页搜索、时间过滤等功能",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或查询语句"
            },
            "search_type": {
                "type": "string",
                "description": "搜索类型",
                "enum": ["web", "video", "image"],
                "default": "web"
            },
            "time_filter": {
                "type": "string",
                "description": "时间过滤条件",
                "enum": ["week", "month", "year", "semiyear"],
                "default": None
            },
            "max_results": {
                "type": "integer",
                "description": "返回结果数量，网页搜索默认20，最大50",
                "default": 20,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    },
    category="search",
    tags={"search", "web", "internet", "information"}
)
async def web_search(
    query: str,
    search_type: str = "web",
    time_filter: Optional[str] = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    网络搜索
    
    Args:
        query: 搜索关键词
        search_type: 搜索类型
        time_filter: 时间过滤
        max_results: 最大结果数
        
    Returns:
        搜索结果
    """
    try:
        logger.info(f"执行网络搜索: {query}, 类型: {search_type}")
        
        client = _get_search_client()
        result = await client.web_search(
            query=query,
            search_type=search_type,
            time_filter=time_filter,
            max_results=max_results
        )
        
        if result.get("success"):
            data = result.get("data", {})
            results = data.get("results", [])
            
            # 格式化搜索结果
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", ""),
                    "score": item.get("score", 0)
                })
                
            logger.info(f"搜索成功，找到 {len(formatted_results)} 条结果")
            
            return {
                "success": True,
                "query": query,
                "total": data.get("total", 0),
                "results": formatted_results
            }
        else:
            error_msg = result.get("message", "搜索失败")
            logger.error(f"搜索失败: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
            
    except Exception as e:
        logger.error(f"搜索异常: {e}")
        return {
            "success": False,
            "message": f"搜索失败: {str(e)}"
        }


@mcp_tool(
    name="search_news",
    description="搜索最新的新闻资讯，支持时间过滤",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "新闻搜索关键词"
            },
            "time_filter": {
                "type": "string",
                "description": "时间过滤，默认一周内",
                "enum": ["week", "month", "year", "semiyear"],
                "default": "week"
            },
            "max_results": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    },
    category="search",
    tags={"search", "news", "information"}
)
async def search_news(
    query: str,
    time_filter: str = "week",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    搜索新闻
    
    Args:
        query: 搜索关键词
        time_filter: 时间过滤
        max_results: 最大结果数
        
    Returns:
        新闻搜索结果
    """
    return await web_search(
        query=query,
        search_type="web",
        time_filter=time_filter,
        max_results=max_results
    )


@mcp_tool(
    name="get_current_time",
    description="获取当前的日期和时间信息",
    parameters={
        "type": "object",
        "properties": {}
    },
    category="datetime",
    tags={"time", "datetime", "current"}
)
async def get_current_time() -> Dict[str, Any]:
    """
    获取当前时间
    
    Returns:
        当前时间信息
    """
    from datetime import datetime
    import pytz
    
    try:
        # 使用中国时区
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        
        return {
            "success": True,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y年%m月%d日"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "weekday_cn": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()],
            "timestamp": int(now.timestamp())
        }
        
    except Exception as e:
        logger.error(f"获取时间失败: {e}")
        return {
            "success": False,
            "message": f"获取时间失败: {str(e)}"
        }


@mcp_tool(
    name="calculate",
    description="执行数学计算，支持基本运算和复杂表达式",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '1 + 2 * 3'、'sqrt(16)'"
            }
        },
        "required": ["expression"]
    },
    category="math",
    tags={"math", "calculate", "compute"}
)
async def calculate(expression: str) -> Dict[str, Any]:
    """
    数学计算
    
    Args:
        expression: 数学表达式
        
    Returns:
        计算结果
    """
    try:
        # 安全评估数学表达式
        import ast
        import operator
        import math
        
        # 定义允许的操作
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv
        }
        
        # 定义允许的函数
        allowed_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'max': max,
            'min': min,
            'pow': pow
        }
        
        # 定义允许的常量
        allowed_names = {
            'pi': math.pi,
            'e': math.e
        }
        
        def eval_node(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                op_type = type(node.op)
                if op_type in allowed_operators:
                    return allowed_operators[op_type](left, right)
                raise ValueError(f"不支持的操作: {op_type}")
            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                op_type = type(node.op)
                if op_type in allowed_operators:
                    return allowed_operators[op_type](operand)
                raise ValueError(f"不支持的一元操作: {op_type}")
            elif isinstance(node, ast.Call):
                func_name = node.func.id if isinstance(node.func, ast.Name) else None
                if func_name not in allowed_functions:
                    raise ValueError(f"不支持的函数: {func_name}")
                args = [eval_node(arg) for arg in node.args]
                return allowed_functions[func_name](*args)
            elif isinstance(node, ast.Name):
                if node.id not in allowed_names:
                    raise ValueError(f"不支持的名称: {node.id}")
                return allowed_names[node.id]
            elif isinstance(node, ast.Expression):
                return eval_node(node.body)
            else:
                raise ValueError(f"不支持的表达式类型: {type(node)}")
        
        # 解析表达式
        tree = ast.parse(expression, mode='eval')
        result = eval_node(tree)
        
        return {
            "success": True,
            "expression": expression,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"计算失败: {e}")
        return {
            "success": False,
            "message": f"计算失败: {str(e)}"
        }
