from typing import Dict, List, Any, Optional
import json
import time
import uuid
from src.core.unified_mcp_protocol import UnifiedMCPProtocol

class ModuleCommunicationProtocol:
    """模块间通信协议 - 定义模块之间的通信标准"""
    
    # 事件类型
    EVENT_TYPES = {
        "TASK_TRIGGERED": "task.triggered",  # 定时任务触发
        "TASK_COMPLETED": "task.completed",  # 定时任务完成
        "MEMO_CREATED": "memo.created",  # 备忘录创建
        "MEMO_UPDATED": "memo.updated",  # 备忘录更新
        "MEMO_DELETED": "memo.deleted",  # 备忘录删除
        "MCP_TOOL_CALL": "mcp.tool_call",  # MCP工具调用
        "MCP_TOOL_RESPONSE": "mcp.tool_response",  # MCP工具响应
        "AGENT_RESPONSE": "agent.response",  # 智能体响应
        "DATA_SYNC": "data.sync",  # 数据同步
    }
    
    @staticmethod
    def create_message(event_type: str, data: Dict[str, Any], sender: str, recipient: str) -> Dict[str, Any]:
        """创建通信消息
        
        Args:
            event_type: 事件类型
            data: 消息数据
            sender: 发送者模块
            recipient: 接收者模块
            
        Returns:
            消息字典
        """
        return {
            "message_id": str(uuid.uuid4()),
            "event_type": event_type,
            "data": data,
            "sender": sender,
            "recipient": recipient,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def serialize_message(message: Dict[str, Any]) -> str:
        """序列化消息
        
        Args:
            message: 消息字典
            
        Returns:
            序列化后的消息字符串
        """
        return json.dumps(message, ensure_ascii=False)
    
    @staticmethod
    def deserialize_message(message_str: str) -> Dict[str, Any]:
        """反序列化消息
        
        Args:
            message_str: 序列化后的消息字符串
            
        Returns:
            消息字典
        """
        return json.loads(message_str)
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """验证消息格式
        
        Args:
            message: 消息字典
            
        Returns:
            是否为有效的消息
        """
        required_fields = ["message_id", "event_type", "data", "sender", "recipient", "timestamp"]
        for field in required_fields:
            if field not in message:
                return False
        return True
    
    @staticmethod
    def create_mcp_tool_call_message(action: str, params: Dict[str, Any], sender: str, recipient: str) -> Dict[str, Any]:
        """创建MCP工具调用消息
        
        Args:
            action: 操作类型
            params: 操作参数
            sender: 发送者模块
            recipient: 接收者模块
            
        Returns:
            消息字典
        """
        # 创建MCP请求
        mcp_request = UnifiedMCPProtocol.create_request(action, params)
        
        # 创建模块间通信消息
        return ModuleCommunicationProtocol.create_message(
            event_type=ModuleCommunicationProtocol.EVENT_TYPES["MCP_TOOL_CALL"],
            data={
                "mcp_request": mcp_request
            },
            sender=sender,
            recipient=recipient
        )
    
    @staticmethod
    def create_mcp_tool_response_message(request_id: str, status: str, data: Any = None, error_code: int = 0, error_message: str = "", sender: str = "", recipient: str = "") -> Dict[str, Any]:
        """创建MCP工具响应消息
        
        Args:
            request_id: 请求ID
            status: 响应状态
            data: 响应数据
            error_code: 错误码
            error_message: 错误信息
            sender: 发送者模块
            recipient: 接收者模块
            
        Returns:
            消息字典
        """
        # 创建MCP响应
        mcp_response = UnifiedMCPProtocol.create_response(
            request_id=request_id,
            status=status,
            data=data,
            error_code=error_code,
            error_message=error_message
        )
        
        # 创建模块间通信消息
        return ModuleCommunicationProtocol.create_message(
            event_type=ModuleCommunicationProtocol.EVENT_TYPES["MCP_TOOL_RESPONSE"],
            data={
                "mcp_response": mcp_response
            },
            sender=sender,
            recipient=recipient
        )

class MessageBroker:
    """消息代理 - 处理模块之间的消息传递"""
    
    def __init__(self):
        """初始化消息代理"""
        self.subscribers = {}
    
    def subscribe(self, event_type: str, callback: callable, module: str):
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            module: 模块名称
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append((callback, module))
    
    def unsubscribe(self, event_type: str, module: str):
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            module: 模块名称
        """
        if event_type in self.subscribers:
            self.subscribers[event_type] = [(callback, m) for callback, m in self.subscribers[event_type] if m != module]
    
    def publish(self, message: Dict[str, Any]):
        """发布消息
        
        Args:
            message: 消息字典
        """
        if not ModuleCommunicationProtocol.validate_message(message):
            print(f"无效的消息格式: {message}")
            return
        
        event_type = message["event_type"]
        if event_type in self.subscribers:
            for callback, module in self.subscribers[event_type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"模块 {module} 处理消息失败: {e}")

# 创建消息代理实例
message_broker = MessageBroker()
