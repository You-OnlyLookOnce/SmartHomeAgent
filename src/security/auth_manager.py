from typing import Dict, Optional
import hashlib
import secrets
import time
import json
import os
from datetime import datetime, timedelta

class AuthManager:
    """认证授权管理器"""
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.token_blacklist = set()
        self._load_users()
    
    def _load_users(self):
        """加载用户数据"""
        users_file = "data/users.json"
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                self.users = json.load(f)
    
    def _save_users(self):
        """保存用户数据"""
        users_file = "data/users.json"
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return key.hex(), salt
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = self._hash_password(password, salt)
        return computed_hash == stored_hash
    
    def register_user(self, username: str, password: str, role: str = "user") -> Dict:
        """注册用户"""
        if username in self.users:
            return {"success": False, "message": "用户名已存在"}
        
        password_hash, salt = self._hash_password(password)
        
        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        self._save_users()
        
        return {"success": True, "message": "用户注册成功"}
    
    def authenticate(self, username: str, password: str) -> Dict:
        """用户认证"""
        if username not in self.users:
            return {"success": False, "message": "用户不存在"}
        
        user = self.users[username]
        if not self.verify_password(password, user["password_hash"], user["salt"]):
            return {"success": False, "message": "密码错误"}
        
        # 更新最后登录时间
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # 生成会话token
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(16)
        
        self.sessions[session_id] = {
            "token": token,
            "username": username,
            "role": user["role"],
            "created_at": time.time(),
            "expires_at": time.time() + 3600 * 24  # 24小时过期
        }
        
        return {
            "success": True,
            "message": "登录成功",
            "token": token,
            "session_id": session_id,
            "user": {
                "username": username,
                "role": user["role"]
            }
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证token"""
        if token in self.token_blacklist:
            return None
        
        for session_id, session in self.sessions.items():
            if session["token"] == token:
                # 检查是否过期
                if time.time() > session["expires_at"]:
                    del self.sessions[session_id]
                    return None
                
                return {
                    "username": session["username"],
                    "role": session["role"],
                    "session_id": session_id
                }
        
        return None
    
    def logout(self, token: str) -> Dict:
        """用户登出"""
        session_info = self.verify_token(token)
        if not session_info:
            return {"success": False, "message": "无效的token"}
        
        session_id = session_info["session_id"]
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        self.token_blacklist.add(token)
        
        return {"success": True, "message": "登出成功"}
    
    def refresh_token(self, old_token: str) -> Dict:
        """刷新token"""
        session_info = self.verify_token(old_token)
        if not session_info:
            return {"success": False, "message": "无效的token"}
        
        session_id = session_info["session_id"]
        if session_id not in self.sessions:
            return {"success": False, "message": "会话不存在"}
        
        # 生成新token
        new_token = secrets.token_urlsafe(32)
        self.sessions[session_id]["token"] = new_token
        self.sessions[session_id]["expires_at"] = time.time() + 3600 * 24
        
        # 将旧token加入黑名单
        self.token_blacklist.add(old_token)
        
        return {
            "success": True,
            "message": "Token刷新成功",
            "token": new_token
        }