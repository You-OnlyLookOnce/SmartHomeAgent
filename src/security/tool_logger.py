import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ToolLogger:
    """工具调用日志系统"""
    
    def __init__(self, log_file: str = "tool_calls.log"):
        """初始化工具日志系统
        
        Args:
            log_file: 日志文件路径
        """
        # 配置日志
        self.logger = logging.getLogger("ToolLogger")
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_tool_call(self, tool_name: str, params: Dict[str, Any], result: Any, status: str = "success"):
        """记录工具调用
        
        Args:
            tool_name: 工具名称
            params: 调用参数
            result: 调用结果
            status: 调用状态 (success/failure)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "params": params,
            "result": str(result)[:1000],  # 限制结果长度
            "status": status
        }
        
        # 记录日志
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_error(self, tool_name: str, params: Dict[str, Any], error: str):
        """记录工具调用错误
        
        Args:
            tool_name: 工具名称
            params: 调用参数
            error: 错误信息
        """
        self.log_tool_call(tool_name, params, error, "failure")
    
    def get_latest_logs(self, count: int = 10) -> list:
        """获取最新的日志记录
        
        Args:
            count: 日志条数
            
        Returns:
            日志记录列表
        """
        try:
            with open("tool_calls.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                latest_logs = []
                for line in reversed(lines):
                    if len(latest_logs) >= count:
                        break
                    try:
                        # 提取JSON部分
                        if " - ToolLogger - INFO - " in line:
                            json_str = line.split(" - ToolLogger - INFO - ")[1].strip()
                            log_entry = json.loads(json_str)
                            latest_logs.append(log_entry)
                    except Exception:
                        pass
                return list(reversed(latest_logs))
        except Exception as e:
            self.logger.error(f"读取日志失败: {str(e)}")
            return []

# 创建全局工具日志实例
tool_logger = ToolLogger()
