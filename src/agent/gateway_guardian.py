import asyncio
import logging
import time
import os
from datetime import datetime

class GatewayGuardian:
    """Gateway守护者 - 崩溃自修复机制"""
    
    def __init__(self):
        self.health_check_interval = 30  # 每30秒检查一次
        self.max_restart_attempts = 3
        self.self_healing_enabled = True
        self.active_connections = []
        self.recent_errors = []
        
        # 确保日志目录存在
        self.log_dir = "data/logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            filename=os.path.join(self.log_dir, "gateway_guardian.log"),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    async def start_health_monitor(self):
        """启动健康监控"""
        logging.info("Gateway守护者启动")
        while self.self_healing_enabled:
            try:
                await self._health_check()
            except Exception as e:
                logging.error(f"健康检查异常: {e}")
                await self._trigger_self_healing()
            
            await asyncio.sleep(self.health_check_interval)
    
    async def _health_check(self) -> bool:
        """执行健康检查"""
        checks = {
            "gateway_process": self._check_process,
            "api_response_time": self._check_api_latency,
            "memory_usage": self._check_memory,
            "llm_service": self._check_llm_service
        }
        
        results = {}
        for name, check_func in checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = False
                logging.error(f"{name} 检查失败: {e}")
        
        # 判断整体健康状态
        all_healthy = all(results.values())
        
        if not all_healthy:
            logging.warning(f"健康检查异常: {results}")
            self.recent_errors.append({
                "timestamp": datetime.now().isoformat(),
                "errors": results
            })
        
        return all_healthy
    
    async def _check_process(self) -> bool:
        """检查Gateway进程"""
        # 模拟进程检查
        return True
    
    async def _check_api_latency(self) -> bool:
        """检查API响应时间"""
        # 模拟API响应时间检查
        return True
    
    async def _check_memory(self) -> bool:
        """检查内存使用情况"""
        # 模拟内存检查
        return True
    
    async def _check_llm_service(self) -> bool:
        """检查LLM服务"""
        # 模拟LLM服务检查
        return True
    
    async def _trigger_self_healing(self):
        """触发自修复"""
        logging.info("开始自修复流程...")
        
        # 1. 记录崩溃现场
        await self._capture_crash_context()
        
        # 2. 尝试重启Gateway进程
        for attempt in range(self.max_restart_attempts):
            try:
                logging.info(f"尝试重启 (第{attempt + 1}次)...")
                await self._restart_gateway()
                
                # 3. 验证重启是否成功
                if await self._verify_restart():
                    logging.info("自修复成功!")
                    await self._send_notification("Gateway已自动恢复")
                    return
                    
            except Exception as e:
                logging.error(f"重启失败: {e}")
                await asyncio.sleep(5)  # 等待5秒后重试
        
        # 4. 所有尝试都失败，发送告警
        logging.critical("自修复失败，需要人工介入")
        await self._send_alert("Gateway自修复失败，请立即处理!")
    
    async def _capture_crash_context(self):
        """记录崩溃现场信息"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "memory_usage": "模拟内存使用",
            "cpu_usage": "模拟CPU使用",
            "active_connections": len(self.get_active_connections()),
            "recent_errors": self.get_recent_errors(10)
        }
        
        # 保存到日志
        logging.critical(f"崩溃上下文: {context}")
        
        # 保存到文件
        crash_file = os.path.join(self.log_dir, f"crash_{int(time.time())}.json")
        import json
        with open(crash_file, "w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
    
    async def _restart_gateway(self):
        """重启Gateway进程"""
        # 模拟重启过程
        logging.info("模拟重启Gateway进程...")
        await asyncio.sleep(2)
    
    async def _verify_restart(self) -> bool:
        """验证重启是否成功"""
        # 模拟验证过程
        logging.info("验证Gateway重启...")
        await asyncio.sleep(1)
        return True
    
    async def _send_notification(self, message: str):
        """发送通知"""
        logging.info(f"发送通知: {message}")
    
    async def _send_alert(self, message: str):
        """发送告警"""
        logging.critical(f"发送告警: {message}")
    
    def get_active_connections(self):
        """获取活跃连接"""
        return self.active_connections
    
    def get_recent_errors(self, count: int):
        """获取最近的错误"""
        return self.recent_errors[-count:]
