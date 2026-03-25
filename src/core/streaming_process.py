# 流式过程数据结构定义

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class StreamingProcess:
    """流式过程基类"""
    def __init__(self, process_type: str, content: str, timestamp: Optional[datetime] = None):
        self.process_type = process_type
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.process_id = f"{process_type}-{int(self.timestamp.timestamp() * 1000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.process_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "process_id": self.process_id
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            process_type=data.get("type"),
            content=data.get("content"),
            timestamp=timestamp
        )

class ThinkingProcess(StreamingProcess):
    """思考过程"""
    def __init__(self, content: str, depth: int = 1, timestamp: Optional[datetime] = None):
        super().__init__("thinking", content, timestamp)
        self.depth = depth
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict["depth"] = self.depth
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThinkingProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            depth=data.get("depth", 1),
            timestamp=timestamp
        )

class SearchProcess(StreamingProcess):
    """搜索过程"""
    def __init__(self, content: str, search_query: str, search_type: str = "web", 
                 status: str = "searching", results: Optional[List[Dict[str, Any]]] = None, 
                 timestamp: Optional[datetime] = None):
        super().__init__("searching", content, timestamp)
        self.search_query = search_query
        self.search_type = search_type
        self.status = status  # searching, completed, failed
        self.results = results or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "search_query": self.search_query,
            "search_type": self.search_type,
            "status": self.status,
            "results": self.results
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            search_query=data.get("search_query"),
            search_type=data.get("search_type", "web"),
            status=data.get("status", "searching"),
            results=data.get("results", []),
            timestamp=timestamp
        )

class ToolCallProcess(StreamingProcess):
    """工具调用过程"""
    def __init__(self, content: str, tool_name: str, parameters: Dict[str, Any], 
                 status: str = "calling", result: Optional[Any] = None, 
                 timestamp: Optional[datetime] = None):
        super().__init__("mcp_tool", content, timestamp)
        self.tool_name = tool_name
        self.parameters = parameters
        self.status = status  # calling, completed, failed
        self.result = result
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCallProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            tool_name=data.get("tool_name"),
            parameters=data.get("parameters", {}),
            status=data.get("status", "calling"),
            result=data.get("result"),
            timestamp=timestamp
        )

class AnalysisProcess(StreamingProcess):
    """分析过程"""
    def __init__(self, content: str, analysis_type: str = "general", 
                 timestamp: Optional[datetime] = None):
        super().__init__("analysis", content, timestamp)
        self.analysis_type = analysis_type
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict["analysis_type"] = self.analysis_type
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            analysis_type=data.get("analysis_type", "general"),
            timestamp=timestamp
        )

class AnswerProcess(StreamingProcess):
    """回答过程"""
    def __init__(self, content: str, is_complete: bool = False, 
                 timestamp: Optional[datetime] = None):
        super().__init__("answer", content, timestamp)
        self.is_complete = is_complete
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict["is_complete"] = self.is_complete
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnswerProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            is_complete=data.get("is_complete", False),
            timestamp=timestamp
        )

class ErrorProcess(StreamingProcess):
    """错误过程"""
    def __init__(self, content: str, error_code: str = "UNKNOWN_ERROR", 
                 timestamp: Optional[datetime] = None):
        super().__init__("error", content, timestamp)
        self.error_code = error_code
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict["error_code"] = self.error_code
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(
            content=data.get("content"),
            error_code=data.get("error_code", "UNKNOWN_ERROR"),
            timestamp=timestamp
        )

class StreamEndProcess(StreamingProcess):
    """流结束过程"""
    def __init__(self, timestamp: Optional[datetime] = None):
        super().__init__("stream_end", "", timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamEndProcess':
        """从字典创建实例"""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()
        return cls(timestamp=timestamp)

# 工厂函数，根据类型创建对应的过程实例
def create_process(process_type: str, **kwargs) -> StreamingProcess:
    """根据类型创建对应的过程实例"""
    process_classes = {
        "thinking": ThinkingProcess,
        "searching": SearchProcess,
        "mcp_tool": ToolCallProcess,
        "analysis": AnalysisProcess,
        "answer": AnswerProcess,
        "error": ErrorProcess,
        "stream_end": StreamEndProcess
    }
    
    if process_type not in process_classes:
        raise ValueError(f"Unknown process type: {process_type}")
    
    return process_classes[process_type](**kwargs)

# 从字典创建过程实例
def process_from_dict(data: Dict[str, Any]) -> StreamingProcess:
    """从字典创建过程实例"""
    process_type = data.get("type")
    return create_process(process_type, **data)
