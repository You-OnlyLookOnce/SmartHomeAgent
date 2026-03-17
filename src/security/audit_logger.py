from typing import Dict, List, Optional
import json
import os
from datetime import datetime
import time

class AuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self):
        self.audit_dir = "data/audit"
        os.makedirs(self.audit_dir, exist_ok=True)
        
        # 审计事件类型
        self.event_types = {
            "authentication": "用户认证",
            "authorization": "权限检查",
            "data_access": "数据访问",
            "data_modification": "数据修改",
            "device_control": "设备控制",
            "security_event": "安全事件",
            "error": "错误事件",
            "system": "系统事件"
        }
    
    def log_event(self, event_type: str, user_id: str, action: str, 
                  details: Dict = None, success: bool = True) -> Dict:
        """记录审计事件"""
        timestamp = datetime.now().isoformat()
        
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "event_name": self.event_types.get(event_type, event_type),
            "user_id": user_id,
            "action": action,
            "success": success,
            "details": details or {},
            "ip_address": details.get("ip_address", "unknown") if details else "unknown",
            "user_agent": details.get("user_agent", "unknown") if details else "unknown"
        }
        
        # 写入审计日志
        log_file = os.path.join(self.audit_dir, f"{datetime.now().strftime('%Y-%m-%d')}.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        return event
    
    def log_authentication(self, user_id: str, action: str, success: bool, 
                          details: Dict = None) -> Dict:
        """记录认证事件"""
        return self.log_event("authentication", user_id, action, details, success)
    
    def log_authorization(self, user_id: str, permission: str, success: bool,
                         details: Dict = None) -> Dict:
        """记录授权事件"""
        return self.log_event("authorization", user_id, 
                            f"检查权限: {permission}", details, success)
    
    def log_data_access(self, user_id: str, resource: str, action: str,
                       details: Dict = None) -> Dict:
        """记录数据访问事件"""
        return self.log_event("data_access", user_id, 
                            f"访问资源: {resource}, 操作: {action}", details, True)
    
    def log_data_modification(self, user_id: str, resource: str, action: str,
                              details: Dict = None) -> Dict:
        """记录数据修改事件"""
        return self.log_event("data_modification", user_id,
                            f"修改资源: {resource}, 操作: {action}", details, True)
    
    def log_device_control(self, user_id: str, device_id: str, action: str,
                          details: Dict = None) -> Dict:
        """记录设备控制事件"""
        return self.log_event("device_control", user_id,
                            f"控制设备: {device_id}, 操作: {action}", details, True)
    
    def log_security_event(self, user_id: str, event: str, severity: str,
                          details: Dict = None) -> Dict:
        """记录安全事件"""
        event_details = details or {}
        event_details["severity"] = severity
        return self.log_event("security_event", user_id, event, event_details, False)
    
    def log_error(self, user_id: str, error: str, details: Dict = None) -> Dict:
        """记录错误事件"""
        return self.log_event("error", user_id, error, details, False)
    
    def get_audit_logs(self, start_date: str = None, end_date: str = None,
                      user_id: str = None, event_type: str = None,
                      limit: int = 100) -> List[Dict]:
        """查询审计日志"""
        logs = []
        
        # 确定查询日期范围
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()
        
        # 遍历日期范围内的日志文件
        current_date = start
        while current_date <= end:
            log_file = os.path.join(self.audit_dir, 
                                   current_date.strftime('%Y-%m-%d') + ".jsonl")
            
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            
                            # 过滤条件
                            if user_id and event.get("user_id") != user_id:
                                continue
                            
                            if event_type and event.get("event_type") != event_type:
                                continue
                            
                            logs.append(event)
                            
                            if len(logs) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue
            
            if len(logs) >= limit:
                break
            
            # 增加一天
            current_date = current_date.replace(day=current_date.day + 1)
        
        return logs
    
    def get_security_events(self, hours: int = 24) -> List[Dict]:
        """获取最近的安全事件"""
        end_time = datetime.now()
        start_time = end_time.replace(hour=end_time.hour - hours)
        
        return self.get_audit_logs(
            start_date=start_time.isoformat(),
            end_date=end_time.isoformat(),
            event_type="security_event",
            limit=1000
        )
    
    def detect_anomalies(self, user_id: str = None, hours: int = 24) -> List[Dict]:
        """检测异常行为"""
        logs = self.get_audit_logs(
            start_date=(datetime.now().replace(
                hour=datetime.now().hour - hours
            )).isoformat(),
            user_id=user_id,
            limit=1000
        )
        
        anomalies = []
        
        # 统计失败登录次数
        failed_logins = [log for log in logs 
                        if log.get("event_type") == "authentication" 
                        and not log.get("success")]
        
        if len(failed_logins) > 5:
            anomalies.append({
                "type": "multiple_failed_logins",
                "severity": "high",
                "count": len(failed_logins),
                "user_id": user_id,
                "details": failed_logins
            })
        
        # 统计权限拒绝次数
        permission_denied = [log for log in logs 
                           if log.get("event_type") == "authorization" 
                           and not log.get("success")]
        
        if len(permission_denied) > 10:
            anomalies.append({
                "type": "multiple_permission_denied",
                "severity": "medium",
                "count": len(permission_denied),
                "user_id": user_id,
                "details": permission_denied
            })
        
        return anomalies