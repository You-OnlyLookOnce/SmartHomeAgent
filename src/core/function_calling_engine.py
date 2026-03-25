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
        
        if not tool_definitions:
            logger.warning("没有注册任何工具，将直接调用LLM生成回复")
            async for chunk in self._direct_llm_response(message, context, stream):
                yield chunk
            return
            
        # 构建系统提示词
        system_prompt = self._build_system_prompt(context)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # 调用LLM进行Function Calling
        logger.info(f"开始Function Calling决策，用户消息: {message[:50]}...")
        
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
                    yield chunk
            else:
                logger.info("LLM决定不调用工具，直接生成回复")
                async for chunk in self._direct_llm_response(message, context, stream):
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
            yield {"type": "answer", "content": response.content}
            
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
