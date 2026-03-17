from typing import Dict, List, Optional

class PromptTree:
    """动态提示树管理器 - SAGE风格"""
    
    def __init__(self):
        self.tree = {}
        self.current_node = None
    
    def build(self, user_request: str) -> Dict:
        """根据用户请求构建动态提示树"""
        # 初始化提示树
        self.tree = {
            "root": {
                "prompt": f"用户请求: {user_request}",
                "children": [],
                "depth": 0
            }
        }
        
        self.current_node = "root"
        return self.tree["root"]
    
    def add_child(self, parent_id: str, prompt: str, action: str) -> str:
        """添加子节点"""
        child_id = f"node_{len(self.tree)}"
        self.tree[child_id] = {
            "prompt": prompt,
            "action": action,
            "children": [],
            "depth": self.tree[parent_id]["depth"] + 1
        }
        
        self.tree[parent_id]["children"].append(child_id)
        return child_id
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点"""
        return self.tree.get(node_id)
    
    def get_current_prompt(self) -> str:
        """获取当前节点的提示"""
        if self.current_node and self.current_node in self.tree:
            return self.tree[self.current_node]["prompt"]
        return ""
    
    def move_to_child(self, child_id: str):
        """移动到子节点"""
        if child_id in self.tree:
            self.current_node = child_id
    
    def backtrack(self):
        """回溯到父节点"""
        # 查找当前节点的父节点
        for node_id, node in self.tree.items():
            if self.current_node in node["children"]:
                self.current_node = node_id
                return True
        return False
    
    def get_tree_structure(self) -> Dict:
        """获取提示树结构"""
        return self.tree