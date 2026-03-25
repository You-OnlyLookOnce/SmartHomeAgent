"""
文件操作 MCP 工具

提供文件读写、搜索等操作功能。
"""

import os
import json
from typing import Dict, Any, Optional, List
import logging
from src.core.mcp_tool_registry import mcp_tool

logger = logging.getLogger(__name__)


@mcp_tool(
    name="read_file",
    description="读取指定文件的内容",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径（相对路径或绝对路径）"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码",
                "default": "utf-8"
            }
        },
        "required": ["file_path"]
    },
    category="file",
    tags={"file", "read", "io"}
)
async def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    读取文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        文件内容
    """
    try:
        # 安全检查：限制文件访问范围
        allowed_dirs = ["data", "config", "logs", "memories"]
        is_allowed = any(d in file_path for d in allowed_dirs)
        
        if not is_allowed and not file_path.startswith("./"):
            return {
                "success": False,
                "message": "只能访问允许目录中的文件"
            }
        
        # 规范化路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"文件不存在: {file_path}"
            }
            
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }
        
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return {
            "success": False,
            "message": f"读取文件失败: {str(e)}"
        }


@mcp_tool(
    name="write_file",
    description="将内容写入指定文件",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径"
            },
            "content": {
                "type": "string",
                "description": "要写入的内容"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码",
                "default": "utf-8"
            },
            "append": {
                "type": "boolean",
                "description": "是否追加模式",
                "default": False
            }
        },
        "required": ["file_path", "content"]
    },
    category="file",
    tags={"file", "write", "io"}
)
async def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    append: bool = False
) -> Dict[str, Any]:
    """
    写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        append: 是否追加
        
    Returns:
        写入结果
    """
    try:
        # 安全检查
        allowed_dirs = ["data", "config", "logs", "memories"]
        is_allowed = any(d in file_path for d in allowed_dirs)
        
        if not is_allowed and not file_path.startswith("./"):
            return {
                "success": False,
                "message": "只能写入允许目录中的文件"
            }
        
        # 规范化路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
            
        return {
            "success": True,
            "file_path": file_path,
            "message": "文件写入成功"
        }
        
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return {
            "success": False,
            "message": f"写入文件失败: {str(e)}"
        }


@mcp_tool(
    name="search_files",
    description="在指定目录中搜索包含关键词的文件",
    parameters={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "搜索目录"
            },
            "keyword": {
                "type": "string",
                "description": "搜索关键词"
            },
            "file_extension": {
                "type": "string",
                "description": "文件扩展名筛选，如 .txt, .json",
                "default": ""
            }
        },
        "required": ["directory", "keyword"]
    },
    category="file",
    tags={"file", "search", "find"}
)
async def search_files(
    directory: str,
    keyword: str,
    file_extension: str = ""
) -> Dict[str, Any]:
    """
    搜索文件
    
    Args:
        directory: 搜索目录
        keyword: 搜索关键词
        file_extension: 文件扩展名筛选
        
    Returns:
        搜索结果
    """
    try:
        # 安全检查
        allowed_dirs = ["data", "config", "logs", "memories"]
        is_allowed = any(d in directory for d in allowed_dirs)
        
        if not is_allowed and not directory.startswith("./"):
            return {
                "success": False,
                "message": "只能搜索允许目录中的文件"
            }
        
        # 规范化路径
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)
            
        if not os.path.exists(directory):
            return {
                "success": False,
                "message": f"目录不存在: {directory}"
            }
            
        matching_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                # 扩展名筛选
                if file_extension and not file.endswith(file_extension):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if keyword in content:
                            # 找到关键词，记录上下文
                            index = content.find(keyword)
                            start = max(0, index - 50)
                            end = min(len(content), index + len(keyword) + 50)
                            context = content[start:end]
                            
                            matching_files.append({
                                "file_path": file_path,
                                "file_name": file,
                                "context": context
                            })
                except Exception:
                    # 忽略无法读取的文件
                    continue
                    
        return {
            "success": True,
            "directory": directory,
            "keyword": keyword,
            "count": len(matching_files),
            "files": matching_files
        }
        
    except Exception as e:
        logger.error(f"搜索文件失败: {e}")
        return {
            "success": False,
            "message": f"搜索文件失败: {str(e)}"
        }


@mcp_tool(
    name="list_directory",
    description="列出指定目录中的文件和子目录",
    parameters={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "目录路径"
            }
        },
        "required": ["directory"]
    },
    category="file",
    tags={"file", "list", "directory"}
)
async def list_directory(directory: str) -> Dict[str, Any]:
    """
    列出目录内容
    
    Args:
        directory: 目录路径
        
    Returns:
        目录内容
    """
    try:
        # 安全检查
        allowed_dirs = ["data", "config", "logs", "memories"]
        is_allowed = any(d in directory for d in allowed_dirs)
        
        if not is_allowed and not directory.startswith("./"):
            return {
                "success": False,
                "message": "只能访问允许目录"
            }
        
        # 规范化路径
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)
            
        if not os.path.exists(directory):
            return {
                "success": False,
                "message": f"目录不存在: {directory}"
            }
            
        items = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            items.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
            })
            
        return {
            "success": True,
            "directory": directory,
            "count": len(items),
            "items": items
        }
        
    except Exception as e:
        logger.error(f"列出目录失败: {e}")
        return {
            "success": False,
            "message": f"列出目录失败: {str(e)}"
        }
