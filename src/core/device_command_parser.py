"""
设备指令解析器模块 - 解析自然语言设备控制指令

功能：
- 使用正则表达式和关键词匹配解析自然语言指令
- 识别设备类型、设备名称/位置、操作类型、参数值
- 返回标准化的命令结构

执行流程：
1. 接收用户输入
2. 匹配设备类型关键词
3. 匹配操作类型关键词
4. 提取参数值
5. 返回标准化命令结构
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """设备类型枚举"""
    LAMP = "lamp"                      # 台灯/灯
    AIR_CONDITIONER = "ac"            # 空调
    CURTAIN = "curtain"               # 窗帘
    UNKNOWN = "unknown"               # 未知


class OperationType(Enum):
    """操作类型枚举"""
    TURN_ON = "turn_on"               # 打开
    TURN_OFF = "turn_off"             # 关闭
    SET_BRIGHTNESS = "set_brightness" # 设置亮度
    SET_COLOR_TEMP = "set_color_temp" # 设置色温
    SET_TEMPERATURE = "set_temperature"  # 设置温度
    SET_MODE = "set_mode"             # 设置模式
    SET_FAN_SPEED = "set_fan_speed"   # 设置风速
    SET_POSITION = "set_position"     # 设置位置
    OPEN = "open"                     # 打开(窗帘)
    CLOSE = "close"                   # 关闭(窗帘)
    STOP = "stop"                     # 停止
    UNKNOWN = "unknown"               # 未知


@dataclass
class ParsedCommand:
    """
    解析后的命令结构
    
    属性：
    - device_type: 设备类型
    - device_name: 设备名称/位置
    - operation: 操作类型
    - params: 参数字典
    - confidence: 置信度(0-1)
    - raw_input: 原始输入
    """
    device_type: DeviceType = DeviceType.UNKNOWN
    device_name: str = ""
    operation: OperationType = OperationType.UNKNOWN
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_input: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_type": self.device_type.value,
            "device_name": self.device_name,
            "operation": self.operation.value,
            "params": self.params,
            "confidence": self.confidence,
            "raw_input": self.raw_input
        }


class DeviceCommandParser:
    """
    设备指令解析器类
    
    解析自然语言设备控制指令，提取设备类型、操作类型和参数。
    
    执行流程：
    1. 初始化时加载关键词映射表
    2. 接收用户输入
    3. 预处理文本(去除多余空格、统一标点)
    4. 匹配设备类型
    5. 匹配操作类型
    6. 提取参数值
    7. 计算置信度
    8. 返回解析结果
    """
    
    # 设备类型关键词映射
    DEVICE_KEYWORDS = {
        DeviceType.LAMP: [
            # 台灯相关
            "台灯", "灯", "灯光", "照明", "客厅灯", "卧室灯", "书房灯",
            "床头灯", "落地灯", "吸顶灯", "吊灯", "壁灯", "夜灯",
            # 色温相关
            "色温", "护眼", "暖光", "冷光", "自然光",
            # 亮度相关
            "亮度", "调亮", "调暗", "亮一点", "暗一点", "太亮了", "太暗了",
            # 英文
            "lamp", "light", "bulb"
        ],
        DeviceType.AIR_CONDITIONER: [
            # 空调相关
            "空调", "冷气", "暖气", "温度", "室温",
            "中央空调", "壁挂空调", "柜机", "挂机",
            # 模式相关
            "制冷", "制热", "除湿", "送风", "风速", "风量", "风力",
            # 温度感受
            "热", "冷", "太热", "太冷", "太热了", "太冷了", "凉快", "暖和",
            # 英文
            "ac", "air conditioner", "air conditioning"
        ],
        DeviceType.CURTAIN: [
            # 窗帘相关
            "窗帘", "百叶窗", "卷帘", "纱帘", "遮光帘",
            "客厅窗帘", "卧室窗帘", "阳台窗帘",
            # 位置相关
            "拉开", "拉上", "升降", "升起", "降下",
            # 英文
            "curtain", "blind", "shade"
        ]
    }
    
    # 操作类型关键词映射
    OPERATION_KEYWORDS = {
        OperationType.TURN_ON: [
            "打开", "开", "开启", "启动", "点亮", "开灯",
            "turn on", "on", "start", "enable"
        ],
        OperationType.TURN_OFF: [
            "关闭", "关", "关掉", "熄灭", "停止", "关机", "关灯",
            "turn off", "off", "stop", "disable", "shutdown"
        ],
        OperationType.SET_BRIGHTNESS: [
            "亮度", "调亮", "调暗", "亮一点", "暗一点",
            "太亮了", "太暗了", "调亮一点", "调暗一点",
            "brightness", "dim", "bright"
        ],
        OperationType.SET_COLOR_TEMP: [
            "色温", "护眼", "暖光", "冷光", "自然光",
            "color temp", "warm light", "cool light", "eye care"
        ],
        OperationType.SET_TEMPERATURE: [
            "温度", "调温", "制冷", "制热", "升温", "降温",
            "调到", "设为", "设置",
            "temperature", "temp", "cool", "heat"
        ],
        OperationType.SET_MODE: [
            "模式", "制冷模式", "制热模式", "除湿", "送风", "自动",
            "mode", "cool mode", "heat mode", "dry", "fan", "auto"
        ],
        OperationType.SET_FAN_SPEED: [
            "风速", "风量", "风力", "风档", "风速调到", "风速设置",
            "fan speed", "wind speed", "blower"
        ],
        OperationType.SET_POSITION: [
            "位置", "开到", "关到", "调到一半", "一半",
            "position", "half", "partial"
        ],
        OperationType.OPEN: [
            "打开", "全开", "拉开", "升起", "开",
            "open", "pull up", "raise"
        ],
        OperationType.CLOSE: [
            "关闭", "全关", "拉上", "降下", "关",
            "close", "pull down", "lower"
        ],
        OperationType.STOP: [
            "停止", "暂停", "停",
            "stop", "pause", "halt"
        ]
    }
    
    # 参数提取正则表达式
    PARAM_PATTERNS = {
        # 亮度值 (0-100)
        "brightness": [
            r'(\d+)%?\s*亮度',
            r'亮度\s*(\d+)%?',
            r'调到\s*(\d+)%?',
            r'(\d+)%?\s*亮',
        ],
        # 温度值 (16-30)
        "temperature": [
            r'(\d+)\s*度',
            r'(\d+)\s*°C?',
            r'温度\s*(\d+)',
            r'调到\s*(\d+)',
        ],
        # 风速档位 (1-5)
        "fan_speed": [
            r'(\d+)\s*档',
            r'(\d+)\s*挡',
            r'风速\s*(\d+)',
        ],
        # 窗帘位置 (0-100)
        "position": [
            r'(\d+)%?\s*位置',
            r'位置\s*(\d+)%?',
            r'开到\s*(\d+)%?',
            r'关到\s*(\d+)%?',
            r'一半'  # 特殊值
        ],
        # 时间值 (分钟)
        "timer": [
            r'(\d+)\s*分钟',
            r'(\d+)\s*分',
            r'定时\s*(\d+)',
        ]
    }
    
    # 色温模式映射
    COLOR_TEMP_MODES = {
        "normal": ["正常", "普通", "标准", "自然", "normal", "standard"],
        "eye_care": ["护眼", "暖光", "护眼模式", "eye care", "warm", "eye_care"],
        "cool": ["冷光", "cool", "cold"]
    }
    
    # 空调模式映射
    AC_MODES = {
        "cool": ["制冷", "冷气", "cool", "cooling", "cold"],
        "heat": ["制热", "暖气", "heat", "heating", "warm"],
        "dry": ["除湿", "干燥", "dry", "dehumidify"],
        "fan": ["送风", "通风", "fan", "ventilate"],
        "auto": ["自动", "智能", "auto", "automatic"]
    }
    
    def __init__(self):
        """初始化设备指令解析器"""
        self._compile_patterns()
        logger.info("设备指令解析器初始化完成")
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self._compiled_patterns = {}
        for param_name, patterns in self.PARAM_PATTERNS.items():
            self._compiled_patterns[param_name] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def parse(self, user_input: str) -> ParsedCommand:
        """
        解析用户输入
        
        执行流程：
        1. 预处理输入文本
        2. 识别设备类型
        3. 识别操作类型
        4. 提取参数
        5. 计算置信度
        6. 返回解析结果
        
        Args:
            user_input: 用户输入的自然语言指令
            
        Returns:
            解析后的命令结构
        """
        if not user_input or not user_input.strip():
            return ParsedCommand(
                raw_input=user_input,
                confidence=0.0
            )
        
        # 预处理
        processed_input = self._preprocess(user_input)
        
        # 创建设备名称映射
        device_name = self._extract_device_name(processed_input)
        
        # 识别设备类型
        device_type = self._detect_device_type(processed_input)
        
        # 识别操作类型
        operation = self._detect_operation_type(processed_input, device_type)
        
        # 提取参数
        params = self._extract_params(processed_input, device_type, operation)
        
        # 计算置信度
        confidence = self._calculate_confidence(
            device_type, operation, params, processed_input
        )
        
        return ParsedCommand(
            device_type=device_type,
            device_name=device_name,
            operation=operation,
            params=params,
            confidence=confidence,
            raw_input=user_input
        )
    
    def _preprocess(self, text: str) -> str:
        """
        预处理输入文本
        
        Args:
            text: 原始输入
            
        Returns:
            处理后的文本
        """
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 统一标点符号
        text = text.replace('，', ',').replace('。', '.').replace('？', '?')
        # 转换为小写(便于英文匹配)
        return text.strip().lower()
    
    def _extract_device_name(self, text: str) -> str:
        """
        提取设备名称/位置
        
        Args:
            text: 处理后的文本
            
        Returns:
            设备名称
        """
        # 匹配模式: "把XX的灯"、"客厅的灯"、"卧室空调"
        patterns = [
            r'把([\u4e00-\u9fa5]+?)(?:的|灯|空调|窗帘)',
            r'([\u4e00-\u9fa5]+?)(?:的|灯|空调|窗帘)',
            r'([\u4e00-\u9fa5]+?)(?:灯|空调|窗帘)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # 过滤掉常见的非位置词
                if name not in ["把", "将", "把", "给"]:
                    return name
        
        return ""
    
    def _detect_device_type(self, text: str) -> DeviceType:
        """
        检测设备类型
        
        Args:
            text: 处理后的文本
            
        Returns:
            设备类型
        """
        scores = {device_type: 0 for device_type in DeviceType}
        
        for device_type, keywords in self.DEVICE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    # 根据关键词长度加权，更具体的词权重更高
                    scores[device_type] += len(keyword)
        
        # 返回得分最高的类型
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return DeviceType.UNKNOWN
    
    def _detect_operation_type(self, text: str, device_type: DeviceType) -> OperationType:
        """
        检测操作类型
        
        Args:
            text: 处理后的文本
            device_type: 已识别的设备类型
            
        Returns:
            操作类型
        """
        scores = {op_type: 0 for op_type in OperationType}
        
        for op_type, keywords in self.OPERATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[op_type] += len(keyword)
        
        # 根据设备类型调整操作类型的优先级
        if device_type == DeviceType.LAMP:
            # 台灯相关操作优先级
            if "亮度" in text or "亮" in text or "暗" in text:
                scores[OperationType.SET_BRIGHTNESS] += 10
            if "色温" in text or "护眼" in text:
                scores[OperationType.SET_COLOR_TEMP] += 10
                
        elif device_type == DeviceType.AIR_CONDITIONER:
            # 空调相关操作优先级
            if "度" in text or "温度" in text:
                scores[OperationType.SET_TEMPERATURE] += 10
            if "风速" in text or "档" in text or "挡" in text:
                scores[OperationType.SET_FAN_SPEED] += 10
            if "模式" in text:
                scores[OperationType.SET_MODE] += 10
                
        elif device_type == DeviceType.CURTAIN:
            # 窗帘相关操作优先级
            if "一半" in text or "50%" in text:
                scores[OperationType.SET_POSITION] += 10
            if "打开" in text or "开" in text:
                scores[OperationType.OPEN] += 5
            if "关闭" in text or "关" in text:
                scores[OperationType.CLOSE] += 5
        
        # 返回得分最高的操作类型
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return OperationType.UNKNOWN
    
    def _extract_params(self, text: str, device_type: DeviceType, 
                       operation: OperationType) -> Dict[str, Any]:
        """
        提取参数值
        
        Args:
            text: 处理后的文本
            device_type: 设备类型
            operation: 操作类型
            
        Returns:
            参数字典
        """
        params = {}
        
        # 根据操作类型提取对应参数
        if operation == OperationType.SET_BRIGHTNESS:
            brightness = self._extract_brightness(text)
            if brightness is not None:
                params["brightness"] = brightness
            
        elif operation == OperationType.SET_COLOR_TEMP:
            color_temp = self._extract_color_temp(text)
            if color_temp:
                params["color_temp"] = color_temp
            
        elif operation == OperationType.SET_TEMPERATURE:
            temperature = self._extract_temperature(text)
            if temperature is not None:
                params["temperature"] = temperature
            
        elif operation == OperationType.SET_MODE:
            mode = self._extract_ac_mode(text)
            if mode:
                params["mode"] = mode
            
        elif operation == OperationType.SET_FAN_SPEED:
            fan_speed = self._extract_fan_speed(text)
            if fan_speed is not None:
                params["fan_speed"] = fan_speed
            
        elif operation == OperationType.SET_POSITION:
            position = self._extract_position(text)
            if position is not None:
                params["position"] = position
            
        elif operation in [OperationType.OPEN, OperationType.CLOSE]:
            # 检查是否有位置参数
            position = self._extract_position(text)
            if position is not None:
                params["position"] = position
                operation = OperationType.SET_POSITION
        
        # 提取定时参数
        timer = self._extract_timer(text)
        if timer is not None:
            params["timer"] = timer
        
        return params
    
    def _extract_brightness(self, text: str) -> Optional[int]:
        """提取亮度值"""
        # 处理相对描述
        if "太亮" in text or "调暗" in text:
            # 降低亮度，假设当前是100，调到50
            return 50
        if "太暗" in text or "调亮" in text:
            # 增加亮度，假设当前是50，调到80
            return 80
        
        # 提取具体数值
        for pattern in self._compiled_patterns.get("brightness", []):
            match = pattern.search(text)
            if match:
                try:
                    value = int(match.group(1))
                    return max(0, min(100, value))  # 限制在0-100范围内
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_temperature(self, text: str) -> Optional[int]:
        """提取温度值"""
        for pattern in self._compiled_patterns.get("temperature", []):
            match = pattern.search(text)
            if match:
                try:
                    value = int(match.group(1))
                    return max(16, min(30, value))  # 限制在16-30范围内
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_fan_speed(self, text: str) -> Optional[int]:
        """提取风速档位"""
        for pattern in self._compiled_patterns.get("fan_speed", []):
            match = pattern.search(text)
            if match:
                try:
                    value = int(match.group(1))
                    return max(1, min(5, value))  # 限制在1-5范围内
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_position(self, text: str) -> Optional[int]:
        """提取窗帘位置"""
        # 处理特殊值
        if "一半" in text:
            return 50
        
        for pattern in self._compiled_patterns.get("position", []):
            match = pattern.search(text)
            if match:
                try:
                    value = int(match.group(1))
                    return max(0, min(100, value))  # 限制在0-100范围内
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_color_temp(self, text: str) -> Optional[str]:
        """提取色温模式"""
        for mode, keywords in self.COLOR_TEMP_MODES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return mode
        return None
    
    def _extract_ac_mode(self, text: str) -> Optional[str]:
        """提取空调模式"""
        for mode, keywords in self.AC_MODES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return mode
        return None
    
    def _extract_timer(self, text: str) -> Optional[int]:
        """提取定时值(分钟)"""
        for pattern in self._compiled_patterns.get("timer", []):
            match = pattern.search(text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _calculate_confidence(self, device_type: DeviceType, operation: OperationType,
                             params: Dict[str, Any], text: str) -> float:
        """
        计算解析置信度
        
        Args:
            device_type: 设备类型
            operation: 操作类型
            params: 参数
            text: 原始文本
            
        Returns:
            置信度(0-1)
        """
        confidence = 0.0
        
        # 设备类型识别成功
        if device_type != DeviceType.UNKNOWN:
            confidence += 0.3
        
        # 操作类型识别成功
        if operation != OperationType.UNKNOWN:
            confidence += 0.3
        
        # 参数提取成功
        if params:
            confidence += 0.2
        
        # 文本长度适中(太短可能信息不足)
        if 5 <= len(text) <= 50:
            confidence += 0.1
        
        # 包含明确的设备关键词
        device_keywords_count = sum(
            1 for keywords in self.DEVICE_KEYWORDS.values()
            for keyword in keywords
            if keyword.lower() in text
        )
        if device_keywords_count > 0:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def is_device_command(self, text: str, threshold: float = 0.5) -> bool:
        """
        判断是否为设备控制指令
        
        Args:
            text: 用户输入
            threshold: 置信度阈值
            
        Returns:
            是否为设备控制指令
        """
        result = self.parse(text)
        return result.confidence >= threshold and result.device_type != DeviceType.UNKNOWN
    
    def get_command_suggestions(self, text: str) -> List[str]:
        """
        获取命令建议
        
        Args:
            text: 用户输入
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 台灯相关建议
        if any(kw in text for kw in ["灯", "台灯", "light"]):
            suggestions.extend([
                "打开台灯",
                "关闭台灯",
                "台灯亮度调到50%",
                "台灯色温调到护眼模式"
            ])
        
        # 空调相关建议
        if any(kw in text for kw in ["空调", "温度", "ac"]):
            suggestions.extend([
                "打开空调制冷模式",
                "把空调调到26度",
                "空调风速调到3档",
                "关闭空调"
            ])
        
        # 窗帘相关建议
        if any(kw in text for kw in ["窗帘", "curtain"]):
            suggestions.extend([
                "打开窗帘",
                "关闭窗帘",
                "窗帘关到一半"
            ])
        
        return suggestions


# 创建解析器实例
device_command_parser = DeviceCommandParser()


# 便捷函数
def parse_device_command(text: str) -> Dict[str, Any]:
    """
    解析设备命令的便捷函数
    
    Args:
        text: 用户输入
        
    Returns:
        解析结果字典
    """
    return device_command_parser.parse(text).to_dict()


def is_device_command(text: str, threshold: float = 0.5) -> bool:
    """
    判断是否为设备命令的便捷函数
    
    Args:
        text: 用户输入
        threshold: 置信度阈值
        
    Returns:
        是否为设备控制指令
    """
    return device_command_parser.is_device_command(text, threshold)
