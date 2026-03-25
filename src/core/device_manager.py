"""
设备管理器模块 - 管理所有设备的状态和配置

功能：
- 设备CRUD操作
- 内存存储+文件持久化
- 集成文件操作MCP进行数据持久化
- 设备状态管理
- 自动保存和备份机制

执行流程：
1. 初始化时从文件加载设备配置
2. 提供设备CRUD接口
3. 设备变更时自动保存到文件(延迟1秒，避免频繁写入)
4. 定期同步状态到文件(每30秒)
5. 配置文件自动备份(保留最近5个版本)
6. 通过MCP适配器与设备通信
"""

import os
import json
import asyncio
import logging
import shutil
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from src.skills.mcp_skills.device_mcp_adapter import DeviceMCPAdapter, DeviceModel, DeviceType
from src.skills.mcp_skills.file_operations_mcp import FileOperationsMCP

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    设备管理器类

    管理所有智能家居设备的状态和配置，提供设备CRUD操作，
    支持内存存储和文件持久化，具备自动保存和备份功能。

    执行流程：
    1. 初始化时从文件加载设备配置
    2. 提供设备CRUD接口
    3. 设备变更时自动保存到文件(延迟1秒)
    4. 定期同步状态到文件(每30秒)
    5. 配置文件自动备份(保留最近5个版本)
    6. 通过MCP适配器与设备通信
    """

    # 默认设备配置文件路径
    DEFAULT_CONFIG_FILE = "data/devices/device_config.json"
    # 备份目录路径
    BACKUP_DIR = "data/devices/backups"
    # 保留的备份版本数量
    MAX_BACKUP_COUNT = 5
    # 自动保存延迟时间(秒)
    AUTO_SAVE_DELAY = 1.0
    # 定期同步间隔(秒)
    PERIODIC_SYNC_INTERVAL = 30.0

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化设备管理器

        Args:
            config_file: 设备配置文件路径，默认使用 DEFAULT_CONFIG_FILE
        """
        self._config_file = config_file or self.DEFAULT_CONFIG_FILE
        self._mcp_adapter = DeviceMCPAdapter()
        self._file_mcp = FileOperationsMCP()
        self._lock = asyncio.Lock()

        # 自动保存相关
        self._pending_save = False
        self._save_timer = None
        self._state_change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        # 定期同步任务
        self._periodic_sync_task = None
        self._initialized = False

        # 确保数据目录存在
        self._ensure_data_dir()

        logger.info(f"设备管理器初始化完成，配置文件: {self._config_file}")



    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        # 确保主配置目录存在
        data_dir = os.path.dirname(self._config_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"创建数据目录: {data_dir}")

        # 确保备份目录存在
        if not os.path.exists(self.BACKUP_DIR):
            os.makedirs(self.BACKUP_DIR, exist_ok=True)
            logger.info(f"创建备份目录: {self.BACKUP_DIR}")

    async def start_periodic_sync(self) -> None:
        """启动定期同步任务"""
        if self._periodic_sync_task is None:
            self._periodic_sync_task = asyncio.create_task(self._periodic_sync_loop())
            logger.info("定期同步任务已启动")

    async def stop_periodic_sync(self) -> None:
        """停止定期同步任务"""
        if self._periodic_sync_task:
            self._periodic_sync_task.cancel()
            try:
                await self._periodic_sync_task
            except asyncio.CancelledError:
                pass
            self._periodic_sync_task = None
            logger.info("定期同步任务已停止")

    async def _periodic_sync_loop(self) -> None:
        """定期同步循环"""
        while True:
            try:
                await asyncio.sleep(self.PERIODIC_SYNC_INTERVAL)
                await self._save_to_file()
                logger.debug("定期同步完成")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期同步失败: {str(e)}")

    def _trigger_auto_save(self) -> None:
        """触发自动保存(延迟执行)"""
        self._pending_save = True

        # 取消现有的定时器
        if self._save_timer:
            self._save_timer.cancel()

        # 创建新的定时器
        async def delayed_save():
            await asyncio.sleep(self.AUTO_SAVE_DELAY)
            if self._pending_save:
                await self._save_to_file()
                self._pending_save = False

        self._save_timer = asyncio.create_task(delayed_save())
        logger.debug(f"自动保存已触发，将在{self.AUTO_SAVE_DELAY}秒后执行")

    async def _create_backup(self) -> Optional[str]:
        """
        创建配置文件备份

        Returns:
            备份文件路径或None
        """
        try:
            if not os.path.exists(self._config_file):
                return None

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"device_config_backup_{timestamp}.json"
            backup_path = os.path.join(self.BACKUP_DIR, backup_filename)

            # 复制文件
            shutil.copy2(self._config_file, backup_path)
            logger.info(f"配置已备份到: {backup_path}")

            # 清理旧备份
            await self._cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None

    async def _cleanup_old_backups(self) -> None:
        """清理旧备份文件，只保留最近N个"""
        try:
            if not os.path.exists(self.BACKUP_DIR):
                return

            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(self.BACKUP_DIR):
                if filename.startswith("device_config_backup_") and filename.endswith(".json"):
                    filepath = os.path.join(self.BACKUP_DIR, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))

            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # 删除旧备份
            for filepath, _ in backup_files[self.MAX_BACKUP_COUNT:]:
                os.remove(filepath)
                logger.info(f"删除旧备份: {filepath}")

        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")

    def register_state_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注册状态变更回调函数

        Args:
            callback: 回调函数，接收device_id和state两个参数
        """
        if callback not in self._state_change_callbacks:
            self._state_change_callbacks.append(callback)
            logger.info(f"状态变更回调已注册，当前数量: {len(self._state_change_callbacks)}")

    def unregister_state_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注销状态变更回调函数

        Args:
            callback: 回调函数
        """
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)
            logger.info(f"状态变更回调已注销，当前数量: {len(self._state_change_callbacks)}")

    async def _notify_state_change(self, device_id: str, state: Dict[str, Any]) -> None:
        """
        通知状态变更

        Args:
            device_id: 设备ID
            state: 新状态
        """
        for callback in self._state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(device_id, state)
                else:
                    callback(device_id, state)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {str(e)}")

    async def initialize(self) -> Dict[str, Any]:
        """
        初始化设备管理器 - 从文件加载设备配置

        执行流程：
        1. 检查配置文件是否存在
        2. 读取并解析配置文件
        3. 加载所有设备到内存
        4. 恢复设备状态
        5. 启动定期同步任务
        6. 注册状态变更回调

        Returns:
            初始化结果
        """
        async with self._lock:
            try:
                # 检查配置文件是否存在
                if os.path.exists(self._config_file):
                    # 读取配置文件
                    content = await self._file_mcp.read_file_async(self._config_file)

                    if content.startswith("错误:"):
                        logger.warning(f"读取配置文件失败: {content}")
                        self._initialized = True
                        await self.start_periodic_sync()
                        return {
                            "success": True,
                            "code": 200,
                            "message": "配置文件不存在或读取失败，将创建新配置",
                            "data": {"loaded_devices": 0}
                        }

                    # 解析JSON
                    devices_data = json.loads(content)

                    # 加载设备
                    loaded_count = 0
                    for device_data in devices_data.get("devices", []):
                        try:
                            result = await self._mcp_adapter.register_device(
                                device_type=device_data["device_type"],
                                device_id=device_data["device_id"],
                                device_name=device_data["device_name"]
                            )

                            if result.get("success"):
                                # 恢复设备状态
                                if "current_state" in device_data:
                                    await self._mcp_adapter.sync_device_state(
                                        device_data["device_id"],
                                        device_data["current_state"]
                                    )
                                loaded_count += 1

                        except Exception as e:
                            logger.error(f"加载设备失败: {str(e)}")

                    logger.info(f"从配置文件加载了 {loaded_count} 个设备")

                    # 标记为已初始化
                    self._initialized = True

                    # 启动定期同步
                    await self.start_periodic_sync()

                    # 注册MCP适配器的状态变更回调
                    self._mcp_adapter.register_state_change_callback(self._on_device_state_changed)

                    return {
                        "success": True,
                        "code": 200,
                        "message": f"成功加载 {loaded_count} 个设备",
                        "data": {"loaded_devices": loaded_count}
                    }
                else:
                    logger.info("配置文件不存在，将创建新配置")
                    self._initialized = True
                    await self.start_periodic_sync()
                    return {
                        "success": True,
                        "code": 200,
                        "message": "配置文件不存在，将创建新配置",
                        "data": {"loaded_devices": 0}
                    }

            except Exception as e:
                logger.error(f"初始化设备管理器失败: {str(e)}")
                self._initialized = False
                return {
                    "success": False,
                    "code": 500,
                    "message": f"初始化失败: {str(e)}",
                    "data": None
                }

    async def _on_device_state_changed(self, device_id: str, state: Dict[str, Any]) -> None:
        """
        设备状态变更回调

        Args:
            device_id: 设备ID
            state: 新状态
        """
        # 通知外部回调
        await self._notify_state_change(device_id, state)

        # 触发自动保存
        self._trigger_auto_save()

    async def _save_to_file(self) -> Dict[str, Any]:
        """
        将设备配置保存到文件（内部方法）

        执行流程：
        1. 获取所有设备数据
        2. 创建备份（如果文件已存在）
        3. 构建保存数据
        4. 写入文件
        5. 返回保存结果

        Returns:
            保存结果
        """
        try:
            # 获取所有设备
            devices = await self._mcp_adapter.get_all_devices()

            # 如果文件已存在，先创建备份
            if os.path.exists(self._config_file):
                await self._create_backup()

            # 构建保存数据
            save_data = {
                "version": "1.0.0",
                "last_saved": datetime.now().isoformat(),
                "device_count": len(devices),
                "devices": [device.to_dict() for device in devices]
            }

            # 转换为JSON字符串
            content = json.dumps(save_data, ensure_ascii=False, indent=2)

            # 写入文件
            result = await self._file_mcp.create_file_async(
                file_path=self._config_file,
                content=content,
                overwrite=True
            )

            if result.startswith("错误:"):
                logger.error(f"保存配置文件失败: {result}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"保存失败: {result}",
                    "data": None
                }

            logger.info(f"设备配置已保存到文件: {self._config_file}，共 {len(devices)} 个设备")
            return {
                "success": True,
                "code": 200,
                "message": "配置保存成功",
                "data": {"device_count": len(devices)}
            }

        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"保存失败: {str(e)}",
                "data": None
            }

    # ========== CRUD 操作 ==========

    async def create_device(self, device_type: str, device_id: str, device_name: str,
                           auto_save: bool = True) -> Dict[str, Any]:
        """
        创建设备

        执行流程：
        1. 验证设备类型
        2. 通过MCP适配器注册设备
        3. 自动保存到文件（可选）

        Args:
            device_type: 设备类型
            device_id: 设备唯一标识
            device_name: 设备名称
            auto_save: 是否自动保存到文件

        Returns:
            操作结果
        """
        async with self._lock:
            # 注册设备
            result = await self._mcp_adapter.register_device(device_type, device_id, device_name)

            if result.get("success") and auto_save:
                # 自动保存
                await self._save_to_file()

            return result

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备信息

        Args:
            device_id: 设备唯一标识

        Returns:
            设备信息
        """
        device_model = await self._mcp_adapter.get_device_model(device_id)

        if not device_model:
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
            "data": device_model.to_dict()
        }

    async def get_all_devices(self) -> Dict[str, Any]:
        """
        获取所有设备

        Returns:
            所有设备列表
        """
        devices = await self._mcp_adapter.get_all_devices()

        return {
            "success": True,
            "code": 200,
            "message": f"共 {len(devices)} 个设备",
            "data": [device.to_dict() for device in devices]
        }

    async def update_device(self, device_id: str, updates: Dict[str, Any],
                           auto_save: bool = True) -> Dict[str, Any]:
        """
        更新设备信息

        Args:
            device_id: 设备唯一标识
            updates: 更新字段字典
            auto_save: 是否自动保存到文件

        Returns:
            操作结果
        """
        async with self._lock:
            device_model = await self._mcp_adapter.get_device_model(device_id)

            if not device_model:
                return {
                    "success": False,
                    "code": 404,
                    "message": f"设备 '{device_id}' 不存在",
                    "data": None
                }

            # 更新设备名称
            if "device_name" in updates:
                device_model.device_name = updates["device_name"]
                device_model.last_updated = datetime.now()

            # 更新设备状态
            if "current_state" in updates:
                result = await self._mcp_adapter.sync_device_state(device_id, updates["current_state"])
                if not result.get("success"):
                    return result

            # 自动保存
            if auto_save:
                await self._save_to_file()

            return {
                "success": True,
                "code": 200,
                "message": "设备更新成功",
                "data": device_model.to_dict()
            }

    async def delete_device(self, device_id: str, auto_save: bool = True) -> Dict[str, Any]:
        """
        删除设备

        Args:
            device_id: 设备唯一标识
            auto_save: 是否自动保存到文件

        Returns:
            操作结果
        """
        async with self._lock:
            result = await self._mcp_adapter.unregister_device(device_id)

            if result.get("success") and auto_save:
                await self._save_to_file()

            return result

    # ========== 设备控制操作 ==========

    async def execute_command(self, device_id: str, command: str,
                             params: Dict[str, Any] = None,
                             auto_save: bool = True) -> Dict[str, Any]:
        """
        执行设备命令

        Args:
            device_id: 设备唯一标识
            command: 命令名称
            params: 命令参数
            auto_save: 是否自动保存到文件

        Returns:
            执行结果
        """
        params = params or {}

        result = await self._mcp_adapter.execute_command(device_id, command, params)

        if result.get("success") and auto_save:
            # 异步保存，不阻塞返回
            asyncio.create_task(self._save_to_file())

        return result

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备状态

        Args:
            device_id: 设备唯一标识

        Returns:
            设备状态
        """
        return await self._mcp_adapter.get_device_status(device_id)

    async def sync_device_state(self, device_id: str, state: Dict[str, Any],
                               auto_save: bool = True) -> Dict[str, Any]:
        """
        同步设备状态

        Args:
            device_id: 设备唯一标识
            state: 状态字典
            auto_save: 是否自动保存到文件

        Returns:
            同步结果
        """
        result = await self._mcp_adapter.sync_device_state(device_id, state)

        if result.get("success") and auto_save:
            asyncio.create_task(self._save_to_file())

        return result

    # ========== 批量操作 ==========

    async def batch_execute(self, device_ids: List[str], command: str,
                           params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        批量执行命令

        Args:
            device_ids: 设备ID列表
            command: 命令名称
            params: 命令参数

        Returns:
            批量执行结果
        """
        params = params or {}
        results = {}

        for device_id in device_ids:
            result = await self.execute_command(device_id, command, params, auto_save=False)
            results[device_id] = result

        # 批量保存
        await self._save_to_file()

        success_count = sum(1 for r in results.values() if r.get("success"))

        return {
            "success": True,
            "code": 200,
            "message": f"批量执行完成，成功 {success_count}/{len(device_ids)}",
            "data": results
        }

    async def scene_execute(self, scene_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scene_config: 场景配置
                {
                    "scene_name": "回家模式",
                    "actions": [
                        {"device_id": "lamp_1", "command": "turn_on", "params": {}},
                        {"device_id": "ac_1", "command": "set_temperature", "params": {"temperature": 26}},
                    ]
                }

        Returns:
            场景执行结果
        """
        scene_name = scene_config.get("scene_name", "未命名场景")
        actions = scene_config.get("actions", [])

        results = []
        for action in actions:
            device_id = action.get("device_id")
            command = action.get("command")
            params = action.get("params", {})

            if device_id and command:
                result = await self.execute_command(device_id, command, params, auto_save=False)
                results.append({
                    "device_id": device_id,
                    "command": command,
                    "result": result
                })

        # 保存所有变更
        await self._save_to_file()

        success_count = sum(1 for r in results if r["result"].get("success"))

        return {
            "success": True,
            "code": 200,
            "message": f"场景 '{scene_name}' 执行完成，成功 {success_count}/{len(actions)}",
            "data": {
                "scene_name": scene_name,
                "results": results
            }
        }

    # ========== 搜索和过滤 ==========

    async def search_devices(self, device_type: str = None,
                            keyword: str = None) -> Dict[str, Any]:
        """
        搜索设备

        Args:
            device_type: 设备类型过滤
            keyword: 关键词过滤

        Returns:
            搜索结果
        """
        devices = await self._mcp_adapter.get_all_devices()
        results = []

        for device in devices:
            # 按类型过滤
            if device_type and device.device_type.value != device_type:
                continue

            # 按关键词过滤
            if keyword and keyword.lower() not in device.device_name.lower():
                continue

            results.append(device.to_dict())

        return {
            "success": True,
            "code": 200,
            "message": f"找到 {len(results)} 个设备",
            "data": results
        }

    async def get_devices_by_type(self, device_type: str) -> Dict[str, Any]:
        """
        按类型获取设备

        Args:
            device_type: 设备类型

        Returns:
            设备列表
        """
        return await self.search_devices(device_type=device_type)

    # ========== 配置管理 ==========

    async def save_config(self) -> Dict[str, Any]:
        """
        手动保存配置到文件

        Returns:
            保存结果
        """
        async with self._lock:
            return await self._save_to_file()

    async def load_config(self) -> Dict[str, Any]:
        """
        手动从文件加载配置

        Returns:
            加载结果
        """
        async with self._lock:
            return await self.initialize()

    async def export_config(self, export_path: str) -> Dict[str, Any]:
        """
        导出配置到指定路径

        Args:
            export_path: 导出文件路径

        Returns:
            导出结果
        """
        try:
            # 获取所有设备
            devices = await self._mcp_adapter.get_all_devices()

            # 构建导出数据
            export_data = {
                "version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "devices": [device.to_dict() for device in devices]
            }

            # 转换为JSON字符串
            content = json.dumps(export_data, ensure_ascii=False, indent=2)

            # 写入文件
            result = await self._file_mcp.create_file_async(
                file_path=export_path,
                content=content,
                overwrite=True
            )

            if result.startswith("错误:"):
                return {
                    "success": False,
                    "code": 500,
                    "message": f"导出失败: {result}",
                    "data": None
                }

            return {
                "success": True,
                "code": 200,
                "message": f"配置已导出到: {export_path}",
                "data": {"export_path": export_path, "device_count": len(devices)}
            }

        except Exception as e:
            logger.error(f"导出配置失败: {str(e)}")
            return {
                "success": False,
                "code": 500,
                "message": f"导出失败: {str(e)}",
                "data": None
            }

    async def import_config(self, import_path: str,
                           merge: bool = False) -> Dict[str, Any]:
        """
        从文件导入配置

        Args:
            import_path: 导入文件路径
            merge: 是否合并（True=合并，False=覆盖）

        Returns:
            导入结果
        """
        async with self._lock:
            try:
                # 读取文件
                content = await self._file_mcp.read_file_async(import_path)

                if content.startswith("错误:"):
                    return {
                        "success": False,
                        "code": 400,
                        "message": f"读取导入文件失败: {content}",
                        "data": None
                    }

                # 解析JSON
                import_data = json.loads(content)

                if not merge:
                    # 清空现有设备
                    devices = await self._mcp_adapter.get_all_devices()
                    for device in devices:
                        await self._mcp_adapter.unregister_device(device.device_id)

                # 导入设备
                imported_count = 0
                for device_data in import_data.get("devices", []):
                    try:
                        result = await self._mcp_adapter.register_device(
                            device_type=device_data["device_type"],
                            device_id=device_data["device_id"],
                            device_name=device_data["device_name"]
                        )

                        if result.get("success"):
                            # 恢复设备状态
                            if "current_state" in device_data:
                                await self._mcp_adapter.sync_device_state(
                                    device_data["device_id"],
                                    device_data["current_state"]
                                )
                            imported_count += 1

                    except Exception as e:
                        logger.error(f"导入设备失败: {str(e)}")

                # 保存到配置文件
                await self._save_to_file()

                return {
                    "success": True,
                    "code": 200,
                    "message": f"成功导入 {imported_count} 个设备",
                    "data": {"imported_devices": imported_count}
                }

            except Exception as e:
                logger.error(f"导入配置失败: {str(e)}")
                return {
                    "success": False,
                    "code": 500,
                    "message": f"导入失败: {str(e)}",
                    "data": None
                }

    # ========== 辅助方法 ==========

    def get_supported_device_types(self) -> List[Dict[str, str]]:
        """
        获取支持的设备类型

        Returns:
            设备类型列表
        """
        return self._mcp_adapter.get_device_types()

    async def get_supported_commands(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备支持的命令

        Args:
            device_id: 设备ID

        Returns:
            支持的命令列表
        """
        return await self._mcp_adapter.get_supported_commands(device_id)

    def register_state_change_callback(self, callback) -> None:
        """
        注册状态变更回调

        Args:
            callback: 回调函数
        """
        self._mcp_adapter.register_state_change_callback(callback)

    def unregister_state_change_callback(self, callback) -> None:
        """
        注销状态变更回调

        Args:
            callback: 回调函数
        """
        self._mcp_adapter.unregister_state_change_callback(callback)


# 创建设备管理器实例
device_manager = DeviceManager()
