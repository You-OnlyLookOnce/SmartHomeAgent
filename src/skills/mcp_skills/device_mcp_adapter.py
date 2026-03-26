"""
设备MCP适配器模块 - 基于MCP协议整合所有设备API

功能：
- 创建设备数据模型
- 实现状态同步机制
- 指令响应处理
- 继承MCPBase类
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.core.unified_mcp_protocol import MCPBase, UnifiedMCPProtocol
from src.core.notification_service import notification_service
from src.skills.device_skills.lamp_api import LampAPI, LampState
from src.skills.device_skills.ac_api import AirConditionerAPI, ACState
from src.skills.device_skills.curtain_api import CurtainAPI, CurtainState

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """设备类型枚举"""
    LAMP = "lamp"                      # 台灯
    AIR_CONDITIONER = "air_conditioner"  # 空调
    CURTAIN = "curtain"                # 窗帘


@dataclass
class DeviceModel:
    """
    设备数据模型

    属性：
    - device_id: 设备唯一标识
    - device_name: 设备名称
    - device_type: 设备类型
    - current_state: 当前状态字典
    - supported_functions: 支持的功能列表
    - created_at: 创建时间
    - last_updated: 最后更新时间
    """
    device_id: str
    device_name: str
    device_type: DeviceType
    current_state: Dict[str, Any] = field(default_factory=dict)
    supported_functions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type.value,
            "current_state": self.current_state,
            "supported_functions": self.supported_functions,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceModel':
        """从字典创建实例"""
        return cls(
            device_id=data["device_id"],
            device_name=data["device_name"],
            device_type=DeviceType(data["device_type"]),
            current_state=data.get("current_state", {}),
            supported_functions=data.get("supported_functions", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
        )


class DeviceMCPAdapter(MCPBase):
    """
    设备MCP适配器类

    基于MCP协议整合所有设备API，提供统一的设备管理接口。
    支持台灯、空调、窗帘等设备的控制和管理。

    执行流程：
    1. 接收MCP请求
    2. 解析设备类型和操作
    3. 调用对应的设备API
    4. 返回统一格式的响应
    """

    def __init__(self):
        """初始化设备MCP适配器"""
        super().__init__()
        # 设备实例字典 {device_id: device_instance}
        self._devices: Dict[str, Any] = {}
        # 设备模型字典 {device_id: DeviceModel}
        self._device_models: Dict[str, DeviceModel] = {}
        # 状态变更回调函数列表
        self._state_change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        # 锁用于线程安全
        self._lock = asyncio.Lock()
        # 状态缓存 {device_id: {state, timestamp}}
        self._status_cache: Dict[str, Dict[str, Any]] = {}
        # 订阅管理 {device_id: [subscriber_callback]}
        self._subscriptions: Dict[str, List[Callable[[str, Dict[str, Any]], None]]] = {}
        logger.info("设备MCP适配器初始化完成")

    async def register_device(self, device_type: str, device_id: str, device_name: str) -> Dict[str, Any]:
        """
        注册新设备

        执行流程：
        1. 验证设备类型
        2. 创建设备API实例
        3. 创建设备模型
        4. 保存到设备字典

        Args:
            device_type: 设备类型 ("lamp", "air_conditioner", "curtain")
            device_id: 设备唯一标识
            device_name: 设备名称

        Returns:
            操作结果字典
        """
        async with self._lock:
            # 检查设备ID是否已存在
            if device_id in self._devices:
                return {
                    "success": False,
                    "code": 400,
                    "message": f"设备ID '{device_id}' 已存在",
                    "data": None
                }

            try:
                # 创建设备实例
                device_type_enum = DeviceType(device_type)

                if device_type_enum == DeviceType.LAMP:
                    device = LampAPI(device_id=device_id, device_name=device_name)
                elif device_type_enum == DeviceType.AIR_CONDITIONER:
                    device = AirConditionerAPI(device_id=device_id, device_name=device_name)
                elif device_type_enum == DeviceType.CURTAIN:
                    device = CurtainAPI(device_id=device_id, device_name=device_name)
                else:
                    return {
                        "success": False,
                        "code": 400,
                        "message": f"不支持的设备类型: {device_type}",
                        "data": None
                    }

                # 创建设备模型
                device_model = DeviceModel(
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type_enum,
                    supported_functions=device.get_supported_functions().get("functions", [])
                )

                # 保存设备
                self._devices[device_id] = device
                self._device_models[device_id] = device_model

                logger.info(f"设备注册成功 - 类型: {device_type}, ID: {device_id}, 名称: {device_name}")

                return {
                    "success": True,
                    "code": 200,
                    "message": "设备注册成功",
                    "data": device_model.to_dict()
                }

            except ValueError as e:
                valid_types = [e.value for e in DeviceType]
                return {
                    "success": False,
                    "code": 400,
                    "message": f"无效的设备类型 '{device_type}'，有效值: {valid_types}",
                    "data": None
                }
            except Exception as e:
                logger.error(f"设备注册失败: {str(e)}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"设备注册失败: {str(e)}",
                    "data": None
                }

    async def unregister_device(self, device_id: str) -> Dict[str, Any]:
        """
        注销设备

        Args:
            device_id: 设备唯一标识

        Returns:
            操作结果字典
        """
        async with self._lock:
            if device_id not in self._devices:
                return {
                    "success": False,
                    "code": 404,
                    "message": f"设备 '{device_id}' 不存在",
                    "data": None
                }

            # 获取设备信息用于返回
            device_model = self._device_models[device_id]

            # 删除设备
            del self._devices[device_id]
            del self._device_models[device_id]

            logger.info(f"设备已注销 - ID: {device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "设备注销成功",
                "data": device_model.to_dict()
            }

    async def get_device(self, device_id: str) -> Optional[Any]:
        """
        获取设备实例

        Args:
            device_id: 设备唯一标识

        Returns:
            设备实例或None
        """
        return self._devices.get(device_id)

    async def get_device_model(self, device_id: str) -> Optional[DeviceModel]:
        """
        获取设备模型

        Args:
            device_id: 设备唯一标识

        Returns:
            设备模型或None
        """
        return self._device_models.get(device_id)

    async def get_all_devices(self) -> List[DeviceModel]:
        """
        获取所有已注册设备

        Returns:
            设备模型列表
        """
        return list(self._device_models.values())

    async def execute_command(self, device_id: str, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行设备命令

        执行流程：
        1. 查找设备
        2. 验证命令是否支持
        3. 调用设备API执行命令
        4. 更新设备模型状态
        5. 触发状态变更回调
        6. 返回执行结果

        Args:
            device_id: 设备唯一标识
            command: 命令名称
            params: 命令参数

        Returns:
            操作结果字典
        """
        params = params or {}

        async with self._lock:
            # 检查设备是否存在
            if device_id not in self._devices:
                return {
                    "success": False,
                    "code": 404,
                    "message": f"设备 '{device_id}' 不存在",
                    "data": None
                }

            device = self._devices[device_id]
            device_model = self._device_models[device_id]

        try:
            # 执行命令
            if hasattr(device, command):
                method = getattr(device, command)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**params)
                else:
                    result = method(**params)
            else:
                return {
                    "success": False,
                    "code": 400,
                    "message": f"设备不支持命令 '{command}'",
                    "data": None
                }

            # 更新设备模型状态
            if result.get("success") and result.get("data"):
                device_model.current_state = result["data"]
                device_model.last_updated = datetime.now()

                # 触发状态变更回调
                await self._notify_state_change(device_id, result["data"])

            return result

        except Exception as e:
            logger.error(f"执行命令失败 - 设备: {device_id}, 命令: {command}, 错误: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"执行命令失败: {str(e)}",
                "data": None
            }

    async def get_device_status(self, device_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取设备状态

        Args:
            device_id: 设备唯一标识
            use_cache: 是否使用缓存

        Returns:
            设备状态字典
        """
        if use_cache:
            # 尝试从缓存获取
            cached_result = await self.get_cached_status(device_id)
            if cached_result.get("success"):
                return cached_result
        
        # 缓存不存在或禁用缓存，获取最新状态
        result = await self.execute_command(device_id, "get_status")
        if result.get("success") and result.get("data"):
            # 更新缓存
            await self._update_status_cache(device_id, result["data"])
        return result

    async def sync_device_state(self, device_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步设备状态

        Args:
            device_id: 设备唯一标识
            state: 状态字典

        Returns:
            操作结果字典
        """
        return await self.execute_command(device_id, "set_state", {"state_dict": state})

    async def _notify_state_change(self, device_id: str, state: Dict[str, Any]) -> None:
        """
        通知状态变更

        Args:
            device_id: 设备唯一标识
            state: 新状态
        """
        # 获取设备模型
        device_model = self._device_models.get(device_id)
        if not device_model:
            return

        # 获取之前的状态
        previous_state = device_model.current_state.copy()

        # 更新状态缓存
        await self._update_status_cache(device_id, state)

        # 通知所有状态变更回调
        for callback in self._state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(device_id, state)
                else:
                    callback(device_id, state)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {str(e)}")

        # 通知设备订阅者
        if device_id in self._subscriptions:
            for subscriber_callback in self._subscriptions[device_id]:
                try:
                    if asyncio.iscoroutinefunction(subscriber_callback):
                        await subscriber_callback(device_id, state)
                    else:
                        subscriber_callback(device_id, state)
                except Exception as e:
                    logger.error(f"设备订阅回调执行失败: {str(e)}")

        # 发送设备状态变更通知给智能体
        try:
            await notification_service.create_device_status_notification(
                device_id=device_id,
                device_name=device_model.device_name,
                device_type=device_model.device_type.value,
                previous_state=previous_state,
                current_state=state,
                change_type="status"
            )
            logger.debug(f"设备状态变更通知已发送 - 设备: {device_id}")
        except Exception as e:
            logger.error(f"发送设备状态变更通知失败: {str(e)}")

    def register_state_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注册状态变更回调函数

        Args:
            callback: 回调函数，接收device_id和state两个参数
        """
        self._state_change_callbacks.append(callback)
        logger.info(f"状态变更回调已注册，当前回调数量: {len(self._state_change_callbacks)}")

    def unregister_state_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注销状态变更回调函数

        Args:
            callback: 回调函数
        """
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)
            logger.info(f"状态变更回调已注销，当前回调数量: {len(self._state_change_callbacks)}")

    async def subscribe_to_device(self, device_id: str, callback: Callable[[str, Dict[str, Any]], None]) -> Dict[str, Any]:
        """
        订阅设备状态变更

        Args:
            device_id: 设备唯一标识
            callback: 状态变更回调函数

        Returns:
            操作结果字典
        """
        async with self._lock:
            if device_id not in self._devices:
                return {
                    "success": False,
                    "code": 404,
                    "message": f"设备 '{device_id}' 不存在",
                    "data": None
                }

            if device_id not in self._subscriptions:
                self._subscriptions[device_id] = []

            if callback not in self._subscriptions[device_id]:
                self._subscriptions[device_id].append(callback)
                logger.info(f"设备订阅成功 - 设备: {device_id}, 当前订阅数: {len(self._subscriptions[device_id])}")

            return {
                "success": True,
                "code": 200,
                "message": "设备订阅成功",
                "data": {
                    "device_id": device_id,
                    "subscription_count": len(self._subscriptions[device_id])
                }
            }

    async def unsubscribe_from_device(self, device_id: str, callback: Callable[[str, Dict[str, Any]], None]) -> Dict[str, Any]:
        """
        取消订阅设备状态变更

        Args:
            device_id: 设备唯一标识
            callback: 状态变更回调函数

        Returns:
            操作结果字典
        """
        async with self._lock:
            if device_id not in self._subscriptions:
                return {
                    "success": False,
                    "code": 404,
                    "message": f"设备 '{device_id}' 没有订阅",
                    "data": None
                }

            if callback in self._subscriptions[device_id]:
                self._subscriptions[device_id].remove(callback)
                logger.info(f"设备取消订阅成功 - 设备: {device_id}, 当前订阅数: {len(self._subscriptions[device_id])}")

                # 如果没有订阅者，清理订阅记录
                if len(self._subscriptions[device_id]) == 0:
                    del self._subscriptions[device_id]

            return {
                "success": True,
                "code": 200,
                "message": "设备取消订阅成功",
                "data": {
                    "device_id": device_id,
                    "subscription_count": len(self._subscriptions.get(device_id, []))
                }
            }

    async def get_cached_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取缓存的设备状态

        Args:
            device_id: 设备唯一标识

        Returns:
            设备状态字典
        """
        async with self._lock:
            if device_id not in self._status_cache:
                # 如果缓存不存在，获取最新状态
                status_result = await self.get_device_status(device_id)
                return status_result

            cached_data = self._status_cache[device_id]
            state = cached_data.get("state", {})
            timestamp = cached_data.get("timestamp")

            logger.info(f"从缓存获取设备状态 - 设备: {device_id}, 缓存时间: {timestamp}")

            return {
                "success": True,
                "code": 200,
                "message": "获取设备状态成功（来自缓存）",
                "data": state
            }

    async def clear_status_cache(self, device_id: str = None) -> Dict[str, Any]:
        """
        清除设备状态缓存

        Args:
            device_id: 设备唯一标识（可选，不提供则清除所有缓存）

        Returns:
            操作结果字典
        """
        async with self._lock:
            if device_id:
                if device_id in self._status_cache:
                    del self._status_cache[device_id]
                    logger.info(f"设备状态缓存已清除 - 设备: {device_id}")
                    return {
                        "success": True,
                        "code": 200,
                        "message": f"设备 '{device_id}' 状态缓存已清除",
                        "data": None
                    }
                else:
                    return {
                        "success": False,
                        "code": 404,
                        "message": f"设备 '{device_id}' 没有缓存",
                        "data": None
                    }
            else:
                # 清除所有缓存
                cache_count = len(self._status_cache)
                self._status_cache.clear()
                logger.info(f"所有设备状态缓存已清除 - 清除数量: {cache_count}")
                return {
                    "success": True,
                    "code": 200,
                    "message": f"所有设备状态缓存已清除（共 {cache_count} 个）",
                    "data": None
                }

    async def _update_status_cache(self, device_id: str, state: Dict[str, Any]) -> None:
        """
        更新设备状态缓存

        Args:
            device_id: 设备唯一标识
            state: 新状态
        """
        async with self._lock:
            self._status_cache[device_id] = {
                "state": state,
                "timestamp": datetime.now().isoformat()
            }
            logger.debug(f"设备状态缓存已更新 - 设备: {device_id}")

    # MCP协议处理方法

    async def handle_read(self, params: Dict[str, Any]) -> Any:
        """
        处理读取操作 - 获取设备状态或设备列表

        Args:
            params: 操作参数
                - device_id: 设备ID（可选，不提供则返回所有设备列表）

        Returns:
            设备状态或设备列表
        """
        device_id = params.get("device_id")

        if device_id:
            # 获取指定设备状态
            result = await self.get_device_status(device_id)
            if result.get("success"):
                return result["data"]
            else:
                return f"错误: {result.get('message')}"
        else:
            # 获取所有设备列表
            devices = await self.get_all_devices()
            return [device.to_dict() for device in devices]

    async def handle_create(self, params: Dict[str, Any]) -> Any:
        """
        处理创建操作 - 注册新设备

        Args:
            params: 操作参数
                - device_type: 设备类型
                - device_id: 设备ID
                - device_name: 设备名称

        Returns:
            创建结果
        """
        device_type = params.get("device_type")
        device_id = params.get("device_id")
        device_name = params.get("device_name")

        if not device_type or not device_id:
            return "错误: 缺少device_type或device_id参数"

        result = await self.register_device(device_type, device_id, device_name or device_id)
        if result.get("success"):
            return result["data"]
        else:
            return f"错误: {result.get('message')}"

    async def handle_update(self, params: Dict[str, Any]) -> Any:
        """
        处理更新操作 - 执行设备命令或同步状态

        Args:
            params: 操作参数
                - device_id: 设备ID（必需）
                - command: 命令名称（必需）
                - command_params: 命令参数（可选）

        Returns:
            执行结果
        """
        device_id = params.get("device_id")
        command = params.get("command")
        command_params = params.get("command_params", {})

        if not device_id:
            return "错误: 缺少device_id参数"

        if not command:
            return "错误: 缺少command参数"

        result = await self.execute_command(device_id, command, command_params)
        if result.get("success"):
            return result["data"]
        else:
            return f"错误: {result.get('message')}"

    async def handle_delete(self, params: Dict[str, Any]) -> Any:
        """
        处理删除操作 - 注销设备

        Args:
            params: 操作参数
                - device_id: 设备ID（必需）

        Returns:
            删除结果
        """
        device_id = params.get("device_id")

        if not device_id:
            return "错误: 缺少device_id参数"

        result = await self.unregister_device(device_id)
        if result.get("success"):
            return result["data"]
        else:
            return f"错误: {result.get('message')}"

    async def handle_search(self, params: Dict[str, Any]) -> Any:
        """
        处理搜索操作 - 搜索设备

        Args:
            params: 操作参数
                - device_type: 设备类型（可选，过滤条件）
                - keyword: 关键词（可选，用于搜索设备名称）

        Returns:
            符合条件的设备列表
        """
        device_type = params.get("device_type")
        keyword = params.get("keyword")

        devices = await self.get_all_devices()
        result = []

        for device in devices:
            # 按类型过滤
            if device_type and device.device_type.value != device_type:
                continue

            # 按关键词过滤
            if keyword and keyword.lower() not in device.device_name.lower():
                continue

            result.append(device.to_dict())

        return result

    async def handle_execute(self, params: Dict[str, Any]) -> Any:
        """
        处理执行操作 - 执行复杂的设备操作

        Args:
            params: 操作参数
                - action: 动作类型
                - 其他参数根据动作类型而定

        Returns:
            执行结果
        """
        action = params.get("action")

        if action == "register_device":
            return await self.handle_create(params)
        elif action == "unregister_device":
            return await self.handle_delete(params)
        elif action == "get_device_status":
            return await self.handle_read(params)
        elif action == "execute_command":
            return await self.handle_update(params)
        elif action == "list_devices":
            return await self.handle_read({})
        elif action == "sync_state":
            device_id = params.get("device_id")
            state = params.get("state", {})
            if not device_id:
                return "错误: 缺少device_id参数"
            result = await self.sync_device_state(device_id, state)
            if result.get("success"):
                return result["data"]
            else:
                return f"错误: {result.get('message')}"
        else:
            return f"错误: 不支持的动作类型 '{action}'"

    def get_device_types(self) -> List[Dict[str, str]]:
        """
        获取支持的设备类型列表

        Returns:
            设备类型列表
        """
        return [
            {"type": "lamp", "name": "台灯", "description": "智能台灯，支持亮度调节、色温切换、定时关机"},
            {"type": "air_conditioner", "name": "空调", "description": "智能空调，支持温度设置、模式切换、风速调节"},
            {"type": "curtain", "name": "窗帘", "description": "智能窗帘，支持位置调节、定时开关"},
        ]

    async def get_supported_commands(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备支持的命令列表

        Args:
            device_id: 设备ID

        Returns:
            支持的命令列表
        """
        device = await self.get_device(device_id)
        if not device:
            return {
                "success": False,
                "code": 404,
                "message": f"设备 '{device_id}' 不存在",
                "data": None
            }

        return {
            "success": True,
            "code": 200,
            "message": "获取成功",
            "data": device.get_supported_functions()
        }


# 创建设备MCP适配器实例
device_mcp_adapter = DeviceMCPAdapter()
