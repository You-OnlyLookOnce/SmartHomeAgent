"""
记忆管理 MCP 工具

提供记忆存储、检索和管理功能。
"""

from typing import Dict, Any, Optional, List
import logging
from src.core.mcp_tool_registry import mcp_tool

logger = logging.getLogger(__name__)

# 记忆管理器实例
_memory_manager = None


def _get_memory_manager():
    """获取记忆管理器（懒加载）"""
    global _memory_manager
    if _memory_manager is None:
        from agent.memory_manager import memory_manager
        _memory_manager = memory_manager
    return _memory_manager


@mcp_tool(
    name="store_memory",
    description="存储用户的重要信息到长期记忆中，如用户的喜好、习惯、重要事件等",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要存储的记忆内容"
            },
            "category": {
                "type": "string",
                "description": "记忆类别，如 preference（偏好）、habit（习惯）、event（事件）",
                "enum": ["preference", "habit", "event", "fact", "other"],
                "default": "other"
            },
            "importance": {
                "type": "integer",
                "description": "重要程度（1-10）",
                "minimum": 1,
                "maximum": 10,
                "default": 5
            }
        },
        "required": ["content"]
    },
    category="memory",
    tags={"memory", "store", "remember"}
)
async def store_memory(
    content: str,
    category: str = "other",
    importance: int = 5
) -> Dict[str, Any]:
    """
    存储记忆
    
    Args:
        content: 记忆内容
        category: 记忆类别
        importance: 重要程度
        
    Returns:
        存储结果
    """
    try:
        logger.info(f"存储记忆: {content[:50]}...")
        
        memory_manager = _get_memory_manager()
        
        # 构建记忆信息
        memory_info = {
            "content": content,
            "category": category,
            "importance": importance
        }
        
        # 存储记忆
        result = memory_manager.store_memory_info(memory_info)
        
        if result:
            logger.info("记忆存储成功")
            return {
                "success": True,
                "message": "记忆已存储",
                "memory_id": result.get("id") if isinstance(result, dict) else None
            }
        else:
            return {
                "success": False,
                "message": "记忆存储失败"
            }
            
    except Exception as e:
        logger.error(f"存储记忆失败: {e}")
        return {
            "success": False,
            "message": f"存储记忆失败: {str(e)}"
        }


@mcp_tool(
    name="retrieve_memory",
    description="检索与查询相关的记忆",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "查询关键词"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5,
                "minimum": 1,
                "maximum": 20
            }
        },
        "required": ["query"]
    },
    category="memory",
    tags={"memory", "retrieve", "search"}
)
async def retrieve_memory(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    检索记忆
    
    Args:
        query: 查询关键词
        limit: 返回结果数量
        
    Returns:
        检索结果
    """
    try:
        logger.info(f"检索记忆: {query}")
        
        memory_manager = _get_memory_manager()
        
        # 检索记忆
        memories = memory_manager.retrieve_memories(query, limit=limit)
        
        formatted_memories = []
        for mem in memories:
            formatted_memories.append({
                "content": mem.get("content", ""),
                "category": mem.get("category", "other"),
                "importance": mem.get("importance", 5),
                "timestamp": mem.get("timestamp", "")
            })
            
        logger.info(f"检索到 {len(formatted_memories)} 条记忆")
        
        return {
            "success": True,
            "query": query,
            "count": len(formatted_memories),
            "memories": formatted_memories
        }
        
    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        return {
            "success": False,
            "message": f"检索记忆失败: {str(e)}"
        }


@mcp_tool(
    name="get_all_memories",
    description="获取所有存储的记忆",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "按类别筛选",
                "enum": ["preference", "habit", "event", "fact", "other", "all"],
                "default": "all"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 50,
                "minimum": 1,
                "maximum": 100
            }
        }
    },
    category="memory",
    tags={"memory", "list", "all"}
)
async def get_all_memories(category: str = "all", limit: int = 50) -> Dict[str, Any]:
    """
    获取所有记忆
    
    Args:
        category: 类别筛选
        limit: 返回数量
        
    Returns:
        记忆列表
    """
    try:
        memory_manager = _get_memory_manager()
        
        # 获取所有记忆
        all_memories = memory_manager.get_all_memories()
        
        # 按类别筛选
        if category != "all":
            all_memories = [m for m in all_memories if m.get("category") == category]
            
        # 限制数量
        all_memories = all_memories[:limit]
        
        formatted_memories = []
        for mem in all_memories:
            formatted_memories.append({
                "id": mem.get("id"),
                "content": mem.get("content", ""),
                "category": mem.get("category", "other"),
                "importance": mem.get("importance", 5),
                "timestamp": mem.get("timestamp", "")
            })
            
        return {
            "success": True,
            "count": len(formatted_memories),
            "memories": formatted_memories
        }
        
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        return {
            "success": False,
            "message": f"获取记忆失败: {str(e)}"
        }


@mcp_tool(
    name="delete_memory",
    description="删除指定的记忆",
    parameters={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "string",
                "description": "记忆ID"
            }
        },
        "required": ["memory_id"]
    },
    category="memory",
    tags={"memory", "delete", "remove"}
)
async def delete_memory(memory_id: str) -> Dict[str, Any]:
    """
    删除记忆
    
    Args:
        memory_id: 记忆ID
        
    Returns:
        删除结果
    """
    try:
        logger.info(f"删除记忆: {memory_id}")
        
        memory_manager = _get_memory_manager()
        
        # 删除记忆
        result = memory_manager.delete_memory(memory_id)
        
        if result:
            logger.info("记忆删除成功")
            return {
                "success": True,
                "message": "记忆已删除"
            }
        else:
            return {
                "success": False,
                "message": "记忆删除失败或记忆不存在"
            }
            
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        return {
            "success": False,
            "message": f"删除记忆失败: {str(e)}"
        }
