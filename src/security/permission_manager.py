from typing import Dict, List, Set
import json
import os

class PermissionManager:
    """权限管理器 - 实现最小权限原则"""
    
    def __init__(self):
        self.roles = {}
        self.permissions = {}
        self.user_roles = {}
        self._load_permissions()
    
    def _load_permissions(self):
        """加载权限配置"""
        config_file = "config/permissions.json"
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.roles = config.get("roles", {})
                self.permissions = config.get("permissions", {})
                self.user_roles = config.get("user_roles", {})
        else:
            # 默认权限配置
            self.roles = {
                "admin": ["all"],
                "user": ["device:read", "task:manage", "note:manage"],
                "guest": ["device:read"]
            }
            self.user_roles = {
                "admin": "admin",
                "user": "user"
            }
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户权限集合"""
        user_role = self.user_roles.get(user_id, "guest")
        role_permissions = self.roles.get(user_role, [])
        
        # 如果有all权限，返回所有权限
        if "all" in role_permissions:
            all_permissions = set()
            for role, perms in self.roles.items():
                all_permissions.update(perms)
            all_permissions.remove("all")
            return all_permissions
        
        return set(role_permissions)
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        
        # 检查具体权限
        if permission in user_permissions:
            return True
        
        # 检查权限前缀
        for perm in user_permissions:
            if perm.endswith(":*") and permission.startswith(perm[:-2]):
                return True
        
        return False
    
    def check_device_access(self, user_id: str, device_id: str) -> bool:
        """检查用户是否有设备访问权限"""
        device_permission = f"device:{device_id}"
        return self.check_permission(user_id, device_permission) or \
               self.check_permission(user_id, "device:*")
    
    def check_skill_access(self, user_id: str, skill_name: str) -> bool:
        """检查用户是否有技能访问权限"""
        skill_permission = f"skill:{skill_name}"
        return self.check_permission(user_id, skill_permission) or \
               self.check_permission(user_id, "skill:*")
    
    def get_accessible_devices(self, user_id: str) -> List[str]:
        """获取用户可访问的设备列表"""
        user_permissions = self.get_user_permissions(user_id)
        devices = []
        
        # 检查是否有所有设备权限
        if "device:*" in user_permissions or "all" in user_permissions:
            # 这里应该返回所有设备
            # 暂时返回示例设备
            return ["led_1", "fan_1", "sensor_1"]
        
        # 检查具体设备权限
        for permission in user_permissions:
            if permission.startswith("device:") and ":" in permission[7:]:
                device_id = permission.split(":")[1]
                devices.append(device_id)
        
        return devices
    
    def get_accessible_skills(self, user_id: str) -> List[str]:
        """获取用户可访问的技能列表"""
        user_permissions = self.get_user_permissions(user_id)
        skills = []
        
        # 检查是否有所有技能权限
        if "skill:*" in user_permissions or "all" in user_permissions:
            # 这里应该返回所有技能
            # 暂时返回示例技能
            return ["led_on", "led_off", "fan_control", "sensor_read"]
        
        # 检查具体技能权限
        for permission in user_permissions:
            if permission.startswith("skill:") and ":" in permission[6:]:
                skill_name = permission.split(":")[1]
                skills.append(skill_name)
        
        return skills
    
    def assign_role(self, user_id: str, role: str) -> Dict:
        """为用户分配角色"""
        if role not in self.roles:
            return {"success": False, "message": "角色不存在"}
        
        self.user_roles[user_id] = role
        self._save_permissions()
        
        return {"success": True, "message": f"用户 {user_id} 已分配角色 {role}"}
    
    def _save_permissions(self):
        """保存权限配置"""
        config_file = "config/permissions.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        config = {
            "roles": self.roles,
            "permissions": self.permissions,
            "user_roles": self.user_roles
        }
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)