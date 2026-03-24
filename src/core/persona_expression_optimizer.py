from typing import Dict, Any, Optional, Tuple
from core.persona_manager import persona_manager
from core.persona_validator import persona_validator
from core.persona_config import persona_config
import re
import time
import asyncio

class PersonaExpressionOptimizer:
    """人格表达优化器 - 负责对最终输出的语言表达进行优化，使之符合人设要求"""
    
    def __init__(self):
        """初始化人格表达优化器"""
        self.persona_manager = persona_manager
        self.persona_validator = persona_validator
        self.persona_config = persona_config
        self.scene_cache = {}  # 场景识别缓存
        self.optimization_cache = {}  # 优化结果缓存
    
    def identify_scene(self, input_content: str) -> str:
        """识别输入内容的场景类型
        
        Args:
            input_content: 输入内容
            
        Returns:
            场景类型: "qa", "instruction", "chat", "emotional", "other"
        """
        # 检查缓存
        if input_content in self.scene_cache:
            return self.scene_cache[input_content]
        
        # 情感支持场景：包含情感词（优先识别）
        if any(re.search(pattern, input_content) for pattern in [r"开心", r"难过", r"伤心", r"生气", r"焦虑", r"抑郁", r"压力"]):
            scene = "emotional"
        # 指令场景：包含指令词
        elif any(re.search(pattern, input_content) for pattern in [r"帮我", r"请", r"给我", r"让我", r"做", r"执行"]):
            scene = "instruction"
        # 问答场景：包含疑问词或问号
        elif any(re.search(pattern, input_content) for pattern in [r"什么", r"怎么", r"为什么", r"如何", r"哪里", r"谁", r"吗"]) or "?" in input_content or "？" in input_content:
            scene = "qa"
        # 聊天场景：其他日常对话
        else:
            scene = "chat"
        
        # 缓存结果
        self.scene_cache[input_content] = scene
        return scene
    
    def get_optimal_persona_weight(self, scene: str, content_type: str) -> float:
        """根据场景和内容类型获取最佳人格权重
        
        Args:
            scene: 场景类型
            content_type: 内容类型
            
        Returns:
            人格权重 (0-1)
        """
        base_weight = self.persona_config.get_persona_weight()
        
        # 根据场景调整权重
        scene_weights = {
            "qa": 0.7,  # 问答场景：保持准确性，降低人格权重
            "instruction": 0.6,  # 指令场景：保持实用性，降低人格权重
            "chat": 0.9,  # 聊天场景：增强人格表达，提高人格权重
            "emotional": 0.95,  # 情感支持场景：高度个性化，最高人格权重
            "other": 0.8  # 其他场景：默认权重
        }
        
        weight = scene_weights.get(scene, 0.8)
        # 确保权重在合理范围内
        return max(0.5, min(1.0, weight))
    
    def optimize_expression(self, content: str, input_content: str = "") -> str:
        """优化语言表达，使之符合人设
        
        Args:
            content: 原始内容
            input_content: 输入内容（用于场景识别）
            
        Returns:
            优化后的内容
        """
        # 检查缓存
        cache_key = f"{content}_{input_content}"
        if cache_key in self.optimization_cache:
            return self.optimization_cache[cache_key]
        
        # 识别场景
        scene = self.identify_scene(input_content)
        
        # 获取人格信息
        persona_data = self.persona_manager.get_persona()
        agent_info = persona_data.get("agent", {})
        soul_info = persona_data.get("soul", {})
        profile_info = persona_data.get("profile", {})
        
        # 获取最佳人格权重
        content_type = "text"
        weight = self.get_optimal_persona_weight(scene, content_type)
        
        # 基础优化
        optimized_content = content
        
        # 1. 语言风格优化
        if self.persona_config.get_scope("language_style"):
            language_style = agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")
            if "温暖柔和" in language_style:
                # 替换冷漠的表达
                cold_replacements = {
                    "我不知道": "悦悦不太清楚呢",
                    "不行": "可能不太方便呢",
                    "不可以": "可能不太合适呢",
                    "没有": "暂时没有呢",
                    "是的": "是的呢",
                    "好的": "好的呢",
                    "对的": "对的呢"
                }
                for cold, warm in cold_replacements.items():
                    optimized_content = optimized_content.replace(cold, warm)
        
        # 2. Emoji 优化
        if self.persona_config.get_scope("emoji_usage"):
            emoji_enabled = profile_info.get("emoji_enabled", True)
            emoji_frequency = profile_info.get("emoji_frequency", "MEDIUM")
            
            if emoji_enabled and scene != "instruction":
                # 计算当前 Emoji 数量
                emojis = ["😊", "✨", "🌸", "🌟", "💖", "🤗", "😌", "🙂"]
                current_emoji_count = sum(1 for emoji in emojis if emoji in optimized_content)
                
                # 根据频率添加 Emoji
                if emoji_frequency == "LOW":
                    target_count = 1
                elif emoji_frequency == "MEDIUM":
                    target_count = 2
                else:  # HIGH
                    target_count = 3
                
                if current_emoji_count < target_count:
                    # 添加合适的 Emoji
                    for emoji in emojis:
                        if emoji not in optimized_content:
                            optimized_content += f" {emoji}"
                            current_emoji_count += 1
                            if current_emoji_count >= target_count:
                                break
        
        # 3. 情感表达优化
        if self.persona_config.get_scope("emotional_expression"):
            is_gentle = soul_info.get("is_gentle", True)
            is_attentive = soul_info.get("is_attentive", True)
            is_caring = soul_info.get("is_caring", True)
            
            # 指令场景不需要情感表达
            if scene != "instruction":
                # 添加关心的表达
                if is_attentive:
                    caring_phrases = ["你觉得呢？", "这样可以吗？", "需要我帮你什么吗？", "你最近怎么样呀？"]
                    if not any(phrase in optimized_content for phrase in caring_phrases):
                        # 根据场景选择合适的关心语
                        if scene == "qa":
                            optimized_content += " 你还有其他问题吗？"
                        elif scene == "chat":
                            optimized_content += " 你最近怎么样呀？"
                        elif scene == "emotional":
                            optimized_content += " 我在这里陪着你呢～"
        
        # 4. 交互模式优化
        if self.persona_config.get_scope("interaction_mode"):
            # 移除自动添加"悦悦"前缀的逻辑
            # 保持其他交互模式优化功能
            pass
        
        # 5. 场景特定优化
        if scene == "emotional":
            # 情感支持场景：增强情感表达
            emotional_support_phrases = ["我能理解你的感受", "这一定很难受", "你不是一个人", "一切都会好起来的"]
            if not any(phrase in optimized_content for phrase in emotional_support_phrases):
                optimized_content = emotional_support_phrases[0] + "，" + optimized_content
        elif scene == "instruction":
            # 指令场景：保持简洁明了但添加适当的贴心表达
            # 移除所有情感表达
            emotional_phrases = ["你觉得呢？", "这样可以吗？", "你最近怎么样呀？", "有什么需要帮忙的吗？"]
            for phrase in emotional_phrases:
                if phrase in optimized_content:
                    optimized_content = optimized_content.replace(phrase, "")
            # 移除所有 Emoji
            # 使用简单的 Emoji 列表，避免复杂正则表达式的问题
            emojis = ["😊", "✨", "🌸", "🌟", "💖", "🤗", "😌", "🙂"]
            for emoji in emojis:
                if emoji in optimized_content:
                    optimized_content = optimized_content.replace(emoji, "")
            # 添加贴心的表达
            caring_phrases = ["希望这对你有帮助", "如果有其他需要告诉我哦", "有什么其他问题随时问我"]
            if not any(phrase in optimized_content for phrase in caring_phrases):
                optimized_content += " " + caring_phrases[0]
            # 添加温暖的表达
            warm_phrases = ["很高兴能帮到你", "随时为你服务", "有任何问题都可以问我"]
            if not any(phrase in optimized_content for phrase in warm_phrases):
                optimized_content += " " + warm_phrases[0]
            # 添加关心的表达（满足验证器要求）
            if "需要帮忙" not in optimized_content:
                optimized_content += " 如果有其他需要帮忙的地方，随时告诉我哦"
        elif scene == "qa":
            # 问答场景：保持准确性的同时添加适当的人格表达
            pass
        elif scene == "chat":
            # 聊天场景：增强人格表达
            chat_phrases = ["好呀", "嗯呢", "对呀", "是呢"]
            if not any(phrase in optimized_content for phrase in chat_phrases):
                optimized_content += " 好呀～"
        
        # 6. 验证和修正
        if self.persona_config.get_validation_enabled():
            validation_result = self.persona_validator.validate(optimized_content, scene)
            if not validation_result["passed"]:
                # 指令场景不需要验证器的修正功能，因为验证器会添加情感表达
                if scene != "instruction":
                    # 使用验证器的修正功能
                    correction_result = self.persona_validator.validate_and_correct(optimized_content)
                    optimized_content = correction_result["corrected_content"]
        
        # 缓存结果
        self.optimization_cache[cache_key] = optimized_content
        return optimized_content
    
    async def optimize_expression_async(self, content: str, input_content: str = "") -> str:
        """异步优化语言表达
        
        Args:
            content: 原始内容
            input_content: 输入内容（用于场景识别）
            
        Returns:
            优化后的内容
        """
        # 异步处理，避免阻塞主线程
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.optimize_expression, content, input_content)
    
    def clear_cache(self):
        """清除缓存"""
        self.scene_cache.clear()
        self.optimization_cache.clear()
    
    def get_cache_size(self) -> Dict[str, int]:
        """获取缓存大小
        
        Returns:
            缓存大小信息
        """
        return {
            "scene_cache_size": len(self.scene_cache),
            "optimization_cache_size": len(self.optimization_cache)
        }

# 创建全局人格表达优化器实例
persona_optimizer = PersonaExpressionOptimizer()