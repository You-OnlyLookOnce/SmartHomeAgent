"""
备忘录 MCP 工具

提供备忘录创建、查询和管理功能。
"""

from typing import Dict, Any, Optional, List
import logging
from src.core.mcp_tool_registry import mcp_tool

logger = logging.getLogger(__name__)

# 备忘录管理器实例
_memo_manager = None


def _get_memo_manager():
    """获取备忘录管理器（懒加载）"""
    global _memo_manager
    if _memo_manager is None:
        from agent.memo_manager import memo_manager
        _memo_manager = memo_manager
    return _memo_manager


@mcp_tool(
    name="create_memo",
    description="创建备忘录，记录重要信息、待办事项或笔记",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "备忘录标题"
            },
            "content": {
                "type": "string",
                "description": "备忘录内容"
            },
            "category": {
                "type": "string",
                "description": "备忘录类别",
                "enum": ["todo", "note", "reminder", "idea", "other"],
                "default": "note"
            },
            "tags": {
                "type": "array",
                "description": "标签列表",
                "items": {"type": "string"},
                "default": []
            }
        },
        "required": ["title", "content"]
    },
    category="memo",
    tags={"memo", "note", "create", "record"}
)
async def create_memo(
    title: str,
    content: str,
    category: str = "note",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    创建备忘录
    
    Args:
        title: 标题
        content: 内容
        category: 类别
        tags: 标签
        
    Returns:
        创建结果
    """
    try:
        logger.info(f"创建备忘录: {title}")
        
        memo_manager = _get_memo_manager()
        
        # 创建备忘录
        memo = memo_manager.create_memo(
            title=title,
            content=content,
            category=category,
            tags=tags or []
        )
        
        if memo:
            logger.info(f"备忘录创建成功: {memo.get('id')}")
            return {
                "success": True,
                "message": "备忘录创建成功",
                "memo": {
                    "id": memo.get("id"),
                    "title": memo.get("title"),
                    "content": memo.get("content"),
                    "category": memo.get("category"),
                    "tags": memo.get("tags", []),
                    "created_at": memo.get("created_at")
                }
            }
        else:
            return {
                "success": False,
                "message": "备忘录创建失败"
            }
            
    except Exception as e:
        logger.error(f"创建备忘录失败: {e}")
        return {
            "success": False,
            "message": f"创建备忘录失败: {str(e)}"
        }


@mcp_tool(
    name="get_memos",
    description="获取备忘录列表，支持按类别和标签筛选",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "按类别筛选",
                "enum": ["todo", "note", "reminder", "idea", "other", "all"],
                "default": "all"
            },
            "tag": {
                "type": "string",
                "description": "按标签筛选"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量限制",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            }
        }
    },
    category="memo",
    tags={"memo", "list", "query"}
)
async def get_memos(
    category: str = "all",
    tag: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    获取备忘录列表
    
    Args:
        category: 类别筛选
        tag: 标签筛选
        limit: 数量限制
        
    Returns:
        备忘录列表
    """
    try:
        memo_manager = _get_memo_manager()
        
        # 获取备忘录
        memos = memo_manager.get_memos(
            category=category if category != "all" else None,
            tag=tag,
            limit=limit
        )
        
        formatted_memos = []
        for memo in memos:
            formatted_memos.append({
                "id": memo.get("id"),
                "title": memo.get("title"),
                "content": memo.get("content"),
                "category": memo.get("category"),
                "tags": memo.get("tags", []),
                "created_at": memo.get("created_at"),
                "updated_at": memo.get("updated_at")
            })
            
        return {
            "success": True,
            "count": len(formatted_memos),
            "memos": formatted_memos
        }
        
    except Exception as e:
        logger.error(f"获取备忘录失败: {e}")
        return {
            "success": False,
            "message": f"获取备忘录失败: {str(e)}"
        }


@mcp_tool(
    name="search_memos",
    description="搜索备忘录内容",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量限制",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    },
    category="memo",
    tags={"memo", "search", "find"}
)
async def search_memos(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    搜索备忘录
    
    Args:
        query: 搜索关键词
        limit: 数量限制
        
    Returns:
        搜索结果
    """
    try:
        logger.info(f"搜索备忘录: {query}")
        
        memo_manager = _get_memo_manager()
        
        # 搜索备忘录
        memos = memo_manager.search_memos(query, limit=limit)
        
        formatted_memos = []
        for memo in memos:
            formatted_memos.append({
                "id": memo.get("id"),
                "title": memo.get("title"),
                "content": memo.get("content"),
                "category": memo.get("category"),
                "tags": memo.get("tags", []),
                "created_at": memo.get("created_at")
            })
            
        return {
            "success": True,
            "query": query,
            "count": len(formatted_memos),
            "memos": formatted_memos
        }
        
    except Exception as e:
        logger.error(f"搜索备忘录失败: {e}")
        return {
            "success": False,
            "message": f"搜索备忘录失败: {str(e)}"
        }


@mcp_tool(
    name="update_memo",
    description="更新指定的备忘录",
    parameters={
        "type": "object",
        "properties": {
            "memo_id": {
                "type": "string",
                "description": "备忘录ID"
            },
            "title": {
                "type": "string",
                "description": "新标题"
            },
            "content": {
                "type": "string",
                "description": "新内容"
            },
            "category": {
                "type": "string",
                "description": "新类别"
            },
            "tags": {
                "type": "array",
                "description": "新标签列表",
                "items": {"type": "string"}
            }
        },
        "required": ["memo_id"]
    },
    category="memo",
    tags={"memo", "update", "edit"}
)
async def update_memo(
    memo_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    更新备忘录
    
    Args:
        memo_id: 备忘录ID
        title: 新标题
        content: 新内容
        category: 新类别
        tags: 新标签
        
    Returns:
        更新结果
    """
    try:
        logger.info(f"更新备忘录: {memo_id}")
        
        memo_manager = _get_memo_manager()
        
        # 构建更新数据
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if category is not None:
            update_data["category"] = category
        if tags is not None:
            update_data["tags"] = tags
            
        # 更新备忘录
        result = memo_manager.update_memo(memo_id, update_data)
        
        if result:
            logger.info("备忘录更新成功")
            return {
                "success": True,
                "message": "备忘录已更新"
            }
        else:
            return {
                "success": False,
                "message": "备忘录更新失败或备忘录不存在"
            }
            
    except Exception as e:
        logger.error(f"更新备忘录失败: {e}")
        return {
            "success": False,
            "message": f"更新备忘录失败: {str(e)}"
        }


@mcp_tool(
    name="delete_memo",
    description="删除指定的备忘录",
    parameters={
        "type": "object",
        "properties": {
            "memo_id": {
                "type": "string",
                "description": "备忘录ID"
            }
        },
        "required": ["memo_id"]
    },
    category="memo",
    tags={"memo", "delete", "remove"}
)
async def delete_memo(memo_id: str) -> Dict[str, Any]:
    """
    删除备忘录
    
    Args:
        memo_id: 备忘录ID
        
    Returns:
        删除结果
    """
    try:
        logger.info(f"删除备忘录: {memo_id}")
        
        memo_manager = _get_memo_manager()
        
        # 删除备忘录
        result = memo_manager.delete_memo(memo_id)
        
        if result:
            logger.info("备忘录删除成功")
            return {
                "success": True,
                "message": "备忘录已删除"
            }
        else:
            return {
                "success": False,
                "message": "备忘录删除失败或备忘录不存在"
            }
            
    except Exception as e:
        logger.error(f"删除备忘录失败: {e}")
        return {
            "success": False,
            "message": f"删除备忘录失败: {str(e)}"
        }
