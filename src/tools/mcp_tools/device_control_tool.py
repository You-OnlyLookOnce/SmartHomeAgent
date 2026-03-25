"""
设备控制 MCP 工具

提供智能家居设备控制功能。
"""

from typing import Dict, Any, Optional
import logging
from src.core.mcp_tool_registry import mcp_tool
from src.core.device_manager import device_manager

logger = logging.getLogger(__name__)


@mcp_tool(
    name="control_device",
    description="控制智能家居设备，如开关灯、调节空调温度、控制窗帘等",
    parameters={
        "type": "object",
        "properties": {
            "device_type": {
                "type": "string",
                "description": "设备类型，如 lamp（灯）、ac（空调）、curtain（窗帘）",
                "enum": ["lamp", "ac", "curtain", "fan", "heater"]
            },
            "device_name": {
                "type": "string",
                "description": "设备名称或位置，如 '客厅灯'、'卧室空调'"
            },
            "action": {
                "type": "string",
                "description": "操作类型",
                "enum": ["turn_on", "turn_off", "set_brightness", "set_temperature", "set_mode", "open", "close", "stop"]
            },
            "value": {
                "type": "number",
                "description": "参数值，如亮度值（0-100）、温度值（16-30）"
            },
            "mode": {
                "type": "string",
                "description": "模式，如制冷、制热、送风等",
                "enum": ["cool", "heat", "fan", "auto", "dry"]
            }
        },
        "required": ["device_type", "device_name", "action"]
    },
    category="device",
    tags={"device", "control", "smart_home"}
)
async def control_device(
    device_type: str,
    device_name: str,
    action: str,
    value: Optional[float] = None,
    mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    控制设备
    
    Args:
        device_type: 设备类型
        device_name: 设备名称
        action: 操作类型
        value: 参数值
        mode: 模式
        
    Returns:
        操作结果
    """
    try:
        logger.info(f"控制设备: {device_name} ({device_type}), 操作: {action}")
        
        # 查找或创建设备
        device_id = f"{device_type}_{device_name}"
        device = device_manager.get_device(device_id)
        
        if not device:
            # 自动创建设备
            device = device_manager.create_device(
                device_id=device_id,
                device_type=device_type,
                name=device_name
            )
            logger.info(f"自动创建设备: {device_name}")
        
        # 构建命令参数
        params = {}
        if value is not None:
            params["value"] = value
        if mode is not None:
            params["mode"] = mode
            
        # 执行命令
        result = device_manager.execute_command(device_id, action, params)
        
        if result.get("success"):
            logger.info(f"设备控制成功: {device_name}")
            return {
                "success": True,
                "message": f"{device_name} 操作成功",
                "device_state": result.get("state", {})
            }
        else:
            error_msg = result.get("message", "操作失败")
            logger.error(f"设备控制失败: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
            
    except Exception as e:
        logger.error(f"设备控制异常: {e}")
        return {
            "success": False,
            "message": f"设备控制失败: {str(e)}"
        }


@mcp_tool(
    name="get_device_status",
    description="获取智能家居设备的状态信息",
    parameters={
        "type": "object",
        "properties": {
            "device_type": {
                "type": "string",
                "description": "设备类型，如 lamp、ac、curtain",
                "enum": ["lamp", "ac", "curtain", "fan", "heater"]
            },
            "device_name": {
                "type": "string",
                "description": "设备名称或位置"
            }
        },
        "required": ["device_type", "device_name"]
    },
    category="device",
    tags={"device", "status", "query"}
)
async def get_device_status(device_type: str, device_name: str) -> Dict[str, Any]:
    """
    获取设备状态
    
    Args:
        device_type: 设备类型
        device_name: 设备名称
        
    Returns:
        设备状态
    """
    try:
        device_id = f"{device_type}_{device_name}"
        device = device_manager.get_device(device_id)
        
        if not device:
            return {
                "success": False,
                "message": f"设备 {device_name} 不存在"
            }
            
        state = device.get("state", {})
        
        return {
            "success": True,
            "device_name": device_name,
            "device_type": device_type,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"获取设备状态失败: {e}")
        return {
            "success": False,
            "message": f"获取状态失败: {str(e)}"
        }


@mcp_tool(
    name="list_devices",
    description="列出所有智能家居设备",
    parameters={
        "type": "object",
        "properties": {
            "device_type": {
                "type": "string",
                "description": "按类型筛选设备",
                "enum": ["lamp", "ac", "curtain", "fan", "heater", "all"]
            }
        }
    },
    category="device",
    tags={"device", "list", "query"}
)
async def list_devices(device_type: str = "all") -> Dict[str, Any]:
    """
    列出设备
    
    Args:
        device_type: 设备类型筛选
        
    Returns:
        设备列表
    """
    try:
        devices = device_manager.list_devices()
        
        if device_type != "all":
            devices = [d for d in devices if d.get("type") == device_type]
            
        return {
            "success": True,
            "count": len(devices),
            "devices": [
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "type": d.get("type"),
                    "state": d.get("state", {})
                }
                for d in devices
            ]
        }
        
    except Exception as e:
        logger.error(f"列出设备失败: {e}")
        return {
            "success": False,
            "message": f"获取设备列表失败: {str(e)}"
        }
