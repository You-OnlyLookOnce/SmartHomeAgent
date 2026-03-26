"""
通知服务模块

实现设备状态变更通知机制，将状态变化通知给智能体
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DeviceStatusNotification:
    """
    设备状态变更通知
    
    Attributes:
        device_id: 设备唯一标识
        device_name: 设备名称
        device_type: 设备类型
        previous_state: 变更前状态
        current_state: 变更后状态
        timestamp: 通知时间
        change_type: 变更类型 ("status", "error", "warning")
    """
    device_id: str
    device_name: str
    device_type: str
    previous_state: Dict[str, Any]
    current_state: Dict[str, Any]
    timestamp: datetime = None
    change_type: str = "status"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class NotificationService:
    """
    通知服务类
    
    负责管理设备状态变更通知，将通知发送给智能体
    """
    
    def __init__(self):
        """初始化通知服务"""
        # 通知回调函数列表
        self._notification_callbacks: List[Callable[[DeviceStatusNotification], None]] = []
        # 通知队列
        self._notification_queue: asyncio.Queue[DeviceStatusNotification] = asyncio.Queue()
        # 工作任务
        self._worker_task: asyncio.Task = None
        # 运行状态
        self._running = False
        logger.info("通知服务初始化完成")
    
    async def start(self):
        """启动通知服务"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_notifications())
            logger.info("通知服务已启动")
    
    async def stop(self):
        """停止通知服务"""
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("通知服务已停止")
    
    async def _process_notifications(self):
        """处理通知队列"""
        while self._running:
            try:
                notification = await self._notification_queue.get()
                await self._dispatch_notification(notification)
                self._notification_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理通知失败: {str(e)}")
    
    async def _dispatch_notification(self, notification: DeviceStatusNotification):
        """分发通知给所有回调函数"""
        for callback in self._notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"通知回调执行失败: {str(e)}")
    
    async def send_notification(self, notification: DeviceStatusNotification):
        """
        发送通知
        
        Args:
            notification: 设备状态变更通知
        """
        await self._notification_queue.put(notification)
        logger.debug(f"通知已加入队列 - 设备: {notification.device_id}, 类型: {notification.change_type}")
    
    def register_callback(self, callback: Callable[[DeviceStatusNotification], None]):
        """
        注册通知回调函数
        
        Args:
            callback: 通知回调函数，接收DeviceStatusNotification参数
        """
        if callback not in self._notification_callbacks:
            self._notification_callbacks.append(callback)
            logger.info(f"通知回调已注册，当前回调数量: {len(self._notification_callbacks)}")
    
    def unregister_callback(self, callback: Callable[[DeviceStatusNotification], None]):
        """
        注销通知回调函数
        
        Args:
            callback: 通知回调函数
        """
        if callback in self._notification_callbacks:
            self._notification_callbacks.remove(callback)
            logger.info(f"通知回调已注销，当前回调数量: {len(self._notification_callbacks)}")
    
    async def create_device_status_notification(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        previous_state: Dict[str, Any],
        current_state: Dict[str, Any],
        change_type: str = "status"
    ) -> DeviceStatusNotification:
        """
        创建设备状态变更通知
        
        Args:
            device_id: 设备唯一标识
            device_name: 设备名称
            device_type: 设备类型
            previous_state: 变更前状态
            current_state: 变更后状态
            change_type: 变更类型
        
        Returns:
            设备状态变更通知对象
        """
        notification = DeviceStatusNotification(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            previous_state=previous_state,
            current_state=current_state,
            change_type=change_type
        )
        await self.send_notification(notification)
        return notification

# 创建通知服务实例
notification_service = NotificationService()

# 启动通知服务
async def start_notification_service():
    """启动通知服务"""
    await notification_service.start()

# 停止通知服务
async def stop_notification_service():
    """停止通知服务"""
    await notification_service.stop()