"""
窗帘API模块 - 实现智能窗帘的各项控制功能

功能：
- 开关控制（全开/全关）
- 位置百分比调节(0-100)
- 定时开关设置
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CurtainState:
    """窗帘状态数据类"""
    power: bool = False                    # 开关状态 (True=打开/运行中, False=关闭/停止)
    position: int = 0                      # 窗帘位置 (0-100, 0=完全关闭, 100=完全打开)
    is_moving: bool = False                # 是否正在移动
    timer_open: Optional[datetime] = None  # 定时开启时间
    timer_close: Optional[datetime] = None # 定时关闭时间
    device_id: str = "curtain_default"     # 设备ID
    device_name: str = "窗帘"               # 设备名称
    last_updated: datetime = field(default_factory=datetime.now)  # 最后更新时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "power": self.power,
            "position": self.position,
            "is_moving": self.is_moving,
            "timer_open": self.timer_open.isoformat() if self.timer_open else None,
            "timer_close": self.timer_close.isoformat() if self.timer_close else None,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CurtainState':
        """从字典创建实例"""
        timer_open = None
        if data.get("timer_open"):
            timer_open = datetime.fromisoformat(data["timer_open"])

        timer_close = None
        if data.get("timer_close"):
            timer_close = datetime.fromisoformat(data["timer_close"])

        return cls(
            device_id=data.get("device_id", "curtain_default"),
            device_name=data.get("device_name", "窗帘"),
            power=data.get("power", False),
            position=data.get("position", 0),
            is_moving=data.get("is_moving", False),
            timer_open=timer_open,
            timer_close=timer_close,
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
        )


class CurtainAPI:
    """
    窗帘API类

    提供智能窗帘的完整控制接口，包括开关、位置调节、定时设置等功能。
    所有方法均为异步方法，支持并发操作。
    """

    # 位置范围常量
    MIN_POSITION = 0
    MAX_POSITION = 100

    # 移动速度：每秒移动的百分比
    MOVE_SPEED_PER_SECOND = 10

    # 定时器任务字典 {device_id: {"open": task, "close": task}}
    _timer_tasks: Dict[str, Dict[str, asyncio.Task]] = {}

    def __init__(self, device_id: str = "curtain_default", device_name: str = "窗帘"):
        """
        初始化窗帘API

        Args:
            device_id: 设备唯一标识
            device_name: 设备名称
        """
        self._device_id = device_id
        self._device_name = device_name
        self._state = CurtainState(device_id=device_id, device_name=device_name)
        self._lock = asyncio.Lock()
        self._move_task: Optional[asyncio.Task] = None
        logger.info(f"窗帘API初始化完成 - 设备ID: {device_id}, 名称: {device_name}")

    @property
    def device_id(self) -> str:
        """获取设备ID"""
        return self._device_id

    @property
    def device_name(self) -> str:
        """获取设备名称"""
        return self._device_name

    @property
    def state(self) -> CurtainState:
        """获取当前状态"""
        return self._state

    async def get_status(self) -> Dict[str, Any]:
        """
        获取窗帘当前状态

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

    async def open(self) -> Dict[str, Any]:
        """
        完全打开窗帘 (位置设为100)

        Returns:
            操作结果字典
        """
        return await self.set_position(100)

    async def close(self) -> Dict[str, Any]:
        """
        完全关闭窗帘 (位置设为0)

        Returns:
            操作结果字典
        """
        return await self.set_position(0)

    async def stop(self) -> Dict[str, Any]:
        """
        停止窗帘移动

        Returns:
            操作结果字典
        """
        async with self._lock:
            # 取消正在进行的移动任务
            if self._move_task and not self._move_task.done():
                self._move_task.cancel()
                try:
                    await self._move_task
                except asyncio.CancelledError:
                    pass

            self._state.is_moving = False
            self._state.power = self._state.position > 0
            self._state.last_updated = datetime.now()

            logger.info(f"窗帘已停止移动，当前位置: {self._state.position}% - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"窗帘已停止，当前位置: {self._state.position}%",
                "data": self._state.to_dict()
            }

    async def set_position(self, position: int) -> Dict[str, Any]:
        """
        设置窗帘位置

        Args:
            position: 位置百分比 (0-100, 0=完全关闭, 100=完全打开)

        Returns:
            操作结果字典
        """
        # 参数验证
        if not isinstance(position, int):
            return {
                "success": False,
                "code": 400,
                "message": f"位置值必须是整数，当前类型: {type(position).__name__}",
                "data": None
            }

        if position < self.MIN_POSITION or position > self.MAX_POSITION:
            return {
                "success": False,
                "code": 400,
                "message": f"位置值必须在 {self.MIN_POSITION}-{self.MAX_POSITION} 之间",
                "data": None
            }

        async with self._lock:
            # 如果已经在目标位置
            if self._state.position == position:
                self._state.power = position > 0
                return {
                    "success": True,
                    "code": 200,
                    "message": f"窗帘已经在位置 {position}%",
                    "data": self._state.to_dict()
                }

            # 取消之前的移动任务
            if self._move_task and not self._move_task.done():
                self._move_task.cancel()
                try:
                    await self._move_task
                except asyncio.CancelledError:
                    pass

            # 开始移动
            old_position = self._state.position
            self._state.is_moving = True
            self._state.power = True
            self._state.last_updated = datetime.now()

            # 创建移动任务
            self._move_task = asyncio.create_task(self._move_to_position(position))

            direction = "打开" if position > old_position else "关闭"
            logger.info(f"窗帘开始{direction}，从 {old_position}% 移动到 {position}% - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"窗帘开始移动，目标位置: {position}%",
                "data": self._state.to_dict()
            }

    async def _move_to_position(self, target_position: int) -> None:
        """
        移动窗帘到指定位置（内部方法，模拟移动过程）

        Args:
            target_position: 目标位置
        """
        try:
            current_position = self._state.position
            direction = 1 if target_position > current_position else -1

            while self._state.position != target_position:
                # 计算移动步长
                step = direction * self.MOVE_SPEED_PER_SECOND
                new_position = self._state.position + step

                # 检查是否到达目标
                if (direction == 1 and new_position >= target_position) or \
                   (direction == -1 and new_position <= target_position):
                    new_position = target_position

                self._state.position = new_position

                # 如果到达目标，停止
                if new_position == target_position:
                    break

                # 模拟移动延迟
                await asyncio.sleep(1)

            # 移动完成
            async with self._lock:
                self._state.is_moving = False
                self._state.power = self._state.position > 0
                self._state.last_updated = datetime.now()
                logger.info(f"窗帘移动完成，当前位置: {self._state.position}% - 设备ID: {self._device_id}")

        except asyncio.CancelledError:
            async with self._lock:
                self._state.is_moving = False
                self._state.power = self._state.position > 0
                self._state.last_updated = datetime.now()
                logger.info(f"窗帘移动被取消，当前位置: {self._state.position}% - 设备ID: {self._device_id}")
            raise

    async def set_timer(self, action: str, minutes: int) -> Dict[str, Any]:
        """
        设置定时开关

        Args:
            action: 动作类型 ("open" 或 "close")
            minutes: 多少分钟后执行 (1-1440，即1分钟到24小时)

        Returns:
            操作结果字典
        """
        # 参数验证
        if action not in ["open", "close"]:
            return {
                "success": False,
                "code": 400,
                "message": f"无效的动作类型 '{action}'，有效值: ['open', 'close']",
                "data": None
            }

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
            # 计算执行时间
            timer_time = datetime.now() + timedelta(minutes=minutes)

            if action == "open":
                self._state.timer_open = timer_time
            else:
                self._state.timer_close = timer_time

            self._state.last_updated = datetime.now()

            # 取消之前的定时任务
            await self._cancel_timer(action)

            # 创建新的定时任务
            task = asyncio.create_task(self._timer_task(action, minutes))
            if self._device_id not in CurtainAPI._timer_tasks:
                CurtainAPI._timer_tasks[self._device_id] = {}
            CurtainAPI._timer_tasks[self._device_id][action] = task

            action_name = "打开" if action == "open" else "关闭"
            logger.info(f"窗帘定时{action_name}已设置 - {minutes}分钟后执行 - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"定时{action_name}已设置，{minutes}分钟后执行",
                "data": {
                    **self._state.to_dict(),
                    "timer_minutes": minutes,
                    "timer_action": action
                }
            }

    async def cancel_timer(self, action: Optional[str] = None) -> Dict[str, Any]:
        """
        取消定时任务

        Args:
            action: 动作类型 ("open", "close", 或 None表示取消所有)

        Returns:
            操作结果字典
        """
        async with self._lock:
            cancelled = []

            if action is None:
                # 取消所有定时任务
                for act in ["open", "close"]:
                    if await self._cancel_timer_task(act):
                        cancelled.append(act)
                        if act == "open":
                            self._state.timer_open = None
                        else:
                            self._state.timer_close = None
            else:
                # 取消指定定时任务
                if await self._cancel_timer_task(action):
                    cancelled.append(action)
                    if action == "open":
                        self._state.timer_open = None
                    else:
                        self._state.timer_close = None

            self._state.last_updated = datetime.now()

            if not cancelled:
                return {
                    "success": True,
                    "code": 200,
                    "message": "没有需要取消的定时任务",
                    "data": self._state.to_dict()
                }

            action_names = ["打开" if a == "open" else "关闭" for a in cancelled]
            logger.info(f"窗帘定时任务已取消: {action_names} - 设备ID: {self._device_id}")

            return {
                "success": True,
                "code": 200,
                "message": f"定时任务已取消: {', '.join(action_names)}",
                "data": self._state.to_dict()
            }

    async def _cancel_timer(self, action: str) -> None:
        """取消指定类型的定时任务（内部方法）"""
        await self._cancel_timer_task(action)

    async def _cancel_timer_task(self, action: str) -> bool:
        """取消指定类型的定时任务（内部方法）"""
        if self._device_id in CurtainAPI._timer_tasks:
            if action in CurtainAPI._timer_tasks[self._device_id]:
                task = CurtainAPI._timer_tasks[self._device_id][action]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del CurtainAPI._timer_tasks[self._device_id][action]
                return True
        return False

    async def _timer_task(self, action: str, minutes: int) -> None:
        """
        定时任务（内部方法）

        Args:
            action: 动作类型
            minutes: 等待分钟数
        """
        try:
            await asyncio.sleep(minutes * 60)
            if action == "open":
                await self.open()
                async with self._lock:
                    self._state.timer_open = None
                logger.info(f"窗帘定时打开执行 - 设备ID: {self._device_id}")
            else:
                await self.close()
                async with self._lock:
                    self._state.timer_close = None
                logger.info(f"窗帘定时关闭执行 - 设备ID: {self._device_id}")
        except asyncio.CancelledError:
            action_name = "打开" if action == "open" else "关闭"
            logger.info(f"窗帘定时{action_name}任务被取消 - 设备ID: {self._device_id}")
            raise

    async def set_state(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量设置窗帘状态

        Args:
            state_dict: 状态字典，可包含 power, position, is_moving 等字段

        Returns:
            操作结果字典
        """
        async with self._lock:
            try:
                # 更新电源状态
                if "power" in state_dict:
                    self._state.power = bool(state_dict["power"])

                # 更新位置
                if "position" in state_dict:
                    position = int(state_dict["position"])
                    if self.MIN_POSITION <= position <= self.MAX_POSITION:
                        self._state.position = position

                # 更新移动状态
                if "is_moving" in state_dict:
                    self._state.is_moving = bool(state_dict["is_moving"])

                # 更新定时打开
                if "timer_open" in state_dict:
                    if state_dict["timer_open"] is None:
                        self._state.timer_open = None
                    else:
                        self._state.timer_open = datetime.fromisoformat(state_dict["timer_open"])

                # 更新定时关闭
                if "timer_close" in state_dict:
                    if state_dict["timer_close"] is None:
                        self._state.timer_close = None
                    else:
                        self._state.timer_close = datetime.fromisoformat(state_dict["timer_close"])

                self._state.last_updated = datetime.now()
                logger.info(f"窗帘状态批量更新完成 - 设备ID: {self._device_id}")

                return {
                    "success": True,
                    "code": 200,
                    "message": "状态更新成功",
                    "data": self._state.to_dict()
                }

            except Exception as e:
                logger.error(f"窗帘状态更新失败: {str(e)} - 设备ID: {self._device_id}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"状态更新失败: {str(e)}",
                    "data": None
                }

    def get_supported_functions(self) -> Dict[str, Any]:
        """
        获取窗帘支持的功能列表

        Returns:
            支持的功能列表
        """
        return {
            "device_id": self._device_id,
            "device_name": self._device_name,
            "device_type": "curtain",
            "functions": [
                {"name": "open", "description": "完全打开窗帘", "params": []},
                {"name": "close", "description": "完全关闭窗帘", "params": []},
                {"name": "stop", "description": "停止窗帘移动", "params": []},
                {"name": "set_position", "description": "设置窗帘位置", "params": [
                    {"name": "position", "type": "int", "range": [0, 100], "required": True}
                ]},
                {"name": "set_timer", "description": "设置定时开关", "params": [
                    {"name": "action", "type": "str", "options": ["open", "close"], "required": True},
                    {"name": "minutes", "type": "int", "range": [1, 1440], "required": True}
                ]},
                {"name": "cancel_timer", "description": "取消定时任务", "params": [
                    {"name": "action", "type": "str", "options": ["open", "close"], "required": False}
                ]},
                {"name": "get_status", "description": "获取当前状态", "params": []},
            ]
        }
