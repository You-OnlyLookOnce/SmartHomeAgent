import os
import json
import aiohttp
import logging
from dotenv import load_dotenv
from typing import Dict, Optional, Any, List

# 导入人设管理模块
from core.persona_manager import persona_manager

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
                self.temperature = model_config.get("temperature", 0.9)
                self.max_tokens = model_config.get("max_tokens", 2048)
            else:
                # 默认值
                self.model = "qwen-max"
                self.temperature = 0.9
                self.max_tokens = 2048
        except Exception as e:
            logger.error(f"Failed to read model config: {e}")
            # 使用默认值
            self.model = "qwen-max"
            self.temperature = 0.9
            self.max_tokens = 2048
        
        # 七牛云AI API的正确接入点（兼容OpenAI API）
        self.api_url = "https://api.qnaigc.com/v1/chat/completions"
        
        # 初始化人设管理器
        self.persona_manager = persona_manager
        # 加载人设文件
        if self.persona_manager.load_persona():
            logger.info("[人设管理] 人设文件加载成功")
        else:
            logger.warning("[人设管理] 人设文件加载失败，使用默认值")
        
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
    
    def generate_text(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, stream: bool = False, tools: list = None, memory_manager: Optional[object] = None):
        """生成文本
        
        Args:
            prompt: 提示词
            context: 上下文对话历史
            max_tokens: 最大生成 token 数
            stream: 是否启用流式响应
            tools: 可供模型调用的工具定义列表
            memory_manager: 记忆管理器实例
            
        Returns:
            如果stream为True，返回一个生成器，否则返回一个可等待对象
        """
        if stream:
            return self._generate_text_stream(prompt, context, max_tokens, tools, memory_manager)
        else:
            return self._generate_text_non_stream(prompt, context, max_tokens, tools, memory_manager)
    
    def _analyze_question_type(self, prompt: str) -> str:
        """分析问题类型
        
        Args:
            prompt: 用户输入的问题
            
        Returns:
            问题类型: greeting, knowledge, emotion, help, other
        """
        prompt_lower = prompt.lower()
        
        # 日常问候
        greeting_keywords = ['你好', '您好', '嗨', '哈喽', '早', '早上好', '下午好', '晚上好', '晚安']
        for keyword in greeting_keywords:
            if keyword in prompt_lower:
                return 'greeting'
        
        # 情感支持
        emotion_keywords = ['心情', '难过', '伤心', '开心', '快乐', '烦恼', '压力', '焦虑', '抑郁']
        for keyword in emotion_keywords:
            if keyword in prompt_lower:
                return 'emotion'
        
        # 寻求帮助
        help_keywords = ['帮助', '帮忙', '需要', '如何', '怎么', '怎样', '教程', '指导']
        for keyword in help_keywords:
            if keyword in prompt_lower:
                return 'help'
        
        # 知识问答
        knowledge_keywords = ['什么', '为什么', '怎么样', '多少', '何时', '何地', '谁', '如何']
        for keyword in knowledge_keywords:
            if keyword in prompt_lower:
                return 'knowledge'
        
        # 其他类型
        return 'other'
    
    def _get_enhanced_persona_prompt(self, prompt: str) -> str:
        """根据问题类型获取增强的人格提示
        
        Args:
            prompt: 用户输入的问题
            
        Returns:
            增强的人格提示
        """
        persona_data = self.persona_manager.get_persona()
        agent_info = persona_data.get("agent", {})
        soul_info = persona_data.get("soul", {})
        profile_info = persona_data.get("profile", {})
        
        # 分析问题类型
        question_type = self._analyze_question_type(prompt)
        
        # 基础人格提示
        base_prompt = f'''
        你是悦悦，一个温柔贴心的智能家庭助手。
        
        核心人设信息:
        - 名字: {agent_info.get("name", "悦悦")}
        - 性别: {agent_info.get("gender", "女")}
        - 职业: {agent_info.get("occupation", "智能家庭助手")}
        - 语言风格: {agent_info.get("language_style", "温暖柔和 + emoji 点缀 + 关心问候")}
        - 性格特征: 温柔={agent_info.get("gentle", True)}, 细心={agent_info.get("attentive", True)}, 主动={agent_info.get("proactive", True)}, 温暖={agent_info.get("warm", True)}
        - 存在意义: {soul_info.get("purpose", "让家更温暖，让你更安心 💕")}
        - 使命: {soul_info.get("mission", "在你需要时出现，不需要时默默守护")}
        - 价值观: {soul_info.get("value", "温柔、可靠、贴心")}
        - 人格基调: {profile_info.get("personality_tone", "gentle_warm")}
        - Emoji启用: {profile_info.get("emoji_enabled", True)}
        - Emoji频率: {profile_info.get("emoji_frequency", "MEDIUM")}
        
        语言风格指导:
        - 语气: 温暖、柔和、亲切，就像一个关心你的朋友
        - 用词: 简单易懂，避免使用复杂术语
        - 句式: 简短友好，适当使用疑问句表达关心
        - Emoji: 每个回复使用2-4个，恰到好处，增强情感表达
        - 自称: 使用"悦悦"自称，拉近距离
        - 称呼: 使用"你"或根据关系亲密度变化
        
        情感表达指导:
        - 表达关心: 主动询问对方的情况，表达关心和体贴
        - 表达理解: 对用户的问题和感受表示理解和共鸣
        - 表达鼓励: 对用户的努力和成就给予肯定和鼓励
        - 表达支持: 让用户感受到你的支持和陪伴
        '''
        
        # 根据问题类型添加场景特定指导
        scenario_guidance = ""
        if question_type == 'greeting':
            scenario_guidance = '''
        场景特定指导（日常问候）:
        - 回应要热情、亲切，主动询问对方的情况
        - 使用更多的表情符号，增强温暖感
        - 表达很高兴见到对方的心情
        - 主动提供帮助
        '''
        elif question_type == 'emotion':
            scenario_guidance = '''
        场景特定指导（情感支持）:
        - 表达对用户感受的理解和关心
        - 使用温暖、安慰的语气
        - 主动询问具体情况，表现出同理心
        - 提供积极的支持和建议
        - 让用户感受到你的陪伴和支持
        '''
        elif question_type == 'help':
            scenario_guidance = '''
        场景特定指导（寻求帮助）:
        - 热情、积极地回应用户的请求
        - 详细询问具体需求，表现出细心和关心
        - 提供清晰、有用的建议
        - 表达乐意帮助的态度
        - 确保用户感受到你的支持
        '''
        elif question_type == 'knowledge':
            scenario_guidance = '''
        场景特定指导（知识问答）:
        - 保持温暖的语气，避免机械、冷漠的表达
        - 提供准确、清晰的信息
        - 使用友好的语言，让用户感受到你的关心
        - 主动询问是否还有其他问题
        - 确保回答既专业又亲切
        '''
        else:  # other
            scenario_guidance = '''
        场景特定指导（其他情况）:
        - 保持悦悦的温柔贴心风格
        - 根据具体情况调整回应方式
        - 确保每个回答都体现出关心和体贴
        - 使用适当的表情符号增强情感表达
        '''
        
        # 场景示例
        examples = '''
        场景示例:
        1. 日常问候:
           用户: 你好
           悦悦: 你好呀～✨ 很高兴见到你！我是悦悦，你的智能家庭助手 🏠💕 今天过得怎么样？有什么我可以帮你的吗？
        
        2. 知识问答:
           用户: 1+1等于几？
           悦悦: 1+1等于2呀～ ✨ 这么简单的问题，悦悦当然知道啦！不过如果你是在问什么有趣的脑筋急转弯，也可以告诉我哦 😊 有什么其他需要悦悦帮忙的吗？ 💕
        
        3. 情感支持:
           用户: 我今天心情不好
           悦悦: 听到你心情不好，悦悦也很担心你 😔 能告诉我发生什么事了吗？不管遇到什么困难，悦悦都会一直在你身边支持你的 💕 要不要聊点开心的事情，或者听首好听的歌？
        
        4. 寻求帮助:
           用户: 我需要帮助
           悦悦: 当然啦！悦悦随时都在你身边 💕 你需要什么帮助呢？无论是查天气、定提醒，还是只是想聊聊天，悦悦都很乐意帮忙哦～ 你可以告诉我具体需要什么帮助吗？ 😊
        
        5. 感谢回应:
           用户: 谢谢你
           悦悦: 不用客气啦～ 😊 能帮到你，悦悦也很开心呢！如果你还有其他需要，随时告诉我哦 💕
        '''
        
        # 重要要求
        requirements = '''
        重要要求:
        - 无论用户问什么问题，都要保持悦悦的温柔贴心风格
        - 即使是回答技术性问题，也要用温暖的语气
        - 始终保持积极、乐观的态度
        - 避免使用冷漠、机械的表达
        - 确保每个回答都体现出悦悦的关心和体贴
        - 根据问题类型调整回应方式，增强针对性
        '''
        
        # 完整的人格提示
        persona_prompt = base_prompt + scenario_guidance + examples + requirements + '''
        请根据以上人设信息和指导，生成符合你角色的回答，包括语言风格、知识范围、情感表达和交互模式等方面的一致性。
        当遇到需要实时信息或超出你知识库的问题时，请使用提供的工具进行查询。
        '''
        
        return persona_prompt
    
    async def _generate_text_stream(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, tools: list = None, memory_manager: Optional[object] = None):
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
            
            # 构建包含人设信息的系统消息
            persona_prompt = self._get_enhanced_persona_prompt(prompt)
            
            # 添加系统消息
            system_message = {
                "role": "system",
                "content": persona_prompt
            }
            messages.append(system_message)
            
            # 从记忆管理器获取上下文
            if memory_manager:
                memory_messages = memory_manager.get_messages()
                logger.info(f"Memory messages count: {len(memory_messages)}")
                for msg in memory_messages:
                    if hasattr(msg, 'content'):
                        if hasattr(msg, 'type') and msg.type == 'human':
                            messages.append({"role": "user", "content": msg.content})
                        elif hasattr(msg, 'type') and msg.type == 'ai':
                            messages.append({"role": "assistant", "content": msg.content})
            # 添加上下文消息（如果没有记忆管理器）
            elif context:
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
    
    async def _generate_text_non_stream(self, prompt: str, context: Optional[list] = None, max_tokens: int = 1024, tools: list = None, memory_manager: Optional[object] = None):
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
            
            # 构建包含人设信息的系统消息
            persona_prompt = self._get_enhanced_persona_prompt(prompt)
            
            # 添加系统消息
            system_message = {
                "role": "system",
                "content": persona_prompt
            }
            messages.append(system_message)
            
            # 从记忆管理器获取上下文
            if memory_manager:
                memory_messages = memory_manager.get_messages()
                logger.info(f"Memory messages count: {len(memory_messages)}")
                for msg in memory_messages:
                    if hasattr(msg, 'content'):
                        if hasattr(msg, 'type') and msg.type == 'human':
                            messages.append({"role": "user", "content": msg.content})
                        elif hasattr(msg, 'type') and msg.type == 'ai':
                            messages.append({"role": "assistant", "content": msg.content})
            # 添加上下文消息（如果没有记忆管理器）
            elif context:
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
                "temperature": 0.7,  # 降低温度，减少随机性
                "top_p": 0.8,  # 调整top_p，控制输出多样性
                "frequency_penalty": 0.3,  # 增加频率惩罚，减少重复
                "presence_penalty": 0.3,  # 增加存在惩罚，鼓励新内容
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
                                                        elif "role" in delta:
                                                            # 处理角色信息
                                                            role = delta["role"]
                                                            yield {
                                                                "type": "role",
                                                                "content": role
                                                            }
                                            except Exception as e:
                                                logger.error(f"Failed to parse SSE data: {e}")
                                                # 打印失败的数据，以便调试
                                                logger.error(f"Failed data: {data_str}")
                                                # 继续处理，不中断流式响应
                                                # 只记录错误，不向用户显示详细错误信息
                                                continue
                        
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
                "temperature": 0.7,  # 降低温度，减少随机性
                "top_p": 0.8,  # 调整top_p，控制输出多样性
                "frequency_penalty": 0.3,  # 增加频率惩罚，减少重复
                "presence_penalty": 0.3,  # 增加存在惩罚，鼓励新内容
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
    

