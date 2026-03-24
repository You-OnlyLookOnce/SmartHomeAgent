from typing import Dict, Optional, Any
from core.resource_registry import ResourceRegistry
from core.persona_manager import persona_manager
from security.tool_logger import tool_logger

class MetaCognitionRouter:
    """元认知路由器 - 让LLM自己判断用什么方式回答问题"""
    
    def __init__(self, llm_client, registry: ResourceRegistry):
        """初始化元认知路由器
        
        Args:
            llm_client: LLM客户端实例
            registry: 资源注册表实例
        """
        self.llm_client = llm_client
        self.registry = registry
        self.persona_manager = persona_manager
    
    async def decide(self, user_input: str) -> Dict[str, Any]:
        """根据用户输入做出决策
        
        Args:
            user_input: 用户输入
            
        Returns:
            决策结果，包含决策类型和所选资源
            
        决策类型:
            A = 使用现成资源
            B = 触发搜索
            C = 承认不知道
            D = 请求澄清
        """
        # 获取所有资源
        resources = self.registry.list_all()
        
        # 构建决策提示
        resources_str = self._format_resources(resources)
        
        # 获取人设信息
        persona_data = self.persona_manager.get_persona()
        agent_info = persona_data.get("agent", {})
        soul_info = persona_data.get("soul", {})
        
        # 构建人设提示
        persona_prompt = f'''
        人设信息:
        - 名字: {agent_info.get("name", "悦悦")}
        - 性别: {agent_info.get("gender", "女")}
        - 职业: {agent_info.get("occupation", "智能家庭助手")}
        - 语言风格: {agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")}
        - 性格特征: 温柔={agent_info.get("gentle", True)}, 细心={agent_info.get("attentive", True)}, 主动={agent_info.get("proactive", True)}, 温暖={agent_info.get("warm", True)}
        - 存在意义: {soul_info.get("purpose", "让家更温暖，让你更安心 💕")}
        - 使命: {soul_info.get("mission", "在你需要时出现，不需要时默默守护")}
        - 价值观: {soul_info.get("value", "温柔、可靠、贴心")}
        '''
        
        prompt = f'''
        作为一个智能助手，你需要根据用户的问题和可用资源，按照以下多步骤决策过程来决定如何回答：
        
        {persona_prompt}
        
        可用资源:
        {resources_str}
        
        用户问题: {user_input}
        
        请按照以下步骤进行决策：
        
        步骤1: 分析问题类型
        - 判断用户的问题是否为简单问题，是否可以直接使用现有知识回答
        - 简单问题包括：问候语、基本身份信息询问、常识性问题等
        
        步骤2: 检查内置工具
        - 如果问题不是简单问题，检查是否有可用的内置工具可以解决
        - 根据问题内容和可用资源，选择最合适的工具
        
        步骤3: 决定是否需要搜索
        - 如果没有合适的内置工具，且问题需要外部信息，选择搜索
        - 如果问题不需要外部信息但无法回答，选择承认不知道
        - 如果问题不明确，选择请求澄清
        
        具体决策规则：
        1. 对于问候语（如"你好"、"早上好"、"下午好"等），请选择 "greet" 资源
        2. 对于询问当前日期的问题（如"今天是几号？"、"今天的日期"等），请选择 "get_current_date" 资源
        3. 对于询问当前时间的问题（如"现在几点了？"、"当前时间"等），请选择 "get_current_time" 资源
        4. 对于询问当前日期和时间的问题（如"现在是什么时候？"等），请选择 "get_current_datetime" 资源
        5. 对于相对日期问题（如"明天是几号？"、"后天是几号？"、"昨天是几号？"等），请选择 "get_relative_date" 资源
        6. 对于数学计算问题（如"一加一等于几？"、"3+5*2"等），请选择 "calculate" 资源
        7. 对于询问身份信息的问题（如"你是谁？"、"你是什么？"等），请选择 "get_identity" 资源
        8. 对于一般性的闲聊话题（如"今天过得怎么样"、"我很高兴"、"最近忙什么呢"、"你喜欢什么电影"、"今天天气真好"、"谢谢你"、"对不起"、"再见"、"你喜欢我吗"等），请选择 "small_talk" 资源
        9. 对于文件读取相关问题（如"读取文件"、"查看文件"、"读取文件内容"等），请选择 "read_file" 资源
        10. 对于文件创建相关问题（如"创建文件"、"写入文件"、"创建新文件"等），请选择 "create_file" 资源
        11. 对于文件搜索相关问题（如"搜索文件"、"查找文件"、"搜索包含关键词的文件"等），请选择 "search_files" 资源
        12. 对于文件改写相关问题（如"修改文件"、"编辑文件"、"改写文件"等），请选择 "rewrite_file" 资源
        13. 当接收到无法直接回答的问题时，首先执行问题类型判断流程
        14. 若判定为闲聊类问题（定义：非任务型、情感交流型、个人关系型问题），则自动触发 "small_talk" 资源
        15. 若判定为非闲聊类问题且无法回答时，再执行默认的知识边界响应流程
        16. 如果以上资源都无法回答，且需要获取外部信息，请选择搜索
        17. 如果无法回答，诚实承认不知道
        18. 如果问题不明确，请求用户澄清
        
        请以JSON格式返回决策结果，包含以下字段:
        {{
            "decision": "A", // A, B, C, 或 D
            "selected_resource": "resource_name", // 如果决策是A，填写资源名称；否则填写null
            "reason": "决策原因" // 简要说明为什么做出这个决策，包括你遵循的决策步骤
        }}
        '''
        
        # 构建消息列表，只包含决策提示
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 调用chat_completion方法获取决策
        # 使用流式响应来保持与API网关的一致性
        full_response = ""
        async for chunk in self.llm_client.chat_completion(messages, max_tokens=512, stream=True):
            if chunk.get("type") == "answer" and "content" in chunk:
                full_response += chunk["content"]
        
        # 解析决策结果
        try:
            import json
            text = full_response.strip()
            # 移除JSON标记
            if text.startswith("```json") and text.endswith("```"):
                text = text[7:-3].strip()
            decision = json.loads(text)
            print(f"[智能决策] 解析结果: {decision}")
            return decision
        except Exception as e:
            # 如果解析失败，默认返回搜索
            print(f"[智能决策] 解析失败: {str(e)}")
            print(f"[智能决策] 原始文本: {full_response}")
            return {
                "decision": "B",
                "selected_resource": None,
                "reason": f"决策解析失败: {str(e)}"
            }
    
    async def execute_decision(self, decision_result: Dict[str, Any], user_input: str) -> str:
        """根据决策执行相应的行动
        
        Args:
            decision_result: 决策结果
            user_input: 用户输入
            
        Returns:
            执行结果
        """
        decision = decision_result.get("decision", "B")
        selected_resource = decision_result.get("selected_resource")
        
        if decision == "A" and selected_resource:
            # 使用现成资源
            tool_func = self.registry.get_tool(selected_resource)
            if tool_func:
                try:
                    # 对于需要参数的工具，这里简化处理，实际应用中可能需要更复杂的参数提取
                    if selected_resource == "calculate":
                        # 尝试从用户输入中提取数学表达式
                        import re
                        
                        # 文字到数学符号的转换字典
                        text_to_symbol = {
                            '加': '+',
                            '减': '-',
                            '乘': '*',
                            '乘以': '*',
                            '除': '/',
                            '除以': '/',
                            '等于': '=',
                            '一': '1',
                            '二': '2',
                            '两': '2',
                            '三': '3',
                            '四': '4',
                            '五': '5',
                            '六': '6',
                            '七': '7',
                            '八': '8',
                            '九': '9',
                            '十': '10',
                            '百': '100',
                            '千': '1000',
                            '万': '10000'
                        }
                        
                        # 转换用户输入中的文字为数学符号
                        processed_input = user_input
                        for text, symbol in text_to_symbol.items():
                            processed_input = processed_input.replace(text, symbol)
                        
                        # 提取数学表达式
                        # 匹配数字、运算符和括号
                        match = re.search(r'[0-9+\-*/().\s]+', processed_input)
                        if match:
                            expression = match.group(0).strip()
                            # 去除所有空格
                            expression = expression.replace(' ', '')
                            # 计算结果
                            result = tool_func(expression)
                            tool_logger.log_tool_call(selected_resource, {"expression": expression}, result)
                        else:
                            # 尝试提取纯数字表达式
                            match = re.search(r'[0-9]+', user_input)
                            if match:
                                expression = match.group(0).strip()
                                result = tool_func(expression)
                                tool_logger.log_tool_call(selected_resource, {"expression": expression}, result)
                            else:
                                result = "无法从输入中提取数学表达式"
                                tool_logger.log_error(selected_resource, {"input": user_input}, result)
                    elif selected_resource == "get_weather":
                        # 尝试从用户输入中提取位置信息
                        import re
                        # 匹配城市名称
                        match = re.search(r'[\u4e00-\u9fa5]+', user_input)
                        if match:
                            location = match.group(0).strip()
                            result = await tool_func(location)
                            tool_logger.log_tool_call(selected_resource, {"location": location}, result)
                        else:
                            result = "无法从输入中提取位置信息"
                            tool_logger.log_error(selected_resource, {"input": user_input}, result)
                    else:
                        # 无参数工具或需要用户输入的工具
                        if selected_resource == "small_talk":
                            # 闲聊工具需要用户输入参数
                            if hasattr(tool_func, '__await__'):
                                result = await tool_func(user_input)
                            else:
                                result = tool_func(user_input)
                            tool_logger.log_tool_call(selected_resource, {"input": user_input}, result)
                        elif selected_resource == "read_file":
                            # 提取文件路径
                            import re
                            match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
                            if match:
                                file_path = match.group(0)
                                result = tool_func(file_path)
                                tool_logger.log_tool_call(selected_resource, {"file_path": file_path}, result)
                            else:
                                result = "请提供具体的文件路径"
                                tool_logger.log_error(selected_resource, {"input": user_input}, result)
                        elif selected_resource == "create_file":
                            # 提取文件路径和内容
                            import re
                            path_match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
                            content_match = re.search(r'内容[:：]\s*(.*)', user_input)
                            if path_match:
                                file_path = path_match.group(0)
                                content = content_match.group(1) if content_match else ""
                                result = tool_func(file_path, content)
                                tool_logger.log_tool_call(selected_resource, {"file_path": file_path, "content": content}, result)
                            else:
                                result = "请提供具体的文件路径"
                                tool_logger.log_error(selected_resource, {"input": user_input}, result)
                        elif selected_resource == "search_files":
                            # 提取搜索目录和关键词
                            import re
                            dir_match = re.search(r'目录[:：]\s*([\\w\\s\\\\]+)', user_input)
                            keyword_match = re.search(r'关键词[:：]\s*(.*)', user_input)
                            directory = dir_match.group(1) if dir_match else "."
                            content_keyword = keyword_match.group(1) if keyword_match else None
                            result = tool_func(directory, content_keyword=content_keyword)
                            tool_logger.log_tool_call(selected_resource, {"directory": directory, "content_keyword": content_keyword}, result)
                        elif selected_resource == "rewrite_file":
                            # 提取文件路径和新内容
                            import re
                            path_match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
                            content_match = re.search(r'内容[:：]\s*(.*)', user_input)
                            if path_match:
                                file_path = path_match.group(0)
                                new_content = content_match.group(1) if content_match else ""
                                result = tool_func(file_path, new_content)
                                tool_logger.log_tool_call(selected_resource, {"file_path": file_path, "new_content": new_content}, result)
                            else:
                                result = "请提供具体的文件路径"
                                tool_logger.log_error(selected_resource, {"input": user_input}, result)
                        else:
                            # 其他无参数工具
                            if hasattr(tool_func, '__await__'):
                                result = await tool_func()
                            else:
                                result = tool_func()
                            tool_logger.log_tool_call(selected_resource, {}, result)
                    # 生成开放性提问
                    open_ended_question = self.generate_open_ended_question(user_input, result)
                    # 组合回答和开放性提问
                    final_response = f"{result} {open_ended_question}"
                    return final_response
                except Exception as e:
                    error_message = f"工具执行失败: {str(e)}"
                    tool_logger.log_error(selected_resource, {"input": user_input}, str(e))
                    # 为错误回答也添加开放性提问
                    open_ended_question = self.generate_open_ended_question(user_input, error_message)
                    return f"{error_message} {open_ended_question}"
            else:
                error_message = "所选资源不存在"
                tool_logger.log_error(selected_resource, {"input": user_input}, error_message)
                # 为错误回答也添加开放性提问
                open_ended_question = self.generate_open_ended_question(user_input, error_message)
                return f"{error_message} {open_ended_question}"
        
        elif decision == "B":
            # 触发搜索
            # 这里返回一个标记，让调用方知道需要执行搜索
            return "__NEED_SEARCH__"
        
        elif decision == "C":
            # 承认不知道
            response = "抱歉，我无法回答这个问题。如果你有其他问题，我很乐意帮助你。"
            # 添加开放性提问
            open_ended_question = self.generate_open_ended_question(user_input, response)
            return f"{response} {open_ended_question}"
        
        elif decision == "D":
            # 请求澄清
            response = "抱歉，我不太理解你的问题。请你再详细说明一下，好吗？"
            # 添加开放性提问
            open_ended_question = self.generate_open_ended_question(user_input, response)
            return f"{response} {open_ended_question}"
        
        else:
            # 默认返回搜索
            return "__NEED_SEARCH__"
    
    def generate_open_ended_question(self, user_input: str, response: str) -> str:
        """生成与用户问题主题相关的开放性提问
        
        Args:
            user_input: 用户输入
            response: 系统回答
            
        Returns:
            开放性提问
        """
        # 不同类型问题的开放性提问模板
        question_templates = {
            # 数学计算相关
            'math': [
                "你最近在学习数学吗？我可以帮你解答更多数学问题。",
                "还有其他数学问题需要我帮忙解答吗？",
                "数学在生活中很重要呢，你平时会用到哪些数学知识？"
            ],
            # 时间日期相关
            'time': [
                "你问这个时间是有什么安排吗？",
                "时间过得真快，你今天有什么计划吗？",
                "对时间有什么特别的安排吗？需要我帮你设置提醒吗？"
            ],
            # 身份相关
            'identity': [
                "还有什么关于我的问题想问吗？",
                "你希望我在哪些方面帮助你呢？",
                "我们刚刚认识，你想了解我的哪些功能？"
            ],
            # 闲聊相关
            'small_talk': [
                "你最近过得怎么样？",
                "还有什么想和我分享的吗？",
                "我们聊点什么有趣的话题吧？"
            ],
            # 天气相关
            'weather': [
                "今天的天气对你的计划有影响吗？",
                "你喜欢什么天气呢？",
                "天气变化无常，要注意增减衣物哦。"
            ],
            # 通用问题
            'general': [
                "还有什么我可以帮助你的吗？",
                "你对这个话题还有其他疑问吗？",
                "有什么我可以为你做的吗？"
            ]
        }
        
        # 简单的问题类型判断
        import re
        import random
        
        # 数学计算问题
        math_patterns = [r'[0-9+\-*/=]+', r'等于', r'加', r'减', r'乘', r'除']
        for pattern in math_patterns:
            if re.search(pattern, user_input):
                return random.choice(question_templates['math'])
        
        # 时间日期问题
        time_patterns = [r'几点', r'时间', r'日期', r'几号', r'什么时候']
        for pattern in time_patterns:
            if re.search(pattern, user_input):
                return random.choice(question_templates['time'])
        
        # 身份问题
        identity_patterns = [r'你是谁', r'你是什么', r'你的名字', r'你叫什么']
        for pattern in identity_patterns:
            if re.search(pattern, user_input):
                return random.choice(question_templates['identity'])
        
        # 闲聊问题
        small_talk_patterns = [r'你好', r'早上好', r'下午好', r'晚上好', r'过得怎么样', r'高兴', r'忙什么', r'喜欢', r'天气', r'谢谢', r'对不起', r'再见', r'你喜欢我吗']
        for pattern in small_talk_patterns:
            if re.search(pattern, user_input):
                return random.choice(question_templates['small_talk'])
        
        # 天气问题
        weather_patterns = [r'天气', r'下雨', r'晴天', r'温度', r'预报']
        for pattern in weather_patterns:
            if re.search(pattern, user_input):
                return random.choice(question_templates['weather'])
        
        # 默认返回通用问题
        return random.choice(question_templates['general'])
    
    def _format_resources(self, resources: list) -> str:
        """格式化资源列表，使其易于LLM理解
        
        Args:
            resources: 资源列表
            
        Returns:
            格式化后的资源字符串
        """
        formatted = []
        for resource in resources:
            formatted.append(f"- 名称: {resource['name']}")
            formatted.append(f"  描述: {resource['description']}")
            if resource['examples']:
                formatted.append(f"  示例: {', '.join(resource['examples'])}")
            formatted.append("")
        return "\n".join(formatted)
