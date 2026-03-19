from typing import Dict, List

class HallucinationDetector:
    """幻觉检测器 - ChatDev 思想"""
    
    def __init__(self):
        # 模拟设备列表
        self.devices = {
            "led_1": {"type": "light", "max_brightness": 100, "min_brightness": 0},
            "led_2": {"type": "light", "max_brightness": 100, "min_brightness": 0},
            "fan_1": {"type": "fan", "max_speed": 5, "min_speed": 0},
            "thermostat_1": {"type": "thermostat", "max_temperature": 30, "min_temperature": 16}
        }
    
    async def check_device_exists(self, device_id: str) -> bool:
        """检查设备是否存在"""
        return device_id in self.devices
    
    def validate_parameters(self, command: Dict) -> bool:
        """验证参数是否在合理范围内"""
        skill = command.get("skill")
        params = command.get("params", {})
        device_id = params.get("device_id")
        
        if not device_id or device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        
        if skill == "led_on" or skill == "led_off":
            # 这两个技能不需要额外参数验证
            return True
        elif skill == "led_brightness":
            brightness = params.get("brightness")
            if brightness is None:
                return False
            return device["min_brightness"] <= brightness <= device["max_brightness"]
        elif skill == "fan_control":
            speed = params.get("speed")
            if speed is None:
                return False
            return device["min_speed"] <= speed <= device["max_speed"]
        elif skill == "thermostat_set":
            temperature = params.get("temperature")
            if temperature is None:
                return False
            return device["min_temperature"] <= temperature <= device["max_temperature"]
        
        return True
    
    def check_api_compliance(self, command: Dict) -> bool:
        """检查命令是否符合设备API规范"""
        skill = command.get("skill")
        params = command.get("params", {})
        
        # 检查必需参数
        required_params = {
            "led_on": ["device_id"],
            "led_off": ["device_id"],
            "led_brightness": ["device_id", "brightness"],
            "fan_control": ["device_id", "speed"],
            "thermostat_set": ["device_id", "temperature"]
        }
        
        if skill in required_params:
            for param in required_params[skill]:
                if param not in params:
                    return False
        
        return True
    
    def detect_operation_conflicts(self, command: Dict) -> bool:
        """检测操作冲突"""
        # 简单的冲突检测：同一设备同时执行相反操作
        skill = command.get("skill")
        device_id = command.get("params", {}).get("device_id")
        
        # 这里可以添加更复杂的冲突检测逻辑
        # 暂时返回True，表示没有冲突
        return True
    
    async def validate_device_command(self, command: Dict) -> Dict:
        """验证设备控制命令是否可能为幻觉
        
        检查点:
        1. 设备 ID 是否真实存在？
        2. 参数是否在合理范围内？
        3. 命令是否符合该设备的 API 规范？
        4. 是否有矛盾的操作（如同时开灯和关灯）?
        """
        
        hallucination_checks = {
            "device_exists": await self.check_device_exists(command.get("params", {}).get("device_id")),
            "parameters_valid": self.validate_parameters(command),
            "api_conformant": self.check_api_compliance(command),
            "no_conflict": self.detect_operation_conflicts(command)
        }
        
        issues = []
        for check_name, passed in hallucination_checks.items():
            if not passed:
                issues.append(f"幻觉检测失败：{check_name}")
        
        if issues:
            return {
                "valid": False,
                "issues": issues,
                "suggested_alternatives": self.suggest_fixes(command, issues)
            }
        
        return {"valid": True}
    
    def suggest_fixes(self, command: Dict, issues: List[str]) -> List[str]:
        """为检测到的问题提供修复建议"""
        suggestions = []
        
        if "幻觉检测失败：device_exists" in issues:
            suggestions.append(f"请使用有效的设备ID，可用设备：{list(self.devices.keys())}")
        
        if "幻觉检测失败：parameters_valid" in issues:
            skill = command.get("skill")
            device_id = command.get("params", {}).get("device_id")
            if device_id and device_id in self.devices:
                device = self.devices[device_id]
                if skill == "led_brightness":
                    suggestions.append(f"亮度应在 {device['min_brightness']}-{device['max_brightness']} 之间")
                elif skill == "fan_control":
                    suggestions.append(f"风速应在 {device['min_speed']}-{device['max_speed']} 之间")
                elif skill == "thermostat_set":
                    suggestions.append(f"温度应在 {device['min_temperature']}-{device['max_temperature']} 之间")
        
        if "幻觉检测失败：api_conformant" in issues:
            skill = command.get("skill")
            required_params = {
                "led_on": ["device_id"],
                "led_off": ["device_id"],
                "led_brightness": ["device_id", "brightness"],
                "fan_control": ["device_id", "speed"],
                "thermostat_set": ["device_id", "temperature"]
            }
            if skill in required_params:
                suggestions.append(f"{skill} 需要参数：{required_params[skill]}")
        
        return suggestions