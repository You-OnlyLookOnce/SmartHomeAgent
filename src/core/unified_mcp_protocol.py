from typing import Dict, List, Any, Optional, Union, Callable
import json
import time
import uuid
import logging

class UnifiedMCPProtocol:
    """统一MCP协议 - 定义统一的管理控制程序协议规范"""
    
    # 协议版本
    PROTOCOL_VERSION = "1.0.0"
    
    # 错误码定义
    ERROR_CODES = {
        "SUCCESS": 0,              # 成功
        "INVALID_PARAMS": 1001,    # 参数无效
        "PERMISSION_DENIED": 1002, # 权限不足
        "RESOURCE_NOT_FOUND": 1003, # 资源不存在
        "INTERNAL_ERROR": 1004,    # 内部错误
        "NETWORK_ERROR": 1005,     # 网络错误
        "TIMEOUT": 1006,           # 超时
        "UNSUPPORTED_OPERATION": 1007, # 不支持的操作
    }
    
    # 操作类型
    OPERATION_TYPES = {
        "READ": "read",            # 读取操作
        "CREATE": "create",        # 创建操作
        "UPDATE": "update",        # 更新操作
        "DELETE": "delete",        # 删除操作
        "SEARCH": "search",        # 搜索操作
        "EXECUTE": "execute",      # 执行操作
    }
    
    # 响应状态
    RESPONSE_STATUS = {
        "SUCCESS": "success",      # 成功
        "ERROR": "error",          # 错误
    }
    
    @staticmethod
    def create_request(operation: str, params: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建MCP请求
        
        Args:
            operation: 操作类型
            params: 操作参数
            request_id: 请求ID，如不提供则自动生成
            
        Returns:
            请求字典
        """
        return {
            "request_id": request_id or str(uuid.uuid4()),
            "protocol_version": UnifiedMCPProtocol.PROTOCOL_VERSION,
            "operation": operation,
            "params": params,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def create_response(request_id: str, status: str, data: Any = None, error_code: int = 0, error_message: str = "") -> Dict[str, Any]:
        """创建MCP响应
        
        Args:
            request_id: 请求ID
            status: 响应状态
            data: 响应数据
            error_code: 错误码
            error_message: 错误信息
            
        Returns:
            响应字典
        """
        return {
            "request_id": request_id,
            "protocol_version": UnifiedMCPProtocol.PROTOCOL_VERSION,
            "status": status,
            "data": data,
            "error_code": error_code,
            "error_message": error_message,
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
    def validate_request(request: Dict[str, Any]) -> bool:
        """验证请求格式
        
        Args:
            request: 请求字典
            
        Returns:
            是否为有效的请求
        """
        required_fields = ["request_id", "protocol_version", "operation", "params", "timestamp"]
        for field in required_fields:
            if field not in request:
                return False
        return True
    
    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        """验证响应格式
        
        Args:
            response: 响应字典
            
        Returns:
            是否为有效的响应
        """
        required_fields = ["request_id", "protocol_version", "status", "data", "error_code", "error_message", "timestamp"]
        for field in required_fields:
            if field not in response:
                return False
        return True
    
    @staticmethod
    def create_error_response(request_id: str, error_code: int, error_message: str) -> Dict[str, Any]:
        """创建错误响应
        
        Args:
            request_id: 请求ID
            error_code: 错误码
            error_message: 错误信息
            
        Returns:
            错误响应字典
        """
        return UnifiedMCPProtocol.create_response(
            request_id=request_id,
            status=UnifiedMCPProtocol.RESPONSE_STATUS["ERROR"],
            data=None,
            error_code=error_code,
            error_message=error_message
        )
    
    @staticmethod
    def create_success_response(request_id: str, data: Any = None) -> Dict[str, Any]:
        """创建成功响应
        
        Args:
            request_id: 请求ID
            data: 响应数据
            
        Returns:
            成功响应字典
        """
        return UnifiedMCPProtocol.create_response(
            request_id=request_id,
            status=UnifiedMCPProtocol.RESPONSE_STATUS["SUCCESS"],
            data=data,
            error_code=UnifiedMCPProtocol.ERROR_CODES["SUCCESS"],
            error_message=""
        )

class MCPBase:
    """MCP基类 - 所有MCP实现的基类"""
    
    def __init__(self):
        """初始化MCP"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} 初始化完成")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求
        
        Args:
            request: 请求字典
            
        Returns:
            响应字典
        """
        try:
            # 验证请求格式
            if not UnifiedMCPProtocol.validate_request(request):
                return UnifiedMCPProtocol.create_error_response(
                    request_id=request.get("request_id", str(uuid.uuid4())),
                    error_code=UnifiedMCPProtocol.ERROR_CODES["INVALID_PARAMS"],
                    error_message="无效的请求格式"
                )
            
            # 处理具体操作
            operation = request.get("operation")
            params = request.get("params", {})
            request_id = request.get("request_id")
            
            # 调用具体操作处理方法
            if hasattr(self, f"handle_{operation}"):
                handler = getattr(self, f"handle_{operation}")
                data = await handler(params)
                return UnifiedMCPProtocol.create_success_response(request_id, data)
            else:
                return UnifiedMCPProtocol.create_error_response(
                    request_id=request_id,
                    error_code=UnifiedMCPProtocol.ERROR_CODES["UNSUPPORTED_OPERATION"],
                    error_message=f"不支持的操作: {operation}"
                )
        except Exception as e:
            self.logger.error(f"处理请求失败: {str(e)}")
            return UnifiedMCPProtocol.create_error_response(
                request_id=request.get("request_id", str(uuid.uuid4())),
                error_code=UnifiedMCPProtocol.ERROR_CODES["INTERNAL_ERROR"],
                error_message=f"内部错误: {str(e)}"
            )
    
    async def handle_read(self, params: Dict[str, Any]) -> Any:
        """处理读取操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_read方法")
    
    async def handle_create(self, params: Dict[str, Any]) -> Any:
        """处理创建操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_create方法")
    
    async def handle_update(self, params: Dict[str, Any]) -> Any:
        """处理更新操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_update方法")
    
    async def handle_delete(self, params: Dict[str, Any]) -> Any:
        """处理删除操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_delete方法")
    
    async def handle_search(self, params: Dict[str, Any]) -> Any:
        """处理搜索操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_search方法")
    
    async def handle_execute(self, params: Dict[str, Any]) -> Any:
        """处理执行操作
        
        Args:
            params: 操作参数
            
        Returns:
            操作结果
        """
        raise NotImplementedError("子类必须实现handle_execute方法")