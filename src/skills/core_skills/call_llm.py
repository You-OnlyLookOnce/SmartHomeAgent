from src.skills.skill_base import SkillBase
from src.agent.model_router import ModelRouter
from typing import Dict

class CallLLMSkill(SkillBase):
    """调用大模型技能"""
    
    # 技能元信息
    SKILL_NAME = "call_llm"
    SKILL_DESCRIPTION = "调用大模型"
    SKILL_VERSION = "1.0.0"
    
    # 输入参数定义
    INPUT_SCHEMA = {
        "prompt": {"type": "string", "required": True},
        "task_type": {"type": "string", "default": "简单任务"},
        "max_tokens": {"type": "int", "default": 512}
    }
    
    # 输出结果定义
    OUTPUT_SCHEMA = {
        "success": "bool",
        "message": "string",
        "response": "string"
    }
    
    def __init__(self):
        self.router = ModelRouter()
    
    async def execute(self, params: Dict) -> Dict:
        prompt = params["prompt"]
        task_type = params.get("task_type", "简单任务")
        max_tokens = params.get("max_tokens", 512)
        
        # 构建任务信息
        task = {
            "type": task_type,
            "content": prompt,
            "max_tokens": max_tokens
        }
        
        # 调用模型
        response = await self.router.call(prompt, task)
        
        return {
            "success": True,
            "message": "模型调用成功",
            "response": response
        }
