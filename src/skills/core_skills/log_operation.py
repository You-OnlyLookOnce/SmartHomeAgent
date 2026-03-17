from src.skills.skill_base import SkillBase
from typing import Dict
import time
import os

class LogOperationSkill(SkillBase):
    """操作日志技能"""
    
    # 技能元信息
    SKILL_NAME = "log_operation"
    SKILL_DESCRIPTION = "记录操作日志"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "device_id": {"type": "string", "required": True},
        "action": {"type": "string", "required": True},
        "result": {"type": "dict", "default": {}}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "log_path": "string"
    }
    
    def __init__(self):
        # 确保日志目录存在
        self.log_dir = "data/logs"
        os.makedirs(self.log_dir, exist_ok=True)
    
    async def execute(self, params: Dict) -> Dict:
        device_id = params["device_id"]
        action = params["action"]
        result = params.get("result", {})
        
        # 生成日志内容
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Device: {device_id}, Action: {action}, Result: {result}\n"
        
        # 写入日志文件
        log_file = os.path.join(self.log_dir, f"{time.strftime('%Y-%m-%d')}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        return {
            "success": True,
            "message": "操作日志记录成功",
            "log_path": log_file
        }
    
    async def log_operation(self, device_id: str, action: str, result: Dict):
        """记录操作日志（重写基类方法）"""
        await self.execute({"device_id": device_id, "action": action, "result": result})
