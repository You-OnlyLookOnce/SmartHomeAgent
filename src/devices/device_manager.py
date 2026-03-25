"""
设备管理器 - 智能家居设备管理核心模块

执行流程:
1. 初始化 -> 加载已保存的设备列表
2. 添加设备 -> 创建设备实例 -> 保存到存储
3. 更新设备 -> 修改设备属性 -> 保存到存储
4. 删除设备 -> 从存储中移除
5. 控制设备 -> 验证命令 -> 执行控制 -> 更新状态
6. 状态轮询 -> 定期获取设备状态 -> 更新本地状态
"""

import json
import os
import uuid
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """设备类型枚举"""
    LAMP = "lamp"           # 台灯
    AC = "ac"               # 空调
    CURTAIN = "curtain"     # 窗帘
    UNKNOWN = "unknown"     # 未知


class DeviceStatus(Enum):
    """设备状态枚举"""
    ONLINE = "online"       # 在线
    OFFLINE = "offline"     # 离线
    ERROR = "error"         # 错误


@dataclass
class DeviceState:
    """设备状态数据类"""
    # 通用状态
    power: bool = False                     # 开关状态
    
    # 台灯特有
    brightness: int = 50                    # 亮度 0-100
    color_temp: str = "normal"              # 色温: normal(正常), eye_care(护眼)
    timer_off: Optional[int] = None         # 定时关机(分钟)
    
    # 空调特有
    temperature: int = 26                   # 温度 16-30
    mode: str = "cool"                      # 模式: cool(制冷), heat(制热)
    fan_speed: int = 3                      # 风速 1-5
    
    # 窗帘特有
    position: int = 0                       # 位置 0-100 (0=关闭, 100=全开)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Device:
    """设备数据类"""
    id: str                                 # 设备唯一ID
    name: str                               # 设备名称
    type: str                               # 设备类型
    status: str                             # 设备状态
    state: DeviceState                      # 设备状态详情
    created_at: str                         # 创建时间
    updated_at: str                         # 更新时间
    config: Dict[str, Any] = field(default_factory=dict)  # 设备配置
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "state": self.state.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """从字典创建实例"""
        state_data = data.get("state", {})
        state = DeviceState(**state_data)
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            status=data["status"],
            state=state,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            config=data.get("config", {})
        )


class DeviceManager:
    """
    设备管理器 - 单例模式
    
    功能:
    - 设备的增删改查
    - 设备状态管理
    - 设备控制命令处理
    - 设备状态模拟(用于演示)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_path: str = None):
        """
        初始化设备管理器
        
        Args:
            storage_path: 设备数据存储路径
        """
        if self._initialized:
            return
        
        # 设置存储路径
        if storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_path = os.path.join(base_dir, "data", "devices.json")
        
        self.storage_path = storage_path
        self.devices: Dict[str, Device] = {}
        self._status_poll_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # 加载已保存的设备
        self._load_devices()
        
        # 启动状态轮询线程
        self._start_status_polling()
        
        self._initialized = True
        logger.info("设备管理器初始化完成")
    
    def _load_devices(self) -> None:
        """从存储加载设备列表"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for device_data in data.get("devices", []):
                        device = Device.from_dict(device_data)
                        self.devices[device.id] = device
                logger.info(f"已加载 {len(self.devices)} 个设备")
            except Exception as e:
                logger.error(f"加载设备列表失败: {e}")
    
    def _save_devices(self) -> None:
        """保存设备列表到存储"""
        try:
            data = {
                "devices": [device.to_dict() for device in self.devices.values()]
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存设备列表失败: {e}")
    
    def _start_status_polling(self) -> None:
        """启动设备状态轮询线程"""
        if self._status_poll_thread is None or not self._status_poll_thread.is_alive():
            self._stop_polling.clear()
            self._status_poll_thread = threading.Thread(
                target=self._status_polling_loop,
                daemon=True
            )
            self._status_poll_thread.start()
            logger.info("设备状态轮询已启动")
    
    def _status_polling_loop(self) -> None:
        """
        设备状态轮询循环
        
        执行流程:
        1. 每30秒轮询一次
        2. 模拟设备状态变化
        3. 更新设备在线状态
        """
        while not self._stop_polling.is_set():
            try:
                self._simulate_device_status()
                self._stop_polling.wait(30)  # 30秒轮询间隔
            except Exception as e:
                logger.error(f"状态轮询异常: {e}")
                self._stop_polling.wait(5)  # 异常后5秒重试
    
    def _simulate_device_status(self) -> None:
        """
        模拟设备状态变化
        
        说明:
        - 用于演示环境，模拟真实设备的状态变化
        - 随机切换设备的在线/离线状态
        """
        import random
        for device in self.devices.values():
            # 95%概率保持当前状态，5%概率切换
            if random.random() < 0.05:
                if device.status == DeviceStatus.ONLINE.value:
                    device.status = DeviceStatus.OFFLINE.value
                else:
                    device.status = DeviceStatus.ONLINE.value
                device.updated_at = datetime.now().isoformat()
                logger.debug(f"设备 {device.name} 状态变为 {device.status}")
    
    def stop_status_polling(self) -> None:
        """停止状态轮询"""
        self._stop_polling.set()
        if self._status_poll_thread and self._status_poll_thread.is_alive():
            self._status_poll_thread.join(timeout=2)
            logger.info("设备状态轮询已停止")
    
    # ==================== 设备CRUD操作 ====================
    
    def create_device(
        self,
        name: str,
        device_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Device:
        """
        创建新设备
        
        Args:
            name: 设备名称
            device_type: 设备类型 (lamp/ac/curtain)
            config: 设备配置(可选)
        
        Returns:
            创建的设备实例
        
        Raises:
            ValueError: 设备类型无效或名称为空
        
        执行流程:
        1. 验证参数 -> 2. 创建设备 -> 3. 初始化状态 -> 4. 保存 -> 5. 返回
        """
        # 参数验证
        if not name or not name.strip():
            raise ValueError("设备名称不能为空")
        
        if device_type not in [t.value for t in DeviceType]:
            raise ValueError(f"无效的设备类型: {device_type}")
        
        # 创建设备
        now = datetime.now().isoformat()
        device = Device(
            id=str(uuid.uuid4()),
            name=name.strip(),
            type=device_type,
            status=DeviceStatus.ONLINE.value,
            state=DeviceState(),
            created_at=now,
            updated_at=now,
            config=config or {}
        )
        
        # 根据设备类型初始化默认状态
        self._init_device_state(device)
        
        # 保存设备
        self.devices[device.id] = device
        self._save_devices()
        
        logger.info(f"创建设备: {device.name} (ID: {device.id})")
        return device
    
    def _init_device_state(self, device: Device) -> None:
        """根据设备类型初始化默认状态"""
        if device.type == DeviceType.LAMP.value:
            device.state = DeviceState(
                power=False,
                brightness=50,
                color_temp="normal",
                timer_off=None
            )
        elif device.type == DeviceType.AC.value:
            device.state = DeviceState(
                power=False,
                temperature=26,
                mode="cool",
                fan_speed=3
            )
        elif device.type == DeviceType.CURTAIN.value:
            device.state = DeviceState(
                power=False,
                position=0
            )
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        获取单个设备
        
        Args:
            device_id: 设备ID
        
        Returns:
            设备实例或None
        """
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Device]:
        """
        获取所有设备列表
        
        Returns:
            设备列表
        """
        return list(self.devices.values())
    
    def update_device(
        self,
        device_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Device]:
        """
        更新设备信息
        
        Args:
            device_id: 设备ID
            name: 新名称(可选)
            config: 新配置(可选)
        
        Returns:
            更新后的设备实例或None
        
        Raises:
            ValueError: 设备名称无效
        """
        device = self.devices.get(device_id)
        if not device:
            return None
        
        # 更新名称
        if name is not None:
            if not name.strip():
                raise ValueError("设备名称不能为空")
            device.name = name.strip()
        
        # 更新配置
        if config is not None:
            device.config.update(config)
        
        device.updated_at = datetime.now().isoformat()
        self._save_devices()
        
        logger.info(f"更新设备: {device.name} (ID: {device.id})")
        return device
    
    def delete_device(self, device_id: str) -> bool:
        """
        删除设备
        
        Args:
            device_id: 设备ID
        
        Returns:
            是否删除成功
        """
        if device_id not in self.devices:
            return False
        
        device = self.devices.pop(device_id)
        self._save_devices()
        
        logger.info(f"删除设备: {device.name} (ID: {device.id})")
        return True
    
    # ==================== 设备控制操作 ====================
    
    def control_device(
        self,
        device_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        控制设备
        
        Args:
            device_id: 设备ID
            command: 控制命令
            params: 命令参数(可选)
        
        Returns:
            控制结果字典
        
        执行流程:
        1. 验证设备存在 -> 2. 验证设备在线 -> 3. 验证命令 -> 4. 执行控制 -> 5. 更新状态 -> 6. 返回结果
        """
        params = params or {}
        
        # 1. 验证设备存在
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "error_code": "DEVICE_NOT_FOUND",
                "message": "设备不存在"
            }
        
        # 2. 验证设备在线
        if device.status != DeviceStatus.ONLINE.value:
            return {
                "success": False,
                "error_code": "DEVICE_OFFLINE",
                "message": "设备离线，无法控制"
            }
        
        # 3. 根据设备类型执行控制
        try:
            if device.type == DeviceType.LAMP.value:
                result = self._control_lamp(device, command, params)
            elif device.type == DeviceType.AC.value:
                result = self._control_ac(device, command, params)
            elif device.type == DeviceType.CURTAIN.value:
                result = self._control_curtain(device, command, params)
            else:
                return {
                    "success": False,
                    "error_code": "UNSUPPORTED_DEVICE_TYPE",
                    "message": "不支持的设备类型"
                }
            
            # 更新设备状态
            if result.get("success"):
                device.updated_at = datetime.now().isoformat()
                self._save_devices()
            
            return result
            
        except Exception as e:
            logger.error(f"控制设备失败: {e}")
            return {
                "success": False,
                "error_code": "CONTROL_ERROR",
                "message": f"控制失败: {str(e)}"
            }
    
    def _control_lamp(
        self,
        device: Device,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        控制台灯
        
        支持的命令:
        - power_on: 开灯
        - power_off: 关灯
        - set_brightness: 设置亮度 (参数: brightness 0-100)
        - set_color_temp: 设置色温 (参数: color_temp normal/eye_care)
        - set_timer: 设置定时关机 (参数: minutes)
        """
        state = device.state
        
        if command == "power_on":
            state.power = True
            return {"success": True, "message": "台灯已打开"}
        
        elif command == "power_off":
            state.power = False
            return {"success": True, "message": "台灯已关闭"}
        
        elif command == "set_brightness":
            brightness = params.get("brightness")
            if brightness is None or not isinstance(brightness, int):
                return {"success": False, "error_code": "INVALID_PARAM", "message": "亮度参数无效"}
            if not 0 <= brightness <= 100:
                return {"success": False, "error_code": "OUT_OF_RANGE", "message": "亮度范围应为0-100"}
            state.brightness = brightness
            return {"success": True, "message": f"亮度已设置为 {brightness}%"}
        
        elif command == "set_color_temp":
            color_temp = params.get("color_temp")
            if color_temp not in ["normal", "eye_care"]:
                return {"success": False, "error_code": "INVALID_PARAM", "message": "色温参数无效"}
            state.color_temp = color_temp
            return {"success": True, "message": f"色温已切换为 {'正常' if color_temp == 'normal' else '护眼'}模式"}
        
        elif command == "set_timer":
            minutes = params.get("minutes")
            if minutes is not None:
                if not isinstance(minutes, int) or minutes < 0:
                    return {"success": False, "error_code": "INVALID_PARAM", "message": "定时参数无效"}
            state.timer_off = minutes
            if minutes:
                return {"success": True, "message": f"已设置 {minutes} 分钟后自动关闭"}
            else:
                return {"success": True, "message": "已取消定时关闭"}
        
        else:
            return {"success": False, "error_code": "UNKNOWN_COMMAND", "message": "未知命令"}
    
    def _control_ac(
        self,
        device: Device,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        控制空调
        
        支持的命令:
        - power_on: 开机
        - power_off: 关机
        - set_temperature: 设置温度 (参数: temperature 16-30)
        - set_mode: 设置模式 (参数: mode cool/heat)
        - set_fan_speed: 设置风速 (参数: fan_speed 1-5)
        """
        state = device.state
        
        if command == "power_on":
            state.power = True
            return {"success": True, "message": "空调已开启"}
        
        elif command == "power_off":
            state.power = False
            return {"success": True, "message": "空调已关闭"}
        
        elif command == "set_temperature":
            temperature = params.get("temperature")
            if temperature is None or not isinstance(temperature, int):
                return {"success": False, "error_code": "INVALID_PARAM", "message": "温度参数无效"}
            if not 16 <= temperature <= 30:
                return {"success": False, "error_code": "OUT_OF_RANGE", "message": "温度范围应为16-30°C"}
            state.temperature = temperature
            return {"success": True, "message": f"温度已设置为 {temperature}°C"}
        
        elif command == "set_mode":
            mode = params.get("mode")
            if mode not in ["cool", "heat"]:
                return {"success": False, "error_code": "INVALID_PARAM", "message": "模式参数无效"}
            state.mode = mode
            return {"success": True, "message": f"已切换为 {'制冷' if mode == 'cool' else '制热'}模式"}
        
        elif command == "set_fan_speed":
            fan_speed = params.get("fan_speed")
            if fan_speed is None or not isinstance(fan_speed, int):
                return {"success": False, "error_code": "INVALID_PARAM", "message": "风速参数无效"}
            if not 1 <= fan_speed <= 5:
                return {"success": False, "error_code": "OUT_OF_RANGE", "message": "风速范围应为1-5档"}
            state.fan_speed = fan_speed
            return {"success": True, "message": f"风速已设置为 {fan_speed} 档"}
        
        else:
            return {"success": False, "error_code": "UNKNOWN_COMMAND", "message": "未知命令"}
    
    def _control_curtain(
        self,
        device: Device,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        控制窗帘
        
        支持的命令:
        - open: 全开
        - close: 全关
        - stop: 停止
        - set_position: 设置位置 (参数: position 0-100)
        """
        state = device.state
        
        if command == "open":
            state.power = True
            state.position = 100
            return {"success": True, "message": "窗帘已打开"}
        
        elif command == "close":
            state.power = False
            state.position = 0
            return {"success": True, "message": "窗帘已关闭"}
        
        elif command == "stop":
            return {"success": True, "message": "窗帘已停止"}
        
        elif command == "set_position":
            position = params.get("position")
            if position is None or not isinstance(position, int):
                return {"success": False, "error_code": "INVALID_PARAM", "message": "位置参数无效"}
            if not 0 <= position <= 100:
                return {"success": False, "error_code": "OUT_OF_RANGE", "message": "位置范围应为0-100%"}
            state.position = position
            state.power = position > 0
            return {"success": True, "message": f"窗帘位置已设置为 {position}%"}
        
        else:
            return {"success": False, "error_code": "UNKNOWN_COMMAND", "message": "未知命令"}
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备实时状态
        
        Args:
            device_id: 设备ID
        
        Returns:
            设备状态字典或None
        """
        device = self.devices.get(device_id)
        if not device:
            return None
        
        return {
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "status": device.status,
            "state": device.state.to_dict(),
            "updated_at": device.updated_at
        }


# 全局设备管理器实例
device_manager = DeviceManager()
