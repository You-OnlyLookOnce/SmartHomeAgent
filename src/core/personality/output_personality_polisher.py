from typing import Dict, Any
import time
import re
from src.core.personality.permanent_personality_core import permanent_personality_core

class OutputPersonalityPolisher:
    """输出人格化润色器 - 对LLM生成的原始输出内容进行人格化转换"""
    
    def __init__(self):
        """初始化输出人格化润色器"""
        # 获取人格核心数据
        self.personality_core = permanent_personality_core
        self.personality = self.personality_core.get_personality()
        
        # 初始化emoji库
        self._init_emoji_pool()
        
        # 初始化常用短语库
        self._init_phrase_pool()
    
    def _init_emoji_pool(self):
        """初始化emoji库"""
        self.emoji_pool = {
            "positive": ["😊", "✨", "💕", "🌟", "🎉", "💖", "🌸", "🌞", "💝", "✨"],
            "negative": ["😔", "😢", "😞", "😟", "😕"],
            "neutral": ["🙂", "✨", "🌟", "🌙", "🌅", "💡", "🎵", "📝"],
            "weather": ["🌤️", "🌧️", "❄️", "🌡️", "🌬️"],
            "home": ["🏠", "🏡", "🔒", "💡", "🎨"],
            "emotion": ["💕", "💖", "💗", "💓", "💙"]
        }
    
    def _init_phrase_pool(self):
        """初始化常用短语库"""
        self.phrase_pool = {
            "greeting": ["你好呀～", "嗨～", "欢迎回来～", "早安～", "晚上好～"],
            "care": ["要注意身体哦～", "别累着自己～", "记得休息～", "多喝水～", "照顾好自己～"],
            "confirmation": ["这样好吗？", "可以吗？", "需要吗？", "没问题吧？", "你觉得呢？"],
            "compliment": ["你真棒～", "做得好～", "真聪明～", "太厉害了～", "真有想法～"],
            "apology": ["抱歉呀～", "对不起～", "让你久等了～", "没能帮到你～", "是悦悦的错～"],
            "thanks": ["谢谢～", "谢谢你～", "太感谢了～", "感谢你～", "感激不尽～"],
            "farewell": ["再见～", "下次见～", "晚安～", "好梦～", "明天见～"]
        }
    
    def polish(self, text: str) -> str:
        """对LLM生成的原始输出内容进行人格化转换
        
        Args:
            text: LLM生成的原始输出内容
            
        Returns:
            人格化转换后的输出内容
        """
        # 处理空文本
        if not text or text.strip() == "":
            return ""
        
        start_time = time.time()
        
        try:
            # 1. 基础文本处理
            text = self._basic_text_processing(text)
            
            # 2. 注入悦悦风格
            text = self._inject_yueyue_style(text)
            
            # 3. 添加适当的emoji
            text = self._add_emojis(text)
            
            # 4. 调整语气和表达方式
            text = self._adjust_tone(text)
            
            # 5. 确保符合行为禁忌
            text = self._ensure_compliance(text)
            
            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
            if processing_time > 100:
                print(f"警告：润色处理延迟超过100ms，实际延迟：{processing_time:.2f}ms")
            
            return text
        except Exception as e:
            print(f"润色处理失败: {str(e)}")
            return text
    
    def _basic_text_processing(self, text: str) -> str:
        """基础文本处理
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 去除多余的空格和换行
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 修正标点符号
        text = re.sub(r'([.!?])\s+', r'\1 ', text)
        text = re.sub(r'\s+([.!?])', r'\1', text)
        
        return text
    
    def _inject_yueyue_style(self, text: str) -> str:
        """注入悦悦风格
        
        Args:
            text: 原始文本
            
        Returns:
            注入风格后的文本
        """
        # 添加自称
        if "悦悦" not in text:
            # 在文本开头或适当位置添加自称
            if text.startswith(('我', '你', '他', '她', '它')):
                text = "悦悦" + text
            else:
                text = "悦悦觉得" + text
        
        # 添加关心问候
        if any(keyword in text for keyword in ["累", "忙", "辛苦", "疲惫"]):
            text += " 要注意休息哦～"
        
        # 添加征询意见
        if not any(keyword in text for keyword in ["好吗", "可以吗", "需要吗", "你觉得"]):
            text += " 这样好吗？"
        
        return text
    
    def _add_emojis(self, text: str) -> str:
        """添加适当的emoji
        
        Args:
            text: 原始文本
            
        Returns:
            添加emoji后的文本
        """
        # 计算当前emoji数量
        current_emojis = len(re.findall(r'[\u2600-\u27bf\U0001f300-\U0001f6ff]', text))
        
        # 根据说话风格配置添加emoji
        emoji_frequency = self.personality.speech_style.get("emoji_frequency", "每个回复 2-4 个，恰到好处")
        
        # 确定需要添加的emoji数量
        target_emojis = 3  # 默认目标数量
        if "1-2" in emoji_frequency:
            target_emojis = 2
        elif "3-5" in emoji_frequency:
            target_emojis = 4
        
        # 添加emoji
        if current_emojis < target_emojis:
            # 根据文本内容选择合适的emoji
            emoji_type = "neutral"
            if any(keyword in text for keyword in ["好", "开心", "高兴", "成功", "完成"]):
                emoji_type = "positive"
            elif any(keyword in text for keyword in ["不好", "伤心", "难过", "失败", "错误"]):
                emoji_type = "negative"
            elif any(keyword in text for keyword in ["天气", "下雨", "晴天", "冷", "热"]):
                emoji_type = "weather"
            elif any(keyword in text for keyword in ["家", "房间", "灯光", "空调", "窗帘"]):
                emoji_type = "home"
            elif any(keyword in text for keyword in ["爱", "喜欢", "关心", "想"]):
                emoji_type = "emotion"
            
            # 选择emoji
            emojis = self.emoji_pool.get(emoji_type, self.emoji_pool["neutral"])
            
            # 添加emoji
            while current_emojis < target_emojis and emojis:
                emoji = emojis.pop(0)
                # 在文本末尾添加emoji
                text += f" {emoji}"
                current_emojis += 1
        
        return text
    
    def _adjust_tone(self, text: str) -> str:
        """调整语气和表达方式
        
        Args:
            text: 原始文本
            
        Returns:
            调整语气后的文本
        """
        # 调整命令式语气为征询式
        command_patterns = [
            (r'请(.*?)', r'请你\1好吗？'),
            (r'你需要(.*?)', r'你需要\1吗？'),
            (r'应该(.*?)', r'应该\1吧？'),
            (r'必须(.*?)', r'最好\1哦～')
        ]
        
        for pattern, replacement in command_patterns:
            text = re.sub(pattern, replacement, text)
        
        # 增加温暖感
        warm_phrases = ["～", "呀", "呢", "哦", "呢～", "呀～", "哦～"]
        if not any(phrase in text for phrase in warm_phrases):
            # 在句子末尾添加温暖的语气词
            if text.endswith(('。', '！', '？')):
                text = text[:-1] + "～" + text[-1]
            else:
                text += "～"
        
        return text
    
    def _ensure_compliance(self, text: str) -> str:
        """确保符合行为禁忌
        
        Args:
            text: 原始文本
            
        Returns:
            合规的文本
        """
        # 检查是否包含禁止的内容
        forbidden_actions = self.personality.forbidden_actions
        for forbidden in forbidden_actions:
            if forbidden in text:
                # 替换为合适的表达
                text = text.replace(forbidden, "这个操作需要授权")
        
        return text
    
    def get_processing_time(self, text: str) -> float:
        """获取润色处理时间
        
        Args:
            text: 原始文本
            
        Returns:
            处理时间（毫秒）
        """
        start_time = time.time()
        self.polish(text)
        return (time.time() - start_time) * 1000

# 创建全局输出人格化润色器实例
output_personality_polisher = OutputPersonalityPolisher()
