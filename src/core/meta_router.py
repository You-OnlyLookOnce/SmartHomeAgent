from typing import Dict, Optional, Any
from core.resource_registry import ResourceRegistry
from core.persona_manager import persona_manager
from core.device_command_parser import device_command_parser, is_device_command
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
            E = 设备控制
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
        13. 对于记录、保存内容的请求（如"帮我记录..."、"帮我保存..."、"记录一下..."等），如果内容需要外部信息支持（如食谱、新闻、事实信息等），请选择搜索
        14. 对于"帮我记录做西红柿炒鸡蛋的做法"这样的请求，由于需要获取外部信息来了解具体做法，应该选择决策类型 "B"（触发搜索）
        15. 对于需要创建备忘录的请求，只有当用户已经提供了完整的内容时，才选择决策类型 "A" 和 "create_memo" 资源；如果需要外部信息支持，应该先选择决策类型 "B"（触发搜索）
        15. 当接收到无法直接回答的问题时，首先执行问题类型判断流程
        16. 若判定为闲聊类问题（定义：非任务型、情感交流型、个人关系型问题），则自动触发 "small_talk" 资源
        17. 若判定为非闲聊类问题且无法回答时，再执行默认的知识边界响应流程
        18. 如果以上资源都无法回答，且需要获取外部信息，请选择搜索
        19. 如果无法回答，诚实承认不知道
        20. 如果问题不明确，请求用户澄清
        
        设备控制相关决策规则（规则21-30）：
        21. 对于台灯控制指令（如"打开台灯"、"关闭台灯"、"台灯调亮一点"、"台灯调暗一点"、"客厅灯太亮了"、"把台灯调暗一点"、"台灯色温调到护眼模式"等），请选择决策类型 "E"（设备控制），并在 device_info 中包含设备类型 "lamp"、操作类型和参数
        22. 对于空调控制指令（如"打开空调"、"关闭空调"、"把空调调到26度"、"打开空调制冷模式"、"空调风速调到3挡"、"温度调高一点"等），请选择决策类型 "E"（设备控制），并在 device_info 中包含设备类型 "ac"、操作类型和参数
        23. 对于窗帘控制指令（如"打开窗帘"、"关闭窗帘"、"窗帘关到一半"、"窗帘开到50%"等），请选择决策类型 "E"（设备控制），并在 device_info 中包含设备类型 "curtain"、操作类型和参数
        24. 对于包含设备关键词（如"灯"、"台灯"、"空调"、"窗帘"、"温度"、"亮度"等）的指令，请先判断是否为设备控制指令，如果是则选择决策类型 "E"
        25. 对于"把XX的灯打开/关闭"这样的指令，识别设备位置/名称，选择决策类型 "E"
        26. 对于调节类指令（如"调亮"、"调暗"、"调温"、"调速"等），如果涉及设备，选择决策类型 "E"
        27. 对于"太亮了"、"太暗了"、"太热了"、"太冷了"等环境感受描述，视为设备控制指令，选择决策类型 "E"
        28. 设备控制指令的返回格式必须包含：decision="E"、device_info（包含device_type、operation、params、device_name）
        29. 如果无法确定具体设备或操作，但明显是设备控制意图，选择决策类型 "E" 并在 reason 中说明
        30. 设备控制指令不需要搜索，直接通过设备管理器执行
        
        请以JSON格式返回决策结果，包含以下字段:
        {{
            "decision": "A", // A, B, C, D 或 E
            "selected_resource": "resource_name", // 如果决策是A，填写资源名称；否则填写null
            "device_info": {{ // 如果决策是E（设备控制），填写设备信息；否则填写null
                "device_type": "lamp|ac|curtain",
                "device_name": "设备名称或位置",
                "operation": "操作类型",
                "params": {{}}
            }},
            "reason": "决策原因" // 简要说明为什么做出这个决策，包括你遵循的决策步骤
        }}
        
        注意：在返回JSON之前，请先使用设备指令解析器分析用户输入，如果解析结果置信度>=0.5且识别到设备类型，则直接返回决策类型 "E"。
        '''
        
        # 首先使用设备指令解析器进行预处理
        parsed_command = device_command_parser.parse(user_input)
        print(f"[智能决策] 设备指令解析结果: {parsed_command.to_dict()}")
        
        # 如果解析结果置信度>=0.5且识别到设备类型，直接返回设备控制决策
        if parsed_command.confidence >= 0.5 and parsed_command.device_type.value != "unknown":
            print(f"[智能决策] 识别为设备控制指令，置信度: {parsed_command.confidence}")
            return {
                "decision": "E",
                "selected_resource": None,
                "device_info": {
                    "device_type": parsed_command.device_type.value,
                    "device_name": parsed_command.device_name,
                    "operation": parsed_command.operation.value,
                    "params": parsed_command.params
                },
                "reason": f"识别到设备控制指令: {parsed_command.device_type.value} - {parsed_command.operation.value}，置信度: {parsed_command.confidence:.2f}"
            }
        
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
        
        elif decision == "E":
            # 设备控制
            return await self._execute_device_control(decision_result, user_input)
        
        else:
            # 默认返回搜索
            return "__NEED_SEARCH__"
    
    async def _execute_device_control(self, decision_result: Dict[str, Any], user_input: str) -> str:
        """执行设备控制
        
        执行流程：
        1. 从决策结果中提取设备信息
        2. 查找或创建设备
        3. 执行控制命令
        4. 返回执行结果反馈
        
        Args:
            decision_result: 决策结果，包含device_info
            user_input: 用户输入
            
        Returns:
            执行结果反馈
        """
        device_info = decision_result.get("device_info", {})
        device_type = device_info.get("device_type")
        device_name = device_info.get("device_name", "")
        operation = device_info.get("operation")
        params = device_info.get("params", {})
        
        print(f"[设备控制] 执行控制: type={device_type}, name={device_name}, op={operation}, params={params}")
        
        try:
            # 导入设备管理器
            from src.core.device_manager import device_manager
            
            # 查找现有设备
            all_devices = await device_manager.get_all_devices()
            target_device = None
            
            # 优先根据设备名称/位置查找
            if device_name:
                for device in all_devices.get("data", []):
                    if device_name in device.get("device_name", ""):
                        target_device = device
                        break
            
            # 如果没有找到，根据设备类型查找第一个匹配的设备
            if not target_device:
                for device in all_devices.get("data", []):
                    if device.get("device_type") == device_type:
                        target_device = device
                        break
            
            # 如果没有找到设备，自动创建一个默认设备
            if not target_device:
                print(f"[设备控制] 未找到设备，自动创建默认设备: {device_type}")
                
                # 生成设备ID
                import uuid
                device_id = f"{device_type}_{uuid.uuid4().hex[:8]}"
                default_name = device_name if device_name else f"默认{self._get_device_type_name(device_type)}"
                
                # 创建设备
                create_result = await device_manager.create_device(
                    device_type=device_type,
                    device_id=device_id,
                    device_name=default_name
                )
                
                if create_result.get("success"):
                    target_device = create_result.get("data")
                    print(f"[设备控制] 设备创建成功: {device_id}")
                else:
                    error_msg = f"设备创建失败: {create_result.get('message', '未知错误')}"
                    print(f"[设备控制] {error_msg}")
                    return f"{error_msg} 有什么其他我可以帮你的吗？"
            
            device_id = target_device.get("device_id")
            
            # 将操作类型映射为设备命令
            command = self._map_operation_to_command(operation, params)
            
            if not command:
                return f"抱歉，我不确定如何执行这个操作。你可以尝试说得更具体一些吗？"
            
            # 执行命令
            print(f"[设备控制] 发送命令: device={device_id}, command={command['command']}, params={command.get('params', {})}")
            result = await device_manager.execute_command(
                device_id=device_id,
                command=command["command"],
                params=command.get("params", {})
            )
            
            # 生成反馈消息
            if result.get("success"):
                feedback = self._generate_success_feedback(device_type, operation, params, target_device.get("device_name", ""))
            else:
                feedback = f"操作失败: {result.get('message', '未知错误')}"
            
            print(f"[设备控制] 执行结果: {feedback}")
            
            # 添加开放性提问
            open_ended_question = self.generate_open_ended_question(user_input, feedback)
            return f"{feedback} {open_ended_question}"
            
        except Exception as e:
            error_msg = f"设备控制执行失败: {str(e)}"
            print(f"[设备控制] {error_msg}")
            import traceback
            traceback.print_exc()
            open_ended_question = self.generate_open_ended_question(user_input, error_msg)
            return f"{error_msg} {open_ended_question}"
    
    def _get_device_type_name(self, device_type: str) -> str:
        """获取设备类型中文名称"""
        type_names = {
            "lamp": "台灯",
            "ac": "空调",
            "curtain": "窗帘"
        }
        return type_names.get(device_type, device_type)
    
    def _map_operation_to_command(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """将操作类型映射为设备命令
        
        Args:
            operation: 操作类型
            params: 参数
            
        Returns:
            命令字典 {"command": str, "params": dict}
        """
        # 台灯操作映射
        lamp_commands = {
            "turn_on": {"command": "power_on", "params": {}},
            "turn_off": {"command": "power_off", "params": {}},
            "set_brightness": {"command": "set_brightness", "params": {"brightness": params.get("brightness", 50)}},
            "set_color_temp": {"command": "set_color_temp", "params": {"color_temp": params.get("color_temp", "normal")}},
        }
        
        # 空调操作映射
        ac_commands = {
            "turn_on": {"command": "power_on", "params": {}},
            "turn_off": {"command": "power_off", "params": {}},
            "set_temperature": {"command": "set_temperature", "params": {"temperature": params.get("temperature", 26)}},
            "set_mode": {"command": "set_mode", "params": {"mode": params.get("mode", "cool")}},
            "set_fan_speed": {"command": "set_fan_speed", "params": {"fan_speed": params.get("fan_speed", 3)}},
        }
        
        # 窗帘操作映射
        curtain_commands = {
            "turn_on": {"command": "open", "params": {}},
            "turn_off": {"command": "close", "params": {}},
            "open": {"command": "open", "params": {}},
            "close": {"command": "close", "params": {}},
            "stop": {"command": "stop", "params": {}},
            "set_position": {"command": "set_position", "params": {"position": params.get("position", 50)}},
        }
        
        # 根据操作类型选择对应的命令映射
        if operation in lamp_commands:
            return lamp_commands[operation]
        elif operation in ac_commands:
            return ac_commands[operation]
        elif operation in curtain_commands:
            return curtain_commands[operation]
        
        return None
    
    def _generate_success_feedback(self, device_type: str, operation: str, params: Dict[str, Any], device_name: str) -> str:
        """生成成功反馈消息
        
        Args:
            device_type: 设备类型
            operation: 操作类型
            params: 参数
            device_name: 设备名称
            
        Returns:
            反馈消息
        """
        name_prefix = f"{device_name}" if device_name else ""
        
        if device_type == "lamp":
            if operation == "turn_on":
                return f"{name_prefix}已打开，希望这个亮度适合你"
            elif operation == "turn_off":
                return f"{name_prefix}已关闭，早点休息哦"
            elif operation == "set_brightness":
                brightness = params.get("brightness", 50)
                if brightness < 30:
                    return f"{name_prefix}亮度已调暗到{brightness}%，适合休息"
                elif brightness > 70:
                    return f"{name_prefix}亮度已调高到{brightness}%，阅读更清晰"
                else:
                    return f"{name_prefix}亮度已调到{brightness}%"
            elif operation == "set_color_temp":
                color_temp = params.get("color_temp", "normal")
                if color_temp == "eye_care":
                    return f"{name_prefix}已切换到护眼模式，保护视力"
                else:
                    return f"{name_prefix}色温已调整"
                    
        elif device_type == "ac":
            if operation == "turn_on":
                return f"{name_prefix}已开启，马上就会凉快了"
            elif operation == "turn_off":
                return f"{name_prefix}已关闭，节能环保"
            elif operation == "set_temperature":
                temp = params.get("temperature", 26)
                return f"{name_prefix}温度已调到{temp}度，舒适宜人"
            elif operation == "set_mode":
                mode = params.get("mode", "cool")
                mode_names = {"cool": "制冷", "heat": "制热", "dry": "除湿", "fan": "送风", "auto": "自动"}
                return f"{name_prefix}已切换到{mode_names.get(mode, mode)}模式"
            elif operation == "set_fan_speed":
                speed = params.get("fan_speed", 3)
                return f"{name_prefix}风速已调到{speed}档"
                
        elif device_type == "curtain":
            if operation in ["turn_on", "open"]:
                return f"{name_prefix}已打开，阳光照进来了"
            elif operation in ["turn_off", "close"]:
                return f"{name_prefix}已关闭，保护隐私"
            elif operation == "set_position":
                position = params.get("position", 50)
                if position == 50:
                    return f"{name_prefix}已关到一半，光线刚刚好"
                else:
                    return f"{name_prefix}位置已调到{position}%"
            elif operation == "stop":
                return f"{name_prefix}已停止"
        
        return f"{name_prefix}操作已完成"
    
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
