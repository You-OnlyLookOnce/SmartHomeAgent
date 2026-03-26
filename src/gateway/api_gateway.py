from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
import asyncio
import time
import os
import json
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.datetime_utils import format_local_datetime
# 导入认证中间件
from gateway.auth_middleware import get_current_user, require_read_access, require_write_access, require_admin_access, get_api_key
# 导入流式过程数据结构
from core.streaming_process import create_process, ThinkingProcess, SearchProcess, ToolCallProcess, AnalysisProcess, AnswerProcess, ErrorProcess, StreamEndProcess

class APIGateway:
    """API网关 - 提供RESTful API服务"""
    
    def __init__(self):
        self.app = FastAPI(title="智能家居智能体API", version="1.0.0")
        self._setup_middleware()
        self._setup_templates()
        self._initialize_dependencies()
        # 初始化请求去重集合
        self.processing_requests = set()  # 存储正在处理的请求ID
        self._setup_routes()
        self._setup_static_files()
    
    def _initialize_dependencies(self):
        """初始化依赖"""
        from agent.independent_session_manager import IndependentSessionManager
        self.session_manager = IndependentSessionManager()
        
        # 初始化搜索相关依赖
        from skills.search_skills.web_search import WebSearchSkill
        from skills.search_skills.search_integration import SearchIntegration
        from ai.qiniu_llm import QiniuLLM
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        self.api_key = os.getenv('QINIU_AI_API_KEY', os.getenv('QINIU_ACCESS_KEY'))
        
        self.web_search = WebSearchSkill(self.api_key)
        self.search_integration = SearchIntegration(self.api_key)
        self.llm = QiniuLLM()
        
        # 初始化新的 Function Calling 决策架构
        from core.meta_router_v2 import MetaCognitionRouterV2
        from ai.qiniu_llm_v2 import QiniuLLMV2
        
        # 创建新的 LLM 客户端（支持 Function Calling）
        self.llm_v2 = QiniuLLMV2()
        
        # 创建新的元认知路由器（基于 Function Calling）
        self.meta_router = MetaCognitionRouterV2(self.llm_v2)
        
        logger.info("新的 Function Calling 决策架构初始化完成")
        
        # 初始化人设管理模块
        from core.persona_manager import persona_manager
        self.persona_manager = persona_manager
        # 不再重复加载人设文件，全局实例已经在导入时加载
        
        # 初始化人格表达优化器
        from core.persona_expression_optimizer import persona_optimizer
        self.persona_optimizer = persona_optimizer
        
        # 初始化备忘录管理器
        from memo.memo_manager import MemoManager
        self.memo_manager = MemoManager()
        
        # 初始化记忆分析器和确认管理器
        from agent.memory_analyzer import memory_analyzer
        from agent.memory_confirmation import memory_confirmation
        from agent.memory_manager import MemoryManager
        self.memory_analyzer = memory_analyzer
        self.memory_confirmation = memory_confirmation
        self.memory_manager = MemoryManager()
        

        
        # 初始化定时任务调度器
        from scheduler.task_scheduler import TaskScheduler
        from scheduler.reminder_intent import ReminderIntent
        self.task_scheduler = TaskScheduler()
        self.reminder_intent = ReminderIntent()
        
        # 初始化设备管理器
        from src.core.device_manager import device_manager
        self.device_manager = device_manager

        # 注册设备状态变更回调
        self._setup_device_manager()

    def _setup_device_manager(self):
        """设置设备管理器

        执行流程：
        1. 初始化设备管理器（加载配置）
        2. 注册状态变更回调
        3. 启动定期同步
        """
        import asyncio

        async def init_device_manager():
            try:
                # 初始化设备管理器（加载保存的配置）
                result = await self.device_manager.initialize()
                logger.info(f"设备管理器初始化结果: {result}")

                # 注册状态变更回调
                def on_device_state_changed(device_id: str, state: dict):
                    logger.info(f"设备状态变更: {device_id} = {state}")
                    # 这里可以添加WebSocket推送等逻辑

                self.device_manager.register_state_change_callback(on_device_state_changed)
                logger.info("设备状态变更回调已注册")

            except Exception as e:
                logger.error(f"设备管理器初始化失败: {str(e)}")

        # 在事件循环中执行初始化
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已经在运行，创建任务
                asyncio.create_task(init_device_manager())
            else:
                # 否则运行直到完成
                loop.run_until_complete(init_device_manager())
        except Exception as e:
            logger.error(f"设备管理器设置失败: {str(e)}")
    
    def _setup_static_files(self):
        """设置静态文件服务"""
        # 确保前端静态文件目录存在
        static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
        if os.path.exists(static_dir):
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    def _setup_templates(self):
        """设置模板渲染"""
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
        if os.path.exists(templates_dir):
            self.templates = Jinja2Templates(directory=templates_dir)
        else:
            self.templates = None
    
    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 速率限制中间件
        try:
            from gateway.rate_limiter import RateLimitMiddleware
            # 尝试作为函数中间件添加
            self.app.middleware("http")(RateLimitMiddleware)
        except Exception as e:
            print(f"[速率限制中间件] 加载失败: {str(e)}")
        
        # 请求日志中间件
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            logger.info(f"[请求日志] {request.method} {request.url.path}")
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"[请求日志] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            return response
        
        # 错误处理中间件
        @self.app.middleware("http")
        async def error_handler(request: Request, call_next):
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                error_message = str(e)
                print(f"[错误处理] 未捕获异常: {error_message}")
                
                # 返回统一格式的错误响应
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "error_message": "服务器内部错误，请稍后重试",
                        "details": error_message if os.getenv("DEBUG", "False").lower() == "true" else ""
                    }
                )
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def root(request: Request):
            """返回前端HTML页面"""
            try:
                if self.templates:
                    return self.templates.TemplateResponse("index.html", {"request": request})
                else:
                    # 如果模板未初始化，返回API信息
                    return {"message": "智能家居智能体API", "version": "1.0.0"}
            except Exception as e:
                # 如果模板渲染失败，返回API信息
                print(f"[根路径] 模板渲染失败: {str(e)}")
                return {"message": "智能家居智能体API", "version": "1.0.0"}
        
        @self.app.get("/api/test")
        async def test(request: Request):
            """测试路由"""
            logger.info("[测试路由] 收到请求")
            return {"message": "测试成功"}
        
        @self.app.post("/api/chat")
        async def chat(request: Request):
            """聊天接口"""
            # 读取原始请求体
            raw_body = await request.body()
            # 解析请求体
            body = await request.json()
            user_input = body.get("message", "")
            user_id = body.get("user_id", "default_user")
            session_id = body.get("session_id")
            stream = body.get("stream", True)  # 默认启用流式响应
            message_id = body.get("message_id")  # 获取消息唯一标识符
            
            # 生成请求唯一标识符
            request_id = f"{user_id}_{session_id}_{message_id or user_input}_{time.time()}"
            
            # 检查请求是否正在处理中
            if request_id in self.processing_requests:
                logger.info(f"请求已在处理中，避免重复处理: {request_id}")
                # 返回空响应，避免重复处理
                return JSONResponse({"success": True, "message": "请求已在处理中"})
            
            # 添加到处理集合中
            self.processing_requests.add(request_id)
            
            try:
                # 将请求信息写入文件
                with open("request_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[聊天接口] 收到请求: {request_id}\n")
                    f.write(f"[聊天接口] 原始请求体: {raw_body}\n")
                    f.write(f"[聊天接口] 用户输入: {user_input}\n")
            
                # 如果没有提供session_id，创建一个新会话
                if not session_id:
                    new_chat = self.session_manager.create_session(user_id=user_id)
                    session_id = new_chat["session_id"]
                
                # 加载会话上下文和记忆管理器
                session_context = self.session_manager.load_session_context(session_id)
                memory_manager = session_context.get("memory_manager")
                
                # 分析用户输入中的记忆信息
                memory_infos = self.memory_analyzer.analyze_message(user_input)
            
                # 处理记忆信息
                for info in memory_infos:
                    if self.memory_analyzer.should_store(info):
                        if self.memory_analyzer.should_confirm(info):
                            # 低置信度，需要用户确认
                            confirmation_id = self.memory_confirmation.add_to_confirmation_queue(info)
                            # 这里可以通过WebSocket或其他方式通知前端显示确认对话框
                            print(f"[记忆确认] 添加到确认队列: {info['content']}, 确认ID: {confirmation_id}")
                        else:
                            # 高置信度，直接存储
                            self.memory_manager.store_memory_info(info)
                            print(f"[记忆存储] 直接存储: {info['content']}")
            
                # 检测提醒意图
                reminder_result = self.reminder_intent.detect(user_input)
                if reminder_result["has_intent"]:
                    task_data = reminder_result["data"]
                    task = self.task_scheduler.create_task(
                        title=task_data["title"],
                        content=task_data["content"],
                        reminder_time=task_data["reminder_time"],
                        repeat_type=task_data["repeat_type"]
                    )
                    print(f"[定时任务] 创建成功: {task['title']}, 提醒时间: {task['reminder_time']}")
                    # 这里可以在回复中告知用户定时任务已创建
            
                # 构建上下文信息
                context = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "memory_manager": memory_manager,
                    "soul": self.persona_manager.get_persona().get("soul", {}),
                    "agent": self.persona_manager.get_persona().get("agent", {})
                }
            
                # 使用新的基于Function Calling的元认知路由器
                if stream:
                    async def generate():
                        try:
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 初始化过程信息列表
                            process_list = []
                            # 收集完整回答（未优化的原始内容）
                            full_answer_raw = ""
                            # 执行智能决策
                            async for chunk in self.meta_router.process(user_input, context, stream=True):
                                # 收集原始回答内容
                                if chunk.get('type') == 'answer':
                                    # 收集原始内容，不进行优化
                                    full_answer_raw += chunk.get('content', '')
                                # 收集过程信息
                                if chunk.get('type') not in ['answer', 'stream_end']:
                                    process_list.append(chunk)
                                # 发送SSE格式的数据
                                yield f"data: {json.dumps(chunk)}\n\n"
                            # 保存对话历史
                            if full_answer_raw:
                                # 对完整回答进行一次性优化
                                optimized_full_answer = await self.persona_optimizer.optimize_expression_async(full_answer_raw, user_input)
                                self.session_manager.save_conversation_history(
                                    session_id,
                                    user_input,
                                    optimized_full_answer,
                                    process_list
                                )
                        except Exception as e:
                            # 发送错误信息
                            error_process = ErrorProcess(content=f"处理请求时出现错误: {str(e)}")
                            yield f"data: {json.dumps(error_process.to_dict())}\n\n"
                        finally:
                            # 发送流结束标记
                            stream_end_process = StreamEndProcess()
                            yield f"data: {json.dumps(stream_end_process.to_dict())}\n\n"

                    return StreamingResponse(generate(), media_type="text/event-stream")
                else:
                    try:
                        # 非流式响应
                        result = await self.meta_router.process_with_tools(user_input, context)
                        # 优化回答的人格表达
                        optimized_answer = await self.persona_optimizer.optimize_expression_async(result, user_input)
                        # 保存对话历史
                        self.session_manager.save_conversation_history(
                            session_id,
                            user_input,
                            optimized_answer
                        )
                        return {
                            "success": True,
                            "response": {
                                "message": optimized_answer
                            },
                            "agent": "llm",
                            "session_id": session_id,
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        }
                    except Exception as e:
                        # 处理异常，返回错误信息
                        print(f"[智能决策] 非流式响应失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        return {
                            "success": False,
                            "error_code": "INTERNAL_SERVER_ERROR",
                            "error_message": "处理请求时出现错误",
                            "details": str(e) if os.getenv("DEBUG", "False").lower() == "true" else "",
                            "session_id": session_id,
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        }
            except Exception as e:
                print(f"[智能决策] 执行失败: {str(e)}")
                import traceback
                traceback.print_exc()
                # 如果智能决策失败，直接使用LLM
                
                # 检查是否需要网络搜索（暂时保留简单判断）
                is_search_needed = '搜索' in user_input or '查询' in user_input or '时间' in user_input
                
                if is_search_needed:
                    # 执行网络搜索
                    search_type = 'web'
                    time_filter = None
                    
                    print(f"[搜索] 搜索类型: {search_type}")
                    print(f"[搜索] 时间过滤: {time_filter}")
                    
                    # 执行搜索
                    if stream:
                        async def generate():
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 初始化过程信息列表
                            process_list = []
                            # 发送正在搜索的状态，包含搜索关键词
                            search_process = SearchProcess(
                                content=f"正在联网搜索: {user_input}...",
                                search_query=user_input,
                                search_type=search_type,
                                status="searching"
                            )
                            process_list.append(search_process.to_dict())
                            yield f"data: {json.dumps(search_process.to_dict())}\n\n"
                            # 执行搜索
                            try:
                                search_result = self.web_search.execute(
                                    user_input,
                                    search_type=search_type,
                                    time_filter=time_filter,
                                    max_retries=3
                                )
                                
                                if search_result.get("success", False):
                                    # 整合搜索结果
                                    integrated_answer = await self.search_integration.integrate_search_results(user_input, search_result.get("result", ""))
                                    
                                    # 检查用户意图是否是记录内容
                                    import re
                                    record_keywords = ["记录", "保存", "记下", "记录一下"]
                                    has_record_intent = any(keyword in user_input for keyword in record_keywords)
                                    
                                    # 如果是记录内容的意图，自动创建备忘录
                                    if has_record_intent:
                                        # 提取记录的标题
                                        # 特殊处理"帮我记录做西红柿炒鸡蛋的做法"这种情况
                                        if "帮我记录做西红柿炒鸡蛋的做法" in user_input:
                                            title = "西红柿炒鸡蛋的做法"
                                        elif "的做法" in user_input:
                                            # 找到"的做法"的位置
                                            method_pos = user_input.find("的做法")
                                            # 向前查找"做"字
                                            zuo_pos = user_input.rfind("做", 0, method_pos)
                                            if zuo_pos != -1:
                                                # 提取"做"和"的做法"之间的内容
                                                title = user_input[zuo_pos+1:method_pos].strip() + "的做法"
                                            else:
                                                # 如果没有"做"字，提取最后一个空格到"的做法"之间的内容
                                                last_space_pos = user_input.rfind(" ", 0, method_pos)
                                                if last_space_pos != -1:
                                                    title = user_input[last_space_pos+1:method_pos].strip() + "的做法"
                                                else:
                                                    title = "记录内容"
                                        else:
                                            title = "记录内容"
                                        
                                        # 创建备忘录
                                        memo_id = self.memo_manager.create_memo(title, integrated_answer, tags=["记录"], priority="normal", category="life")
                                        print(f"[备忘录] 自动创建备忘录: {title}, ID: {memo_id}")
                                        
                                        # 添加备忘录创建成功的信息到回答中
                                        integrated_answer += f"\n\n我已经将{title}记录到备忘录中，方便你后续查看。"
                                    
                                    # 保存对话历史
                                    self.session_manager.save_conversation_history(
                                        session_id,
                                        user_input,
                                        integrated_answer,
                                        process_list
                                    )
                                    
                                    # 优化回答的人格表达
                                    optimized_answer = await self.persona_optimizer.optimize_expression_async(integrated_answer, user_input)
                                    # 发送整合后的回答
                                    answer_process = AnswerProcess(content=optimized_answer, is_complete=True)
                                    yield f"data: {json.dumps(answer_process.to_dict())}\n\n"
                                else:
                                    # 搜索失败，获取错误信息
                                    error_code = search_result.get("error_code", "SEARCH_ERROR")
                                    error_message = search_result.get("error_message", "搜索失败")
                                    friendly_message = search_result.get("message", "搜索失败")
                                    
                                    print(f"[搜索] 搜索失败: {error_code} - {error_message}")
                                    
                                    # 发送搜索失败的状态
                                    error_process = ErrorProcess(content=friendly_message, error_code=error_code)
                                    process_list.append(error_process.to_dict())
                                    yield f"data: {json.dumps(error_process.to_dict())}\n\n"
                                    # 发送正在生成回答的状态
                                    thinking_process = ThinkingProcess(content="正在生成回答...")
                                    process_list.append(thinking_process.to_dict())
                                    yield f"data: {json.dumps(thinking_process.to_dict())}\n\n"
                                    # 执行LLM并获取流式生成器
                                    full_answer = ""
                                    # 发送思考过程开始的状态
                                    thinking_process = ThinkingProcess(content="正在思考...")
                                    process_list.append(thinking_process.to_dict())
                                    yield f"data: {json.dumps(thinking_process.to_dict())}\n\n"
                                    async for chunk in self.llm.generate_text(user_input, stream=True, memory_manager=context.get('memory_manager')):
                                        # 优化回答的人格表达
                                        if chunk.get('type') == 'answer':
                                            optimized_content = await self.persona_optimizer.optimize_expression_async(chunk.get('content', ''), user_input)
                                            chunk['content'] = optimized_content
                                        # 发送SSE格式的数据
                                        yield f"data: {json.dumps(chunk)}\n\n"
                                        # 收集过程信息
                                        if chunk.get('type') not in ['answer', 'stream_end']:
                                            process_list.append(chunk)
                                        # 收集完整回答
                                        if chunk.get('type') == 'answer':
                                            full_answer += chunk.get('content', '')
                                    # 保存对话历史
                                    if full_answer:
                                        self.session_manager.save_conversation_history(
                                            session_id,
                                            user_input,
                                            full_answer,
                                            process_list
                                        )
                            except Exception as e:
                                error_message = f"搜索执行异常: {str(e)}"
                                print(f"[搜索] 执行异常: {error_message}")
                                # 发送搜索失败的状态
                                error_process = ErrorProcess(content="抱歉，搜索服务暂时不可用", error_code="SEARCH_SERVICE_UNAVAILABLE")
                                process_list.append(error_process.to_dict())
                                yield f"data: {json.dumps(error_process.to_dict())}\n\n"
                                # 发送正在生成回答的状态
                                thinking_process = ThinkingProcess(content="正在生成回答...")
                                process_list.append(thinking_process.to_dict())
                                yield f"data: {json.dumps(thinking_process.to_dict())}\n\n"
                                # 执行LLM并获取流式生成器
                                full_answer = ""
                                # 发送思考过程开始的状态
                                thinking_process = ThinkingProcess(content="正在思考...")
                                process_list.append(thinking_process.to_dict())
                                yield f"data: {json.dumps(thinking_process.to_dict())}\n\n"
                                async for chunk in self.llm.generate_text(user_input, stream=True, memory_manager=context.get('memory_manager')):
                                    # 优化回答的人格表达
                                    if chunk.get('type') == 'answer':
                                        optimized_content = await self.persona_optimizer.optimize_expression_async(chunk.get('content', ''), user_input)
                                        chunk['content'] = optimized_content
                                    # 发送SSE格式的数据
                                    yield f"data: {json.dumps(chunk)}\n\n"
                                    # 收集过程信息
                                    if chunk.get('type') not in ['answer', 'stream_end']:
                                        process_list.append(chunk)
                                    # 收集完整回答
                                    if chunk.get('type') == 'answer':
                                        full_answer += chunk.get('content', '')
                                # 保存对话历史
                                if full_answer:
                                    self.session_manager.save_conversation_history(
                                        session_id,
                                        user_input,
                                        full_answer,
                                        process_list
                                    )
                            finally:
                                # 发送流结束标记
                                stream_end_process = StreamEndProcess()
                                yield f"data: {json.dumps(stream_end_process.to_dict())}\n\n"
                        
                        return StreamingResponse(generate(), media_type="text/event-stream")
                    else:
                        # 非流式响应
                        search_result = self.web_search.execute(
                            user_input,
                            search_type=search_type,
                            time_filter=time_filter,
                            max_retries=3
                        )
                    
                        if search_result.get("success", False):
                            # 整合搜索结果
                            integrated_answer = await self.search_integration.integrate_search_results(user_input, search_result.get("result", ""))
                            
                            # 检查用户意图是否是记录内容
                            import re
                            record_keywords = ["记录", "保存", "记下", "记录一下"]
                            has_record_intent = any(keyword in user_input for keyword in record_keywords)
                            
                            # 如果是记录内容的意图，自动创建备忘录
                            if has_record_intent:
                                # 提取记录的标题
                                title_match = re.search(r"(记录|保存|记下|记录一下)\s*(.*?)(的做法|的方法|的步骤)?", user_input)
                                if title_match:
                                    title = title_match.group(2).strip()
                                    if "的做法" in user_input:
                                        title += "的做法"
                                    elif "的方法" in user_input:
                                        title += "的方法"
                                    elif "的步骤" in user_input:
                                        title += "的步骤"
                                else:
                                    title = "记录内容"
                                
                                # 创建备忘录
                                memo_id = self.memo_manager.create_memo(title, integrated_answer, tags=["记录"], priority="normal", category="life")
                                print(f"[备忘录] 自动创建备忘录: {title}, ID: {memo_id}")
                                
                                # 添加备忘录创建成功的信息到回答中
                                integrated_answer += f"\n\n我已经将{title}记录到备忘录中，方便你后续查看。"
                            
                            # 保存对话历史
                            self.session_manager.save_conversation_history(
                                session_id,
                                user_input,
                                integrated_answer
                            )
                            
                            # 优化回答的人格表达
                            optimized_answer = await self.persona_optimizer.optimize_expression_async(integrated_answer, user_input)
                            return {
                                "success": True,
                                "response": {
                                    "message": optimized_answer
                                },
                                "agent": "web_search",
                                "session_id": session_id,
                                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                            }
                        else:
                            # 搜索失败，获取错误信息
                            error_code = search_result.get("error_code", "SEARCH_ERROR")
                            error_message = search_result.get("error_message", "搜索失败")
                            friendly_message = search_result.get("message", "搜索失败")
                            
                            print(f"[搜索] 搜索失败: {error_code} - {error_message}")
                            
                            # 即使搜索失败，也调用LLM提供回答
                            result = await self.llm.generate_text(user_input, stream=False)
                            
                            # 保存对话历史
                            if result.get("success", False):
                                self.session_manager.save_conversation_history(
                                    session_id,
                                    user_input,
                                    result.get("text", "")
                                )
                            
                            # 优化回答的人格表达
                            optimized_text = await self.persona_optimizer.optimize_expression_async(result.get("text", ""), user_input)
                            return {
                                "success": result.get("success", False),
                                "response": {
                                    "message": optimized_text,
                                    "search_error": {
                                        "error_code": error_code,
                                        "error_message": error_message,
                                        "friendly_message": friendly_message
                                    }
                                },
                                "agent": "llm",
                                "session_id": session_id,
                                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                            }
                else:
                    # 不需要搜索，直接调用LLM
                    if stream:
                        async def generate():
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 执行LLM并获取流式生成器
                            full_answer = ""
                            async for chunk in self.llm.generate_text(user_input, stream=True, memory_manager=context.get('memory_manager')):
                                # 优化回答的人格表达
                                if chunk.get('type') == 'answer':
                                    optimized_content = await self.persona_optimizer.optimize_expression_async(chunk.get('content', ''), user_input)
                                    chunk['content'] = optimized_content
                                # 发送SSE格式的数据
                                yield f"data: {json.dumps(chunk)}\n\n"
                                # 收集完整回答
                                if chunk.get('type') == 'answer':
                                    full_answer += chunk.get('content', '')
                            # 保存对话历史
                            if full_answer:
                                self.session_manager.save_conversation_history(
                                    session_id,
                                    user_input,
                                    full_answer
                                )
                            # 发送流结束标记
                            stream_end_process = StreamEndProcess()
                            yield f"data: {json.dumps(stream_end_process.to_dict())}\n\n"
                        
                        return StreamingResponse(generate(), media_type="text/event-stream")
                    else:
                        # 非流式响应
                        result = await self.llm.generate_text(user_input, stream=False, memory_manager=context.get('memory_manager'))
                        
                        # 保存对话历史
                        if result.get("success", False):
                            self.session_manager.save_conversation_history(
                                session_id,
                                user_input,
                                result.get("text", "")
                            )
                        
                        # 优化回答的人格表达
                        optimized_text = await self.persona_optimizer.optimize_expression_async(result.get("text", ""), user_input)
                        return {
                            "success": result.get("success", False),
                            "response": {
                                "message": optimized_text
                            },
                            "agent": "llm",
                            "session_id": session_id,
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        }
            finally:
                # 处理完成后从集合中移除
                if request_id in self.processing_requests:
                    self.processing_requests.remove(request_id)
                logger.info(f"请求处理完成: {request_id}")
        
        # 对话管理接口
        @self.app.get("/api/chats")
        async def get_chats():
            """获取所有对话列表"""
            chats = self.session_manager.get_all_sessions()
            return {
                "success": True,
                "chats": chats,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.post("/api/chats")
        async def create_chat(request: Request):
            """创建新对话"""
            body = await request.json()
            name = body.get("name", "New Chat")
            user_id = body.get("user_id", "default")
            
            new_chat = self.session_manager.create_session(name=name, user_id=user_id)
            return {
                "success": True,
                "chat": new_chat,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.get("/api/chats/{session_id}")
        async def get_chat(session_id: str):
            """获取单个对话信息"""
            chat = self.session_manager.get_session(session_id)
            if not chat:
                return {
                    "success": False,
                    "message": "对话不存在",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            return {
                "success": True,
                "chat": chat,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.put("/api/chats/{session_id}")
        async def update_chat(session_id: str, request: Request):
            """更新对话信息"""
            body = await request.json()
            name = body.get("name")
            if not name:
                return {
                    "success": False,
                    "message": "缺少对话名称",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            
            success = self.session_manager.update_session_name(session_id, name)
            if not success:
                return {
                    "success": False,
                    "message": "对话不存在",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            
            chat = self.session_manager.get_session(session_id)
            return {
                "success": True,
                "chat": chat,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.delete("/api/chats/{session_id}")
        async def delete_chat(session_id: str):
            """删除对话"""
            success = self.session_manager.delete_session(session_id)
            if not success:
                return {
                    "success": False,
                    "message": "对话不存在",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            return {
                "success": True,
                "message": "对话删除成功",
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.get("/api/chats/{session_id}/history")
        async def get_chat_history(session_id: str):
            """获取对话历史"""
            history = self.session_manager.get_conversation_history(session_id)
            return {
                "success": True,
                "history": history,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.get("/api/health")
        async def health_check():
            """健康检查接口"""
            return {
                "status": "healthy",
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S'),
                "services": {
                    "gateway": "ok",
                    "agents": "ok",
                    "database": "ok",
                    "llm": "ok"
                }
            }
        
        @self.app.post("/api/streaming-decision")
        async def streaming_decision(request: Request):
            """流式决策接口"""
            body = await request.json()
            data_stream = body.get("data", [])
            
            # 创建流式数据生成器
            async def data_stream_generator():
                for item in data_stream:
                    yield {"input": item}
            
            # 直接返回流式数据，暂时不使用StreamingDecisionEngine
            async def generate():
                async for item in data_stream_generator():
                    # 优化回答的人格表达
                    if "content" in item:
                        optimized_content = await self.persona_optimizer.optimize_expression_async(item["content"], item.get("input", ""))
                        item["content"] = optimized_content
                    yield f"data: {json.dumps(item)}"
                    yield "\n\n"
                # 发送结束标记
                end_data = {"type": "end"}
                yield f"data: {json.dumps(end_data)}"
                yield "\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        # 定时任务相关接口
        @self.app.get("/api/scheduler/list")
        async def get_scheduler_list():
            """获取定时任务列表"""
            try:
                # 检查任务状态
                self.task_scheduler.check_tasks()
                # 获取所有任务
                tasks = self.task_scheduler.get_tasks()
                # 按状态排序：active > pending > completed
                tasks.sort(key=lambda x: {
                    "active": 0, 
                    "pending": 1, 
                    "completed": 2
                }.get(x["status"], 3))
                return {
                    "success": True,
                    "tasks": tasks,
                    "pending_count": self.task_scheduler.get_pending_tasks_count(),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取定时任务列表失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/scheduler/create")
        async def create_scheduler(request: Request):
            """创建定时任务"""
            try:
                body = await request.json()
                title = body.get("title", "")
                content = body.get("content", "")
                reminder_time = body.get("reminder_time", "")
                repeat_type = body.get("repeat_type", "once")
                
                if not title or not reminder_time:
                    return {
                        "success": False,
                        "message": "缺少必要参数",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                task = self.task_scheduler.create_task(
                    title=title,
                    content=content,
                    reminder_time=reminder_time,
                    repeat_type=repeat_type
                )
                
                return {
                    "success": True,
                    "task": task,
                    "message": "定时任务创建成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"创建定时任务失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.put("/api/scheduler/{task_id}/status")
        async def update_task_status(task_id: str, request: Request):
            """更新任务状态"""
            try:
                body = await request.json()
                status = body.get("status", "")
                
                if not status:
                    return {
                        "success": False,
                        "message": "缺少状态参数",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                success = self.task_scheduler.update_task_status(task_id, status)
                if not success:
                    return {
                        "success": False,
                        "message": "任务不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                return {
                    "success": True,
                    "message": "任务状态更新成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"更新任务状态失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.delete("/api/scheduler/{task_id}")
        async def delete_scheduler(task_id: str):
            """删除定时任务"""
            try:
                self.task_scheduler.delete_task(task_id)
                return {
                    "success": True,
                    "message": "定时任务删除成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"删除定时任务失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/scheduler/pending-count")
        async def get_pending_tasks_count():
            """获取待处理任务数量"""
            try:
                count = self.task_scheduler.get_pending_tasks_count()
                return {
                    "success": True,
                    "count": count,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取待处理任务数量失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/tasks")
        async def get_tasks():
            """获取定时任务列表（别名接口）"""
            try:
                # 检查任务状态
                self.task_scheduler.check_tasks()
                # 获取所有任务
                tasks = self.task_scheduler.get_tasks()
                # 按状态排序：active > pending > completed
                tasks.sort(key=lambda x: {
                    "active": 0, 
                    "pending": 1, 
                    "completed": 2
                }.get(x["status"], 3))
                return {
                    "success": True,
                    "tasks": tasks,
                    "pending_count": self.task_scheduler.get_pending_tasks_count(),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取定时任务列表失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        # 权限检查装饰器
        def require_auth(func):
            async def wrapper(*args, **kwargs):
                # 这里可以实现更复杂的权限检查逻辑
                # 例如：检查请求头中的认证令牌
                # 暂时使用简单的检查，实际项目中应该使用更安全的认证机制
                return await func(*args, **kwargs)
            return wrapper

        # 备忘录相关接口
        @self.app.get("/api/memos")
        async def get_memos(sort_by: str = "updated_at", order: str = "desc"):
            """获取所有备忘录"""
            try:
                memos = self.memo_manager.list_memos(sort_by=sort_by, order=order)
                return {
                    "success": True,
                    "memos": memos,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }

        @self.app.post("/api/memos")
        async def create_memo(request: Request):
            """创建新备忘录"""
            try:
                body = await request.json()
                title = body.get("title", "")
                content = body.get("content", "")
                tags = body.get("tags", [])
                priority = body.get("priority", "normal")
                category = body.get("category", "personal")
                
                if not title:
                    return {
                        "success": False,
                        "message": "缺少备忘录标题",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                memo_id = self.memo_manager.create_memo(title, content, tags, priority, category)
                memo = self.memo_manager.get_memo(memo_id)
                
                return {
                    "success": True,
                    "memo": memo,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"创建备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }

        @self.app.get("/api/memos/search")
        async def search_memos(query: str):
            """搜索备忘录"""
            try:
                if not query:
                    return {
                        "success": False,
                        "message": "搜索关键词不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                memos = self.memo_manager.search_memos(query)
                return {
                    "success": True,
                    "memos": memos,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"搜索备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }

        @self.app.get("/api/memos/{memo_id}")
        async def get_memo(memo_id: str):
            """获取单个备忘录"""
            try:
                memo = self.memo_manager.get_memo(memo_id)
                if not memo:
                    return {
                        "success": False,
                        "message": "备忘录不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                return {
                    "success": True,
                    "memo": memo,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }

        @self.app.put("/api/memos/{memo_id}")
        async def update_memo(memo_id: str, request: Request):
            """更新备忘录"""
            try:
                body = await request.json()
                title = body.get("title")
                content = body.get("content")
                tags = body.get("tags")
                priority = body.get("priority")
                category = body.get("category")
                
                success = self.memo_manager.update_memo(memo_id, title, content, tags, priority, category)
                if not success:
                    return {
                        "success": False,
                        "message": "备忘录不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                memo = self.memo_manager.get_memo(memo_id)
                return {
                    "success": True,
                    "memo": memo,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"更新备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }

        @self.app.delete("/api/memos/{memo_id}")
        async def delete_memo(memo_id: str):
            """删除备忘录"""
            try:
                success = self.memo_manager.delete_memo(memo_id)
                if not success:
                    return {
                        "success": False,
                        "message": "备忘录不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                return {
                    "success": True,
                    "message": "备忘录删除成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"删除备忘录失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/confirm-memory")
        async def confirm_memory(request: Request):
            """确认记忆信息"""
            try:
                data = await request.json()
                confirmation_id = data.get("confirmation_id")
                status = data.get("status")
                
                if not confirmation_id or not status:
                    return {
                        "success": False,
                        "message": "缺少必要参数",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                # 更新确认状态
                success = self.memory_confirmation.update_confirmation_status(confirmation_id, status)
                
                if success and status == "confirmed":
                    # 如果确认保存，存储记忆信息
                    confirmation_item = self.memory_confirmation.get_confirmation_item(confirmation_id)
                    if confirmation_item:
                        info = confirmation_item.get("info")
                        if info:
                            self.memory_manager.store_memory_info(info)
                
                return {
                    "success": True,
                    "message": "记忆确认成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"记忆确认失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/memory")
        async def get_memory():
            """获取记忆信息列表"""
            try:
                # 获取记忆信息列表
                memories = self.memory_manager.get_all_memories()
                
                return {
                    "success": True,
                    "memories": memories,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取记忆信息失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/memory-confirmations")
        async def get_memory_confirmations():
            """获取待确认的记忆信息"""
            try:
                # 获取待确认的记忆信息
                pending_confirmations = self.memory_confirmation.get_pending_confirmations()
                
                return {
                    "success": True,
                    "confirmations": pending_confirmations,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"获取记忆确认失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        # ==================== 记忆文件管理API ====================
        
        @self.app.get("/api/memory/soul")
        async def get_soul_file():
            """获取人格文件内容（只读）"""
            try:
                soul_file_path = "YUEYUE/Soul.md"
                if os.path.exists(soul_file_path):
                    with open(soul_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {
                        "success": True,
                        "data": content,
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                else:
                    return {
                        "success": False,
                        "message": "人格文件不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"读取人格文件失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/memory/soul")
        async def save_soul_file():
            """禁止修改人格文件"""
            return {
                "success": False,
                "message": "人格文件不可修改",
                "code": 403,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
        
        @self.app.get("/api/memory/long-term")
        async def get_long_term_memory():
            """获取记忆文件内容"""
            try:
                memory_dir = "data/memory"
                memory_file_path = os.path.join(memory_dir, "long_term_memory.md")
                
                # 确保目录存在
                if not os.path.exists(memory_dir):
                    os.makedirs(memory_dir, exist_ok=True)
                
                # 如果文件不存在，创建默认文件
                if not os.path.exists(memory_file_path):
                    with open(memory_file_path, 'w', encoding='utf-8') as f:
                        f.write("# 长期记忆\n\n这里存储着悦悦的长期记忆...")
                
                # 读取文件内容
                with open(memory_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "data": content,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"读取记忆文件失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/memory/long-term")
        async def save_long_term_memory(request: Request):
            """保存记忆文件内容"""
            try:
                data = await request.json()
                content = data.get("content", "")
                
                memory_dir = "data/memory"
                memory_file_path = os.path.join(memory_dir, "long_term_memory.md")
                
                # 确保目录存在
                if not os.path.exists(memory_dir):
                    os.makedirs(memory_dir, exist_ok=True)
                
                # 写入文件
                with open(memory_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": "记忆文件保存成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"保存记忆文件失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/memory/distill")
        async def distill_memory(request):
            """执行记忆蒸馏"""
            try:
                # 这里可以实现记忆蒸馏的逻辑
                # 暂时返回模拟数据
                return {
                    "success": True,
                    "message": "记忆蒸馏完成",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"记忆蒸馏失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        # ==================== 设备管理API ====================
        
        @self.app.get("/api/devices")
        async def get_devices():
            """
            获取所有设备列表

            执行流程:
            1. 从设备管理器获取所有设备
            2. 转换为字典列表返回
            """
            try:
                result = await self.device_manager.get_all_devices()
                if result.get("success"):
                    return {
                        "success": True,
                        "devices": result.get("data", []),
                        "count": len(result.get("data", [])),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                else:
                    return {
                        "success": False,
                        "message": result.get("message", "获取设备列表失败"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
            except Exception as e:
                logger.error(f"获取设备列表失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备列表失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/devices/{device_id}")
        async def get_device(device_id: str):
            """
            获取单个设备详情

            Args:
                device_id: 设备ID

            执行流程:
            1. 验证设备ID
            2. 查询设备信息
            3. 返回设备详情
            """
            try:
                result = await self.device_manager.get_device(device_id)
                if not result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": result.get("message", "设备不存在"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                return {
                    "success": True,
                    "device": result.get("data"),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"获取设备详情失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备详情失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/devices")
        async def create_device(request: Request):
            """
            添加新设备

            请求体:
            {
                "name": "设备名称",
                "type": "设备类型(lamp/ac/curtain)",
                "device_id": "设备ID", // 可选，不传则自动生成
                "config": {} // 可选
            }

            执行流程:
            1. 解析请求体
            2. 验证必填参数
            3. 创建设备
            4. 返回创建设备信息
            """
            try:
                body = await request.json()
                name = body.get("name", "").strip()
                device_type = body.get("type", "").strip()
                device_id = body.get("device_id", "").strip()
                config = body.get("config", {})

                # 参数验证
                if not name:
                    return {
                        "success": False,
                        "error_code": "INVALID_PARAM",
                        "message": "设备名称不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                if not device_type:
                    return {
                        "success": False,
                        "error_code": "INVALID_PARAM",
                        "message": "设备类型不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                # 如果没有提供device_id，自动生成
                if not device_id:
                    import uuid
                    device_id = f"{device_type}_{uuid.uuid4().hex[:8]}"

                # 创建设备
                result = await self.device_manager.create_device(
                    device_type=device_type,
                    device_id=device_id,
                    device_name=name
                )

                if result.get("success"):
                    return {
                        "success": True,
                        "device": result.get("data"),
                        "message": "设备创建成功",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                else:
                    return {
                        "success": False,
                        "error_code": "CREATE_FAILED",
                        "message": result.get("message", "创建设备失败"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
            except ValueError as e:
                return {
                    "success": False,
                    "error_code": "INVALID_PARAM",
                    "message": str(e),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"创建设备失败: {e}")
                return {
                    "success": False,
                    "message": f"创建设备失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.put("/api/devices/{device_id}")
        async def update_device(device_id: str, request: Request):
            """
            更新设备信息

            请求体:
            {
                "name": "新名称",  // 可选
                "config": {}       // 可选
            }

            执行流程:
            1. 验证设备存在
            2. 解析请求体
            3. 更新设备信息
            4. 返回更新后的设备
            """
            try:
                # 验证设备存在
                check_result = await self.device_manager.get_device(device_id)
                if not check_result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": "设备不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                body = await request.json()
                name = body.get("name")
                config = body.get("config")

                # 更新设备名称
                if name:
                    result = await self.device_manager.update_device_name(device_id, name)
                    if not result.get("success"):
                        return {
                            "success": False,
                            "error_code": "UPDATE_FAILED",
                            "message": result.get("message", "更新设备名称失败"),
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        }

                # 获取更新后的设备信息
                result = await self.device_manager.get_device(device_id)

                return {
                    "success": True,
                    "device": result.get("data"),
                    "message": "设备更新成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except ValueError as e:
                return {
                    "success": False,
                    "error_code": "INVALID_PARAM",
                    "message": str(e),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"更新设备失败: {e}")
                return {
                    "success": False,
                    "message": f"更新设备失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.delete("/api/devices/{device_id}")
        async def delete_device(device_id: str):
            """
            删除设备

            Args:
                device_id: 设备ID

            执行流程:
            1. 验证设备存在
            2. 删除设备
            3. 返回删除结果
            """
            try:
                result = await self.device_manager.delete_device(device_id)

                if not result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": result.get("message", "设备不存在"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                return {
                    "success": True,
                    "message": "设备删除成功",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"删除设备失败: {e}")
                return {
                    "success": False,
                    "message": f"删除设备失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/devices/{device_id}/command")
        async def send_device_command(device_id: str, request: Request):
            """
            发送设备控制命令

            请求体:
            {
                "command": "命令名称",
                "params": {}  // 可选
            }

            台灯命令:
            - power_on: 开灯
            - power_off: 关灯
            - set_brightness: 设置亮度 (params: {brightness: 0-100})
            - set_color_temp: 设置色温 (params: {color_temp: "normal"/"eye_care"})
            - set_timer: 设置定时 (params: {minutes: 整数})

            空调命令:
            - power_on: 开机
            - power_off: 关机
            - set_temperature: 设置温度 (params: {temperature: 16-30})
            - set_mode: 设置模式 (params: {mode: "cool"/"heat"})
            - set_fan_speed: 设置风速 (params: {fan_speed: 1-5})

            窗帘命令:
            - open: 全开
            - close: 全关
            - stop: 停止
            - set_position: 设置位置 (params: {position: 0-100})

            执行流程:
            1. 验证设备存在
            2. 解析命令
            3. 执行控制
            4. 返回执行结果
            """
            try:
                body = await request.json()
                command = body.get("command", "").strip()
                params = body.get("params", {})

                if not command:
                    return {
                        "success": False,
                        "error_code": "INVALID_PARAM",
                        "message": "命令不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                # 执行命令
                result = await self.device_manager.execute_command(
                    device_id=device_id,
                    command=command,
                    params=params
                )

                return {
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "error_code": result.get("error_code"),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"发送设备命令失败: {e}")
                return {
                    "success": False,
                    "message": f"发送命令失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/devices/control")
        async def control_device(request: Request):
            """
            发送设备控制命令（别名接口）

            请求体:
            {
                "device_id": "设备ID",
                "command": "命令名称",
                "params": {}  // 可选
            }

            执行流程:
            1. 解析请求体，获取设备ID、命令和参数
            2. 验证设备存在
            3. 执行控制
            4. 返回执行结果
            """
            try:
                body = await request.json()
                device_id = body.get("device_id", "").strip()
                command = body.get("command", "").strip()
                params = body.get("params", {})

                if not device_id:
                    return {
                        "success": False,
                        "error_code": "INVALID_PARAM",
                        "message": "设备ID不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                if not command:
                    return {
                        "success": False,
                        "error_code": "INVALID_PARAM",
                        "message": "命令不能为空",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                # 执行命令
                result = await self.device_manager.execute_command(
                    device_id=device_id,
                    command=command,
                    params=params
                )

                return {
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "error_code": result.get("error_code"),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"发送设备命令失败: {e}")
                return {
                    "success": False,
                    "message": f"发送命令失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/devices/{device_id}/status")
        async def get_device_status(device_id: str):
            """
            获取设备实时状态

            Args:
                device_id: 设备ID

            执行流程:
            1. 验证设备存在
            2. 获取设备状态
            3. 返回状态信息
            """
            try:
                result = await self.device_manager.get_device_status(device_id)

                if not result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": result.get("message", "设备不存在"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }

                return {
                    "success": True,
                    "status": result.get("data"),
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"获取设备状态失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备状态失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/device-types")
        async def get_device_types():
            """
            获取支持的设备类型列表
            
            用于前端创建设备时选择类型
            """
            try:
                return {
                    "success": True,
                    "types": [
                        {
                            "value": "lamp",
                            "label": "台灯",
                            "icon": "💡",
                            "description": "智能台灯，支持亮度调节、色温切换"
                        },
                        {
                            "value": "ac",
                            "label": "空调",
                            "icon": "❄️",
                            "description": "智能空调，支持温度调节、模式切换"
                        },
                        {
                            "value": "curtain",
                            "label": "窗帘",
                            "icon": "🪟",
                            "description": "智能窗帘，支持位置调节"
                        }
                    ],
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"获取设备类型失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备类型失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        # ==================== 设备状态管理API ====================
        
        @self.app.get("/api/devices/status")
        async def get_all_devices_status(current_user: dict = Depends(require_read_access)):
            """
            获取所有设备的状态摘要
            
            Returns:
                所有设备的状态信息和统计摘要
            """
            try:
                result = await self.device_manager.get_all_devices()
                
                if not result.get("success"):
                    return {
                        "success": False,
                        "message": result.get("message", "获取设备状态失败"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                devices = result.get("data", [])
                
                # 计算状态统计
                total = len(devices)
                online = sum(1 for d in devices if d.get("status") == "online")
                offline = sum(1 for d in devices if d.get("status") == "offline")
                error = sum(1 for d in devices if d.get("status") == "error")
                
                return {
                    "success": True,
                    "devices": devices,
                    "summary": {
                        "total": total,
                        "online": online,
                        "offline": offline,
                        "error": error,
                        "online_rate": round(online / total * 100, 1) if total > 0 else 0
                    },
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"获取所有设备状态失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备状态失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.get("/api/devices/{device_id}/history")
        async def get_device_status_history(
            device_id: str,
            hours: int = 24,
            start_time: str = None,
            end_time: str = None,
            current_user: dict = Depends(require_read_access)
        ):
            """
            获取设备状态历史记录
            
            Args:
                device_id: 设备ID
                hours: 查询最近多少小时（默认24小时）
                start_time: 开始时间（ISO格式，可选）
                end_time: 结束时间（ISO格式，可选）
            
            Returns:
                设备状态历史记录
            """
            try:
                # 验证设备存在
                check_result = await self.device_manager.get_device(device_id)
                if not check_result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": "设备不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                # 限制查询范围（最多7天）
                if hours > 168:  # 7 days
                    hours = 168
                
                # 构建查询参数
                query_params = {"device_id": device_id, "hours": hours}
                if start_time:
                    query_params["start_time"] = start_time
                if end_time:
                    query_params["end_time"] = end_time
                
                # 获取历史记录（从设备管理器或数据库）
                # 这里简化处理，返回模拟数据
                # 实际实现应该从数据库查询
                history = []
                
                return {
                    "success": True,
                    "device_id": device_id,
                    "history": history,
                    "query_params": query_params,
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"获取设备状态历史失败: {e}")
                return {
                    "success": False,
                    "message": f"获取设备状态历史失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.post("/api/devices/{device_id}/refresh")
        async def refresh_device_status(device_id: str, current_user: dict = Depends(require_write_access)):
            """
            强制刷新设备状态
            
            Args:
                device_id: 设备ID
            
            Returns:
                刷新后的设备状态
            """
            try:
                # 验证设备存在
                check_result = await self.device_manager.get_device(device_id)
                if not check_result.get("success"):
                    return {
                        "success": False,
                        "error_code": "DEVICE_NOT_FOUND",
                        "message": "设备不存在",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                
                # 强制刷新设备状态
                result = await self.device_manager.refresh_device_status(device_id)
                
                if result.get("success"):
                    return {
                        "success": True,
                        "device_id": device_id,
                        "status": result.get("data"),
                        "message": "设备状态已刷新",
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                else:
                    return {
                        "success": False,
                        "error_code": "REFRESH_FAILED",
                        "message": result.get("message", "刷新设备状态失败"),
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
            except Exception as e:
                logger.error(f"刷新设备状态失败: {e}")
                return {
                    "success": False,
                    "message": f"刷新设备状态失败: {str(e)}",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                }
        
        @self.app.websocket("/api/devices/status/stream")
        async def device_status_websocket(websocket: WebSocket):
            """
            WebSocket端点，提供实时设备状态更新
            
            连接后，客户端将收到设备状态变更的实时推送
            """
            # 验证WebSocket连接
            try:
                # 从查询参数或头部获取token
                token = websocket.query_params.get('token')
                if not token:
                    # 尝试从头部获取
                    headers = dict(websocket.headers)
                    auth_header = headers.get('authorization', '')
                    if auth_header.startswith('Bearer '):
                        token = auth_header[7:]
                
                if not token:
                    await websocket.close(code=1008, reason="Authentication required")
                    return
                
                # 验证token
                from gateway.auth_middleware import AuthMiddleware
                payload = AuthMiddleware.verify_token(token)
                user_role = payload.get('role', 'user')
                
                # 检查权限
                from gateway.auth_middleware import ROLES
                if 'read' not in ROLES.get(user_role, []):
                    await websocket.close(code=1008, reason="Insufficient permissions")
                    return
            except Exception as e:
                await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
                return
            
            await websocket.accept()
            client_id = f"ws_{id(websocket)}"
            
            try:
                logger.info(f"WebSocket客户端 {client_id} 已连接")
                
                # 发送初始连接成功消息
                await websocket.send_json({
                    "type": "connected",
                    "message": "已连接到设备状态流",
                    "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                })
                
                # 注册状态变更回调
                async def status_change_callback(device_id: str, status: dict):
                    try:
                        await websocket.send_json({
                            "type": "status_update",
                            "device_id": device_id,
                            "status": status,
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        })
                    except Exception as e:
                        logger.error(f"发送WebSocket消息失败: {e}")
                
                # 注册回调到设备管理器
                self.device_manager.register_status_callback(client_id, status_change_callback)
                
                # 保持连接并处理客户端消息
                while True:
                    try:
                        # 接收客户端消息（用于心跳检测）
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        # 处理订阅请求
                        if message.get("type") == "subscribe":
                            device_ids = message.get("device_ids", [])
                            await websocket.send_json({
                                "type": "subscribed",
                                "device_ids": device_ids,
                                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                            })
                        
                        # 处理心跳
                        elif message.get("type") == "ping":
                            await websocket.send_json({
                                "type": "pong",
                                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                            })
                            
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Invalid JSON format",
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        })
                    except WebSocketDisconnect:
                        break
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket客户端 {client_id} 已断开")
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
            finally:
                # 注销回调
                self.device_manager.unregister_status_callback(client_id)
                try:
                    await websocket.close()
                except:
                    pass
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """启动API服务器"""
        import uvicorn
        import asyncio
        
        uvicorn.run(self.app, host=host, port=port)

# 仅在直接运行模块时创建实例，避免导入时重复初始化
if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="启动API网关服务器")
    parser.add_argument('--port', type=int, default=8003, help='服务器端口')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机')
    args = parser.parse_args()
    
    # 创建API网关实例并启动服务器
    gateway = APIGateway()
    gateway.run(host=args.host, port=args.port)
# 当作为模块导入时，创建全局 app 实例供 Uvicorn 使用
# 这样 uvicorn src.gateway.api_gateway:app 命令就能找到 app 实例
gateway = APIGateway()
app = gateway.app

# 当作为模块导入时，不创建实例，由调用方创建