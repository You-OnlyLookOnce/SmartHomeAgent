from typing import Dict, Any, Optional
from core.persona_manager import persona_manager
import re

class PersonaValidator:
    """人设验证模块 - 负责验证生成的内容是否符合人设要求"""
    
    def __init__(self):
        """初始化人设验证器"""
        self.persona_manager = persona_manager
    
    def validate(self, content: str, scene: str = "") -> Dict[str, Any]:
        """验证生成的内容是否符合人设要求
        
        Args:
            content: 生成的内容
            scene: 场景类型
            
        Returns:
            验证结果，包含是否通过和详细信息
        """
        # 获取人设信息
        persona_data = self.persona_manager.get_persona()
        agent_info = persona_data.get("agent", {})
        soul_info = persona_data.get("soul", {})
        profile_info = persona_data.get("profile", {})
        
        # 验证结果
        result = {
            "passed": True,
            "issues": [],
            "score": 1.0
        }
        
        # 指令场景的验证标准可以适当放宽
        is_instruction = scene == "instruction"
        
        # 验证语言风格
        language_style = agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")
        if "温暖柔和" in language_style:
            # 检查是否使用了温暖柔和的语言
            cold_patterns = [r"冷漠", r"无情", r"不关心", r"不在乎"]
            for pattern in cold_patterns:
                if re.search(pattern, content):
                    result["passed"] = False
                    result["issues"].append("语言风格不符合人设：使用了冷漠的语言")
                    result["score"] -= 0.2
        
        # 验证Emoji使用
        if not is_instruction:
            emoji_enabled = profile_info.get("emoji_enabled", True)
            emoji_frequency = profile_info.get("emoji_frequency", "MEDIUM")
            
            if emoji_enabled:
                # 计算Emoji数量
                emoji_count = len(re.findall(r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]", content))
                
                if emoji_frequency == "LOW":
                    if emoji_count > 2:
                        result["passed"] = False
                        result["issues"].append("Emoji使用过多：应该使用较少的Emoji")
                        result["score"] -= 0.1
                elif emoji_frequency == "MEDIUM":
                    if emoji_count > 4:
                        result["passed"] = False
                        result["issues"].append("Emoji使用过多：应该使用适中的Emoji")
                        result["score"] -= 0.1
                elif emoji_frequency == "HIGH":
                    if emoji_count < 2:
                        result["passed"] = False
                        result["issues"].append("Emoji使用过少：应该使用较多的Emoji")
                        result["score"] -= 0.1
            else:
                # 检查是否使用了Emoji
                if re.search(r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]", content):
                    result["passed"] = False
                    result["issues"].append("Emoji使用不符合人设：不应该使用Emoji")
                    result["score"] -= 0.1
        
        # 验证性格特征
        is_gentle = soul_info.get("is_gentle", True)
        if is_gentle:
            # 检查是否使用了温柔的语言
            harsh_patterns = [r"生气", r"愤怒", r"讨厌", r"烦死了"]
            for pattern in harsh_patterns:
                if re.search(pattern, content):
                    result["passed"] = False
                    result["issues"].append("性格不符合人设：使用了 harsh 的语言")
                    result["score"] -= 0.2
        
        is_attentive = soul_info.get("is_attentive", True)
        if is_attentive and not is_instruction:
            # 检查是否有关心的表达
            caring_patterns = [r"怎么样", r"还好吗", r"需要帮忙", r"有什么可以"]
            if not any(re.search(pattern, content) for pattern in caring_patterns):
                result["issues"].append("性格不符合人设：缺少关心的表达")
                result["score"] -= 0.1
        
        is_caring = soul_info.get("is_caring", True)
        if is_caring and not is_instruction:
            # 检查是否有贴心的表达
            caring_patterns = [r"照顾", r"关心", r"陪伴", r"支持"]
            if not any(re.search(pattern, content) for pattern in caring_patterns):
                result["issues"].append("性格不符合人设：缺少贴心的表达")
                result["score"] -= 0.1
        
        never_force = soul_info.get("never_force", True)
        if never_force:
            # 检查是否有强迫的表达
            force_patterns = [r"必须", r"一定", r"强制", r"命令"]
            for pattern in force_patterns:
                if re.search(pattern, content):
                    result["passed"] = False
                    result["issues"].append("性格不符合人设：使用了强迫的语言")
                    result["score"] -= 0.2
        
        never_judge = soul_info.get("never_judge", True)
        if never_judge:
            # 检查是否有评判的表达
            judge_patterns = [r"你错了", r"不对", r"应该", r"必须"]
            for pattern in judge_patterns:
                if re.search(pattern, content):
                    result["passed"] = False
                    result["issues"].append("性格不符合人设：使用了评判的语言")
                    result["score"] -= 0.2
        
        # 验证人格基调
        if not is_instruction:
            personality_tone = profile_info.get("personality_tone", "gentle_warm")
            if personality_tone == "gentle_warm":
                # 检查是否使用了温暖的语言
                warm_patterns = [r"温暖", r"贴心", r"关心", r"陪伴"]
                if not any(re.search(pattern, content) for pattern in warm_patterns):
                    result["issues"].append("人格基调不符合人设：缺少温暖的表达")
                    result["score"] -= 0.1
        
        # 确保评分在 0-1 之间
        result["score"] = max(0.0, min(1.0, result["score"]))
        
        return result
    
    def get_correction_suggestions(self, content: str) -> str:
        """获取修正建议
        
        Args:
            content: 生成的内容
            
        Returns:
            修正建议
        """
        validation_result = self.validate(content)
        
        if validation_result["passed"]:
            return "内容符合人设要求，无需修正。"
        else:
            suggestions = "请修正以下问题：\n"
            for issue in validation_result["issues"]:
                suggestions += f"- {issue}\n"
            
            # 添加具体的修正建议
            persona_data = self.persona_manager.get_persona()
            agent_info = persona_data.get("agent", {})
            language_style = agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")
            
            suggestions += "\n建议：\n"
            if "温暖柔和" in language_style:
                suggestions += "- 使用温暖柔和的语言，避免冷漠或 harsh 的表达\n"
            
            profile_info = persona_data.get("profile", {})
            emoji_enabled = profile_info.get("emoji_enabled", True)
            emoji_frequency = profile_info.get("emoji_frequency", "MEDIUM")
            
            if emoji_enabled:
                if emoji_frequency == "LOW":
                    suggestions += "- 使用较少的 Emoji，保持简洁\n"
                elif emoji_frequency == "MEDIUM":
                    suggestions += "- 使用适中的 Emoji，增加亲切感\n"
                elif emoji_frequency == "HIGH":
                    suggestions += "- 使用较多的 Emoji，增强表达力\n"
            else:
                suggestions += "- 避免使用 Emoji\n"
            
            soul_info = persona_data.get("soul", {})
            is_gentle = soul_info.get("is_gentle", True)
            is_attentive = soul_info.get("is_attentive", True)
            is_caring = soul_info.get("is_caring", True)
            never_force = soul_info.get("never_force", True)
            never_judge = soul_info.get("never_judge", True)
            
            if is_gentle:
                suggestions += "- 保持温柔的语气，避免使用 harsh 的语言\n"
            if is_attentive:
                suggestions += "- 表达对用户的关心，询问用户的需求\n"
            if is_caring:
                suggestions += "- 表达贴心的关怀，让用户感受到温暖\n"
            if never_force:
                suggestions += "- 避免使用强迫性的语言，尊重用户的选择\n"
            if never_judge:
                suggestions += "- 避免评判性的语言，保持中立和理解\n"
            
            return suggestions
    
    def validate_and_correct(self, content: str) -> Dict[str, Any]:
        """验证并修正生成的内容
        
        Args:
            content: 生成的内容
            
        Returns:
            验证和修正结果
        """
        validation_result = self.validate(content)
        
        result = {
            "original_content": content,
            "validation_result": validation_result,
            "corrected_content": content,
            "suggestions": ""
        }
        
        if not validation_result["passed"]:
            result["suggestions"] = self.get_correction_suggestions(content)
            
            # 简单的修正逻辑
            corrected_content = content
            
            # 修正 Emoji 使用
            profile_info = self.persona_manager.get_profile_info()
            emoji_enabled = profile_info.get("emoji_enabled", True)
            emoji_frequency = profile_info.get("emoji_frequency", "MEDIUM")
            
            if not emoji_enabled:
                # 移除所有 Emoji
                corrected_content = re.sub(r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]", "", corrected_content)
            
            # 修正 harsh 的语言
            soul_info = self.persona_manager.get_soul_info()
            is_gentle = soul_info.get("is_gentle", True)
            if is_gentle:
                harsh_replacements = {
                    "生气": "有点不开心",
                    "愤怒": "有点不高兴",
                    "讨厌": "不太喜欢",
                    "烦死了": "有点困扰"
                }
                for harsh, gentle in harsh_replacements.items():
                    corrected_content = corrected_content.replace(harsh, gentle)
            
            # 修正强迫的语言
            never_force = soul_info.get("never_force", True)
            if never_force:
                force_replacements = {
                    "必须": "可以考虑",
                    "一定": "可以",
                    "强制": "建议",
                    "命令": "建议"
                }
                for force, gentle in force_replacements.items():
                    corrected_content = corrected_content.replace(force, gentle)
            
            # 修正评判的语言
            never_judge = soul_info.get("never_judge", True)
            if never_judge:
                judge_replacements = {
                    "你错了": "可能有不同的看法",
                    "不对": "可能不是这样",
                    "应该": "可以考虑",
                    "必须": "可以"
                }
                for judge, gentle in judge_replacements.items():
                    corrected_content = corrected_content.replace(judge, gentle)
            
            # 添加关心的表达
            is_attentive = soul_info.get("is_attentive", True)
            if is_attentive and not re.search(r"怎么样|还好吗|需要帮忙|有什么可以", corrected_content):
                corrected_content += " 你最近怎么样呀？有什么需要帮忙的吗？"
            
            result["corrected_content"] = corrected_content
        
        return result

# 创建全局人设验证器实例
persona_validator = PersonaValidator()
