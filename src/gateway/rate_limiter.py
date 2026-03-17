from typing import Dict
import time
from collections import defaultdict
import asyncio

class RateLimiter:
    """限流器 - 控制请求频率"""
    
    def __init__(self, default_limit: int = 100, default_window: int = 60):
        self.default_limit = default_limit
        self.default_window = default_window
        self.user_limits = {}
        self.user_requests = defaultdict(list)
        self.blocked_users = {}
    
    def set_user_limit(self, user_id: str, limit: int, window: int):
        """设置用户限流"""
        self.user_limits[user_id] = {
            "limit": limit,
            "window": window
        }
    
    def is_allowed(self, user_id: str) -> tuple[bool, Dict]:
        """检查用户是否允许请求"""
        # 检查是否被封禁
        if user_id in self.blocked_users:
            blocked_until = self.blocked_users[user_id]
            if time.time() < blocked_until:
                remaining_time = blocked_until - time.time()
                return False, {
                    "allowed": False,
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": remaining_time
                }
            else:
                del self.blocked_users[user_id]
        
        # 获取用户限流设置
        limit_settings = self.user_limits.get(user_id, {
            "limit": self.default_limit,
            "window": self.default_window
        })
        
        limit = limit_settings["limit"]
        window = limit_settings["window"]
        
        # 清理过期请求记录
        current_time = time.time()
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < window
        ]
        
        # 检查请求频率
        request_count = len(self.user_requests[user_id])
        
        if request_count >= limit:
            # 封禁用户
            block_duration = window * 2
            self.blocked_users[user_id] = current_time + block_duration
            
            return False, {
                "allowed": False,
                "message": "请求过于频繁，已被临时限制",
                "retry_after": block_duration,
                "limit": limit,
                "window": window
            }
        
        # 记录请求
        self.user_requests[user_id].append(current_time)
        
        return True, {
            "allowed": True,
            "remaining": limit - request_count - 1,
            "limit": limit,
            "window": window
        }
    
    def reset_user(self, user_id: str):
        """重置用户限流"""
        if user_id in self.user_requests:
            del self.user_requests[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]