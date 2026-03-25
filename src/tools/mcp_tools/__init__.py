"""
MCP 工具模块

提供所有MCP工具的自动注册和初始化功能。
"""

import logging
from src.core.mcp_tool_registry import mcp_registry
from src.core.function_calling_engine import FunctionCallingEngine

logger = logging.getLogger(__name__)


def register_all_tools():
    """
    注册所有MCP工具
    
    自动导入并注册所有工具模块中的工具。
    """
    logger.info("开始注册MCP工具...")
    
    # 导入设备控制工具
    try:
        from . import device_control_tool
        logger.info("设备控制工具模块已加载")
    except Exception as e:
        logger.error(f"加载设备控制工具失败: {e}")
        
    # 导入网络搜索工具
    try:
        from . import web_search_tool
        logger.info("网络搜索工具模块已加载")
    except Exception as e:
        logger.error(f"加载网络搜索工具失败: {e}")
        
    # 导入记忆管理工具
    try:
        from . import memory_tool
        logger.info("记忆管理工具模块已加载")
    except Exception as e:
        logger.error(f"加载记忆管理工具失败: {e}")
        
    # 导入文件操作工具
    try:
        from . import file_operations_tool
        logger.info("文件操作工具模块已加载")
    except Exception as e:
        logger.error(f"加载文件操作工具失败: {e}")
        
    # 导入定时任务工具
    try:
        from . import scheduler_tool
        logger.info("定时任务工具模块已加载")
    except Exception as e:
        logger.error(f"加载定时任务工具失败: {e}")
        
    # 导入备忘录工具
    try:
        from . import memo_tool
        logger.info("备忘录工具模块已加载")
    except Exception as e:
        logger.error(f"加载备忘录工具失败: {e}")
        
    # 统计注册的工具
    tool_names = mcp_registry.get_tool_names()
    logger.info(f"MCP工具注册完成，共 {len(tool_names)} 个工具: {', '.join(tool_names)}")
    
    return len(tool_names)


def create_function_calling_engine(llm_client) -> FunctionCallingEngine:
    """
    创建Function Calling引擎并注册所有工具
    
    Args:
        llm_client: LLM客户端实例
        
    Returns:
        FunctionCallingEngine实例
    """
    engine = FunctionCallingEngine(llm_client)
    
    # 注册所有MCP工具到引擎
    for tool_name in mcp_registry.get_tool_names():
        tool = mcp_registry.get_tool(tool_name)
        if tool:
            engine.register_tool(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                handler=tool.handler
            )
            
    logger.info(f"Function Calling引擎已创建，注册了 {len(engine.get_registered_tools())} 个工具")
    
    return engine


# 便捷函数：获取所有工具定义（用于Function Calling）
def get_all_tool_definitions():
    """获取所有工具定义（OpenAI格式）"""
    return mcp_registry.get_tool_definitions()


# 便捷函数：执行工具
def execute_tool(tool_name: str, **kwargs):
    """执行指定工具"""
    return mcp_registry.execute_tool(tool_name, **kwargs)


# 模块加载时自动注册工具
register_all_tools()
