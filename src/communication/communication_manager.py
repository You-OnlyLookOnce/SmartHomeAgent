import json
import asyncio
from typing import Dict, Optional, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommunicationManager:
    """通信管理器 - 负责模块间的消息传递"""
    
    def __init__(self):
        """初始化通信管理器"""
        self.message_queue = asyncio.Queue()
        self.subscribers = {}
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息
        
        Args:
            message: 消息内容，包含以下字段：
                - type: 消息类型
                - sender: 发送者
                - receiver: 接收者
                - data: 消息数据
                - timestamp: 时间戳
        """
        logger.info(f"发送消息: {message}")
        await self.message_queue.put(message)
    
    async def receive_message(self) -> Dict[str, Any]:
        """接收消息"""
        message = await self.message_queue.get()
        logger.info(f"接收消息: {message}")
        return message
    
    def subscribe(self, module_name: str, callback: callable):
        """订阅消息
        
        Args:
            module_name: 模块名称
            callback: 回调函数，当接收到消息时调用
        """
        if module_name not in self.subscribers:
            self.subscribers[module_name] = []
        self.subscribers[module_name].append(callback)
        logger.info(f"模块 {module_name} 订阅了消息")
    
    def unsubscribe(self, module_name: str, callback: callable):
        """取消订阅
        
        Args:
            module_name: 模块名称
            callback: 回调函数
        """
        if module_name in self.subscribers:
            self.subscribers[module_name].remove(callback)
            logger.info(f"模块 {module_name} 取消了订阅")
    
    async def process_messages(self):
        """处理消息队列"""
        while True:
            message = await self.receive_message()
            receiver = message.get("receiver")
            if receiver in self.subscribers:
                for callback in self.subscribers[receiver]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"处理消息时出错: {e}")
            else:
                logger.warning(f"没有模块订阅接收者: {receiver}")
    
    async def request_response(self, message: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """发送请求并等待响应
        
        Args:
            message: 请求消息
            timeout: 超时时间（秒）
            
        Returns:
            响应消息
        """
        # 生成请求ID
        request_id = f"req_{id(message)}"
        message["request_id"] = request_id
        
        # 创建响应事件
        response_event = asyncio.Event()
        response = None
        
        # 定义响应回调
        def response_callback(msg):
            nonlocal response, response_event
            if msg.get("request_id") == request_id:
                response = msg
                response_event.set()
        
        # 订阅响应
        self.subscribe(message.get("receiver"), response_callback)
        
        try:
            # 发送请求
            await self.send_message(message)
            # 等待响应
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {message}")
            return None
        finally:
            # 取消订阅
            self.unsubscribe(message.get("receiver"), response_callback)

class Message:
    """消息类"""
    
    @staticmethod
    def create_message(message_type: str, sender: str, receiver: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消息
        
        Args:
            message_type: 消息类型
            sender: 发送者
            receiver: 接收者
            data: 消息数据
            
        Returns:
            消息字典
        """
        import time
        return {
            "type": message_type,
            "sender": sender,
            "receiver": receiver,
            "data": data,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_request(message_type: str, sender: str, receiver: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建请求消息
        
        Args:
            message_type: 消息类型
            sender: 发送者
            receiver: 接收者
            data: 消息数据
            
        Returns:
            请求消息字典
        """
        message = Message.create_message(message_type, sender, receiver, data)
        message["request_id"] = f"req_{id(message)}"
        return message
    
    @staticmethod
    def create_response(request: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """创建响应消息
        
        Args:
            request: 请求消息
            data: 响应数据
            
        Returns:
            响应消息字典
        """
        import time
        return {
            "type": "response",
            "sender": request.get("receiver"),
            "receiver": request.get("sender"),
            "data": data,
            "request_id": request.get("request_id"),
            "timestamp": time.time()
        }

# 全局通信管理器实例
communication_manager = CommunicationManager()
