"""
MCP 工具注册中心

统一管理所有MCP工具的注册、发现和调用。
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
import logging
import importlib
import inspect

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    category: str = "general"
    tags: Set[str] = field(default_factory=set)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "tags": list(self.tags),
            "enabled": self.enabled
        }
        
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class MCPToolRegistry:
    """
    MCP工具注册中心
    
    提供统一的工具注册、发现和管理功能。
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.tools: Dict[str, MCPTool] = {}
        self.categories: Dict[str, List[str]] = {}
        self._initialized = True
        logger.info("MCP工具注册中心初始化完成")
        
    def register(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        category: str = "general",
        tags: Optional[Set[str]] = None,
        enabled: bool = True
    ) -> Callable:
        """
        注册工具的装饰器
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema格式）
            category: 工具类别
            tags: 工具标签
            enabled: 是否启用
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            # 如果没有提供参数定义，尝试从函数签名推断
            if parameters is None:
                params = self._infer_parameters_from_function(func)
            else:
                params = parameters
                
            tool = MCPTool(
                name=name,
                description=description,
                parameters=params,
                handler=func,
                category=category,
                tags=tags or set(),
                enabled=enabled
            )
            
            self._register_tool(tool)
            return func
            
        return decorator
        
    def register_tool(self, tool: MCPTool) -> None:
        """
        直接注册工具对象
        
        Args:
            tool: MCP工具对象
        """
        self._register_tool(tool)
        
    def _register_tool(self, tool: MCPTool) -> None:
        """
        内部注册工具
        
        Args:
            tool: MCP工具对象
        """
        # 检查名称冲突
        if tool.name in self.tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
            
        self.tools[tool.name] = tool
        
        # 更新类别索引
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        if tool.name not in self.categories[tool.category]:
            self.categories[tool.category].append(tool.name)
            
        logger.info(f"工具 {tool.name} 注册成功（类别: {tool.category}）")
        
    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        if name not in self.tools:
            return False
            
        tool = self.tools[name]
        
        # 从类别索引中移除
        if tool.category in self.categories:
            if name in self.categories[tool.category]:
                self.categories[tool.category].remove(name)
                
        # 从工具字典中移除
        del self.tools[name]
        
        logger.info(f"工具 {name} 已注销")
        return True
        
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            MCP工具对象，如果不存在则返回None
        """
        return self.tools.get(name)
        
    def get_tools_by_category(self, category: str) -> List[MCPTool]:
        """
        获取指定类别的所有工具
        
        Args:
            category: 工具类别
            
        Returns:
            工具列表
        """
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
        
    def get_tools_by_tag(self, tag: str) -> List[MCPTool]:
        """
        获取指定标签的所有工具
        
        Args:
            tag: 工具标签
            
        Returns:
            工具列表
        """
        return [tool for tool in self.tools.values() if tag in tool.tags]
        
    def get_all_tools(self, enabled_only: bool = True) -> List[MCPTool]:
        """
        获取所有工具
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            工具列表
        """
        if enabled_only:
            return [tool for tool in self.tools.values() if tool.enabled]
        return list(self.tools.values())
        
    def get_tool_definitions(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        获取所有工具定义（OpenAI格式）
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            工具定义列表
        """
        tools = self.get_all_tools(enabled_only)
        return [tool.to_openai_format() for tool in tools]
        
    def get_tool_names(self, enabled_only: bool = True) -> List[str]:
        """
        获取所有工具名称
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            工具名称列表
        """
        if enabled_only:
            return [name for name, tool in self.tools.items() if tool.enabled]
        return list(self.tools.keys())
        
    def get_categories(self) -> List[str]:
        """
        获取所有工具类别
        
        Returns:
            类别列表
        """
        return list(self.categories.keys())
        
    def enable_tool(self, name: str) -> bool:
        """
        启用工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功启用
        """
        if name in self.tools:
            self.tools[name].enabled = True
            logger.info(f"工具 {name} 已启用")
            return True
        return False
        
    def disable_tool(self, name: str) -> bool:
        """
        禁用工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功禁用
        """
        if name in self.tools:
            self.tools[name].enabled = False
            logger.info(f"工具 {name} 已禁用")
            return True
        return False
        
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 工具不存在
            RuntimeError: 工具执行失败
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 {name} 不存在")
            
        if not tool.enabled:
            raise RuntimeError(f"工具 {name} 已被禁用")
            
        try:
            logger.info(f"执行工具 {name}，参数: {kwargs}")
            
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**kwargs)
            else:
                result = tool.handler(**kwargs)
                
            logger.info(f"工具 {name} 执行成功")
            return result
            
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}")
            raise RuntimeError(f"工具执行失败: {e}")
            
    def clear(self) -> None:
        """清空所有工具"""
        self.tools.clear()
        self.categories.clear()
        logger.info("所有工具已清空")
        
    def to_json(self) -> str:
        """
        导出为JSON字符串
        
        Returns:
            JSON字符串
        """
        data = {
            "tools": [tool.to_dict() for tool in self.tools.values()],
            "categories": self.categories
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
        
    def _infer_parameters_from_function(self, func: Callable) -> Dict[str, Any]:
        """
        从函数签名推断参数定义
        
        Args:
            func: 函数对象
            
        Returns:
            参数定义（JSON Schema格式）
        """
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # 跳过self和cls
            if param_name in ('self', 'cls'):
                continue
                
            param_info = {"type": "string", "description": f"参数 {param_name}"}
            
            # 根据默认值判断类型
            if param.default is not inspect.Parameter.empty:
                if isinstance(param.default, bool):
                    param_info["type"] = "boolean"
                elif isinstance(param.default, int):
                    param_info["type"] = "integer"
                elif isinstance(param.default, float):
                    param_info["type"] = "number"
                elif isinstance(param.default, (list, tuple)):
                    param_info["type"] = "array"
                elif isinstance(param.default, dict):
                    param_info["type"] = "object"
            else:
                required.append(param_name)
                
            properties[param_name] = param_info
            
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
    def load_tools_from_module(self, module_path: str) -> int:
        """
        从模块加载工具
        
        Args:
            module_path: 模块路径（如 'tools.device_tools'）
            
        Returns:
            加载的工具数量
        """
        try:
            module = importlib.import_module(module_path)
            
            count = 0
            for name in dir(module):
                obj = getattr(module, name)
                if hasattr(obj, '_mcp_tool'):
                    tool_info = obj._mcp_tool
                    tool = MCPTool(
                        name=tool_info['name'],
                        description=tool_info['description'],
                        parameters=tool_info.get('parameters', {}),
                        handler=obj,
                        category=tool_info.get('category', 'general'),
                        tags=set(tool_info.get('tags', [])),
                        enabled=tool_info.get('enabled', True)
                    )
                    self._register_tool(tool)
                    count += 1
                    
            logger.info(f"从模块 {module_path} 加载了 {count} 个工具")
            return count
            
        except Exception as e:
            logger.error(f"从模块 {module_path} 加载工具失败: {e}")
            return 0


# 全局注册中心实例
mcp_registry = MCPToolRegistry()


def mcp_tool(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None,
    category: str = "general",
    tags: Optional[Set[str]] = None,
    enabled: bool = True
):
    """
    MCP工具装饰器（便捷函数）
    
    使用示例：
        @mcp_tool(
            name="get_weather",
            description="获取指定城市的天气信息",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            },
            category="weather",
            tags={"weather", "info"}
        )
        async def get_weather(city: str) -> str:
            # 实现代码
            pass
    """
    return mcp_registry.register(
        name=name,
        description=description,
        parameters=parameters,
        category=category,
        tags=tags,
        enabled=enabled
    )
