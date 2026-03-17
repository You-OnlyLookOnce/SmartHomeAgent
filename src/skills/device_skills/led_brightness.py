from src.skills.skill_base import SkillBase
from typing import Dict

class LedBrightnessSkill(SkillBase):
    """LED亮度调节技能"""
    
    # 技能元信息
    SKILL_NAME = "led_brightness"
    SKILL_DESCRIPTION = "调节LED灯亮度"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "device_id": {"type": "string", "required": True},
        "brightness": {"type": "int", "required": True, "range": [0, 100]}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "device_state": "dict"
    }
    
    async def execute(self, params: Dict) -> Dict:
        device_id = params["device_id"]
        brightness = params["brightness"]
        
        # 1. 调用串口控制器
        # 实际实现时需要连接到真实的硬件控制器
        result = {
            "status": "ok",
            "state": {
                "device_id": device_id,
                "status": "on" if brightness > 0 else "off",
                "brightness": brightness
            }
        }
        
        # 2. 记录日志
        await self.log_operation(device_id, "led_brightness", result)
        
        # 3. 返回结果
        return {
            "success": result["status"] == "ok",
            "message": f"已将灯 {device_id} 亮度调整为 {brightness}%",
            "device_state": result.get("state", {})
        }
