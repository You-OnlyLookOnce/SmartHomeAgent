from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import asyncio
from datetime import datetime
import time

class APIGateway:
    """API网关 - 提供RESTful API服务"""
    
    def __init__(self):
        self.app = FastAPI(title="智能家居智能体API", version="1.0.0")
        self._setup_middleware()
        self._setup_routes()
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """初始化依赖"""
        from src.agents.agent_cluster import AgentCluster
        self.agent_cluster = AgentCluster()
    
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
        async def root():
            return {"message": "智能家居智能体API", "version": "1.0.0"}
        
        @self.app.post("/api/chat")
        async def chat(request: Dict):
            """聊天接口"""
            user_input = request.get("message", "")
            user_id = request.get("user_id", "default_user")
            
            result = await self.agent_cluster.execute_task(user_input)
            
            return {
                "success": result.get("success", False),
                "response": result.get("result", {}),
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
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """启动API服务器"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)