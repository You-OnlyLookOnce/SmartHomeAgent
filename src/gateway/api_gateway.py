from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
import asyncio
import time
import os
import json

from src.tools.datetime_utils import format_local_datetime

class APIGateway:
    """API网关 - 提供RESTful API服务"""
    
    def __init__(self):
        self.app = FastAPI(title="智能家居智能体API", version="1.0.0")
        self._setup_middleware()
        self._setup_static_files()
        self._setup_templates()
        self._setup_routes()
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """初始化依赖"""
        from src.agent.independent_session_manager import IndependentSessionManager
        self.session_manager = IndependentSessionManager()
        
        # 初始化搜索相关依赖
        from src.skills.search_skills.web_search import WebSearchSkill
        from src.skills.search_skills.search_judgment import SearchJudgment
        from src.skills.search_skills.search_integration import SearchIntegration
        from src.ai.qiniu_llm import QiniuLLM
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        self.api_key = os.getenv('QINIU_AI_API_KEY', os.getenv('QINIU_ACCESS_KEY'))
        
        self.web_search = WebSearchSkill(self.api_key)
        self.search_judgment = SearchJudgment()
        self.search_integration = SearchIntegration(self.api_key)
        self.llm = QiniuLLM()
    
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
        
        # 请求日志中间件
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
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
                return self.templates.TemplateResponse("index.html", {"request": request})
            except AttributeError:
                # 如果模板未设置，返回API信息
                return {"message": "智能家居智能体API", "version": "1.0.0"}
        
        @self.app.post("/api/chat")
        async def chat(request: Request):
            """聊天接口"""
            body = await request.json()
            user_input = body.get("message", "")
            user_id = body.get("user_id", "default_user")
            session_id = body.get("session_id")
            stream = body.get("stream", True)  # 默认启用流式响应
            
            # 如果没有提供session_id，创建一个新会话
            if not session_id:
                new_chat = self.session_manager.create_session(user_id=user_id)
                session_id = new_chat["session_id"]
            
            # 传递用户ID和session_id作为上下文
            context = {"user_id": user_id, "session_id": session_id, "stream": stream}
            
            # 检查是否需要网络搜索
            is_search_needed = self.search_judgment.is_search_needed(user_input)
            print(f"[搜索] 用户查询: {user_input}")
            print(f"[搜索] 是否需要搜索: {is_search_needed}")
            
            # 强制对日期相关查询执行搜索
            date_related_keywords = ["今天是几号", "明天是几号", "今天星期几", "明天星期几", "今年是哪一年", "现在几点了", "几点了", "今天日期", "明天日期", "当前时间", "现在时间", "日期", "时间", "联网搜索"]
            force_search = any(keyword in user_input for keyword in date_related_keywords)
            
            if is_search_needed or force_search:
                # 执行网络搜索
                search_type = self.search_judgment.get_search_type(user_input)
                time_filter = self.search_judgment.get_time_filter(user_input)
                
                print(f"[搜索] 搜索类型: {search_type}")
                print(f"[搜索] 时间过滤: {time_filter}")
                print(f"[搜索] 强制搜索: {force_search}")
                
                # 执行搜索
                try:
                    search_result = self.web_search.execute(
                        user_input,
                        search_type=search_type,
                        time_filter=time_filter,
                        max_retries=3
                    )
                except Exception as e:
                    error_message = f"搜索执行异常: {str(e)}"
                    print(f"[搜索] 执行异常: {error_message}")
                    # 即使搜索失败，也调用LLM提供回答
                    if stream:
                        async def generate():
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 发送搜索失败的状态
                            error_data = {"type": "error", "content": "抱歉，搜索服务暂时不可用"}
                            yield f"data: {json.dumps(error_data)}\n\n"
                            # 发送正在生成回答的状态
                            generating_data = {"type": "generating", "content": "正在生成回答..."}
                            yield f"data: {json.dumps(generating_data)}\n\n"
                            # 执行LLM并获取流式生成器
                            async for chunk in self.llm.generate_text(user_input, stream=True):
                                # 发送SSE格式的数据
                                yield f"data: {json.dumps(chunk)}\n\n"
                        
                        return StreamingResponse(generate(), media_type="text/event-stream")
                    else:
                        # 非流式响应
                        result = await self.llm.generate_text(user_input, stream=False)
                        
                        # 保存对话历史
                        if result.get("success", False):
                            self.session_manager.save_conversation_history(
                                session_id,
                                user_input,
                                result.get("text", "")
                            )
                        
                        return {
                            "success": result.get("success", False),
                            "response": {
                                "message": result.get("text", ""),
                                "search_error": {
                                    "error_code": "EXECUTION_ERROR",
                                    "error_message": error_message,
                                    "friendly_message": "抱歉，搜索服务暂时不可用"
                                }
                            },
                            "agent": "llm",
                            "session_id": session_id,
                            "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                        }
                
                if search_result.get("success", False):
                    # 整合搜索结果
                    integrated_answer = await self.search_integration.integrate_search_results(user_input, search_result.get("result", ""))
                    
                    # 保存对话历史
                    self.session_manager.save_conversation_history(
                        session_id,
                        user_input,
                        integrated_answer
                    )
                    
                    if stream:
                        async def generate():
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 发送正在搜索的状态
                            searching_data = {"type": "searching", "content": "正在联网搜索..."}
                            yield f"data: {json.dumps(searching_data)}\n\n"
                            # 发送整合后的回答
                            answer_data = {"type": "answer", "content": integrated_answer}
                            yield f"data: {json.dumps(answer_data)}\n\n"
                            end_data = {"type": "stream_end"}
                            yield f"data: {json.dumps(end_data)}\n\n"
                        
                        return StreamingResponse(generate(), media_type="text/event-stream")
                    else:
                        return {
                            "success": True,
                            "response": {
                                "message": integrated_answer
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
                    if stream:
                        async def generate():
                            # 首先发送会话ID
                            session_id_data = {"type": "session_id", "content": session_id}
                            yield f"data: {json.dumps(session_id_data)}\n\n"
                            # 发送搜索失败的状态
                            error_data = {"type": "error", "content": friendly_message}
                            yield f"data: {json.dumps(error_data)}\n\n"
                            # 发送正在生成回答的状态
                            generating_data = {"type": "generating", "content": "正在生成回答..."}
                            yield f"data: {json.dumps(generating_data)}\n\n"
                            # 执行LLM并获取流式生成器
                            async for chunk in self.llm.generate_text(user_input, stream=True):
                                # 发送SSE格式的数据
                                yield f"data: {json.dumps(chunk)}\n\n"
                        
                        return StreamingResponse(generate(), media_type="text/event-stream")
                    else:
                        # 非流式响应
                        result = await self.llm.generate_text(user_input, stream=False)
                        
                        # 保存对话历史
                        if result.get("success", False):
                            self.session_manager.save_conversation_history(
                                session_id,
                                user_input,
                                result.get("text", "")
                            )
                        
                        return {
                            "success": result.get("success", False),
                            "response": {
                                "message": result.get("text", ""),
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
                        async for chunk in self.llm.generate_text(user_input, stream=True):
                            # 发送SSE格式的数据
                            yield f"data: {json.dumps(chunk)}\n\n"
                    
                    return StreamingResponse(generate(), media_type="text/event-stream")
                else:
                    # 非流式响应
                    result = await self.llm.generate_text(user_input, stream=False)
                    
                    # 保存对话历史
                    if result.get("success", False):
                        self.session_manager.save_conversation_history(
                            session_id,
                            user_input,
                            result.get("text", "")
                        )
                    
                    return {
                        "success": result.get("success", False),
                        "response": {
                            "message": result.get("text", "")
                        },
                        "agent": "llm",
                        "session_id": session_id,
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
        
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
        async def create_chat(request: Dict):
            """创建新对话"""
            name = request.get("name", "New Chat")
            user_id = request.get("user_id", "default")
            
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
        async def update_chat(session_id: str, request: Dict):
            """更新对话信息"""
            name = request.get("name")
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
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """启动API服务器"""
        import uvicorn
        import asyncio
        
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    # 创建API网关实例并启动服务器
    gateway = APIGateway()
    gateway.run(port=8003)

# 创建API网关实例并导出app变量，供uvicorn使用
gateway = APIGateway()
app = gateway.app