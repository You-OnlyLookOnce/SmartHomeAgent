from typing import Dict, List, Optional, Callable, Any
import asyncio

class Tool:
    """工具基类"""
    
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        try:
            result = await self.func(**kwargs)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 注册设备控制工具
        self.register_tool(
            "control_device",
            "控制设备，参数：device_id (设备ID), action (动作，如on/off), params (可选参数)",
            self._control_device
        )
        
        # 注册任务管理工具
        self.register_tool(
            "create_reminder",
            "创建提醒，参数：title (标题), time (时间), description (描述)",
            self._create_reminder
        )
        
        # 注册天气查询工具
        self.register_tool(
            "get_weather",
            "获取天气信息，参数：location (位置)",
            self._get_weather
        )
        
        # 注册时间查询工具
        self.register_tool(
            "get_time",
            "获取当前时间",
            self._get_time
        )
    
    def register_tool(self, name: str, description: str, func: Callable):
        """注册工具"""
        self.tools[name] = Tool(name, description, func)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
    
    async def _control_device(self, device_id: str, action: str, params: Dict = None) -> Dict[str, Any]:
        """控制设备"""
        return {
            "message": f"已{action}设备 {device_id}",
            "device_id": device_id,
            "action": action,
            "params": params
        }
    
    async def _create_reminder(self, title: str, time: str = None, description: str = None) -> Dict[str, Any]:
        """创建提醒"""
        return {
            "message": f"已创建提醒: {title}",
            "title": title,
            "time": time,
            "description": description
        }
    
    async def _get_weather(self, location: str) -> Dict[str, Any]:
        """获取天气信息"""
        # 模拟天气数据
        return {
            "location": location,
            "temperature": "25°C",
            "condition": "晴朗",
            "humidity": "60%",
            "wind": "微风"
        }
    
    async def _get_time(self) -> Dict[str, Any]:
        """获取当前时间"""
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "time": current_time
        }
