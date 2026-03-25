from typing import Dict, Any, Optional
import json
import os

class MemoryConfirmation:
    """记忆确认管理器 - 负责处理低置信度信息的确认流程"""
    
    def __init__(self):
        """初始化记忆确认管理器"""
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent_memory")
        self.confirmation_queue_file = os.path.join(self.base_dir, "confirmation_queue.json")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 初始化确认队列
        self.confirmation_queue = self._load_confirmation_queue()
    
    def _load_confirmation_queue(self) -> list:
        """加载确认队列
        
        Returns:
            确认队列列表
        """
        try:
            if os.path.exists(self.confirmation_queue_file):
                with open(self.confirmation_queue_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载确认队列失败: {e}")
        return []
    
    def _save_confirmation_queue(self):
        """保存确认队列"""
        try:
            with open(self.confirmation_queue_file, "w", encoding="utf-8") as f:
                json.dump(self.confirmation_queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存确认队列失败: {e}")
    
    def add_to_confirmation_queue(self, info: Dict[str, Any]) -> str:
        """添加信息到确认队列
        
        Args:
            info: 识别到的信息
            
        Returns:
            确认ID
        """
        try:
            # 生成确认ID
            confirmation_id = f"confirm_{len(self.confirmation_queue) + 1}"
            
            # 构建确认项
            confirmation_item = {
                'id': confirmation_id,
                'info': info,
                'status': 'pending',  # pending, confirmed, rejected
                'timestamp': os.path.getmtime(self.confirmation_queue_file) if os.path.exists(self.confirmation_queue_file) else os.time()
            }
            
            # 添加到队列
            self.confirmation_queue.append(confirmation_item)
            self._save_confirmation_queue()
            
            return confirmation_id
        except Exception as e:
            print(f"添加到确认队列失败: {e}")
            return None
    
    def get_confirmation_item(self, confirmation_id: str) -> Optional[Dict[str, Any]]:
        """获取确认项
        
        Args:
            confirmation_id: 确认ID
            
        Returns:
            确认项
        """
        for item in self.confirmation_queue:
            if item['id'] == confirmation_id:
                return item
        return None
    
    def update_confirmation_status(self, confirmation_id: str, status: str) -> bool:
        """更新确认状态
        
        Args:
            confirmation_id: 确认ID
            status: 状态（confirmed, rejected）
            
        Returns:
            是否更新成功
        """
        try:
            for item in self.confirmation_queue:
                if item['id'] == confirmation_id:
                    item['status'] = status
                    self._save_confirmation_queue()
                    return True
            return False
        except Exception as e:
            print(f"更新确认状态失败: {e}")
            return False
    
    def get_pending_confirmations(self) -> list:
        """获取待确认的信息
        
        Returns:
            待确认的信息列表
        """
        return [item for item in self.confirmation_queue if item['status'] == 'pending']
    
    def clear_confirmation_queue(self):
        """清空确认队列"""
        try:
            self.confirmation_queue = []
            self._save_confirmation_queue()
        except Exception as e:
            print(f"清空确认队列失败: {e}")

# 创建记忆确认管理器实例
memory_confirmation = MemoryConfirmation()