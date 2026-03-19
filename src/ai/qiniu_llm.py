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
    
    def __init__(self):
        """初始化七牛云大模型"""
        load_dotenv()
        # 七牛云 AI API 需要使用专门的 API Key，而不是普通的 Access Key
        self.api_key = os.getenv('QINIU_AI_API_KEY', os.getenv('QINIU_ACCESS_KEY'))
        # 使用七牛云支持的模型名称
        self.model = "gemini-2.5-flash"
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
                async with aiohttp.ClientSession() as session:
                    # 设置超时
                    timeout_obj = aiohttp.ClientTimeout(total=timeout)
                    session = aiohttp.ClientSession(timeout=timeout_obj)
                    
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
    
    async def generate_text(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024) -> Dict[str, Any]:
        """生成文本
        
        Args:
            prompt: 提示词
            context: 上下文对话历史
            max_tokens: 最大生成 token 数
            
        Returns:
            生成的文本和相关信息
        """
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
                "content": "你是悦悦，一个具有独特个性的智能助手。请根据用户的问题提供详细、有用的回答。"
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
            result = await self.chat_completion(messages, max_tokens)
            logger.info(f"chat_completion returned: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Exception in generate_text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat_completion(self, messages: list, max_tokens: int = 1024, stream: bool = False, tools: list = None, tool_choice: str = "auto") -> Dict[str, Any]:
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
        print("chat_completion called")
        print(f"API URL: {self.api_url}")
        print(f"Model: {self.model}")
        print(f"API Key: {'***' if self.api_key else 'Not configured'}")
        print(f"API Key length: {len(self.api_key) if self.api_key else 0}")
        print(f"Stream: {stream}, Tools: {tools}, Tool choice: {tool_choice}")
        
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
                "temperature": 0.7,
                "top_p": 0.95,
                "stream": stream
            }
            
            # 添加工具调用参数
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            print(f"Sending API request to: {self.api_url}")
            print(f"Messages count: {len(messages)}")
            print(f"First message: {json.dumps(messages[0], ensure_ascii=False) if messages else 'None'}")
            print(f"Headers: {headers}")
            
            # 处理流式响应
            if stream:
                # 流式响应需要特殊处理，不使用通用API请求方法
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, headers=headers, json=payload) as response:
                        print(f"Response status: {response.status}")
                        print(f"Response headers: {dict(response.headers)}")
                        
                        try:
                            # 处理流式响应
                            chunks = []
                            async for chunk in response.content:
                                if chunk:
                                    chunks.append(chunk)
                            
                            # 合并所有chunk并解析
                            response_data = b''.join(chunks)
                            data = json.loads(response_data)
                            print(f"Stream response data: {json.dumps(data, ensure_ascii=False)}")
                        except Exception as e:
                            print(f"Failed to parse response JSON: {e}")
                            return {
                                "success": False,
                                "error": f"Failed to parse response: {e}"
                            }
                        
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
    
    async def web_search(self, query: str, max_results: int = 20, search_type: str = "web", time_filter: str = None, site_filter: list = None) -> Dict[str, Any]:
        """全网搜索
        
        Args:
            query: 搜索关键词或查询语句
            max_results: 返回结果数量，网页搜索默认20，最大50，视频最大10（默认5），图片搜索最大30（默认15）
            search_type: 搜索类型，默认"web"（网页搜索）
            time_filter: 时间过滤，可选值：week（一周内）、month（一月内）、year（一年内）、semiyear(半年内)
            site_filter: 站点过滤，指定搜索特定网站的内容（最多20个）
            
        Returns:
            搜索结果和相关信息
        """
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"web_search called with query: {query}")
            logger.info(f"max_results: {max_results}, search_type: {search_type}")
            logger.info(f"time_filter: {time_filter}, site_filter: {site_filter}")
            
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求参数
            payload = {
                "query": query,
                "max_results": max_results,
                "search_type": search_type
            }
            
            # 添加可选参数
            if time_filter:
                payload["time_filter"] = time_filter
            if site_filter:
                payload["site_filter"] = site_filter
            
            # 全网搜索 API 接入点
            search_api_url = "https://api.qnaigc.com/v1/search"
            
            logger.info(f"Sending search API request to: {search_api_url}")
            logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # 使用通用API请求方法
            response = await self._api_request("POST", search_api_url, headers=headers, data=payload)
            
            if response["success"]:
                data = response["data"]
                logger.info(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                if "success" in data and data["success"]:
                    return {
                        "success": True,
                        "data": data["data"]
                    }
                else:
                    error_message = data.get("message", "Search failed")
                    logger.error(f"Search failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
            else:
                return response
            
        except Exception as e:
            logger.error(f"Exception during web search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def real_time_inference(self, input_data: Dict[str, Any], model: str = None) -> Dict[str, Any]:
        """实时推理
        
        Args:
            input_data: 输入数据，支持文本、图像或文件
            model: 使用的模型名称，默认使用类初始化时的模型
            
        Returns:
            推理结果和相关信息
        """
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"real_time_inference called with input type: {list(input_data.keys())}")
            
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 使用指定的模型或默认模型
            target_model = model or self.model
            
            # 构建请求参数
            payload = {
                "model": target_model
            }
            
            # 处理不同类型的输入
            if "text" in input_data:
                # 文本输入
                messages = [
                    {
                        "role": "user",
                        "content": input_data["text"]
                    }
                ]
                payload["messages"] = messages
            elif "image_url" in input_data:
                # 图像输入（图片文字识别）
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "识别图片中的内容"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": input_data["image_url"]
                                }
                            }
                        ]
                    }
                ]
                payload["messages"] = messages
            elif "file_url" in input_data and "file_type" in input_data:
                # 文件识别
                messages = [
                    {
                        "role": "user",
                        "content": f"识别 {input_data['file_type']} 文件中的内容"
                    }
                ]
                payload["messages"] = messages
                payload["file"] = {
                    "type": input_data["file_type"],
                    "url": input_data["file_url"]
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid input data. Please provide 'text', 'image_url', or 'file_url' and 'file_type'."
                }
            
            # 实时推理 API 接入点（与聊天补全相同）
            inference_api_url = "https://api.qnaigc.com/v1/chat/completions"
            
            logger.info(f"Sending inference API request to: {inference_api_url}")
            logger.info(f"Model: {target_model}")
            logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # 使用通用API请求方法
            response = await self._api_request("POST", inference_api_url, headers=headers, data=payload)
            
            if response["success"]:
                data = response["data"]
                logger.info(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                if "choices" in data and len(data["choices"]) > 0:
                    text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    logger.info(f"Inference result: {text[:100]}...")
                    return {
                        "success": True,
                        "text": text,
                        "usage": usage
                    }
                else:
                    logger.error("No choices in response")
                    return {
                        "success": False,
                        "error": "No response from model"
                    }
            else:
                return response
            
        except Exception as e:
            logger.error(f"Exception during real time inference: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_batch_inference_task(self, name: str, model: str, input_files_url: str, description: str = None) -> Dict[str, Any]:
        """创建批量推理任务
        
        Args:
            name: 任务名称
            model: 使用的模型名称，目前支持 deepseek-v3、deepseek-r1、deepseek-r1-32b
            input_files_url: 输入文件的URL地址
            description: 任务描述
            
        Returns:
            任务创建结果和任务ID
        """
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"create_batch_inference_task called with name: {name}, model: {model}")
            logger.info(f"input_files_url: {input_files_url}, description: {description}")
            
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求参数
            payload = {
                "name": name,
                "model": model,
                "input_files_url": input_files_url
            }
            
            # 添加可选参数
            if description:
                payload["description"] = description
            
            # 批量推理 API 接入点
            batch_api_url = "https://api.qnaigc.com/v1/batchjob/inference"
            
            logger.info(f"Sending batch inference task creation request to: {batch_api_url}")
            logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # 使用通用API请求方法
            response = await self._api_request("POST", batch_api_url, headers=headers, data=payload)
            
            if response["success"]:
                data = response["data"]
                logger.info(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                if "id" in data:
                    return {
                        "success": True,
                        "task_id": data["id"]
                    }
                else:
                    logger.error("No task ID in response")
                    return {
                        "success": False,
                        "error": "No task ID returned"
                    }
            else:
                return response
            
        except Exception as e:
            logger.error(f"Exception during batch inference task creation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_batch_inference_task(self, task_id: str) -> Dict[str, Any]:
        """查询批量推理任务状态
        
        Args:
            task_id: 批量任务ID
            
        Returns:
            任务状态和详细信息
        """
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"get_batch_inference_task called with task_id: {task_id}")
            
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 批量推理 API 接入点
            batch_api_url = f"https://api.qnaigc.com/v1/batchjob/inference/{task_id}"
            
            logger.info(f"Sending batch inference task query request to: {batch_api_url}")
            
            # 使用通用API请求方法
            response = await self._api_request("GET", batch_api_url, headers=headers)
            
            if response["success"]:
                data = response["data"]
                logger.info(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                return {
                    "success": True,
                    "data": data
                }
            else:
                return response
            
        except Exception as e:
            logger.error(f"Exception during batch inference task query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_batch_inference_tasks(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """列出批量推理任务
        
        Args:
            page: 页码，默认1
            page_size: 每页记录数，默认100
            
        Returns:
            任务列表
        """
        try:
            # 检查API密钥
            api_key_check = self._check_api_key()
            if api_key_check:
                return api_key_check
                
            logger.info(f"list_batch_inference_tasks called with page: {page}, page_size: {page_size}")
            
            # 七牛云 AI API 使用 Bearer Token 认证
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建查询参数
            params = {
                "page": page,
                "page_size": page_size
            }
            
            # 批量推理 API 接入点
            batch_api_url = "https://api.qnaigc.com/v1/batchjob/inferences"
            
            logger.info(f"Sending batch inference tasks list request to: {batch_api_url}")
            
            # 使用通用API请求方法
            response = await self._api_request("GET", batch_api_url, headers=headers, params=params)
            
            if response["success"]:
                data = response["data"]
                logger.info(f"Response data: {json.dumps(data, ensure_ascii=False)}")
                
                return {
                    "success": True,
                    "data": data
                }
            else:
                return response
            
        except Exception as e:
            logger.error(f"Exception during batch inference tasks list: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
