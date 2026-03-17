from src.skills.skill_base import SkillBase
from typing import Dict

class LedOffSkill(SkillBase):
    """关灯技能"""
    
    # 技能元信息
    SKILL_NAME = "led_off"
    SKILL_DESCRIPTION = "关闭指定LED灯"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "device_id": {"type": "string", "required": True}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "device_state": "dict"
    }
    
    async def execute(self, params: Dict) -> Dict:
        device_id = params["device_id"]
        
        # 1. 调用串口控制器
        # 实际实现时需要连接到真实的硬件控制器
        result = {
            "status": "ok",
            "state": {
                "device_id": device_id,
                "status": "off",
                "brightness": 0
            }
        }
        
        # 2. 记录日志
        await self.log_operation(device_id, "led_off", result)
        
        # 3. 返回结果
        return {
            "success": result["status"] == "ok",
            "message": f"已关闭灯 {device_id}",
            "device_state": result.get("state", {})
        }
