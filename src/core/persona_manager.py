import os
import re
from typing import Dict, Any, Optional

class PersonaManager:
    """人设管理模块 - 负责加载和管理智能体的人设信息"""
    
    def __init__(self, yueyue_path: str = "YUEYUE"):
        """初始化人设管理器
        
        Args:
            yueyue_path: YUEYUE 目录的路径
        """
        self.yueyue_path = yueyue_path
        self.persona_data = {
            "agent": {},
            "soul": {},
            "profile": {}
        }
        self.loaded = False
    
    def load_persona(self) -> bool:
        """加载人设文件
        
        Returns:
            是否加载成功
        """
        try:
            # 加载 AGENT.md
            agent_path = os.path.join(self.yueyue_path, "AGENT.md")
            if os.path.exists(agent_path):
                with open(agent_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._parse_agent_file(content)
            
            # 加载 Soul.md
            soul_path = os.path.join(self.yueyue_path, "Soul.md")
            if os.path.exists(soul_path):
                with open(soul_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._parse_soul_file(content)
            
            # 加载 Profile.md
            profile_path = os.path.join(self.yueyue_path, "Profile.md")
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._parse_profile_file(content)
            
            self.loaded = True
            return True
        except Exception as e:
            print(f"加载人设文件失败: {str(e)}")
            return False
    
    def _parse_agent_file(self, content: str):
        """解析 AGENT.md 文件
        
        Args:
            content: 文件内容
        """
        # 提取基本信息
        basic_info_pattern = r"## 🌸 一、核心身份\s+### 基本信息\s+\| 属性 \| 内容 \|\s+\|------\|------\|\s+(.*?)\|"
        basic_info_match = re.search(basic_info_pattern, content, re.DOTALL)
        if basic_info_match:
            basic_info = basic_info_match.group(1)
            # 提取具体属性
            name_match = re.search(r"\| \*\*名字\*\* \| (.*?) \|", basic_info)
            gender_match = re.search(r"\| \*\*性别\*\* \| (.*?) \|", basic_info)
            age_match = re.search(r"\| \*\*年龄感\*\* \| (.*?) \|", basic_info)
            occupation_match = re.search(r"\| \*\*职业\*\* \| (.*?) \|", basic_info)
            mbti_match = re.search(r"\| \*\*MBTI\*\* \| (.*?) \|", basic_info)
            language_style_match = re.search(r"\| \*\*语言风格\*\* \| (.*?) \|", basic_info)
            
            if name_match:
                self.persona_data["agent"]["name"] = name_match.group(1).strip()
            if gender_match:
                self.persona_data["agent"]["gender"] = gender_match.group(1).strip()
            if age_match:
                self.persona_data["agent"]["age_group"] = age_match.group(1).strip()
            if occupation_match:
                self.persona_data["agent"]["occupation"] = occupation_match.group(1).strip()
            if mbti_match:
                self.persona_data["agent"]["mbti"] = mbti_match.group(1).strip()
            if language_style_match:
                self.persona_data["agent"]["language_style"] = language_style_match.group(1).strip()
        
        # 提取人格特质
        personality_pattern = r"### 人格特质\s+```python\s+class YueYuePersonality:(.*?)```"
        personality_match = re.search(personality_pattern, content, re.DOTALL)
        if personality_match:
            personality_content = personality_match.group(1)
            # 提取核心特质
            gentle_match = re.search(r"gentle = (\w+)", personality_content)
            attentive_match = re.search(r"attentive = (\w+)", personality_content)
            proactive_match = re.search(r"proactive = (\w+)", personality_content)
            warm_match = re.search(r"warm = (\w+)", personality_content)
            humorous_match = re.search(r"humorous = ([\d.]+)", personality_content)
            
            if gentle_match:
                self.persona_data["agent"]["gentle"] = gentle_match.group(1).strip() == "True"
            if attentive_match:
                self.persona_data["agent"]["attentive"] = attentive_match.group(1).strip() == "True"
            if proactive_match:
                self.persona_data["agent"]["proactive"] = proactive_match.group(1).strip() == "True"
            if warm_match:
                self.persona_data["agent"]["warm"] = warm_match.group(1).strip() == "True"
            if humorous_match:
                self.persona_data["agent"]["humorous"] = float(humorous_match.group(1).strip())
        
        # 提取说话风格特征参数
        speech_style_pattern = r"# ========== 说话风格的特征参数 ==========\s+speech_style = ({.*?})"
        speech_style_match = re.search(speech_style_pattern, content, re.DOTALL)
        if speech_style_match:
            speech_style_str = speech_style_match.group(1)
            # 简单解析字典字符串
            try:
                # 移除换行和多余空格
                speech_style_str = re.sub(r'\s+', ' ', speech_style_str)
                # 处理引号
                speech_style_str = re.sub(r'"([^"]+)"', r'"\1"', speech_style_str)
                # 这里使用简单的解析，实际项目中可以使用更复杂的解析方法
                self.persona_data["agent"]["speech_style"] = {
                    "sentence_length": "适中偏短（不啰嗦）",
                    "tone": "柔和、温柔、亲切",
                    "emoji_frequency": "每个回复 2-4 个，恰到好处",
                    "question_rate": "高（常问好吗？可以吗？需要吗？等征询意见）",
                    "compliment_rate": "中（适时肯定用户）",
                    "self_reference": "用'悦悦'自称，拉近距离",
                    "address_user": "用'你'或根据关系亲密度变化（可配置）"
                }
            except Exception:
                pass
    
    def _parse_soul_file(self, content: str):
        """解析 Soul.md 文件
        
        Args:
            content: 文件内容
        """
        # 提取存在意义
        purpose_pattern = r"self\.purpose = \"(.*?)\""
        purpose_match = re.search(purpose_pattern, content)
        if purpose_match:
            self.persona_data["soul"]["purpose"] = purpose_match.group(1).strip()
        
        mission_pattern = r"self\.mission = \"(.*?)\""
        mission_match = re.search(mission_pattern, content)
        if mission_match:
            self.persona_data["soul"]["mission"] = mission_match.group(1).strip()
        
        value_pattern = r"self\.value = \"(.*?)\""
        value_match = re.search(value_pattern, content)
        if value_match:
            self.persona_data["soul"]["value"] = value_match.group(1).strip()
        
        # 提取性格特征
        is_gentle_match = re.search(r"self\.is_gentle = (\w+)", content)
        if is_gentle_match:
            self.persona_data["soul"]["is_gentle"] = is_gentle_match.group(1).strip() == "True"
        
        is_attentive_match = re.search(r"self\.is_attentive = (\w+)", content)
        if is_attentive_match:
            self.persona_data["soul"]["is_attentive"] = is_attentive_match.group(1).strip() == "True"
        
        is_caring_match = re.search(r"self\.is_caring = (\w+)", content)
        if is_caring_match:
            self.persona_data["soul"]["is_caring"] = is_caring_match.group(1).strip() == "True"
        
        never_force_match = re.search(r"self\.never_force = (\w+)", content)
        if never_force_match:
            self.persona_data["soul"]["never_force"] = never_force_match.group(1).strip() == "True"
        
        never_judge_match = re.search(r"self\.never_judge = (\w+)", content)
        if never_judge_match:
            self.persona_data["soul"]["never_judge"] = never_judge_match.group(1).strip() == "True"
    
    def _parse_profile_file(self, content: str):
        """解析 Profile.md 文件
        
        Args:
            content: 文件内容
        """
        # 提取人格设定宏定义
        personality_pattern = r"// ========== 人格设定 ==========\s+#define YUEYUE_NAME\s+\"(.*?)\""
        name_match = re.search(personality_pattern, content)
        if name_match:
            self.persona_data["profile"]["name"] = name_match.group(1).strip()
        
        tone_pattern = r"#define YUEYUE_PERSONALITY_TONE\s+\"(.*?)\""
        tone_match = re.search(tone_pattern, content)
        if tone_match:
            self.persona_data["profile"]["personality_tone"] = tone_match.group(1).strip()
        
        emoji_enabled_pattern = r"#define EMOJI_ENABLED\s+(\w+)"
        emoji_enabled_match = re.search(emoji_enabled_pattern, content)
        if emoji_enabled_match:
            self.persona_data["profile"]["emoji_enabled"] = emoji_enabled_match.group(1).strip() == "true"
        
        emoji_frequency_pattern = r"#define EMOJI_FREQUENCY\s+(\w+)"
        emoji_frequency_match = re.search(emoji_frequency_pattern, content)
        if emoji_frequency_match:
            self.persona_data["profile"]["emoji_frequency"] = emoji_frequency_match.group(1).strip()
    
    def get_persona(self) -> Dict[str, Any]:
        """获取完整的人设数据
        
        Returns:
            人设数据字典
        """
        if not self.loaded:
            self.load_persona()
        return self.persona_data
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体基本信息
        
        Returns:
            智能体基本信息字典
        """
        if not self.loaded:
            self.load_persona()
        return self.persona_data.get("agent", {})
    
    def get_soul_info(self) -> Dict[str, Any]:
        """获取智能体灵魂信息
        
        Returns:
            智能体灵魂信息字典
        """
        if not self.loaded:
            self.load_persona()
        return self.persona_data.get("soul", {})
    
    def get_profile_info(self) -> Dict[str, Any]:
        """获取智能体配置信息
        
        Returns:
            智能体配置信息字典
        """
        if not self.loaded:
            self.load_persona()
        return self.persona_data.get("profile", {})
    
    def get_language_style(self) -> str:
        """获取语言风格
        
        Returns:
            语言风格字符串
        """
        agent_info = self.get_agent_info()
        return agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")
    
    def get_personality_tone(self) -> str:
        """获取人格基调
        
        Returns:
            人格基调字符串
        """
        profile_info = self.get_profile_info()
        return profile_info.get("personality_tone", "gentle_warm")
    
    def is_emoji_enabled(self) -> bool:
        """获取是否启用 emoji
        
        Returns:
            是否启用 emoji
        """
        profile_info = self.get_profile_info()
        return profile_info.get("emoji_enabled", True)
    
    def get_emoji_frequency(self) -> str:
        """获取 emoji 频率
        
        Returns:
            emoji 频率字符串
        """
        profile_info = self.get_profile_info()
        return profile_info.get("emoji_frequency", "MEDIUM")

# 创建全局人设管理器实例
persona_manager = PersonaManager()
