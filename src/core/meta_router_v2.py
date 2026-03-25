"""
元认知路由器 V2

基于 LLM Function Calling 的新一代决策引擎。
移除所有人工规则，完全由 LLM 自主决策。
"""

from typing import Dict, Optional, Any, AsyncGenerator, Union
import logging
from src.core.mcp_tool_registry import mcp_registry
from src.core.function_calling_engine import FunctionCallingEngine
from src.agent.memory_manager import MemoryManager
from src.core.personality import permanent_personality_core, output_personality_polisher

# 导入并注册所有 MCP 工具
import src.core.mcp_tools_init

logger = logging.getLogger(__name__)


class MetaCognitionRouterV2:
    """
    元认知路由器 V2
    
    基于 Function Calling 的智能决策引擎，完全由 LLM 自主决策：
    1. 接收用户输入
    2. 调用 LLM Function Calling 决定使用哪些工具
    3. 执行工具并获取结果
    4. 生成最终回复
    
    不再使用 A/B/C/D/E 决策类型和人工规则。
    """
    
    def __init__(self, llm_client):
        """
        初始化元认知路由器 V2
        
        Args:
            llm_client: LLM 客户端实例（需要支持 Function Calling）
        """
        self.llm_client = llm_client
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager()
        
        # 初始化人格核心模块
        self.personality_core = permanent_personality_core
        
        # 初始化人格化润色器
        self.polisher = output_personality_polisher
        
        # 与长期记忆模块一同完成初始化流程
        self.personality_core.initialize_with_long_term_memory(self.memory_manager.memory_system.long_term_memory)
        
        # 创建 Function Calling 引擎
        self.engine = FunctionCallingEngine(llm_client)
        
        # 注册所有 MCP 工具
        self._register_all_tools()
        
        logger.info("MetaCognitionRouterV2 初始化完成")
        
    def _register_all_tools(self):
        """注册所有 MCP 工具到引擎"""
        for tool_name in mcp_registry.get_tool_names():
            tool = mcp_registry.get_tool(tool_name)
            if tool:
                self.engine.register_tool(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters,
                    handler=tool.handler
                )
                
        registered_count = len(self.engine.get_registered_tools())
        logger.info(f"已注册 {registered_count} 个工具到决策引擎")
        
    async def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            context: 上下文信息（包含 soul、agent、profile 等）
            stream: 是否使用流式响应
            
        Yields:
            处理过程中的各种事件和最终结果
        """
        context = context or {}
        session_id = context.get("session_id", "default_session")
        
        logger.info(f"开始处理用户输入: {user_input[:50]}...")
        logger.info(f"stream参数: {stream}")
        logger.info(f"会话ID: {session_id}")
        
        try:
            # 1. 用户输入接收阶段
            # 将用户输入内容完整写入对话记忆模块
            self.memory_manager.process_user_input(session_id, user_input)
            logger.info("用户输入已写入对话记忆")
            
            # 2. ReAct循环处理阶段 - 记忆整合步骤
            # 从四个记忆模块中读取全部相关信息
            memory_context = self.memory_manager.get_memory_context(session_id)
            logger.info("获取记忆上下文完成")
            
            # 整合上下文
            combined_context = {
                **context,
                **memory_context
            }
            
            # 3. 使用 Function Calling 引擎处理（决策判断步骤）
            logger.info("调用engine.process_message...")
            
            # 存储最终回复
            final_response = ""
            
            async for chunk in self.engine.process_message(
                message=user_input,
                context=combined_context,
                stream=stream
            ):
                logger.info(f"收到chunk: {chunk}")
                
                # 处理工具调用结果
                if chunk.get("type") == "tool_result":
                    # 3.3 工具调用分支
                    # 工具执行完成后，将完整调用结果写入执行记忆模块
                    tool_name = chunk.get("tool_name")
                    parameters = chunk.get("parameters", {})
                    result = chunk.get("result", {})
                    
                    if tool_name:
                        self.memory_manager.process_tool_execution(session_id, tool_name, parameters, result)
                        logger.info(f"工具执行记录已写入执行记忆: {tool_name}")
                
                # 收集最终回复
                if chunk.get("type") == "answer":
                    final_response += chunk.get("content", "")
                
                # 对于流式响应，直接 yield 原始 chunk
                # 人格化润色将在所有 chunk 收集完成后进行
                yield chunk
            
            # 4. 最终回复生成阶段
            # 对回复内容进行人格化润色
            if final_response:
                # 使用人格化润色器处理回复内容
                polished_response = self.polisher.polish(final_response)
                logger.info(f"人格化润色完成，原始长度: {len(final_response)}, 润色后长度: {len(polished_response)}")
                
                # 将润色后的智能体回复内容写入对话记忆模块
                self.memory_manager.process_agent_response(session_id, polished_response)
                logger.info("智能体回复已写入对话记忆")
                
                # 替换最终回复为润色后的版本
                final_response = polished_response
                
        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "content": f"抱歉，处理你的请求时出现了错误: {str(e)}"
            }
            
    async def process_with_tools(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        处理用户输入（非流式，返回完整结果）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            完整回复
        """
        logger.info(f"process_with_tools 被调用，用户输入: {user_input[:50]}...")
        
        try:
            # 调用 process 方法处理用户输入
            # 由于 process 方法已经在内部处理了人格化润色
            # 我们需要一个新的方法来获取润色后的完整结果
            # 这里直接返回最终的润色结果
            
            # 临时存储最终回复
            final_response = ""
            error_response = None
            
            async for chunk in self.process(user_input, context, stream=False):
                logger.info(f"收到chunk: {chunk}")
                if chunk.get("type") == "answer":
                    final_response += chunk.get("content", "")
                elif chunk.get("type") == "error":
                    error_response = chunk.get("content", "抱歉，处理失败了")
            
            if error_response:
                return error_response
            
            # 对最终回复进行人格化润色
            if final_response:
                polished_response = self.polisher.polish(final_response)
                logger.info(f"人格化润色完成，原始长度: {len(final_response)}, 润色后长度: {len(polished_response)}")
                return polished_response
            else:
                return "抱歉，我没有理解你的意思"
        except Exception as e:
            logger.error(f"process_with_tools 出错: {e}")
            return f"抱歉，处理失败了: {str(e)}"
        
    async def _process_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理流式响应
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Yields:
            处理过程中的各种事件和最终结果
        """
        async for chunk in self.process(user_input, context, stream=True):
            yield chunk
        
    async def _process_non_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理非流式响应
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            包含完整回复的字典
        """
        full_response = []
        error_response = None
        
        async for chunk in self.process(user_input, context, stream=False):
            if chunk.get("type") == "answer":
                full_response.append(chunk.get("content", ""))
            elif chunk.get("type") == "error":
                error_response = chunk.get("content", "抱歉，处理失败了")
        
        if error_response:
            return {"content": error_response}
        
        final_response = "".join(full_response) if full_response else "抱歉，我没有理解你的意思"
        
        # 对最终回复进行人格化润色
        if final_response != "抱歉，我没有理解你的意思":
            polished_response = self.polisher.polish(final_response)
            return {"content": polished_response}
        else:
            return {"content": final_response}
        
    def get_available_tools(self) -> list:
        """
        获取可用工具列表
        
        Returns:
            工具名称列表
        """
        return self.engine.get_registered_tools()
        
    def add_tool(self, name: str, description: str, parameters: dict, handler):
        """
        动态添加工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义
            handler: 处理函数
        """
        self.engine.register_tool(name, description, parameters, handler)
        logger.info(f"动态添加工具: {name}")
        
    def remove_tool(self, name: str):
        """
        移除工具
        
        Args:
            name: 工具名称
        """
        # FunctionCallingEngine 暂不支持移除工具，可以通过重新创建引擎实现
        logger.warning(f"移除工具功能暂未实现: {name}")
