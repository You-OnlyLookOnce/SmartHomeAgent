from typing import Dict, List, Type
import importlib
import os

class SkillManager:
    """技能管理器"""
    
    def __init__(self):
        self.skills = {}
        self._load_skills()
    
    def _load_skills(self):
        """加载所有技能"""
        # 技能目录
        skill_dirs = [
            "src/skills/core_skills",
            "src/skills/device_skills",
            "src/skills/memory_skills",
            "src/skills/search_skills",
            "src/skills/task_skills"
        ]
        
        for skill_dir in skill_dirs:
            if os.path.exists(skill_dir):
                for file in os.listdir(skill_dir):
                    if file.endswith(".py") and not file.startswith("__init__"):
                        module_name = f"src.skills.{skill_dir.split('/')[-1]}.{file[:-3]}"
                        try:
                            module = importlib.import_module(module_name)
                            # 查找技能类
                            for name, obj in module.__dict__.items():
                                if hasattr(obj, "SKILL_NAME") and hasattr(obj, "execute"):
                                    self.skills[obj.SKILL_NAME] = obj
                        except Exception as e:
                            print(f"加载技能 {module_name} 失败: {e}")
    
    def get_skill(self, skill_name: str) -> Type:
        """获取技能类"""
        return self.skills.get(skill_name)
    
    async def execute_skill(self, skill_name: str, params: Dict) -> Dict:
        """执行技能"""
        skill_class = self.get_skill(skill_name)
        if not skill_class:
            return {
                "success": False,
                "message": f"技能 {skill_name} 不存在"
            }
        
        try:
            skill = skill_class()
            result = await skill.execute(params)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"技能执行失败: {str(e)}"
            }
    
    def list_skills(self) -> List[Dict]:
        """列出所有技能"""
        skill_list = []
        for skill_name, skill_class in self.skills.items():
            skill_list.append({
                "name": skill_name,
                "description": skill_class.SKILL_DESCRIPTION,
                "version": skill_class.SKILL_VERSION,
                "input_schema": skill_class.INPUT_SCHEMA,
                "output_schema": skill_class.OUTPUT_SCHEMA
            })
        return skill_list
