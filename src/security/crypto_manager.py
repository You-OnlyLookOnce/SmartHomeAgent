from typing import Dict, Any
import hashlib
import base64
import os
import json

class CryptoManager:
    """加密管理器 - 数据加密和脱敏"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or self._load_or_generate_key()
        self._initialize_cipher()
    
    def _load_or_generate_key(self) -> str:
        """加载或生成密钥"""
        key_file = "data/secret.key"
        
        if os.path.exists(key_file):
            with open(key_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            key = base64.b64encode(os.urandom(32)).decode('utf-8')
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(key)
            return key
    
    def _initialize_cipher(self):
        """初始化加密器"""
        # 使用简单的XOR加密作为示例
        # 实际应用中应该使用更安全的加密算法
        pass
    
    def encrypt(self, plaintext: str) -> str:
        """加密数据"""
        # 简单的XOR加密示例
        key = self.master_key.encode('utf-8')
        plaintext_bytes = plaintext.encode('utf-8')
        
        encrypted = bytearray()
        for i, byte in enumerate(plaintext_bytes):
            encrypted.append(byte ^ key[i % len(key)])
        
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """解密数据"""
        # 简单的XOR解密示例
        key = self.master_key.encode('utf-8')
        encrypted = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
        
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ key[i % len(key)])
        
        return decrypted.decode('utf-8')
    
    def encrypt_dict(self, data: Dict, sensitive_fields: list) -> Dict:
        """加密字典中的敏感字段"""
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict, sensitive_fields: list) -> Dict:
        """解密字典中的敏感字段"""
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except:
                    pass
        
        return decrypted_data
    
    def mask_sensitive_data(self, data: str, data_type: str = "general") -> str:
        """脱敏敏感数据"""
        if not data:
            return data
        
        if data_type == "phone":
            # 手机号脱敏：138****1234
            if len(data) >= 11:
                return data[:3] + "****" + data[-4:]
        
        elif data_type == "email":
            # 邮箱脱敏：a***@example.com
            if "@" in data:
                parts = data.split("@")
                username = parts[0]
                domain = parts[1]
                if len(username) > 3:
                    return username[:1] + "***" + "@" + domain
                else:
                    return "***@" + domain
        
        elif data_type == "id_card":
            # 身份证脱敏：110101********1234
            if len(data) >= 18:
                return data[:6] + "********" + data[-4:]
        
        elif data_type == "credit_card":
            # 信用卡脱敏：**** **** **** 1234
            if len(data) >= 16:
                return "**** **** **** " + data[-4:]
        
        elif data_type == "password":
            # 密码脱敏：******
            return "*" * len(data)
        
        else:
            # 通用脱敏：显示首尾各2个字符
            if len(data) > 4:
                return data[:2] + "****" + data[-2:]
            else:
                return "*" * len(data)
        
        return data
    
    def hash_data(self, data: str) -> str:
        """哈希数据"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def generate_hmac(self, data: str, secret: str) -> str:
        """生成HMAC签名"""
        import hmac
        return hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac(self, data: str, signature: str, secret: str) -> bool:
        """验证HMAC签名"""
        computed_signature = self.generate_hmac(data, secret)
        return computed_signature == signature