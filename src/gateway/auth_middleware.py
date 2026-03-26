"""
认证中间件模块

实现JWT token认证和基于角色的访问控制
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 从环境变量获取密钥，默认使用开发密钥
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-for-development')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 角色定义
ROLES = {
    'admin': ['read', 'write', 'admin'],
    'user': ['read'],
    'service': ['read', 'write']
}

# 安全方案
security = HTTPBearer()

class AuthMiddleware:
    """认证中间件类"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """获取当前用户"""
        token = credentials.credentials
        payload = AuthMiddleware.verify_token(token)
        return payload
    
    @staticmethod
    async def require_role(required_role: str):
        """要求特定角色"""
        async def role_checker(current_user: Dict[str, Any] = Depends(AuthMiddleware.get_current_user)):
            user_role = current_user.get('role', 'user')
            if user_role not in ROLES or required_role not in ROLES.get(user_role, []):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required role: {required_role}"
                )
            return current_user
        return role_checker

    @staticmethod
    async def require_read_access():
        """要求读取权限"""
        return await AuthMiddleware.require_role('read')
    
    @staticmethod
    async def require_write_access():
        """要求写入权限"""
        return await AuthMiddleware.require_role('write')
    
    @staticmethod
    async def require_admin_access():
        """要求管理员权限"""
        return await AuthMiddleware.require_role('admin')

# 简化的API密钥认证（用于MCP集成）
class APIKeyAuth:
    """API密钥认证"""
    
    # 从环境变量获取API密钥，默认使用开发密钥
    API_KEY = os.environ.get('API_KEY', 'dev-api-key-123')
    
    @staticmethod
    def verify_api_key(api_key: str) -> bool:
        """验证API密钥"""
        return api_key == APIKeyAuth.API_KEY
    
    @staticmethod
    async def get_api_key(request: Request):
        """从请求中获取API密钥"""
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        
        if not APIKeyAuth.verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return api_key

# 认证依赖项
get_current_user = AuthMiddleware.get_current_user
try:
    from fastapi import Depends
    require_read_access = AuthMiddleware.require_read_access
    require_write_access = AuthMiddleware.require_write_access
    require_admin_access = AuthMiddleware.require_admin_access
    get_api_key = APIKeyAuth.get_api_key
except ImportError:
    # 如果在非FastAPI环境中导入，提供默认实现
    pass