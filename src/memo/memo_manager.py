import json
import os
import time
import uuid
from datetime import datetime

class MemoManager:
    def __init__(self, base_dir=None):
        # 初始化备忘录存储目录
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'memos')
        self.base_dir = base_dir
        self._ensure_directory()
        # 初始化文件操作MCP
        from skills.mcp_skills.file_operations_mcp import file_operations_mcp
        self.file_operations = file_operations_mcp
    
    def _ensure_directory(self):
        """确保备忘录存储目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
    
    def create_memo(self, title, content, tags=None, priority='normal', category='personal'):
        """创建新备忘录
        
        Args:
            title: 备忘录标题
            content: 备忘录内容
            tags: 标签列表
            priority: 优先级 (high/normal/low)
            category: 分类 (personal/work/study/other)
            
        Returns:
            memo_id: 新创建的备忘录ID
        """
        # 生成唯一ID
        memo_id = str(uuid.uuid4())
        
        # 构建备忘录数据结构
        memo_data = {
            'id': memo_id,
            'title': title,
            'content': content,
            'tags': tags or [],
            'priority': priority,
            'category': category,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 生成唯一文件名
        filename = self._generate_unique_filename(memo_id)
        filepath = os.path.join(self.base_dir, filename)
        
        # 序列化并使用文件操作MCP保存
        memo_content = json.dumps(memo_data, ensure_ascii=False, indent=2)
        result = self.file_operations.create_file(filepath, memo_content, overwrite=False)
        
        # 检查操作结果
        if "错误" in result:
            raise Exception(f"创建备忘录文件失败: {result}")
        
        return memo_id
    
    def _generate_unique_filename(self, memo_id):
        """生成唯一的文件名"""
        timestamp = int(time.time() * 1000)
        return f"memo_{memo_id}_{timestamp}.json"
    
    def get_memo(self, memo_id):
        """获取备忘录
        
        Args:
            memo_id: 备忘录ID
            
        Returns:
            memo_data: 备忘录数据，如果不存在返回None
        """
        # 查找对应ID的备忘录文件
        for filename in os.listdir(self.base_dir):
            if f"memo_{memo_id}_" in filename and filename.endswith('.json'):
                filepath = os.path.join(self.base_dir, filename)
                # 使用文件操作MCP读取文件
                content = self.file_operations.read_file(filepath)
                if "错误" not in content:
                    return json.loads(content)
        return None
    
    def update_memo(self, memo_id, title=None, content=None, tags=None, priority=None, category=None):
        """更新备忘录
        
        Args:
            memo_id: 备忘录ID
            title: 新标题
            content: 新内容
            tags: 新标签列表
            priority: 新优先级
            category: 新分类
            
        Returns:
            bool: 更新是否成功
        """
        # 查找对应ID的备忘录文件
        for filename in os.listdir(self.base_dir):
            if f"memo_{memo_id}_" in filename and filename.endswith('.json'):
                filepath = os.path.join(self.base_dir, filename)
                
                # 读取现有数据
                file_content = self.file_operations.read_file(filepath)
                if "错误" in file_content:
                    return False
                memo_data = json.loads(file_content)
                
                # 更新字段
                if title is not None:
                    memo_data['title'] = title
                if content is not None:
                    memo_data['content'] = content
                if tags is not None:
                    memo_data['tags'] = tags
                if priority is not None:
                    memo_data['priority'] = priority
                if category is not None:
                    memo_data['category'] = category
                memo_data['updated_at'] = datetime.now().isoformat()
                
                # 写回文件
                memo_content = json.dumps(memo_data, ensure_ascii=False, indent=2)
                result = self.file_operations.create_file(filepath, memo_content, overwrite=True)
                if "错误" in result:
                    return False
                
                return True
        return False
    
    def delete_memo(self, memo_id):
        """删除备忘录
        
        Args:
            memo_id: 备忘录ID
            
        Returns:
            bool: 删除是否成功
        """
        # 查找对应ID的备忘录文件
        for filename in os.listdir(self.base_dir):
            if f"memo_{memo_id}_" in filename and filename.endswith('.json'):
                filepath = os.path.join(self.base_dir, filename)
                # 使用文件操作MCP删除文件
                result = self.file_operations.delete_file(filepath)
                if "错误" not in result:
                    return True
                else:
                    print(f"删除备忘录文件失败: {result}")
                    return False
        return False
    
    def list_memos(self, sort_by='updated_at', order='desc'):
        """列出所有备忘录
        
        Args:
            sort_by: 排序字段 (created_at/updated_at/priority)
            order: 排序顺序 (asc/desc)
            
        Returns:
            list: 备忘录列表
        """
        memos = []
        
        # 读取所有备忘录文件
        for filename in os.listdir(self.base_dir):
            if filename.endswith('.json') and filename.startswith('memo_'):
                filepath = os.path.join(self.base_dir, filename)
                try:
                    # 使用文件操作MCP读取文件
                    content = self.file_operations.read_file(filepath)
                    if "错误" not in content:
                        memo_data = json.loads(content)
                        memos.append(memo_data)
                except Exception as e:
                    print(f"读取备忘录文件 {filename} 时出错: {e}")
        
        # 排序
        if sort_by == 'priority':
            priority_order = {'high': 0, 'normal': 1, 'low': 2}
            memos.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 1), 
                      reverse=(order == 'desc'))
        else:
            memos.sort(key=lambda x: x.get(sort_by, ''), 
                      reverse=(order == 'desc'))
        
        return memos
    
    def search_memos(self, query):
        """搜索备忘录
        
        Args:
            query: 搜索关键词
            
        Returns:
            list: 匹配的备忘录列表
        """
        matched_memos = []
        query_lower = query.lower()
        
        for filename in os.listdir(self.base_dir):
            if filename.endswith('.json') and filename.startswith('memo_'):
                filepath = os.path.join(self.base_dir, filename)
                try:
                    # 使用文件操作MCP读取文件
                    content = self.file_operations.read_file(filepath)
                    if "错误" not in content:
                        memo_data = json.loads(content)
                        
                        # 检查标题、内容和标签是否包含搜索关键词
                        if (query_lower in memo_data.get('title', '').lower() or
                            query_lower in memo_data.get('content', '').lower() or
                            any(query_lower in tag.lower() for tag in memo_data.get('tags', []))):
                            matched_memos.append(memo_data)
                except Exception as e:
                    print(f"搜索时读取备忘录文件 {filename} 时出错: {e}")
        
        return matched_memos
