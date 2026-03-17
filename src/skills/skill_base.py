from typing import Dict, Any

class SkillBase:
    """技能基类"""
    
    # 技能元信息
    SKILL_NAME = "base"
    SKILL_DESCRIPTION = "基础技能"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {}
    
    # 输出结果定义
    OUTPUT_SCHEMA = {}
    
    async def execute(self, params: Dict) -> Dict:
        """执行技能"""
        raise NotImplementedError("子类必须实现execute方法")
    
    async def log_operation(self, device_id: str, action: str, result: Dict):
        """记录操作日志"""
        # 这里可以实现日志记录逻辑
        pass
