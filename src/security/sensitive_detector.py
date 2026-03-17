from typing import Dict, List, Tuple
import re

class SensitiveDataDetector:
    """敏感信息检测器"""
    
    def __init__(self):
        self.patterns = {
            "phone": [
                r'1[3-9]\d{9}',  # 中国手机号
                r'\+86\s*1[3-9]\d{9}',  # 带区号的中国手机号
            ],
            "email": [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            "id_card": [
                r'\d{17}[\dXx]',  # 中国身份证
            ],
            "credit_card": [
                r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',  # 信用卡
            ],
            "password": [
                r'password\s*[:=]\s*\S+',
                r'pwd\s*[:=]\s*\S+',
                r'passwd\s*[:=]\s*\S+',
            ],
            "api_key": [
                r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
                r'secret[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
                r'access[_-]?token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
            ],
            "ip_address": [
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            ],
            "bank_account": [
                r'\d{16,19}',  # 银行卡号
            ],
        }
    
    def detect(self, text: str) -> Dict[str, List[Tuple[str, int, int]]]:
        """检测文本中的敏感信息"""
        results = {}
        
        for data_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    matches.append((match.group(), match.start(), match.end()))
            
            if matches:
                results[data_type] = matches
        
        return results
    
    def has_sensitive_data(self, text: str) -> bool:
        """检查是否包含敏感数据"""
        detections = self.detect(text)
        return len(detections) > 0
    
    def mask_sensitive_data(self, text: str) -> str:
        """脱敏文本中的敏感数据"""
        detections = self.detect(text)
        
        masked_text = text
        offset = 0
        
        for data_type, matches in detections.items():
            for match, start, end in matches:
                # 计算脱敏后的位置
                masked_start = start + offset
                masked_end = end + offset
                
                # 根据类型进行脱敏
                if data_type == "phone":
                    masked_value = match[:3] + "****" + match[-4:]
                elif data_type == "email":
                    parts = match.split("@")
                    username = parts[0]
                    domain = parts[1]
                    if len(username) > 3:
                        masked_value = username[:1] + "***@" + domain
                    else:
                        masked_value = "***@" + domain
                elif data_type == "id_card":
                    masked_value = match[:6] + "********" + match[-4:]
                elif data_type == "credit_card":
                    masked_value = "**** **** **** " + match[-4:]
                else:
                    masked_value = "*" * len(match)
                
                # 替换文本
                masked_text = masked_text[:masked_start] + masked_value + masked_text[masked_end:]
                
                # 更新偏移量
                offset += len(masked_value) - len(match)
        
        return masked_text
    
    def filter_sensitive_data(self, data: Dict, sensitive_fields: List[str] = None) -> Dict:
        """过滤字典中的敏感数据"""
        if sensitive_fields is None:
            sensitive_fields = ["password", "pwd", "secret", "token", "key", "api_key"]
        
        filtered_data = {}
        
        for key, value in data.items():
            # 检查键名是否包含敏感字段
            is_sensitive = any(sensitive_field in key.lower() for sensitive_field in sensitive_fields)
            
            if is_sensitive:
                # 脱敏敏感数据
                if isinstance(value, str):
                    filtered_data[key] = "****"
                else:
                    filtered_data[key] = "[FILTERED]"
            else:
                # 检查值是否包含敏感信息
                if isinstance(value, str) and self.has_sensitive_data(value):
                    filtered_data[key] = self.mask_sensitive_data(value)
                else:
                    filtered_data[key] = value
        
        return filtered_data