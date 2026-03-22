from typing import Dict, List, Optional, Callable, Any

class ResourceRegistry:
    """资源注册表 - 管理所有可用能力"""
    
    def __init__(self):
        """初始化资源注册表"""
        self.resources: Dict[str, Dict] = {}
    
    def register(self, name: str, description: str, tool_func: Callable, examples: List[str] = None):
        """注册新资源
        
        Args:
            name: 资源名称
            description: 资源描述，要让LLM能理解什么时候使用
            tool_func: 工具函数
            examples: 使用示例
        """
        if examples is None:
            examples = []
        
        self.resources[name] = {
            "name": name,
            "description": description,
            "tool_func": tool_func,
            "examples": examples
        }
    
    def list_all(self) -> List[Dict]:
        """列出所有资源供LLM阅读
        
        Returns:
            资源列表
        """
        return list(self.resources.values())
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """根据名称获取工具
        
        Args:
            name: 资源名称
            
        Returns:
            工具函数，如果不存在返回None
        """
        resource = self.resources.get(name)
        if resource:
            return resource.get("tool_func")
        return None
    
    def get_resource(self, name: str) -> Optional[Dict]:
        """根据名称获取资源
        
        Args:
            name: 资源名称
            
        Returns:
            资源信息，如果不存在返回None
        """
        return self.resources.get(name)
    
    def has_resource(self, name: str) -> bool:
        """检查资源是否存在
        
        Args:
            name: 资源名称
            
        Returns:
            是否存在
        """
        return name in self.resources

def create_default_registry() -> ResourceRegistry:
    """创建默认资源注册表，包含基础能力
    
    Returns:
        资源注册表实例
    """
    registry = ResourceRegistry()
    
    # 导入工具函数
    import datetime
    import math
    
    # 时间日期工具
    def get_current_datetime() -> str:
        """获取当前日期和时间"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_current_date() -> str:
        """获取当前日期"""
        return datetime.date.today().strftime("%Y-%m-%d")
    
    def get_current_time() -> str:
        """获取当前时间"""
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    # 计算器工具
    def calculate(expression: str) -> str:
        """计算数学表达式
        
        Args:
            expression: 数学表达式
            
        Returns:
            计算结果
        """
        try:
            # 安全计算，只允许基本算术操作
            result = eval(expression, {"__builtins__": None}, {"math": math})
            return str(result)
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    # 身份信息工具
    def get_identity() -> str:
        """获取智能体身份信息"""
        return "我是悦悦，你的智能助手！我是一个由人工智能驱动的智能体，旨在帮助你解答各种问题，提供信息，以及与你进行友好的交流。"
    
    # 打招呼工具
    def greet() -> str:
        """回复用户的问候语"""
        import random
        greetings = [
            "你好！很高兴见到你！",
            "嗨！你好啊！",
            "你好，有什么可以帮你的吗？",
            "哈喽！今天过得怎么样？",
            "你好呀！有什么我可以协助你的吗？"
        ]
        return random.choice(greetings)
    
    # 相对日期处理工具
    def get_relative_date() -> str:
        """处理相对日期问题，如'明天是几号'、'后天是几号'等"""
        import datetime
        today = datetime.date.today()
        
        # 构建相对日期映射
        relative_dates = {
            '明天': today + datetime.timedelta(days=1),
            '后天': today + datetime.timedelta(days=2),
            '昨天': today + datetime.timedelta(days=-1),
            '前天': today + datetime.timedelta(days=-2)
        }
        
        # 返回相对日期信息
        result = []
        for key, date in relative_dates.items():
            result.append(f"{key}是{date.strftime('%Y-%m-%d')}")
        return '; '.join(result)
    
    # 注册基础资源
    registry.register(
        name="get_current_datetime",
        description="获取当前日期和时间，格式为YYYY-MM-DD HH:MM:SS，用于回答'现在是什么时候？'、'当前时间'等问题",
        tool_func=get_current_datetime,
        examples=["现在是什么时候？", "当前时间", "现在的日期和时间", "现在几点几分？", "现在的具体时间"]
    )
    
    registry.register(
        name="get_current_date",
        description="获取当前日期，格式为YYYY-MM-DD，用于回答'今天是几号？'、'今天的日期'等问题",
        tool_func=get_current_date,
        examples=["今天是几号？", "今天的日期", "现在是什么日期", "今天是几月几号？", "今天是哪一天？"]
    )
    
    registry.register(
        name="get_current_time",
        description="获取当前时间，格式为HH:MM:SS，用于回答'现在几点了？'、'当前时间'等问题",
        tool_func=get_current_time,
        examples=["现在几点了？", "当前时间", "现在的时间", "现在几点钟？", "现在的具体时间"]
    )
    
    registry.register(
        name="calculate",
        description="计算数学表达式，支持基本算术操作",
        tool_func=calculate,
        examples=["一加一等于几？", "3+5*2", "100除以5"]
    )
    
    registry.register(
        name="get_identity",
        description="获取智能体的身份信息",
        tool_func=get_identity,
        examples=["你是谁？", "你是什么？", "你的名字"]
    )
    
    registry.register(
        name="greet",
        description="回复用户的问候语，用于回答'你好'、'早上好'、'下午好'等问候语",
        tool_func=greet,
        examples=["你好", "你好啊", "早上好", "下午好", "晚上好", "嗨", "哈喽"]
    )
    
    registry.register(
        name="get_relative_date",
        description="处理相对日期问题，用于回答'明天是几号'、'后天是几号'、'昨天是几号'等相对日期问题",
        tool_func=get_relative_date,
        examples=["明天是几号", "后天是几号", "昨天是几号", "前天是几号"]
    )
    
    return registry

# 创建默认注册表实例
registry = create_default_registry()
