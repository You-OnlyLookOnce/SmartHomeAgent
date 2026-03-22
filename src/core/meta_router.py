from typing import Dict, Optional, Any
from src.core.resource_registry import ResourceRegistry
from src.core.persona_manager import persona_manager

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
        作为一个智能助手，你需要根据用户的问题和可用资源，决定如何回答。
        
        {persona_prompt}
        
        可用资源:
        {resources_str}
        
        用户问题: {user_input}
        
        请根据以下规则做出决策:
        1. 对于问候语（如"你好"、"早上好"、"下午好"等），请选择 "greet" 资源
        2. 对于询问当前日期的问题（如"今天是几号？"、"今天的日期"等），请选择 "get_current_date" 资源
        3. 对于询问当前时间的问题（如"现在几点了？"、"当前时间"等），请选择 "get_current_time" 资源
        4. 对于询问当前日期和时间的问题（如"现在是什么时候？"等），请选择 "get_current_datetime" 资源
        5. 对于相对日期问题（如"明天是几号？"、"后天是几号？"、"昨天是几号？"等），请选择 "get_relative_date" 资源
        6. 对于数学计算问题（如"一加一等于几？"、"3+5*2"等），请选择 "calculate" 资源
        7. 对于询问身份信息的问题（如"你是谁？"、"你是什么？"等），请选择 "get_identity" 资源
        8. 如果以上资源都无法回答，且需要获取外部信息，请选择搜索
        9. 如果无法回答，诚实承认不知道
        10. 如果问题不明确，请求用户澄清
        
        请以JSON格式返回决策结果，包含以下字段:
        {{
            "decision": "A", // A, B, C, 或 D
            "selected_resource": "resource_name", // 如果决策是A，填写资源名称；否则填写null
            "reason": "决策原因" // 简要说明为什么做出这个决策
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
        result = await self.llm_client.chat_completion(messages, max_tokens=512, stream=False)
        
        # 解析决策结果
        try:
            if result.get("success", False):
                import json
                text = result.get("text", "{}")
                # 移除JSON标记
                text = text.strip()
                if text.startswith("```json") and text.endswith("```"):
                    text = text[7:-3].strip()
                decision = json.loads(text)
                print(f"[智能决策] 解析结果: {decision}")
                return decision
            else:
                # 如果LLM调用失败，默认返回搜索
                print(f"[智能决策] LLM调用失败: {result.get('error', '未知错误')}")
                return {
                    "decision": "B",
                    "selected_resource": None,
                    "reason": "LLM决策失败，默认选择搜索"
                }
        except Exception as e:
            # 如果解析失败，默认返回搜索
            print(f"[智能决策] 解析失败: {str(e)}")
            print(f"[智能决策] 原始文本: {result.get('text', '{}')}")
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
                        else:
                            # 尝试提取纯数字表达式
                            match = re.search(r'[0-9]+', user_input)
                            if match:
                                expression = match.group(0).strip()
                                result = tool_func(expression)
                            else:
                                result = "无法从输入中提取数学表达式"
                    else:
                        # 无参数工具
                        result = tool_func()
                    return result
                except Exception as e:
                    return f"工具执行失败: {str(e)}"
            else:
                return "所选资源不存在"
        
        elif decision == "B":
            # 触发搜索
            # 这里返回一个标记，让调用方知道需要执行搜索
            return "__NEED_SEARCH__"
        
        elif decision == "C":
            # 承认不知道
            return "抱歉，我无法回答这个问题。如果你有其他问题，我很乐意帮助你。"
        
        elif decision == "D":
            # 请求澄清
            return "抱歉，我不太理解你的问题。请你再详细说明一下，好吗？"
        
        else:
            # 默认返回搜索
            return "__NEED_SEARCH__"
    
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
