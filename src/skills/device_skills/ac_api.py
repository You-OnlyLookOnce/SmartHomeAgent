"""
空调API模块 - 实现空调的各项控制功能

功能：
- 开关控制
- 温度设置(16-30)
- 模式切换(制冷/制热/送风/除湿/自动)
- 风速调节(1-5挡)
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ACMode(Enum):
    """空调运行模式"""
    COOL = "cool"          # 制冷模式
    HEAT = "heat"          # 制热模式
    FAN = "fan"            # 送风模式
    DRY = "dry"            # 除湿模式
    AUTO = "auto"          # 自动模式


class ACWindSpeed(Enum):
    """空调风速档位"""
    LEVEL_1 = 1            # 1挡 - 低风
    LEVEL_2 = 2            # 2挡 - 中风
    LEVEL_3 = 3            # 3挡 - 高风
    LEVEL_4 = 4            # 4挡 - 强力
    LEVEL_5 = 5            # 5挡 - 自动/超强


@dataclass
class ACState:
    """空调状态数据类"""
    power: bool = False                    # 开关状态
    temperature: int = 26                  # 设定温度 (16-30)
    mode: ACMode = ACMode.COOL             # 运行模式
    wind_speed: ACWindSpeed = ACWindSpeed.LEVEL_3  # 风速档位
    current_temp: float = 25.0             # 当前环境温度
    device_id: str = "ac_default"          # 设备ID
    device_name: str = "空调"               # 设备名称
    last_updated: datetime = field(default_factory=datetime.now)  # 最后更新时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "power": self.power,
            "temperature": self.temperature,
            "mode": self.mode.value,
            "wind_speed": self.wind_speed.value,
            "current_temp": self.current_temp,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ACState':
        """从字典创建实例"""
        return cls(
            device_id=data.get("device_id", "ac_default"),
            device_name=data.get("device_name", "空调"),
            power=data.get("power", False),
            temperature=data.get("temperature", 26),
            mode=ACMode(data.get("mode", "cool")),
            wind_speed=ACWindSpeed(data.get("wind_speed", 3)),
            current_temp=data.get("current_temp", 25.0),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
        )


class AirConditionerAPI:
    """
    空调API类

    提供空调的完整控制接口，包括开关、温度设置、模式切换、风速调节等功能。
    所有方法均为异步方法，支持并发操作。
    """

    # 温度范围常量
    MIN_TEMPERATURE = 16
    MAX_TEMPERATURE = 30

    # 风速档位范围
    MIN_WIND_SPEED = 1
    MAX_WIND_SPEED = 5

    def __init__(self, device_id: str = "ac_default", device_name: str = "空调"):
        """
        初始化空调API

        Args:
            device_id: 设备唯一标识
            device_name: 设备名称
        """
        self._device_id = device_id
        self._device_name = device_name
        self._state = ACState(device_id=device_id, device_name=device_name)
        self._lock = asyncio.Lock()
        logger.info(f"空调API初始化完成 - 设备ID: {device_id}, 名称: {device_name}")

    @property
    def device_id(self) -> str:
        """获取设备ID"""
        return self._device_id

    @property
    def device_name(self) -> str:
        """获取设备名称"""
        return self._device_name

    @property
    def state(self) -> ACState:
        """获取当前状态"""
        return self._state

    async def get_status(self) -> Dict[str, Any]:
        """
        获取空调当前状态

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
        打开空调

        Returns:
            操作结果字典
        """
        async with self._lock:
            if self._state.power:
                return {
                    "success": True,
                    "code": 200,
                    "message": "空调已经是开启状态",
                    "data": self._state.to_dict()
                }

            self._state.power = True
            self._state.last_updated = datetime.now()
            logger.info(f"空调已开启 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "空调已开启",
                "data": self._state.to_dict()
            }

    async def turn_off(self) -> Dict[str, Any]:
        """
        关闭空调

        Returns:
            操作结果字典
        """
        async with self._lock:
            if not self._state.power:
                return {
                    "success": True,
                    "code": 200,
                    "message": "空调已经是关闭状态",
                    "data": self._state.to_dict()
                }

            self._state.power = False
            self._state.last_updated = datetime.now()
            logger.info(f"空调已关闭 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "空调已关闭",
                "data": self._state.to_dict()
            }

    async def set_temperature(self, temperature: int) -> Dict[str, Any]:
        """
        设置空调温度

        Args:
            temperature: 温度值 (16-30)

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(temperature, int):
            return {
                "success": False,
                "code": 400,
                "message": f"温度值必须是整数，当前类型: {type(temperature).__name__}",
                "data": None
            }

        if temperature < self.MIN_TEMPERATURE or temperature > self.MAX_TEMPERATURE:
            return {
                "success": False,
                "code": 400,
                "message": f"温度值必须在 {self.MIN_TEMPERATURE}-{self.MAX_TEMPERATURE} 之间",
                "data": None
            }

        async with self._lock:
            old_temp = self._state.temperature
            self._state.temperature = temperature
            self._state.last_updated = datetime.now()

            # 如果空调关闭，自动开启
            if not self._state.power:
                self._state.power = True
                logger.info(f"空调温度设为{temperature}°C，自动开启 - 设备ID: {self._device_id}")
            else:
                logger.info(f"空调温度从 {old_temp}°C 调整为 {temperature}°C - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"温度已设置为 {temperature}°C",
                "data": self._state.to_dict()
            }

    async def set_mode(self, mode: str) -> Dict[str, Any]:
        """
        设置空调运行模式

        Args:
            mode: 运行模式 ("cool"/"heat"/"fan"/"dry"/"auto")

        Returns:
            操作结果字典
        """
        # 参数验证
        try:
            ac_mode = ACMode(mode)
        except ValueError:
            valid_values = [e.value for e in ACMode]
            return {
                "success": False,
                "code": 400,
                "message": f"无效的运行模式 '{mode}'，有效值: {valid_values}",
                "data": None
            }

        async with self._lock:
            old_mode = self._state.mode
            self._state.mode = ac_mode
            self._state.last_updated = datetime.now()

            # 如果空调关闭，自动开启
            if not self._state.power:
                self._state.power = True
                logger.info(f"空调模式切换为{ac_mode.value}，自动开启 - 设备ID: {self._device_id}")
            else:
                logger.info(f"空调模式从 {old_mode.value} 切换为 {ac_mode.value} - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"运行模式已切换为 {ac_mode.value}",
                "data": self._state.to_dict()
            }

    async def set_wind_speed(self, speed: int) -> Dict[str, Any]:
        """
        设置空调风速档位

        Args:
            speed: 风速档位 (1-5)

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(speed, int):
            return {
                "success": False,
                "code": 400,
                "message": f"风速档位必须是整数，当前类型: {type(speed).__name__}",
                "data": None
            }

        if speed < self.MIN_WIND_SPEED or speed > self.MAX_WIND_SPEED:
            return {
                "success": False,
                "code": 400,
                "message": f"风速档位必须在 {self.MIN_WIND_SPEED}-{self.MAX_WIND_SPEED} 之间",
                "data": None
            }

        async with self._lock:
            old_speed = self._state.wind_speed
            self._state.wind_speed = ACWindSpeed(speed)
            self._state.last_updated = datetime.now()

            # 如果空调关闭，自动开启
            if not self._state.power:
                self._state.power = True
                logger.info(f"空调风速设为{speed}挡，自动开启 - 设备ID: {self._device_id}")
            else:
                logger.info(f"空调风速从 {old_speed.value}挡 调整为 {speed}挡 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"风速已设置为 {speed}挡",
                "data": self._state.to_dict()
            }

    async def set_current_temperature(self, current_temp: float) -> Dict[str, Any]:
        """
        设置当前环境温度（用于模拟或传感器数据更新）

        Args:
            current_temp: 当前环境温度

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(current_temp, (int, float)):
            return {
                "success": False,
                "code": 400,
                "message": f"温度必须是数字，当前类型: {type(current_temp).__name__}",
                "data": None
            }

        if current_temp < -20 or current_temp > 60:
            return {
                "success": False,
                "code": 400,
                "message": "当前温度值不合理，应在 -20°C 到 60°C 之间",
                "data": None
            }

        async with self._lock:
            self._state.current_temp = float(current_temp)
            self._state.last_updated = datetime.now()
            logger.info(f"空调环境温度更新为 {current_temp}°C - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"当前环境温度已更新为 {current_temp}°C",
                "data": self._state.to_dict()
            }

    async def quick_cool(self) -> Dict[str, Any]:
        """
        快速制冷模式 - 自动设置为制冷模式、最低温度、最高风速

        Returns:
            操作结果字典
        """
        async with self._lock:
            self._state.power = True
            self._state.mode = ACMode.COOL
            self._state.temperature = self.MIN_TEMPERATURE
            self._state.wind_speed = ACWindSpeed.LEVEL_5
            self._state.last_updated = datetime.now()

            logger.info(f"空调快速制冷模式已启动 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"快速制冷模式已启动，温度设为{self.MIN_TEMPERATURE}°C，风速5挡",
                "data": self._state.to_dict()
            }

    async def quick_heat(self) -> Dict[str, Any]:
        """
        快速制热模式 - 自动设置为制热模式、最高温度、最高风速

        Returns:
            操作结果字典
        """
        async with self._lock:
            self._state.power = True
            self._state.mode = ACMode.HEAT
            self._state.temperature = self.MAX_TEMPERATURE
            self._state.wind_speed = ACWindSpeed.LEVEL_5
            self._state.last_updated = datetime.now()

            logger.info(f"空调快速制热模式已启动 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"快速制热模式已启动，温度设为{self.MAX_TEMPERATURE}°C，风速5挡",
                "data": self._state.to_dict()
            }

    async def energy_save_mode(self) -> Dict[str, Any]:
        """
        节能模式 - 自动设置为自动模式、适中温度、低风速

        Returns:
            操作结果字典
        """
        async with self._lock:
            self._state.power = True
            self._state.mode = ACMode.AUTO
            self._state.temperature = 26  # 推荐节能温度
            self._state.wind_speed = ACWindSpeed.LEVEL_1
            self._state.last_updated = datetime.now()

            logger.info(f"空调节能模式已启动 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "节能模式已启动，温度26°C，自动模式，低风速",
                "data": self._state.to_dict()
            }

    async def sleep_mode(self) -> Dict[str, Any]:
        """
        睡眠模式 - 自动设置为睡眠友好参数

        Returns:
            操作结果字典
        """
        async with self._lock:
            self._state.power = True
            self._state.mode = ACMode.AUTO
            self._state.temperature = 27  # 睡眠推荐温度
            self._state.wind_speed = ACWindSpeed.LEVEL_1  # 最低风速，静音
            self._state.last_updated = datetime.now()

            logger.info(f"空调睡眠模式已启动 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": "睡眠模式已启动，温度27°C，自动模式，静音风速",
                "data": self._state.to_dict()
            }

    async def set_state(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量设置空调状态

        Args:
            state_dict: 状态字典，可包含 power, temperature, mode, wind_speed 等字段

        Returns:
            操作结果字典
        """
        async with self._lock:
            try:
                # 更新电源状态
                if "power" in state_dict:
                    self._state.power = bool(state_dict["power"])

                # 更新温度
                if "temperature" in state_dict:
                    temp = int(state_dict["temperature"])
                    if self.MIN_TEMPERATURE <= temp <= self.MAX_TEMPERATURE:
                        self._state.temperature = temp

                # 更新模式
                if "mode" in state_dict:
                    self._state.mode = ACMode(state_dict["mode"])

                # 更新风速
                if "wind_speed" in state_dict:
                    speed = int(state_dict["wind_speed"])
                    if self.MIN_WIND_SPEED <= speed <= self.MAX_WIND_SPEED:
                        self._state.wind_speed = ACWindSpeed(speed)

                # 更新当前温度
                if "current_temp" in state_dict:
                    self._state.current_temp = float(state_dict["current_temp"])

                self._state.last_updated = datetime.now()
                logger.info(f"空调状态批量更新完成 - 设备ID: {self._device_id}")

                return {
                    "success": True,
                    "code": 200,
                    "message": "状态更新成功",
                    "data": self._state.to_dict()
                }

            except Exception as e:
                logger.error(f"空调状态更新失败: {str(e)} - 设备ID: {self._device_id}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"状态更新失败: {str(e)}",
                    "data": None
                }

    def get_supported_functions(self) -> Dict[str, Any]:
        """
        获取空调支持的功能列表

        Returns:
            支持的功能列表
        """
        return {
            "device_id": self._device_id,
            "device_name": self._device_name,
            "device_type": "air_conditioner",
            "functions": [
                {"name": "turn_on", "description": "打开空调", "params": []},
                {"name": "turn_off", "description": "关闭空调", "params": []},
                {"name": "set_temperature", "description": "设置温度", "params": [
                    {"name": "temperature", "type": "int", "range": [16, 30], "required": True}
                ]},
                {"name": "set_mode", "description": "设置运行模式", "params": [
                    {"name": "mode", "type": "str", "options": ["cool", "heat", "fan", "dry", "auto"], "required": True}
                ]},
                {"name": "set_wind_speed", "description": "设置风速档位", "params": [
                    {"name": "speed", "type": "int", "range": [1, 5], "required": True}
                ]},
                {"name": "quick_cool", "description": "快速制冷模式", "params": []},
                {"name": "quick_heat", "description": "快速制热模式", "params": []},
                {"name": "energy_save_mode", "description": "节能模式", "params": []},
                {"name": "sleep_mode", "description": "睡眠模式", "params": []},
                {"name": "get_status", "description": "获取当前状态", "params": []},
            ]
        }
