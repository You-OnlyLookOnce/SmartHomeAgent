from typing import Dict, List, Optional, Callable, Any
import asyncio
import subprocess
import os
import json

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
        
        # 注册浏览器工具
        self.register_tool(
            "browser_use",
            "控制浏览器，参数：action (操作类型), url (网页URL), params (其他参数)",
            self._browser_use
        )
        
        # 注册命令行工具
        self.register_tool(
            "execute_shell_command",
            "执行命令行指令，参数：command (要执行的命令), timeout (超时时间)",
            self._execute_shell_command
        )
        
        # 注册文件读取工具
        self.register_tool(
            "read_file",
            "读取文本文件，参数：file_path (文件路径)",
            self._read_file
        )
        
        # 注册文件写入工具
        self.register_tool(
            "write_file",
            "写入/创建文本文件，参数：file_path (文件路径), content (文件内容)",
            self._write_file
        )
        
        # 注册记忆搜索工具
        self.register_tool(
            "memory_search",
            "语义搜索记忆，参数：query (搜索查询), max_results (最大返回结果数)",
            self._memory_search
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
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义，用于LLM工具调用"""
        tool_definitions = []
        for tool_name, tool in self.tools.items():
            # 简化版工具定义
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            tool_definitions.append(tool_def)
        return tool_definitions
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found"
            }
        return await tool.execute(**kwargs)
    
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
    
    async def _browser_use(self, action: str, url: str, params: Dict = None) -> Dict[str, Any]:
        """控制浏览器"""
        # 模拟浏览器操作
        return {
            "action": action,
            "url": url,
            "params": params,
            "message": f"已执行{action}操作，访问{url}"
        }
    
    async def _execute_shell_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """执行命令行指令"""
        try:
            # 执行命令
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "command": command,
                "error": str(e)
            }
    
    async def _read_file(self, file_path: str) -> Dict[str, Any]:
        """读取文本文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "file_path": file_path,
                "content": content
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入/创建文本文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "file_path": file_path,
                "message": "文件写入成功"
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _memory_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """语义搜索记忆"""
        # 模拟记忆搜索
        return {
            "query": query,
            "max_results": max_results,
            "results": [
                {
                    "content": "这是一条模拟的记忆结果",
                    "score": 0.95
                },
                {
                    "content": "这是另一条模拟的记忆结果",
                    "score": 0.88
                }
            ]
        }

