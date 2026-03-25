"""
定时任务 MCP 工具

提供任务创建、查询和管理功能。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from src.core.mcp_tool_registry import mcp_tool

logger = logging.getLogger(__name__)

# 任务调度器实例
_task_scheduler = None


def _get_task_scheduler():
    """获取任务调度器（懒加载）"""
    global _task_scheduler
    if _task_scheduler is None:
        from agent.task_scheduler import task_scheduler
        _task_scheduler = task_scheduler
    return _task_scheduler


@mcp_tool(
    name="create_task",
    description="创建定时任务或提醒，如设置闹钟、创建待办事项等",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "任务标题"
            },
            "content": {
                "type": "string",
                "description": "任务内容或描述"
            },
            "reminder_time": {
                "type": "string",
                "description": "提醒时间，格式：YYYY-MM-DD HH:MM:SS"
            },
            "repeat_type": {
                "type": "string",
                "description": "重复类型",
                "enum": ["none", "daily", "weekly", "monthly", "yearly"],
                "default": "none"
            }
        },
        "required": ["title", "content", "reminder_time"]
    },
    category="scheduler",
    tags={"task", "reminder", "schedule", "todo"}
)
async def create_task(
    title: str,
    content: str,
    reminder_time: str,
    repeat_type: str = "none"
) -> Dict[str, Any]:
    """
    创建任务
    
    Args:
        title: 任务标题
        content: 任务内容
        reminder_time: 提醒时间
        repeat_type: 重复类型
        
    Returns:
        创建结果
    """
    try:
        logger.info(f"创建任务: {title}")
        
        scheduler = _get_task_scheduler()
        
        # 创建任务
        task = scheduler.create_task(
            title=title,
            content=content,
            reminder_time=reminder_time,
            repeat_type=repeat_type
        )
        
        if task:
            logger.info(f"任务创建成功: {task.get('id')}")
            return {
                "success": True,
                "message": "任务创建成功",
                "task": {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "content": task.get("content"),
                    "reminder_time": task.get("reminder_time"),
                    "repeat_type": task.get("repeat_type")
                }
            }
        else:
            return {
                "success": False,
                "message": "任务创建失败"
            }
            
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return {
            "success": False,
            "message": f"创建任务失败: {str(e)}"
        }


@mcp_tool(
    name="get_tasks",
    description="获取所有定时任务列表",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "任务状态筛选",
                "enum": ["pending", "completed", "all"],
                "default": "all"
            }
        }
    },
    category="scheduler",
    tags={"task", "list", "query"}
)
async def get_tasks(status: str = "all") -> Dict[str, Any]:
    """
    获取任务列表
    
    Args:
        status: 状态筛选
        
    Returns:
        任务列表
    """
    try:
        scheduler = _get_task_scheduler()
        
        # 获取所有任务
        all_tasks = scheduler.get_all_tasks()
        
        # 按状态筛选
        if status != "all":
            all_tasks = [t for t in all_tasks if t.get("status") == status]
            
        formatted_tasks = []
        for task in all_tasks:
            formatted_tasks.append({
                "id": task.get("id"),
                "title": task.get("title"),
                "content": task.get("content"),
                "reminder_time": task.get("reminder_time"),
                "repeat_type": task.get("repeat_type"),
                "status": task.get("status"),
                "created_at": task.get("created_at")
            })
            
        return {
            "success": True,
            "count": len(formatted_tasks),
            "tasks": formatted_tasks
        }
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return {
            "success": False,
            "message": f"获取任务列表失败: {str(e)}"
        }


@mcp_tool(
    name="delete_task",
    description="删除指定的定时任务",
    parameters={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            }
        },
        "required": ["task_id"]
    },
    category="scheduler",
    tags={"task", "delete", "remove"}
)
async def delete_task(task_id: str) -> Dict[str, Any]:
    """
    删除任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        删除结果
    """
    try:
        logger.info(f"删除任务: {task_id}")
        
        scheduler = _get_task_scheduler()
        
        # 删除任务
        result = scheduler.delete_task(task_id)
        
        if result:
            logger.info("任务删除成功")
            return {
                "success": True,
                "message": "任务已删除"
            }
        else:
            return {
                "success": False,
                "message": "任务删除失败或任务不存在"
            }
            
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return {
            "success": False,
            "message": f"删除任务失败: {str(e)}"
        }
