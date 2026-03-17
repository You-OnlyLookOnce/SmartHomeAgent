from typing import Dict, List, Callable
import asyncio
import time
import json

class AgentProtocol:
    """Agent通信协议 - 定义Agent间的消息格式和通信规则"""
    
    def __init__(self):
        self.message_handlers = {}
        self.message_queue = asyncio.Queue()
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, from_agent: str, to_agent: str, message_type: str, content: Dict):
        """发送消息到指定Agent"""
        message = {
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content,
            "timestamp": time.time(),
            "message_id": self._generate_message_id()
        }
        
        await self.message_queue.put(message)
        return message
    
    async def broadcast_message(self, from_agent: str, message_type: str, content: Dict):
        """广播消息到所有Agent"""
        message = {
            "from": from_agent,
            "to": "broadcast",
            "type": message_type,
            "content": content,
            "timestamp": time.time(),
            "message_id": self._generate_message_id()
        }
        
        await self.message_queue.put(message)
        return message
    
    async def process_messages(self):
        """处理消息队列"""
        while True:
            message = await self.message_queue.get()
            
            # 路由消息到目标Agent
            if message["to"] == "broadcast":
                await self._handle_broadcast(message)
            else:
                await self._handle_direct_message(message)
    
    async def _handle_direct_message(self, message: Dict):
        """处理直接消息"""
        handler = self.message_handlers.get(message["type"])
        if handler:
            await handler(message)
    
    async def _handle_broadcast(self, message: Dict):
        """处理广播消息"""
        handler = self.message_handlers.get(message["type"])
        if handler:
            await handler(message)
    
    def _generate_message_id(self) -> str:
        """生成消息ID"""
        return f"msg_{int(time.time() * 1000)}_{hash(str(time.time()))}"