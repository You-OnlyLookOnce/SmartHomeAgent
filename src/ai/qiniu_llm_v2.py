"""
七牛云 LLM 客户端 V2

支持 Function Calling 的新版本，集成七牛云 AI 大模型推理 API。
API 文档：https://developer.qiniu.com/aitokenapi/13379/real-time-ai-interface-api
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResponse:
    """工具调用响应"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatCompletionResponse:
    """聊天完成响应"""
    content: str
    tool_calls: Optional[List[ToolCallResponse]] = None
    model: str = ""
    usage: Optional[Dict[str, int]] = None


class QiniuLLMV2:
    """
    七牛云 LLM 客户端 V2
    
    支持：
    - 普通聊天完成
    - 流式响应
    - Function Calling
    - 工具调用
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.qnaigc.com/v1",
        model: str = "kimi-k2.5"
    ):
        """
        初始化客户端
        
        Args:
            api_key: API密钥，默认从环境变量获取
            base_url: API基础URL
            model: 默认模型
        """
        self.api_key = api_key or os.getenv('QINIU_AI_API_KEY') or os.getenv('QINIU_ACCESS_KEY')
        self.base_url = base_url.rstrip('/')
        self.model = model
        
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置 QINIU_AI_API_KEY 环境变量")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"QiniuLLM V2 初始化完成，模型: {model}")
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> ChatCompletionResponse:
        """
        聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式响应
            
        Returns:
            聊天完成响应
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API请求失败: {response.status} - {error_text}")
                        
                    data = await response.json()
                    
                    # 解析响应
                    choice = data['choices'][0]
                    message = choice['message']
                    
                    # 解析工具调用
                    tool_calls = None
                    if 'tool_calls' in message:
                        tool_calls = [
                            ToolCallResponse(
                                id=tc['id'],
                                name=tc['function']['name'],
                                arguments=json.loads(tc['function']['arguments'])
                            )
                            for tc in message['tool_calls']
                        ]
                        
                    return ChatCompletionResponse(
                        content=message.get('content', ''),
                        tool_calls=tool_calls,
                        model=data.get('model', ''),
                        usage=data.get('usage')
                    )
                    
        except Exception as e:
            logger.error(f"聊天完成请求失败: {e}")
            raise
            
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            流式响应块
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API请求失败: {response.status} - {error_text}")
                        
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if not line or line == 'data: [DONE]':
                            continue
                            
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    
                                    if 'content' in delta:
                                        yield {
                                            "type": "answer",
                                            "content": delta['content']
                                        }
                                    elif 'tool_calls' in delta:
                                        yield {
                                            "type": "tool_calls",
                                            "tool_calls": delta['tool_calls']
                                        }
                                        
                            except json.JSONDecodeError:
                                continue
                                
                    yield {"type": "stream_end"}
                    
        except Exception as e:
            logger.error(f"流式聊天完成请求失败: {e}")
            yield {"type": "error", "content": str(e)}
            
    async def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tool_choice: str = "auto"
    ) -> ChatCompletionResponse:
        """
        带工具调用的聊天完成（Function Calling）
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            tool_choice: 工具选择策略（"auto", "none", 或指定工具）
            
        Returns:
            聊天完成响应（可能包含工具调用）
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API请求失败: {response.status} - {error_text}")
                        
                    data = await response.json()
                    
                    # 解析响应
                    choice = data['choices'][0]
                    message = choice['message']
                    
                    # 解析工具调用
                    tool_calls = None
                    if 'tool_calls' in message and message['tool_calls']:
                        tool_calls = [
                            ToolCallResponse(
                                id=tc['id'],
                                name=tc['function']['name'],
                                arguments=tc['function']['arguments']
                            )
                            for tc in message['tool_calls']
                        ]
                        
                    return ChatCompletionResponse(
                        content=message.get('content', ''),
                        tool_calls=tool_calls,
                        model=data.get('model', ''),
                        usage=data.get('usage')
                    )
                    
        except Exception as e:
            logger.error(f"工具调用请求失败: {e}")
            raise
            
    async def web_search(
        self,
        query: str,
        search_type: str = "web",
        time_filter: Optional[str] = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        全网搜索
        
        API文档：https://developer.qiniu.com/aitokenapi/13192/web-search-api
        
        Args:
            query: 搜索关键词
            search_type: 搜索类型（"web", "video", "image"）
            time_filter: 时间过滤（"week", "month", "year", "semiyear"）
            max_results: 最大结果数
            
        Returns:
            搜索结果
        """
        url = f"{self.base_url}/web-search"
        
        payload = {
            "query": query,
            "search_type": search_type,
            "max_results": max_results
        }
        
        if time_filter:
            payload["time_filter"] = time_filter
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"搜索请求失败: {response.status} - {error_text}")
                        
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"搜索请求失败: {e}")
            raise
            
    def set_model(self, model: str) -> None:
        """
        设置默认模型
        
        Args:
            model: 模型名称
        """
        self.model = model
        logger.info(f"默认模型已设置为: {model}")
        
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            模型名称列表
        """
        # 七牛云支持的模型列表
        return [
            "kimi-k2.5",
            "kimi-k2",
            "kimi-k1.5",
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "gemini-2.5-flash",
            "gemini-2.5-flash-image"
        ]


# 便捷函数：创建默认客户端
def create_qiniu_llm_v2(
    api_key: Optional[str] = None,
    model: str = "kimi-k2.5"
) -> QiniuLLMV2:
    """
    创建七牛云 LLM 客户端 V2
    
    Args:
        api_key: API密钥
        model: 模型名称
        
    Returns:
        QiniuLLMV2 实例
    """
    return QiniuLLMV2(api_key=api_key, model=model)
