"""
台灯API模块 - 实现台灯的各项控制功能

功能：
- 亮度调节(0-100)
- 开关控制
- 定时关机
- 色温切换(正常/护眼模式)
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LampColorTemp(Enum):
    """台灯色温模式"""
    NORMAL = "normal"      # 正常模式 (5000K-6500K)
    EYE_PROTECTION = "eye_protection"  # 护眼模式 (3000K-4000K)


@dataclass
class LampState:
    """台灯状态数据类"""
    power: bool = False                    # 开关状态
    brightness: int = 50                   # 亮度 (0-100)
    color_temp: LampColorTemp = LampColorTemp.NORMAL  # 色温模式
    timer_off: Optional[datetime] = None   # 定时关机时间
    device_id: str = "lamp_default"        # 设备ID
    device_name: str = "台灯"               # 设备名称
    last_updated: datetime = field(default_factory=datetime.now)  # 最后更新时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "power": self.power,
            "brightness": self.brightness,
            "color_temp": self.color_temp.value,
            "timer_off": self.timer_off.isoformat() if self.timer_off else None,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LampState':
        """从字典创建实例"""
        timer_off = None
        if data.get("timer_off"):
            timer_off = datetime.fromisoformat(data["timer_off"])

        return cls(
            device_id=data.get("device_id", "lamp_default"),
            device_name=data.get("device_name", "台灯"),
            power=data.get("power", False),
            brightness=data.get("brightness", 50),
            color_temp=LampColorTemp(data.get("color_temp", "normal")),
            timer_off=timer_off,
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
        )


class LampAPI:
    """
    台灯API类

    提供台灯的完整控制接口，包括开关、亮度调节、色温切换、定时关机等功能。
    所有方法均为异步方法，支持并发操作。
    """

    # 亮度范围常量
    MIN_BRIGHTNESS = 0
    MAX_BRIGHTNESS = 100

    # 定时器任务字典 {device_id: asyncio.Task}
    _timer_tasks: Dict[str, asyncio.Task] = {}

    def __init__(self, device_id: str = "lamp_default", device_name: str = "台灯"):
        """
        初始化台灯API

        Args:
            device_id: 设备唯一标识
            device_name: 设备名称
        """
        self._device_id = device_id
        self._device_name = device_name
        self._state = LampState(device_id=device_id, device_name=device_name)
        self._lock = asyncio.Lock()
        logger.info(f"台灯API初始化完成 - 设备ID: {device_id}, 名称: {device_name}")

    @property
    def device_id(self) -> str:
        """获取设备ID"""
        return self._device_id

    @property
    def device_name(self) -> str:
        """获取设备名称"""
        return self._device_name

    @property
    def state(self) -> LampState:
        """获取当前状态"""
        return self._state

    async def get_status(self) -> Dict[str, Any]:
        """
        获取台灯当前状态

        Returns:
            包含设备状态的字典
        """
        async with self._lock:
            return {
                "success": True,
                "code": 200,
                "message": "获取状态成功",
                "data": self._state.to_dict()
            }

    async def turn_on(self) -> Dict[str, Any]:
        """
        打开台灯

        Returns:
            操作结果字典
        """
        async with self._lock:
            if self._state.power:
                return {
                    "success": True,
                    "code": 200,
                    "message": "台灯已经是开启状态",
                    "data": self._state.to_dict()
                }

            self._state.power = True
            self._state.last_updated = datetime.now()
            logger.info(f"台灯已开启 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "台灯已开启",
                "data": self._state.to_dict()
            }

    async def turn_off(self) -> Dict[str, Any]:
        """
        关闭台灯

        Returns:
            操作结果字典
        """
        async with self._lock:
            if not self._state.power:
                return {
                    "success": True,
                    "code": 200,
                    "message": "台灯已经是关闭状态",
                    "data": self._state.to_dict()
                }

            self._state.power = False
            self._state.last_updated = datetime.now()

            # 取消定时关机任务
            await self._cancel_timer()

            logger.info(f"台灯已关闭 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "台灯已关闭",
                "data": self._state.to_dict()
            }

    async def set_brightness(self, brightness: int) -> Dict[str, Any]:
        """
        设置台灯亮度

        Args:
            brightness: 亮度值 (0-100)

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(brightness, int):
            return {
                "success": False,
                "code": 400,
                "message": f"亮度值必须是整数，当前类型: {type(brightness).__name__}",
                "data": None
            }

        if brightness < self.MIN_BRIGHTNESS or brightness > self.MAX_BRIGHTNESS:
            return {
                "success": False,
                "code": 400,
                "message": f"亮度值必须在 {self.MIN_BRIGHTNESS}-{self.MAX_BRIGHTNESS} 之间",
                "data": None
            }

        async with self._lock:
            old_brightness = self._state.brightness
            self._state.brightness = brightness
            self._state.last_updated = datetime.now()

            # 如果亮度为0，自动关闭
            if brightness == 0:
                self._state.power = False
                await self._cancel_timer()
                logger.info(f"台灯亮度设为0，自动关闭 - 设备ID: {self._device_id}")
            # 如果亮度大于0且台灯关闭，自动开启
            elif brightness > 0 and not self._state.power:
                self._state.power = True
                logger.info(f"台灯亮度设为{brightness}，自动开启 - 设备ID: {self._device_id}")
            else:
                logger.info(f"台灯亮度从 {old_brightness} 调整为 {brightness} - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"亮度已设置为 {brightness}",
                "data": self._state.to_dict()
            }

    async def set_color_temp(self, color_temp: str) -> Dict[str, Any]:
        """
        设置色温模式

        Args:
            color_temp: 色温模式 ("normal" 或 "eye_protection")

        Returns:
            操作结果字典
        """
        # 参数验证
        try:
            temp_mode = LampColorTemp(color_temp)
        except ValueError:
            valid_values = [e.value for e in LampColorTemp]
            return {
                "success": False,
                "code": 400,
                "message": f"无效的色温模式 '{color_temp}'，有效值: {valid_values}",
                "data": None
            }

        async with self._lock:
            old_temp = self._state.color_temp
            self._state.color_temp = temp_mode
            self._state.last_updated = datetime.now()

            logger.info(f"台灯色温从 {old_temp.value} 切换为 {temp_mode.value} - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"色温已切换为 {temp_mode.value}",
                "data": self._state.to_dict()
            }

    async def set_timer_off(self, minutes: int) -> Dict[str, Any]:
        """
        设置定时关机

        Args:
            minutes: 多少分钟后自动关机 (1-1440，即1分钟到24小时)

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(minutes, int):
            return {
                "success": False,
                "code": 400,
                "message": f"时间必须是整数，当前类型: {type(minutes).__name__}",
                "data": None
            }

        if minutes < 1 or minutes > 1440:
            return {
                "success": False,
                "code": 400,
                "message": "定时时间必须在 1-1440 分钟之间 (1分钟到24小时)",
                "data": None
            }

        async with self._lock:
            # 如果台灯未开启，无法设置定时关机
            if not self._state.power:
                return {
                    "success": False,
                    "code": 400,
                    "message": "台灯未开启，无法设置定时关机",
                    "data": None
                }

            # 计算关机时间
            timer_off_time = datetime.now() + timedelta(minutes=minutes)
            self._state.timer_off = timer_off_time
            self._state.last_updated = datetime.now()

            # 取消之前的定时任务（如果有）
            await self._cancel_timer()

            # 创建新的定时任务
            task = asyncio.create_task(self._timer_off_task(minutes))
            LampAPI._timer_tasks[self._device_id] = task

            logger.info(f"台灯定时关机已设置 - {minutes}分钟后自动关闭 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"定时关机已设置，{minutes}分钟后自动关闭",
                "data": {
                    **self._state.to_dict(),
                    "timer_off_minutes": minutes
                }
            }

    async def cancel_timer_off(self) -> Dict[str, Any]:
        """
        取消定时关机

        Returns:
            操作结果字典
        """
        async with self._lock:
            if self._state.timer_off is None:
                return {
                    "success": True,
                    "code": 200,
                    "message": "没有设置定时关机",
                    "data": self._state.to_dict()
                }

            await self._cancel_timer()
            self._state.timer_off = None
            self._state.last_updated = datetime.now()

            logger.info(f"台灯定时关机已取消 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "定时关机已取消",
                "data": self._state.to_dict()
            }

    async def _cancel_timer(self) -> None:
        """取消定时任务（内部方法）"""
        if self._device_id in LampAPI._timer_tasks:
            task = LampAPI._timer_tasks[self._device_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del LampAPI._timer_tasks[self._device_id]

    async def _timer_off_task(self, minutes: int) -> None:
        """
        定时关机任务（内部方法）

        Args:
            minutes: 等待分钟数
        """
        try:
            await asyncio.sleep(minutes * 60)
            async with self._lock:
                if self._state.power:
                    self._state.power = False
                    self._state.timer_off = None
                    self._state.last_updated = datetime.now()
                    logger.info(f"台灯定时关机执行 - 设备ID: {self._device_id}")
        except asyncio.CancelledError:
            logger.info(f"台灯定时关机任务被取消 - 设备ID: {self._device_id}")
            raise

    async def set_state(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量设置台灯状态

        Args:
            state_dict: 状态字典，可包含 power, brightness, color_temp 等字段

        Returns:
            操作结果字典
        """
        async with self._lock:
            try:
                # 更新电源状态
                if "power" in state_dict:
                    self._state.power = bool(state_dict["power"])

                # 更新亮度
                if "brightness" in state_dict:
                    brightness = int(state_dict["brightness"])
                    if self.MIN_BRIGHTNESS <= brightness <= self.MAX_BRIGHTNESS:
                        self._state.brightness = brightness

                # 更新色温
                if "color_temp" in state_dict:
                    self._state.color_temp = LampColorTemp(state_dict["color_temp"])

                # 更新定时关机
                if "timer_off" in state_dict:
                    if state_dict["timer_off"] is None:
                        self._state.timer_off = None
                        await self._cancel_timer()
                    else:
                        self._state.timer_off = datetime.fromisoformat(state_dict["timer_off"])

                self._state.last_updated = datetime.now()
                logger.info(f"台灯状态批量更新完成 - 设备ID: {self._device_id}")

                return {
                    "success": True,
                    "code": 200,
                    "message": "状态更新成功",
                    "data": self._state.to_dict()
                }

            except Exception as e:
                logger.error(f"台灯状态更新失败: {str(e)} - 设备ID: {self._device_id}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"状态更新失败: {str(e)}",
                    "data": None
                }

    def get_supported_functions(self) -> Dict[str, Any]:
        """
        获取台灯支持的功能列表

        Returns:
            支持的功能列表
        """
        return {
            "device_id": self._device_id,
            "device_name": self._device_name,
            "device_type": "lamp",
            "functions": [
                {"name": "turn_on", "description": "打开台灯", "params": []},
                {"name": "turn_off", "description": "关闭台灯", "params": []},
                {"name": "set_brightness", "description": "设置亮度", "params": [
                    {"name": "brightness", "type": "int", "range": [0, 100], "required": True}
                ]},
                {"name": "set_color_temp", "description": "设置色温模式", "params": [
                    {"name": "color_temp", "type": "str", "options": ["normal", "eye_protection"], "required": True}
                ]},
                {"name": "set_timer_off", "description": "设置定时关机", "params": [
                    {"name": "minutes", "type": "int", "range": [1, 1440], "required": True}
                ]},
                {"name": "cancel_timer_off", "description": "取消定时关机", "params": []},
                {"name": "get_status", "description": "获取当前状态", "params": []},
            ]
        }
