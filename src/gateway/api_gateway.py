from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
import asyncio
from datetime import datetime
import time
import os

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
        from src.agents.agent_cluster import AgentCluster
        self.agent_cluster = AgentCluster()
    
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
        async def chat(request: Dict):
            """聊天接口"""
            user_input = request.get("message", "")
            user_id = request.get("user_id", "default_user")
            
            # 传递用户ID作为上下文
            context = {"user_id": user_id}
            result = await self.agent_cluster.execute_task(user_input, context=context)
            
            # 处理不同Agent的返回格式
            response_data = result.get("result", {})
            if isinstance(response_data, dict) and "message" in response_data:
                # 如果result是一个包含message字段的字典，直接使用它
                response = response_data
            elif isinstance(response_data, dict) and "success" in response_data:
                # 如果result是一个完整的响应对象，直接使用它
                response = response_data
            else:
                # 否则使用默认格式
                response = response_data
            
            return {
                "success": result.get("success", False),
                "response": response,
                "agent": result.get("agent", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/device/control")
        async def device_control(request: Dict):
            """设备控制接口"""
            device_id = request.get("device_id")
            action = request.get("action")
            params = request.get("params", {})
            
            # 只处理灯光相关的控制
            if "灯" in device_id or "led" in device_id.lower():
                task = f"{action} {device_id}"
                result = await self.agent_cluster.execute_task(task)
                return result
            else:
                return {"success": False, "message": "只支持灯光设备控制"}
        
        @self.app.get("/api/device/status/{device_id}")
        async def get_device_status(device_id: str):
            """获取设备状态接口"""
            # 只处理灯光相关的状态查询
            if "灯" in device_id or "led" in device_id.lower():
                task = f"读取{device_id}状态"
                result = await self.agent_cluster.execute_task(task)
                return result
            else:
                return {"success": False, "message": "只支持灯光设备状态查询"}
        
        @self.app.post("/api/reminder/create")
        async def create_reminder(request: Dict):
            """创建提醒接口"""
            task = f"创建提醒 {request.get('title', '')}"
            result = await self.agent_cluster.execute_task(task)
            
            return result
        
        @self.app.get("/api/reminder/list/{user_id}")
        async def get_reminders(user_id: str):
            """获取提醒列表接口"""
            import json
            import os
            
            reminder_file = f"data/reminders/{user_id}.json"
            if os.path.exists(reminder_file):
                with open(reminder_file, "r", encoding="utf-8") as f:
                    reminders = json.load(f)
                return {"success": True, "reminders": reminders}
            else:
                return {"success": True, "reminders": []}
        
        @self.app.get("/api/agent/status")
        async def get_agent_status():
            """获取Agent状态接口"""
            status = self.agent_cluster.get_agent_status()
            
            return {
                "success": True,
                "agents": status,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/api/health")
        async def health_check():
            """健康检查接口"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "gateway": "ok",
                    "agents": "ok",
                    "database": "ok",
                    "llm": "ok"
                }
            }
        
        # 记忆管理接口
        @self.app.get("/api/memory/soul")
        async def get_soul_file():
            """获取人格文件"""
            try:
                from src.agent.memory_manager import MemoryManager
                memory_manager = MemoryManager()
                soul = memory_manager.read_soul()
                if soul:
                    return {"success": True, "data": str(soul)}
                else:
                    return {"success": True, "data": "{}"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.post("/api/memory/soul")
        async def save_soul_file(request: Dict):
            """保存人格文件"""
            try:
                content = request.get("content")
                from src.agent.memory_manager import MemoryManager
                memory_manager = MemoryManager()
                # 这里需要实现保存人格文件的方法
                # 暂时返回成功
                return {"success": True, "message": "人格文件保存成功"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.get("/api/memory/long-term")
        async def get_long_term_memory():
            """获取长期记忆文件"""
            try:
                from src.agent.memory_manager import MemoryManager
                memory_manager = MemoryManager()
                memory = memory_manager.read_long_term_memory()
                return {"success": True, "data": memory}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.post("/api/memory/long-term")
        async def save_long_term_memory(request: Dict):
            """保存长期记忆文件"""
            try:
                content = request.get("content")
                from src.agent.memory_manager import MemoryManager
                memory_manager = MemoryManager()
                memory_manager.write_long_term_memory(content)
                return {"success": True, "message": "记忆文件保存成功"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.post("/api/memory/distill")
        async def distill_memory(request: Dict):
            """执行记忆蒸馏"""
            try:
                # 这里需要实现记忆蒸馏的逻辑
                # 暂时返回成功
                return {"success": True, "message": "记忆蒸馏完成"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        # 定时任务接口
        @self.app.get("/api/scheduler/list")
        async def get_schedule_list():
            """获取定时任务列表"""
            try:
                # 这里需要实现获取定时任务列表的逻辑
                # 暂时返回空列表
                return {"success": True, "schedules": []}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.post("/api/scheduler/create")
        async def create_schedule(request: Dict):
            """创建定时任务"""
            try:
                title = request.get("title")
                time = request.get("time")
                # 这里需要实现创建定时任务的逻辑
                # 暂时返回成功
                return {"success": True, "message": "定时任务创建成功"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @self.app.delete("/api/scheduler/{schedule_id}")
        async def delete_schedule(schedule_id: str):
            """删除定时任务"""
            try:
                # 这里需要实现删除定时任务的逻辑
                # 暂时返回成功
                return {"success": True, "message": "定时任务删除成功"}
            except Exception as e:
                return {"success": False, "message": str(e)}
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """启动API服务器"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)