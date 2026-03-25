"""
MCP 工具初始化模块

负责注册所有 MCP 工具到 MCP 工具注册中心。
"""

import logging
import os
from src.core.mcp_tool_registry import mcp_registry
from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp
from src.skills.mcp_skills.device_mcp_adapter import device_mcp_adapter
from src.skills.search_skills.web_search import WebSearchSkill

# 创建WebSearchSkill实例
api_key = os.getenv('QINIU_AI_API_KEY') or os.getenv('QINIU_ACCESS_KEY')
web_search = WebSearchSkill(api_key)

logger = logging.getLogger(__name__)


def register_all_mcp_tools():
    """
    注册所有 MCP 工具到注册中心
    
    执行流程：
    1. 注册文件操作工具
    2. 注册设备控制工具
    3. 注册其他工具
    """
    logger.info("开始注册 MCP 工具...")
    
    # 注册文件操作工具
    _register_file_operations_tools()
    
    # 注册设备控制工具
    _register_device_control_tools()
    
    # 注册其他工具
    _register_other_tools()
    
    logger.info(f"MCP 工具注册完成，共注册 {len(mcp_registry.get_tool_names())} 个工具")


def _register_file_operations_tools():
    """注册文件操作工具"""
    logger.info("注册文件操作工具...")
    
    # 注册读取文件工具
    mcp_registry.register(
        name="read_file",
        description="读取指定文件的内容",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["file_path"]
        },
        category="file_operations",
        tags={"file", "read"}
    )(file_operations_mcp.read_file)
    
    # 注册创建文件工具
    mcp_registry.register(
        name="create_file",
        description="创建新文件",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "文件内容"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "是否覆盖已存在的文件",
                    "default": False
                }
            },
            "required": ["file_path", "content"]
        },
        category="file_operations",
        tags={"file", "create"}
    )(file_operations_mcp.create_file)
    
    # 注册搜索文件工具
    mcp_registry.register(
        name="search_files",
        description="搜索文件",
        parameters={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "搜索目录"
                },
                "filename_pattern": {
                    "type": "string",
                    "description": "文件名模式（支持通配符）"
                },
                "file_extension": {
                    "type": "string",
                    "description": "文件扩展名"
                },
                "content_keyword": {
                    "type": "string",
                    "description": "内容关键词"
                }
            },
            "required": ["directory"]
        },
        category="file_operations",
        tags={"file", "search"}
    )(file_operations_mcp.search_files)
    
    # 注册改写文件工具
    mcp_registry.register(
        name="rewrite_file",
        description="改写文件内容",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "new_content": {
                    "type": "string",
                    "description": "新内容"
                },
                "start_line": {
                    "type": "integer",
                    "description": "开始行（从1开始）"
                },
                "end_line": {
                    "type": "integer",
                    "description": "结束行（从1开始）"
                }
            },
            "required": ["file_path", "new_content"]
        },
        category="file_operations",
        tags={"file", "rewrite"}
    )(file_operations_mcp.rewrite_file)
    
    # 注册删除文件工具
    mcp_registry.register(
        name="delete_file",
        description="删除文件",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["file_path"]
        },
        category="file_operations",
        tags={"file", "delete"}
    )(file_operations_mcp.delete_file)
    
    logger.info("文件操作工具注册完成")


def _register_device_control_tools():
    """注册设备控制工具"""
    logger.info("注册设备控制工具...")
    
    # 注册获取设备列表工具
    mcp_registry.register(
        name="get_device_list",
        description="获取所有已注册设备列表",
        parameters={
            "type": "object",
            "properties": {}
        },
        category="device_control",
        tags={"device", "list"}
    )(device_mcp_adapter.get_all_devices)
    
    # 注册获取设备状态工具
    mcp_registry.register(
        name="get_device_status",
        description="获取指定设备的状态",
        parameters={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "设备ID"
                }
            },
            "required": ["device_id"]
        },
        category="device_control",
        tags={"device", "status"}
    )(device_mcp_adapter.get_device_status)
    
    # 注册执行设备命令工具
    mcp_registry.register(
        name="execute_device_command",
        description="执行设备命令",
        parameters={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "设备ID"
                },
                "command": {
                    "type": "string",
                    "description": "命令名称"
                },
                "params": {
                    "type": "object",
                    "description": "命令参数"
                }
            },
            "required": ["device_id", "command"]
        },
        category="device_control",
        tags={"device", "command"}
    )(device_mcp_adapter.execute_command)
    
    # 注册注册设备工具
    mcp_registry.register(
        name="register_device",
        description="注册新设备",
        parameters={
            "type": "object",
            "properties": {
                "device_type": {
                    "type": "string",
                    "description": "设备类型（lamp, air_conditioner, curtain）"
                },
                "device_id": {
                    "type": "string",
                    "description": "设备ID"
                },
                "device_name": {
                    "type": "string",
                    "description": "设备名称"
                }
            },
            "required": ["device_type", "device_id"]
        },
        category="device_control",
        tags={"device", "register"}
    )(device_mcp_adapter.register_device)
    
    # 注册注销设备工具
    mcp_registry.register(
        name="unregister_device",
        description="注销设备",
        parameters={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "设备ID"
                }
            },
            "required": ["device_id"]
        },
        category="device_control",
        tags={"device", "unregister"}
    )(device_mcp_adapter.unregister_device)
    
    logger.info("设备控制工具注册完成")


def _register_other_tools():
    """注册其他工具"""
    logger.info("注册其他工具...")
    
    # 注册搜索工具
    # 创建一个包装函数，确保它是一个协程函数
    async def search_wrapper(**kwargs):
        return await web_search.async_search(**kwargs)
    
    mcp_registry.register(
        name="web_search",
        description="全网搜索信息",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "search_type": {
                    "type": "string",
                    "description": "搜索类型（web, video, image）",
                    "default": "web"
                },
                "time_filter": {
                    "type": "string",
                    "description": "时间过滤（week, month, year, semiyear）"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 20
                }
            },
            "required": ["query"]
        },
        category="search",
        tags={"search", "web"}
    )(search_wrapper)
    
    logger.info("其他工具注册完成")


# 在模块导入时自动注册所有工具
register_all_mcp_tools()
