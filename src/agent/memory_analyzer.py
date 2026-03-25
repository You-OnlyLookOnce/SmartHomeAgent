from typing import Dict, Any, List, Tuple
import re
import json
from ai.qiniu_llm import QiniuLLM

class MemoryAnalyzer:
    """记忆分析器 - 负责识别和分类对话中的用户信息"""
    
    def __init__(self):
        """初始化记忆分析器"""
        self.llm = QiniuLLM()
        
        # 规则匹配的关键词
        self.keywords = {
            'values': ['价值观', '信念', '原则', '底线', '信仰', '理想', '目标', '追求'],
            'preferences': ['喜欢', '偏好', '希望', '想要', '需要', '不要', '讨厌', '反感'],
            'background': ['背景', '经历', '学历', '工作', '职业', '经验', '历史', '过去'],
            'project': ['项目', '计划', '任务', '目标', '工作', '学习', '研究', '开发']
        }
        
        # 置信度阈值
        self.confidence_threshold = 0.59
    
    def analyze_message(self, message: str) -> List[Dict[str, Any]]:
        """分析消息中的用户信息
        
        Args:
            message: 用户消息
            
        Returns:
            识别到的信息列表，每个元素包含类型、内容和置信度
        """
        results = []
        
        # Layer 1: 规则匹配
        rule_based_results = self._rule_based_analysis(message)
        results.extend(rule_based_results)
        
        # Layer 2: LLM分析（针对低置信度或复杂情况）
        if not rule_based_results or any(r['confidence'] < 0.7 for r in rule_based_results):
            llm_results = self._llm_based_analysis(message)
            results.extend(llm_results)
        
        return results
    
    def _rule_based_analysis(self, message: str) -> List[Dict[str, Any]]:
        """基于规则的分析
        
        Args:
            message: 用户消息
            
        Returns:
            识别到的信息列表
        """
        results = []
        
        # 检查每种类型的关键词
        for info_type, type_keywords in self.keywords.items():
            for keyword in type_keywords:
                if keyword in message:
                    # 提取包含关键词的句子
                    sentences = message.split('。')
                    for sentence in sentences:
                        if keyword in sentence:
                            # 计算置信度（基于关键词出现频率和位置）
                            confidence = self._calculate_confidence(sentence, keyword, info_type)
                            
                            results.append({
                                'type': info_type,
                                'content': sentence.strip(),
                                'confidence': confidence,
                                'method': 'rule'
                            })
                            break
        
        return results
    
    def _llm_based_analysis(self, message: str) -> List[Dict[str, Any]]:
        """基于LLM的分析
        
        Args:
            message: 用户消息
            
        Returns:
            识别到的信息列表
        """
        try:
            prompt = f"""请分析以下用户消息，识别其中是否包含用户的背景信息、个人偏好或价值观，并按照以下格式返回结果：
        
        消息：{message}
        
        分析结果：
        [
            {
                "type": "values|preferences|background|project",
                "content": "识别到的具体信息",
                "confidence": 0.0-1.0
            }
        ]
        
        注意：
        1. 只返回JSON格式的分析结果，不要包含其他内容
        2. 确保confidence值在0.0到1.0之间
        3. 只有确实识别到相关信息时才返回结果
        4. 对于不确定的信息，给出较低的confidence值"""
            
            response = self.llm.generate(prompt)
            
            # 提取JSON结果
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                results = json.loads(json_str)
                
                # 添加method字段
                for result in results:
                    result['method'] = 'llm'
                
                return results
        except Exception as e:
            print(f"LLM分析失败: {e}")
        
        return []
    
    def _calculate_confidence(self, sentence: str, keyword: str, info_type: str) -> float:
        """计算置信度
        
        Args:
            sentence: 包含关键词的句子
            keyword: 关键词
            info_type: 信息类型
            
        Returns:
            置信度（0.0-1.0）
        """
        # 基础置信度
        base_confidence = 0.6
        
        # 根据关键词在句子中的位置调整置信度
        keyword_index = sentence.find(keyword)
        if keyword_index < len(sentence) // 3:
            # 关键词在句子开头，置信度更高
            base_confidence += 0.1
        
        # 根据信息类型调整置信度
        type_bonus = {
            'values': 0.2,  # 价值观信息更重要
            'preferences': 0.1,  # 偏好信息次重要
            'background': 0.15,  # 背景信息重要
            'project': 0.05  # 项目信息相对不重要
        }
        
        base_confidence += type_bonus.get(info_type, 0)
        
        # 确保置信度在0.0-1.0之间
        return min(1.0, max(0.0, base_confidence))
    
    def classify_info_level(self, info_type: str) -> int:
        """根据信息类型分类层级
        
        Args:
            info_type: 信息类型
            
        Returns:
            层级（L1-L5）
        """
        level_map = {
            'values': 5,  # L5: 价值观
            'preferences': 4,  # L4: 用户偏好
            'background': 3,  # L3: 背景信息
            'project': 3  # L3: 项目背景
        }
        
        return level_map.get(info_type, 2)  # 默认L2
    
    def should_store(self, info: Dict[str, Any]) -> bool:
        """判断是否应该存储信息
        
        Args:
            info: 识别到的信息
            
        Returns:
            是否应该存储
        """
        # 只有L3+的信息才存储
        level = self.classify_info_level(info['type'])
        return level >= 3
    
    def should_confirm(self, info: Dict[str, Any]) -> bool:
        """判断是否需要用户确认
        
        Args:
            info: 识别到的信息
            
        Returns:
            是否需要确认
        """
        return info['confidence'] < self.confidence_threshold

# 创建记忆分析器实例
memory_analyzer = MemoryAnalyzer()