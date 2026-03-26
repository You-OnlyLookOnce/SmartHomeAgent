"""
速率限制中间件模块

实现API请求速率限制，防止滥用
"""

import time
from typing import Dict, Optional
from fastapi import HTTPException, Request
try:
    from fastapi.middleware.base import BaseHTTPMiddleware
except ImportError:
    from fastapi.middleware import Middleware

class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        # 存储请求信息 {ip: {endpoint: {count, last_reset}}}
        self.requests: Dict[str, Dict[str, Dict[str, float]]] = {}
        # 速率限制配置 (请求数/时间窗口(秒))
        self.rate_limits = {
            'default': (100, 60),  # 100请求/分钟
            'status_refresh': (6, 60),  # 6请求/分钟
            'websocket': (5, 60)  # 5连接/分钟
        }
    
    def check_rate_limit(self, ip: str, endpoint: str) -> bool:
        """检查速率限制
        
        Args:
            ip: 请求IP
            endpoint: 请求端点
        
        Returns:
            bool: 是否允许请求
        """
        current_time = time.time()
        
        # 初始化IP记录
        if ip not in self.requests:
            self.requests[ip] = {}
        
        # 初始化端点记录
        if endpoint not in self.requests[ip]:
            self.requests[ip][endpoint] = {
                'count': 0,
                'last_reset': current_time
            }
        
        # 获取限制配置
        limit_key = 'default'
        if 'refresh' in endpoint:
            limit_key = 'status_refresh'
        elif 'stream' in endpoint:
            limit_key = 'websocket'
        
        limit, window = self.rate_limits[limit_key]
        
        # 检查是否需要重置计数器
        if current_time - self.requests[ip][endpoint]['last_reset'] > window:
            self.requests[ip][endpoint]['count'] = 0
            self.requests[ip][endpoint]['last_reset'] = current_time
        
        # 检查是否超过限制
        if self.requests[ip][endpoint]['count'] >= limit:
            return False
        
        # 增加计数器
        self.requests[ip][endpoint]['count'] += 1
        return True
    
    def get_remaining_time(self, ip: str, endpoint: str) -> float:
        """获取剩余时间
        
        Args:
            ip: 请求IP
            endpoint: 请求端点
        
        Returns:
            float: 剩余时间(秒)
        """
        if ip not in self.requests or endpoint not in self.requests[ip]:
            return 0
        
        current_time = time.time()
        last_reset = self.requests[ip][endpoint]['last_reset']
        
        limit_key = 'default'
        if 'refresh' in endpoint:
            limit_key = 'status_refresh'
        elif 'stream' in endpoint:
            limit_key = 'websocket'
        
        _, window = self.rate_limits[limit_key]
        
        remaining = window - (current_time - last_reset)
        return max(0, remaining)

# 创建速率限制器实例
rate_limiter = RateLimiter()

try:
    class RateLimitMiddleware(BaseHTTPMiddleware):
        """速率限制中间件"""
        
        async def dispatch(self, request: Request, call_next):
            # 获取客户端IP
            client_ip = request.client.host
            endpoint = request.url.path
            
            # 检查速率限制
            if not rate_limiter.check_rate_limit(client_ip, endpoint):
                remaining = rate_limiter.get_remaining_time(client_ip, endpoint)
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(int(remaining))
                    }
                )
            
            # 继续处理请求
            response = await call_next(request)
            
            # 添加速率限制信息到响应头
            remaining = rate_limiter.get_remaining_time(client_ip, endpoint)
            response.headers["X-RateLimit-Remaining"] = str(
                rate_limiter.rate_limits.get('default', (100, 60))[0] - 
                rate_limiter.requests.get(client_ip, {}).get(endpoint, {}).get('count', 0)
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + remaining))
            
            return response
except NameError:
    # 如果BaseHTTPMiddleware不可用，使用简单的中间件函数
    async def rate_limit_middleware(request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host
        endpoint = request.url.path
        
        # 检查速率限制
        if not rate_limiter.check_rate_limit(client_ip, endpoint):
            remaining = rate_limiter.get_remaining_time(client_ip, endpoint)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(int(remaining))
                }
            )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加速率限制信息到响应头
        remaining = rate_limiter.get_remaining_time(client_ip, endpoint)
        response.headers["X-RateLimit-Remaining"] = str(
            rate_limiter.rate_limits.get('default', (100, 60))[0] - 
            rate_limiter.requests.get(client_ip, {}).get(endpoint, {}).get('count', 0)
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + remaining))
        
        return response
    
    RateLimitMiddleware = rate_limit_middleware

# 装饰器版本
from functools import wraps

def rate_limit(limit: int, window: int):
    """速率限制装饰器
    
    Args:
        limit: 时间窗口内的最大请求数
        window: 时间窗口(秒)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里需要获取request对象
            # 实际实现需要根据框架调整
            return await func(*args, **kwargs)
        return wrapper
    return decorator