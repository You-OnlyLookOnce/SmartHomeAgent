from typing import Dict, List, Optional
import random
import time

class LoadBalancer:
    """负载均衡器 - 分发请求到不同的Agent实例"""
    
    def __init__(self):
        self.agent_instances = {}
        self.agent_loads = {}
        self.agent_health = {}
        self.agent_capacity = 10
    
    def register_agent(self, agent_id: str, agent_instance, capacity: int = 10):
        """注册Agent实例"""
        self.agent_instances[agent_id] = agent_instance
        self.agent_loads[agent_id] = 0
        self.agent_health[agent_id] = True
        self.agent_capacity = capacity
    
    def update_agent_health(self, agent_id: str, healthy: bool):
        """更新Agent健康状态"""
        self.agent_health[agent_id] = healthy
    
    def select_agent(self, task_type: str) -> Optional[str]:
        """选择合适的Agent实例"""
        # 过滤健康的Agent
        healthy_agents = [
            agent_id for agent_id, health in self.agent_health.items()
            if health
        ]
        
        if not healthy_agents:
            return None
        
        # 根据任务类型选择Agent
        task_agent_map = {
            "device_control": ["device_control"],
            "note": ["note_keeper"],
            "task": ["task_manager"],
            "security": ["security"]
        }
        
        candidate_agents = task_agent_map.get(task_type, list(self.agent_instances.keys()))
        
        # 过滤可用且健康的Agent
        available_agents = [
            agent_id for agent_id in candidate_agents
            if agent_id in healthy_agents
        ]
        
        if not available_agents:
            # 使用所有健康的Agent
            available_agents = healthy_agents
        
        # 负载均衡策略：选择负载最低的Agent
        selected_agent = min(
            available_agents,
            key=lambda agent_id: self.agent_loads[agent_id]
        )
        
        return selected_agent
    
    def increment_load(self, agent_id: str):
        """增加Agent负载"""
        if agent_id in self.agent_loads:
            self.agent_loads[agent_id] += 1
    
    def decrement_load(self, agent_id: str):
        """减少Agent负载"""
        if agent_id in self.agent_loads and self.agent_loads[agent_id] > 0:
            self.agent_loads[agent_id] -= 1
    
    def get_load_stats(self) -> Dict:
        """获取负载统计"""
        return {
            agent_id: {
                "load": self.agent_loads[agent_id],
                "capacity": self.agent_capacity,
                "utilization": self.agent_loads[agent_id] / self.agent_capacity,
                "healthy": self.agent_health[agent_id]
            }
            for agent_id in self.agent_instances.keys()
        }