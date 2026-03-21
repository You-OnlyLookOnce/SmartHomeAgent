import os
import json
import aiohttp
import logging
from dotenv import load_dotenv
from typing import Dict, Optional, Any, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QiniuLLM:
    """七牛云大模型客户端（真实API调用）"""
    
    def __init__(self, model_type: str = "decision"):
        """初始化七牛云大模型
        
        Args:
            model_type: 模型类型，可选值："decision"（决策模型）或 "expert"（专家模型）
        """
        load_dotenv()
        # 七牛云 AI API 需要使用专门的 API Key，而不是普通的 Access Key
        self.api_key = os.getenv('QINIU_AI_API_KEY', os.getenv('QINIU_ACCESS_KEY'))
        
        # 从配置文件读取模型设置
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "modules", "model_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            if "model" in config and model_type in config["model"]:
                model_config = config["model"][model_type]
                self.model = model_config.get("name", "qwen-max")
                self.temperature = model_config.get("temperature", 0.7)
                self.max_tokens = model_config.get("max_tokens", 2048)
            else:
                # 默认值
                self.model = "qwen-max"
                self.temperature = 0.7
                self.max_tokens = 2048
        except Exception as e:
            logger.error(f"Failed to read model config: {e}")
            # 使用默认值
            self.model = "qwen-max"
            self.temperature = 0.7
            self.max_tokens = 2048
        
        # 七牛云AI API的正确接入点（兼容OpenAI API）
        self.api_url = "https://api.qnaigc.com/v1/chat/completions"
        
        # 记录初始化信息（不暴露敏感信息）
        logger.info(f"QiniuLLM initialized with model: {self.model}")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"API key configured: {self.api_key is not None}")
        logger.info(f"API key length: {len(self.api_key) if self.api_key else 0}")
    
    async def _handle_api_error(self, response, error_data=None):
        """处理API错误
        
        Args:
            response: HTTP响应对象
            error_data: 已解析的错误数据
            
        Returns:
            错误信息字典
        """
        try:
            if error_data is None:
                # 尝试读取响应文本
                response_text = await response.text()
                logger.error(f"Response text: {response_text}")
                try:
                    error_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接使用响应文本
                    return {
                        "success": False,
                        "error": f"API error: {response.status} - {response_text}"
                    }
            # 处理不同的错误格式
            if isinstance(error_data, dict):
                if 'error' in error_data and isinstance(error_data['error'], dict):
                    # 错误信息在error.message中
                    error_message = error_data['error'].get('message', 'Unknown error')
                else:
                    # 错误信息直接在message中
                    error_message = error_data.get('message', 'Unknown error')
            else:
                error_message = str(error_data)
            logger.error(f"API error: {response.status} - {error_message}")
            
            # 提供更详细的错误信息和解决方案
            if "API key format is incorrect" in error_message:
                error_message = "API key format is incorrect. Please ensure you are using a valid Qiniu AI API key, not an ordinary Access Key or OpenAI key."
            elif "Unauthorized" in error_message:
                error_message = "Authentication failed. Please check your API key and ensure it has the correct permissions."
            elif "not found" in error_message.lower() or "invalid model" in error_message.lower():
                error_message = "Model not found or invalid. Please check the model ID."
            elif "rate limit" in error_message.lower() or "429" in str(response.status):
                error_message = "Rate limit exceeded. Please try again later or contact Qiniu support to increase your quota."
            elif "timeout" in error_message.lower():
                error_message = "Request timeout. Please try again with a shorter prompt or increase the timeout setting."
            elif "internal server error" in error_message.lower() or "500" in str(response.status):
                error_message = "Internal server error. Please try again later."
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to parse error response: {e}")
        
        return {
            "success": False,
            "error": f"API error: {response.status} - {error_message}"
        }
    
    def _check_api_key(self):
        """检查API密钥是否配置
        
        Returns:
            错误信息字典，如果API密钥配置正确则返回None
        """
        if not self.api_key:
            error_msg = "API key is not configured. Please set QINIU_AI_API_KEY or QINIU_ACCESS_KEY in .env file."
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        return None
    
    async def _api_request(self, method: str, url: str, headers: dict = None, data: dict = None, params: dict = None, max_retries: int = 3, timeout: int = 30) -> Dict[str, Any]:
        """通用API请求方法，包含重试机制
        
        Args:
            method: HTTP方法，如"GET"、"POST"
            url: API地址
            headers: 请求头
            data: 请求体数据
            params: 查询参数
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
            
        Returns:
            API响应结果
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 设置超时
                timeout_obj = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                    
                    # 根据方法类型发送请求
                    if method == "GET":
                        async with session.get(url, headers=headers, params=params) as response:
                            logger.info(f"API request {method} {url} - Status: {response.status}")
                            
                            # 检查响应状态
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    return {
                                        "success": True,
                                        "data": data
                                    }
                                except Exception as e:
                                    logger.error(f"Failed to parse response JSON: {e}")
                                    return {
                                        "success": False,
                                        "error": f"Failed to parse response: {e}"
                                    }
                            elif response.status == 429:  # 限流错误，需要重试
                                logger.warning(f"Rate limit exceeded, retrying... ({retry_count + 1}/{max_retries})")
                                retry_count += 1
                                # 等待一段时间后重试
                                import asyncio
                                await asyncio.sleep(2 ** retry_count)  # 指数退避
                            else:
                                # 其他错误，不重试
                                return await self._handle_api_error(response)
                    elif method == "POST":
                        async with session.post(url, headers=headers, json=data) as response:
                            logger.info(f"API request {method} {url} - Status: {response.status}")
                            
                            # 检查响应状态
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    return {
                                        "success": True,
                                        "data": data
                                    }
                                except Exception as e:
                                    logger.error(f"Failed to parse response JSON: {e}")
                                    return {
                                        "success": False,
                                        "error": f"Failed to parse response: {e}"
                                    }
                            elif response.status == 429:  # 限流错误，需要重试
                                logger.warning(f"Rate limit exceeded, retrying... ({retry_count + 1}/{max_retries})")
                                retry_count += 1
                                # 等待一段时间后重试
                                import asyncio
                                await asyncio.sleep(2 ** retry_count)  # 指数退避
                            else:
                                # 其他错误，不重试
                                return await self._handle_api_error(response)
                    else:
                        return {
                            "success": False,
                            "error": f"Unsupported HTTP method: {method}"
                        }
            except aiohttp.ClientError as e:
                # 网络错误，重试
                logger.warning(f"Network error: {e}, retrying... ({retry_count + 1}/{max_retries})")
                retry_count += 1
                # 等待一段时间后重试
                import asyncio
                await asyncio.sleep(2 ** retry_count)  # 指数退避
            except Exception as e:
                # 其他错误，不重试
                logger.error(f"Exception during API request: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # 达到最大重试次数
        return {
            "success": False,
            "error": f"Maximum retries ({max_retries}) exceeded"
        }
    
    def generate_text(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, stream: bool = False, tools: list = None):
        """生成文本
        
        Args:
            prompt: 提示词
            context: 上下文对话历史
            max_tokens: 最大生成 token 数
            stream: 是否启用流式响应
            tools: 可供模型调用的工具定义列表
            
        Returns:
            如果stream为True，返回一个生成器，否则返回一个可等待对象
        """
        if stream:
            return self._generate_text_stream(prompt, context, max_tokens, tools)
        else:
            return self._generate_text_non_stream(prompt, context, max_tokens, tools)
    
    async def _generate_text_stream(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, tools: list = None):
        """生成文本（流式响应）"""
        # 检查API密钥
        api_key_check = self._check_api_key()
        if api_key_check:
            yield {
                "type": "error",
                "content": api_key_check["error"]
            }
            return
            
        try:
            logger.info(f"generate_text called with prompt: {prompt[:50]}...")
            logger.info(f"Context length: {len(context) if context else 0}")
            # 构建消息列表
            messages = []
            
            # 添加系统消息
            system_message = {
                "role": "system",
                "content": "你是悦悦，一个具有独特个性的智能助手。请根据用户的问题提供详细、有用的回答。当遇到需要实时信息或超出你知识库的问题时，请使用提供的工具进行查询。"
            }
            messages.append(system_message)
            
            # 添加上下文消息
            if context:
                for msg in context:
                    if "user" in msg:
                        messages.append({"role": "user", "content": msg["user"]})
                    elif "assistant" in msg:
                        messages.append({"role": "assistant", "content": msg["assistant"]})
                    elif "system" in msg:
                        messages.append({"role": "system", "content": msg["system"]})
                    elif "summary" in msg:
                        # 处理摘要信息
                        messages.append({"role": "system", "content": f"对话摘要：{msg['summary']}"})
            
            # 添加用户当前问题
            messages.append({"role": "user", "content": prompt})
            
            # 调用API
            logger.info(f"Calling chat_completion with {len(messages)} messages")
            async for chunk in self.chat_completion(messages, max_tokens, stream=True, tools=tools):
                yield chunk
            
        except Exception as e:
            logger.error(f"Exception in generate_text: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }
    
    async def _generate_text_non_stream(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, tools: list = None):
        """生成文本（非流式响应）"""
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"generate_text called with prompt: {prompt[:50]}...")
            logger.info(f"Context length: {len(context) if context else 0}")
            # 构建消息列表
            messages = []
            
            # 添加系统消息
            system_message = {
                "role": "system",
                "content": "你是悦悦，一个具有独特个性的智能助手。请根据用户的问题提供详细、有用的回答。当遇到需要实时信息或超出你知识库的问题时，请使用提供的工具进行查询。"
            }
            messages.append(system_message)
            
            # 添加上下文消息
            if context:
                for msg in context:
                    if "user" in msg:
                        messages.append({"role": "user", "content": msg["user"]})
                    elif "assistant" in msg:
                        messages.append({"role": "assistant", "content": msg["assistant"]})
                    elif "system" in msg:
                        messages.append({"role": "system", "content": msg["system"]})
                    elif "summary" in msg:
                        # 处理摘要信息
                        messages.append({"role": "system", "content": f"对话摘要：{msg['summary']}"})
            
            # 添加用户当前问题
            messages.append({"role": "user", "content": prompt})
            
            # 调用API
            logger.info(f"Calling chat_completion with {len(messages)} messages")
            # 非流式响应时，收集所有chunk并返回完整响应
            full_response = ""
            async for chunk in self.chat_completion(messages, max_tokens, stream=True, tools=tools):
                if chunk.get("type") == "answer" and "content" in chunk:
                    full_response += chunk["content"]
            
            if full_response:
                return {
                    "success": True,
                    "text": full_response
                }
            else:
                return {
                    "success": False,
                    "error": "No response from model"
                }
            
        except Exception as e:
            logger.error(f"Exception in generate_text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def chat_completion(self, messages: list, max_tokens: int = 1024, stream: bool = False, tools: list = None, tool_choice: str = "auto"):
        """聊天完成
        
        Args:
            messages: 消息列表，包含角色和内容
            max_tokens: 最大生成 token 数
            stream: 是否启用流式响应
            tools: 可供模型调用的工具定义列表
            tool_choice: 工具调用策略，可选值："none", "auto", "required"或指定具体工具
            
        Returns:
            生成的文本和相关信息
        """
        if stream:
            return self._chat_completion_stream(messages, max_tokens, tools, tool_choice)
        else:
            return self._chat_completion_non_stream(messages, max_tokens, tools, tool_choice)
    
    async def _chat_completion_stream(self, messages: list, max_tokens: int = 1024, tools: list = None, tool_choice: str = "auto"):
        """聊天完成（流式响应）"""
        print("chat_completion called")
        print(f"API URL: {self.api_url}")
        print(f"Model: {self.model}")
        print(f"API Key: {'***' if self.api_key else 'Not configured'}")
        print(f"API Key length: {len(self.api_key) if self.api_key else 0}")
        print(f"Stream: True, Tools: {tools}, Tool choice: {tool_choice}")
        
        # 检查API密钥
        api_key_check = self._check_api_key()
        if api_key_check:
            yield {
                "type": "error",
                "content": api_key_check["error"]
            }
            return
        
        try:
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "top_p": 0.95,
                "stream": True
            }
            
            # 添加工具调用参数
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            logger.info(f"Sending API request to: {self.api_url}")
            logger.info(f"Messages count: {len(messages)}")
            logger.info(f"First message: {json.dumps(messages[0], ensure_ascii=False) if messages else 'None'}")
            # 不打印完整headers，避免暴露敏感信息
            logger.info("Headers: Content-Type and Authorization set")
            
            # 流式响应需要特殊处理，不使用通用API请求方法
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    logger.info(f"Response status: {response.status}")
                    # 不打印完整headers，避免暴露敏感信息
                    logger.info("Response headers received")
                    
                    try:
                        # 实时处理流式响应
                        buffer = b''
                        has_content = False
                        async for chunk in response.content:
                            if chunk:
                                buffer += chunk
                                # 处理SSE格式的数据
                                lines = buffer.split(b'\n')
                                buffer = lines.pop()  # 保留不完整的最后一行
                                
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith(b'data: '):
                                        data_str = line[6:].decode('utf-8')
                                        if data_str == '[DONE]':
                                            continue
                                        if data_str:
                                            try:
                                                data = json.loads(data_str)
                                                if "error" in data:
                                                    # 处理API错误
                                                    error_message = data["error"].get("message", "API error")
                                                    yield {
                                                        "type": "error",
                                                        "content": f"API错误: {error_message}"
                                                    }
                                                elif "choices" in data and len(data["choices"]) > 0:
                                                    choice = data["choices"][0]
                                                    if "delta" in choice:
                                                        delta = choice["delta"]
                                                        if "content" in delta:
                                                            content = delta["content"]
                                                            has_content = True
                                                            # 实时返回流式数据
                                                            yield {
                                                                "type": "answer",
                                                                "content": content
                                                            }
                                                        elif "tool_calls" in delta:
                                                            # 处理工具调用
                                                            tool_calls = delta["tool_calls"]
                                                            has_content = True
                                                            yield {
                                                                "type": "tool_call",
                                                                "tool_calls": tool_calls
                                                            }
                                            except Exception as e:
                                                logger.error(f"Failed to parse SSE data: {e}")
                                                # 打印失败的数据，以便调试
                                                logger.error(f"Failed data: {data_str}")
                                                yield {
                                                    "type": "error",
                                                    "content": f"解析响应数据失败: {str(e)}"
                                                }
                        
                        # 流式响应结束
                        # 无论buffer是否为空，都正常结束流式响应
                        # 因为即使buffer不为空，也可能是正常的响应结束
                        # 如果没有收到任何内容，返回一个错误消息
                        if not has_content:
                            yield {
                                "type": "error",
                                "content": "API调用失败，未收到任何响应"
                            }
                        yield {
                            "type": "stream_end"
                        }
                    except Exception as e:
                        logger.error(f"Failed to process stream response: {e}")
                        yield {
                            "type": "error",
                            "content": f"处理响应流失败: {str(e)}"
                        }
        except Exception as e:
            logger.error(f"Exception during API call: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "content": f"API调用失败: {str(e)}"
            }
    
    async def _chat_completion_non_stream(self, messages: list, max_tokens: int = 1024, tools: list = None, tool_choice: str = "auto"):
        """聊天完成（非流式响应）"""
        print("chat_completion called")
        print(f"API URL: {self.api_url}")
        print(f"Model: {self.model}")
        print(f"API Key: {'***' if self.api_key else 'Not configured'}")
        print(f"API Key length: {len(self.api_key) if self.api_key else 0}")
        print(f"Stream: False, Tools: {tools}, Tool choice: {tool_choice}")
        
        # 检查API密钥
        api_key_check = self._check_api_key()
        if api_key_check:
            return api_key_check
        
        try:
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "top_p": 0.95,
                "stream": False
            }
            
            # 添加工具调用参数
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            print(f"Sending API request to: {self.api_url}")
            print(f"Messages count: {len(messages)}")
            print(f"First message: {json.dumps(messages[0], ensure_ascii=False) if messages else 'None'}")
            print(f"Headers: {headers}")
            
            # 非流式响应使用通用API请求方法
            response = await self._api_request("POST", self.api_url, headers=headers, data=payload)
            
            if response["success"]:
                data = response["data"]
                print(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                if "choices" in data and len(data["choices"]) > 0:
                    text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    tool_calls = data["choices"][0]["message"].get("tool_calls", None)
                    print(f"Generated text: {text[:100]}...")
                    
                    result = {
                        "success": True,
                        "text": text,
                        "usage": usage
                    }
                    
                    if tool_calls:
                        result["tool_calls"] = tool_calls
                    
                    return result
                else:
                    print("No choices in response")
                    return {
                        "success": False,
                        "error": "No response from model"
                    }
            else:
                return response
        except Exception as e:
            print(f"Exception during API call: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    

