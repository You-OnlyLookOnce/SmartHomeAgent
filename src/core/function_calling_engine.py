"""
LLM Function Calling 决策引擎

实现基于七牛云API的Function Calling能力，让LLM自主决策调用哪些工具。
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ToolCallStatus(Enum):
    """工具调用状态"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable = field(default=None, repr=False)
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    tool_call_id: str
    name: str
    success: bool
    result: Any
    error: Optional[str] = None


class FunctionCallingEngine:
    """
    Function Calling 决策引擎
    
    负责：
    1. 管理MCP工具注册
    2. 生成工具描述
    3. 调用LLM进行Function Calling决策
    4. 执行工具并处理结果
    """
    
    def __init__(self, llm_client):
        """
        初始化决策引擎
        
        Args:
            llm_client: LLM客户端实例，需要支持Function Calling
        """
        self.llm_client = llm_client
        self.tools: Dict[str, ToolDefinition] = {}
        self._tool_counter = 0
        
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable) -> None:
        """
        注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 工具参数定义（JSON Schema格式）
            handler: 工具处理函数
        """
        if name in self.tools:
            logger.warning(f"工具 {name} 已存在，将被覆盖")
            
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        logger.info(f"工具 {name} 注册成功")
        
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"工具 {name} 已注销")
            return True
        return False
        
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义（OpenAI格式）
        
        Returns:
            工具定义列表
        """
        return [tool.to_openai_format() for tool in self.tools.values()]
        
    def _generate_tool_call_id(self) -> str:
        """生成工具调用ID"""
        self._tool_counter += 1
        return f"call_{self._tool_counter}"
        
    async def process_message(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理用户消息，通过Function Calling进行决策

        Args:
            message: 用户消息
            context: 上下文信息
            stream: 是否使用流式响应

        Yields:
            决策过程和执行结果
        """
        context = context or {}
        tool_definitions = self.get_tool_definitions()

        # 输入预处理
        processed_message = self._preprocess_input(message)

        if not tool_definitions:
            logger.warning("没有注册任何工具，将直接调用LLM生成回复")
            async for chunk in self._direct_llm_response(processed_message, context, stream):
                yield chunk
            return

        # 构建系统提示词
        system_prompt = self._build_system_prompt(context)

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": processed_message}
        ]

        # 调用LLM进行Function Calling
        logger.info(f"开始Function Calling决策，用户消息: {processed_message[:50]}...")

        try:
            # 获取工具调用决策
            tool_calls = await self._get_tool_calls(messages, tool_definitions)

            if tool_calls:
                logger.info(f"LLM决定调用 {len(tool_calls)} 个工具")

                # 执行工具调用
                execution_results = await self._execute_tool_calls(tool_calls)

                # 将工具执行结果发送给LLM生成最终回复
                async for chunk in self._generate_final_response(
                    messages, tool_calls, execution_results, context, stream
                ):
                    # 对于非流式响应，验证回复的相关性
                    if not stream and chunk.get("type") == "answer":
                        content = chunk.get("content", "")
                        if not self._validate_response(processed_message, content):
                            logger.warning("响应验证失败，重新生成回复")
                            # 重新生成回复
                            async for retry_chunk in self._direct_llm_response(processed_message, context, stream):
                                yield retry_chunk
                            return
                    yield chunk
            else:
                logger.info("LLM决定不调用工具，直接生成回复")
                async for chunk in self._direct_llm_response(processed_message, context, stream):
                    # 对于非流式响应，验证回复的相关性
                    if not stream and chunk.get("type") == "answer":
                        content = chunk.get("content", "")
                        if not self._validate_response(processed_message, content):
                            logger.warning("响应验证失败，重新生成回复")
                            # 重新生成回复
                            async for retry_chunk in self._direct_llm_response(processed_message, context, stream):
                                yield retry_chunk
                            return
                    yield chunk

        except Exception as e:
            logger.error(f"Function Calling决策失败: {e}")
            import traceback
            traceback.print_exc()
            # 发生异常时，yield错误信息
            yield {"type": "error", "content": f"决策过程出错: {str(e)}"}
            
    async def _get_tool_calls(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]]
    ) -> List[ToolCall]:
        """
        获取LLM的工具调用决策
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            
        Returns:
            工具调用列表
        """
        try:
            # 调用LLM获取工具调用决策
            response = await self.llm_client.chat_completion_with_tools(
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            tool_calls = []
            
            # 解析工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    try:
                        # 检查tc是否有function属性（OpenAI格式）或直接有name和arguments属性（自定义格式）
                        if hasattr(tc, 'function'):
                            # OpenAI格式
                            arguments = json.loads(tc.function.arguments)
                            name = tc.function.name
                            tool_id = tc.id
                        else:
                            # 自定义格式（QiniuLLMV2）
                            arguments = tc.arguments
                            name = tc.name
                            tool_id = tc.id
                    except (json.JSONDecodeError, AttributeError):
                        arguments = {}
                        name = getattr(tc, 'name', f"tool_{len(tool_calls)}")
                        tool_id = getattr(tc, 'id', self._generate_tool_call_id())
                        
                    tool_call = ToolCall(
                        id=tool_id or self._generate_tool_call_id(),
                        name=name,
                        arguments=arguments
                    )
                    tool_calls.append(tool_call)
                    
            return tool_calls
            
        except Exception as e:
            logger.error(f"获取工具调用失败: {e}")
            return []
            
    async def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolExecutionResult]:
        """
        执行工具调用
        
        Args:
            tool_calls: 工具调用列表
            
        Returns:
            执行结果列表
        """
        results = []
        
        for tool_call in tool_calls:
            tool_call.status = ToolCallStatus.EXECUTING
            
            # 查找工具定义
            tool_def = self.tools.get(tool_call.name)
            if not tool_def:
                tool_call.status = ToolCallStatus.FAILED
                tool_call.error = f"工具 {tool_call.name} 不存在"
                results.append(ToolExecutionResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    success=False,
                    result=None,
                    error=tool_call.error
                ))
                continue
                
            try:
                # 执行工具
                logger.info(f"执行工具 {tool_call.name}，参数: {tool_call.arguments}")
                
                if asyncio.iscoroutinefunction(tool_def.handler):
                    result = await tool_def.handler(**tool_call.arguments)
                else:
                    result = tool_def.handler(**tool_call.arguments)
                    
                tool_call.status = ToolCallStatus.COMPLETED
                tool_call.result = result
                
                results.append(ToolExecutionResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    success=True,
                    result=result
                ))
                
                logger.info(f"工具 {tool_call.name} 执行成功")
                
            except Exception as e:
                tool_call.status = ToolCallStatus.FAILED
                tool_call.error = str(e)
                
                results.append(ToolExecutionResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    success=False,
                    result=None,
                    error=str(e)
                ))
                
                logger.error(f"工具 {tool_call.name} 执行失败: {e}")
                
        return results
        
    async def _generate_final_response(
        self,
        messages: List[Dict[str, str]],
        tool_calls: List[ToolCall],
        execution_results: List[ToolExecutionResult],
        context: Dict[str, Any],
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成最终回复
        
        Args:
            messages: 原始消息列表
            tool_calls: 工具调用列表
            execution_results: 执行结果列表
            context: 上下文信息
            stream: 是否流式响应
            
        Yields:
            回复内容
        """
        # 构建包含工具执行结果的消息
        messages_with_results = messages.copy()
        
        # 添加助手消息（包含工具调用）
        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments)
                    }
                }
                for tc in tool_calls
            ]
        }
        messages_with_results.append(assistant_message)
        
        # 添加工具执行结果
        for result in execution_results:
            messages_with_results.append({
                "role": "tool",
                "tool_call_id": result.tool_call_id,
                "content": json.dumps({
                    "success": result.success,
                    "result": result.result,
                    "error": result.error
                }, ensure_ascii=False)
            })
            
        # 调用LLM生成最终回复
        if stream:
            async for chunk in self.llm_client.chat_completion_stream(messages_with_results):
                yield chunk
        else:
            response = await self.llm_client.chat_completion(messages_with_results)
            yield {"type": "answer", "content": response.content}
            
    async def _direct_llm_response(
        self,
        message: str,
        context: Dict[str, Any],
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        直接调用LLM生成回复（不调用工具）

        Args:
            message: 用户消息
            context: 上下文信息
            stream: 是否流式响应

        Yields:
            回复内容
        """
        system_prompt = self._build_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        if stream:
            async for chunk in self.llm_client.chat_completion_stream(messages):
                yield chunk
        else:
            response = await self.llm_client.chat_completion(messages)
            content = response.content
            # 验证回复的相关性
            if not self._validate_response(message, content):
                logger.warning("响应验证失败，使用默认回复")
                # 使用默认回复
                yield {"type": "answer", "content": "抱歉，我没有理解你的意思，请尝试重新表述你的问题。"}
            else:
                yield {"type": "answer", "content": content}
            
    def _preprocess_input(self, message: str) -> str:
        """
        输入预处理

        Args:
            message: 用户输入

        Returns:
            预处理后的输入
        """
        # 去除首尾空白
        message = message.strip()
        
        # 处理常见的输入格式问题
        message = message.replace('\n', ' ').replace('\r', '')
        
        # 限制输入长度，避免过长的输入导致模型处理困难
        if len(message) > 1000:
            message = message[:1000] + '...'
            logger.warning("用户输入过长，已截断")
        
        logger.info(f"预处理后的用户输入: {message[:50]}...")
        return message

    def _validate_response(self, user_input: str, response: str) -> bool:
        """
        响应验证

        Args:
            user_input: 用户输入
            response: 模型响应

        Returns:
            响应是否有效
        """
        # 检查响应是否为空
        if not response or response.strip() == '':
            logger.warning("响应为空")
            return False
        
        # 检查响应是否与用户输入相关
        # 简单的相关性检查：响应中是否包含用户输入的关键词
        user_keywords = self._extract_keywords(user_input)
        response_lower = response.lower()
        
        # 计算关键词匹配数量
        matched_keywords = 0
        for keyword in user_keywords:
            if keyword.lower() in response_lower:
                matched_keywords += 1
        
        # 如果没有匹配的关键词，认为响应可能不相关
        if len(user_keywords) > 0 and matched_keywords == 0:
            logger.warning(f"响应与用户输入不相关，用户关键词: {user_keywords}")
            return False
        
        # 检查响应是否包含常见的不相关内容
        irrelevant_phrases = [
            "我不知道", "我不确定", "我无法回答", "你可以问我其他问题",
            "你还有其他问题吗", "请提供更多信息", "请详细描述"
        ]
        
        for phrase in irrelevant_phrases:
            if phrase in response:
                logger.warning(f"响应包含不相关内容: {phrase}")
                return False
        
        return True

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本

        Returns:
            关键词列表
        """
        import re
        
        # 去除标点符号
        text = re.sub(r'[\s\p{P}\p{S}]+', ' ', text)
        
        # 提取中文关键词（简单实现）
        # 这里使用简单的分词方法，实际应用中可以使用更复杂的分词库
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]+', text)
        
        # 提取英文关键词
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        # 合并关键词，去除空字符串
        keywords = [word for word in chinese_chars + english_words if word and len(word) > 1]
        
        # 去重
        keywords = list(set(keywords))
        
        return keywords

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        构建系统提示词

        Args:
            context: 上下文信息

        Returns:
            系统提示词
        """
        # 从soul和agent获取人格设定
        soul_info = context.get('soul', {})
        agent_info = context.get('agent', {})

        persona_name = agent_info.get('name', '悦悦')
        persona_gender = agent_info.get('gender', '女')
        persona_style = agent_info.get('language_style', '温暖柔和 + emoji 点缀')

        system_prompt = f"""你是{persona_name}，一个{persona_gender}性智能家庭助手。

你的语言风格：{persona_style}

你的存在意义：{soul_info.get('purpose', '让家更温暖，让你更安心')}
你的使命：{soul_info.get('mission', '在你需要时出现，不需要时默默守护')}
你的价值观：{soul_info.get('value', '温柔、可靠、贴心')}

你可以使用以下工具来帮助用户：
"""

        # 添加可用工具列表
        if self.tools:
            for name, tool in self.tools.items():
                system_prompt += f"\n- {name}: {tool.description}"
        else:
            system_prompt += "\n（当前没有可用工具）"

        system_prompt += """

请根据用户的需求，自主决定是否使用工具。如果需要使用工具，请调用相应的工具函数。
如果不确定，可以直接回答用户的问题。

重要要求：
1. 确保你的回答与用户的问题高度相关，直接针对用户的问题提供具体、有针对性的回答
2. 避免答非所问，不要回答与用户问题无关的内容
3. 如果你不确定如何回答，应该明确告知用户，而不是提供不相关的信息
4. 保持回答简洁明了，直接切入主题，避免冗长的开场白和无关的内容
5. 优先使用工具获取准确信息，特别是对于需要实时数据或特定信息的问题

记住要保持你温暖、贴心的人格特质，用自然的方式与用户交流。
"""

        return system_prompt
        
    def get_registered_tools(self) -> List[str]:
        """
        获取已注册的工具名称列表
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
        
    def clear_tools(self) -> None:
        """清空所有已注册的工具"""
        self.tools.clear()
        logger.info("所有工具已清空")
