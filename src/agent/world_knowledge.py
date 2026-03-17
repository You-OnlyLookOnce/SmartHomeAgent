from typing import Dict, Any

class WorldKnowledgeManager:
    """世界知识管理器 - Lares风格"""
    
    def __init__(self):
        # 隐藏的真实世界状态
        self.hidden_state = {
            'pets': {},  # 宠物位置
            'people': {},  # 人员位置
            'movable_items': {}  # 可移动物品
        }
        
        # Agent可知的公开状态
        self.public_state = {
            'devices': {},  # 设备状态
            'rooms': {},  # 房间布局
            'known_info': []  # 已知信息
        }
    
    def get_agent_knowledge(self) -> Dict:
        """获取Agent视角的世界知识"""
        return {
            'devices': self.public_state['devices'],
            'rooms': self.public_state['rooms'],
            'known_info': self.public_state['known_info']
        }
    
    def update_from_action(self, action: str, result: Dict):
        """从动作结果更新世界知识"""
        if action == 'moveRobot':
            # 机器人可以发现隐藏状态
            if result.get('found_items'):
                self.public_state['known_info'].extend(result['found_items'])
        
        # 设备状态始终公开
        if 'device_state' in result:
            self.public_state['devices'].update(result['device_state'])
    
    def add_hidden_discovery(self, category: str, item: str, location: str):
        """添加新发现的隐藏物体"""
        if category in self.hidden_state:
            self.hidden_state[category][item] = location
    
    def update_device_state(self, device_id: str, state: Dict):
        """更新设备状态"""
        self.public_state['devices'][device_id] = state
    
    def get_device_state(self, device_id: str) -> Dict:
        """获取设备状态"""
        return self.public_state['devices'].get(device_id, {})
    
    def sync_world_knowledge(self) -> Dict:
        """同步世界知识"""
        return {
            "devices": self.public_state['devices'],
            "rooms": self.public_state['rooms'],
            "known_info": self.public_state['known_info'],
            "timestamp": "2026-03-16T18:30:00"
        }
    
    def reset(self):
        """重置世界知识"""
        self.hidden_state = {
            'pets': {},
            'people': {},
            'movable_items': {}
        }
        self.public_state = {
            'devices': {},
            'rooms': {},
            'known_info': []
        }
