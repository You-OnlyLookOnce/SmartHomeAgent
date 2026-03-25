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
        description="获取当前日期和时间，格式为YYYY-MM-DD HH:MM:SS，用于回答'现在是什么时候？'、'当前时间'等需要同时知道日期和时间的问题",
        tool_func=get_current_datetime,
        examples=["现在是什么时候？", "当前时间", "现在的日期和时间", "现在几点几分？", "现在的具体时间", "今天现在几点？", "现在是几号几点？"]
    )
    
    registry.register(
        name="get_current_date",
        description="获取当前日期，格式为YYYY-MM-DD，用于回答'今天是几号？'、'今天的日期'等只需要日期信息的问题",
        tool_func=get_current_date,
        examples=["今天是几号？", "今天的日期", "现在是什么日期", "今天是几月几号？", "今天是哪一天？", "今天几号？", "今天的具体日期"]
    )
    
    registry.register(
        name="get_current_time",
        description="获取当前时间，格式为HH:MM:SS，用于回答'现在几点了？'、'当前时间'等只需要时间信息的问题",
        tool_func=get_current_time,
        examples=["现在几点了？", "当前时间", "现在的时间", "现在几点钟？", "现在的具体时间", "现在几点？", "当前几点？"]
    )
    
    registry.register(
        name="calculate",
        description="计算数学表达式，支持基本算术操作（加、减、乘、除），用于回答数学计算问题",
        tool_func=calculate,
        examples=["一加一等于几？", "3+5*2", "100除以5", "25减10", "4乘以6", "100加200", "50除以2"]
    )
    
    registry.register(
        name="get_identity",
        description="获取智能体的身份信息，用于回答'你是谁？'、'你是什么？'等关于智能体身份的问题",
        tool_func=get_identity,
        examples=["你是谁？", "你是什么？", "你的名字", "你叫什么名字？", "你是做什么的？", "你的身份是什么？", "你是什么类型的助手？"]
    )
    
    registry.register(
        name="greet",
        description="回复用户的问候语，用于回答'你好'、'早上好'、'下午好'等问候语",
        tool_func=greet,
        examples=["你好", "你好啊", "早上好", "下午好", "晚上好", "嗨", "哈喽", "嗨你好", "你好呀", "早上好呀", "下午好呀", "晚上好呀"]
    )
    
    registry.register(
        name="get_relative_date",
        description="处理相对日期问题，用于回答'明天是几号'、'后天是几号'、'昨天是几号'等相对日期问题",
        tool_func=get_relative_date,
        examples=["明天是几号", "后天是几号", "昨天是几号", "前天是几号", "明天的日期", "后天的日期", "昨天的日期", "前天的日期"]
    )
    
    # 注册本地时间工具
    try:
        from src.skills.mcp_skills.simple_local_time_tool import simple_local_time_tool
        
        # 注册本地时间工具
        registry.register(
            name="get_local_time",
            description="获取当前时间和日期信息，包括年、月、日、时、分、秒，用于回答'现在是什么时候？'、'当前时间'等时间相关问题",
            tool_func=simple_local_time_tool.get_time,
            examples=["现在是什么时候？", "当前时间", "现在的日期和时间", "现在几点几分？", "现在的具体时间", "今天现在几点？", "现在是几号几点？"]
        )
    except Exception as e:
        print(f"注册本地时间工具失败: {str(e)}")
    
    # 注册本地天气工具
    try:
        from src.skills.mcp_skills.simple_local_weather_tool import simple_local_weather_tool
        
        # 注册天气工具
        registry.register(
            name="get_weather",
            description="获取指定位置的天气信息，包括温度、天气状况、湿度、风力等详细信息，用于回答'北京的天气怎么样？'、'上海今天天气如何？'等天气相关问题",
            tool_func=simple_local_weather_tool.get_weather,
            examples=["北京的天气怎么样？", "上海今天天气如何？", "广州的天气", "深圳今天的温度", "杭州的天气状况", "成都今天天气好吗？", "武汉的天气如何？"]
        )
    except Exception as e:
        print(f"注册本地天气工具失败: {str(e)}")
    
    # 注册闲聊工具
    try:
        from src.skills.mcp_skills.small_talk_tool import get_small_talk_response
        
        # 注册闲聊工具
        registry.register(
            name="small_talk",
            description="处理一般性的闲聊话题，如问候、情感表达、日常对话、兴趣爱好、天气相关、赞美、感谢、道歉、告别等，用于回答'你好'、'今天过得怎么样'、'我很高兴'等闲聊类问题",
            tool_func=get_small_talk_response,
            examples=["你好", "今天过得怎么样", "我很高兴", "最近忙什么呢", "你喜欢什么电影", "今天天气真好", "谢谢你", "对不起", "再见"]
        )
    except Exception as e:
        print(f"注册闲聊工具失败: {str(e)}")
    
    # 注册文件操作MCP工具
    try:
        from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp
        
        # 注册文件读取工具
        registry.register(
            name="read_file",
            description="读取文件内容，用于回答'读取文件'、'查看文件'等文件读取相关问题",
            tool_func=file_operations_mcp.read_file,
            examples=["读取文件 D:\\test.txt", "查看文件内容", "读取文件内容"]
        )
        
        # 注册文件创建工具
        registry.register(
            name="create_file",
            description="创建文件，用于回答'创建文件'、'写入文件'等文件创建相关问题",
            tool_func=file_operations_mcp.create_file,
            examples=["创建文件 D:\\test.txt", "写入文件内容", "创建新文件"]
        )
        
        # 注册文件搜索工具
        registry.register(
            name="search_files",
            description="搜索文件，用于回答'搜索文件'、'查找文件'等文件搜索相关问题",
            tool_func=file_operations_mcp.search_files,
            examples=["搜索文件", "查找文件", "搜索包含关键词的文件"]
        )
        
        # 注册文件改写工具
        registry.register(
            name="rewrite_file",
            description="改写文件内容，用于回答'修改文件'、'编辑文件'等文件改写相关问题",
            tool_func=file_operations_mcp.rewrite_file,
            examples=["修改文件", "编辑文件内容", "改写文件"]
        )
    except Exception as e:
        print(f"注册文件操作MCP工具失败: {str(e)}")
    
    # 注册备忘录工具
    try:
        from src.memo.memo_manager import MemoManager
        memo_manager = MemoManager()
        
        # 注册创建备忘录工具
        registry.register(
            name="create_memo",
            description="创建新备忘录，用于回答'创建备忘录'、'新建备忘录'等备忘录创建相关问题",
            tool_func=memo_manager.create_memo,
            examples=["创建备忘录", "新建备忘录", "创建一个关于会议的备忘录"]
        )
        
        # 注册获取备忘录工具
        registry.register(
            name="get_memo",
            description="获取单个备忘录，用于回答'获取备忘录'、'查看备忘录'等备忘录获取相关问题",
            tool_func=memo_manager.get_memo,
            examples=["获取备忘录", "查看备忘录", "获取备忘录详情"]
        )
        
        # 注册更新备忘录工具
        registry.register(
            name="update_memo",
            description="更新备忘录，用于回答'更新备忘录'、'修改备忘录'等备忘录更新相关问题",
            tool_func=memo_manager.update_memo,
            examples=["更新备忘录", "修改备忘录", "编辑备忘录内容"]
        )
        
        # 注册删除备忘录工具
        registry.register(
            name="delete_memo",
            description="删除备忘录，用于回答'删除备忘录'、'移除备忘录'等备忘录删除相关问题",
            tool_func=memo_manager.delete_memo,
            examples=["删除备忘录", "移除备忘录", "删除这个备忘录"]
        )
        
        # 注册列出备忘录工具
        registry.register(
            name="list_memos",
            description="列出所有备忘录，用于回答'列出备忘录'、'查看所有备忘录'等备忘录列表相关问题",
            tool_func=memo_manager.list_memos,
            examples=["列出备忘录", "查看所有备忘录", "获取备忘录列表"]
        )
        
        # 注册搜索备忘录工具
        registry.register(
            name="search_memos",
            description="搜索备忘录，用于回答'搜索备忘录'、'查找备忘录'等备忘录搜索相关问题",
            tool_func=memo_manager.search_memos,
            examples=["搜索备忘录", "查找备忘录", "搜索包含关键词的备忘录"]
        )
    except Exception as e:
        print(f"注册备忘录工具失败: {str(e)}")
    
    return registry

# 创建默认注册表实例
registry = create_default_registry()
