from typing import List, Dict, Any
import time
import uuid

class ExecutionMemory:
    """执行记忆模块 - 作为MCP工具调用的"操作日志本"
    
    详细记录每一步MCP工具调用的完整信息（包括调用参数、返回结果、执行状态等），
    并实时反馈给LLM以确认操作执行成功与否。
    """
    
    def __init__(self):
        """初始化执行记忆模块"""
        self.executions = {}
        self.last_updated = time.time()
    
    def add_execution(self, session_id: str, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """添加工具执行记录
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            parameters: 工具调用参数
            result: 工具执行结果
        """
        if session_id not in self.executions:
            self.executions[session_id] = []
        
        execution = {
            "execution_id": f"exec_{uuid.uuid4().hex[:8]}",
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "timestamp": time.time(),
            "status": "success" if result.get("success", False) else "failed"
        }
        
        self.executions[session_id].append(execution)
        self.last_updated = time.time()
        return execution["execution_id"]
    
    def get_executions(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有执行记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话的所有执行记录
        """
        if session_id in self.executions:
            return self.executions[session_id]
        return []
    
    def get_last_n_executions(self, session_id: str, n: int) -> List[Dict[str, Any]]:
        """获取会话的最后n条执行记录
        
        Args:
            session_id: 会话ID
            n: 记录数量
            
        Returns:
            会话的最后n条执行记录
        """
        if session_id in self.executions:
            return self.executions[session_id][-n:]
        return []
    
    def delete_executions(self, session_id: str):
        """删除会话的执行记录
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.executions:
            del self.executions[session_id]
            self.last_updated = time.time()
    
    def clear(self):
        """清空执行记忆"""
        self.executions.clear()
        self.last_updated = time.time()
    
    def get_last_updated(self) -> float:
        """获取最后更新时间
        
        Returns:
            最后更新时间戳
        """
        return self.last_updated
    
    def get_session_ids(self) -> List[str]:
        """获取所有会话ID
        
        Returns:
            所有会话ID
        """
        return list(self.executions.keys())
