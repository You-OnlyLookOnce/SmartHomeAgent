from typing import Dict, List, Optional
import asyncio
from src.agents.workflow_engine import SmartHomeWorkflowEngine
from src.agents.reflection_module import ExecutionReflectionModule

class AgentCluster:
    """Agent集群管理器 - 管理多个Agent实例"""
    
    def __init__(self):
        self.agents = {}
        self.task_router = {}
        self._initialize_agents()
        self._setup_task_routing()
        # 初始化工作流引擎
        self.workflow_engine = SmartHomeWorkflowEngine(self)
        # 初始化反思模块
        self.reflection_module = ExecutionReflectionModule()
    
    def _initialize_agents(self):
        """初始化所有Agent实例"""
        try:
            from src.agents.device_control_agent import DeviceControlAgent
            from src.agents.note_keeper_agent import NoteKeeperAgent
            from src.agents.task_manager_agent import TaskManagerAgent
            from src.agents.security_agent import SecurityAgent
            from src.agents.conversation_agent import ConversationAgent
            
            self.agents = {
                "conversation": ConversationAgent(),
                "device_control": DeviceControlAgent(),
                "note_keeper": NoteKeeperAgent(),
                "task_manager": TaskManagerAgent(),
                "security": SecurityAgent()
            }
            print("Agent集群初始化成功")
        except Exception as e:
            print(f"Agent集群初始化失败: {e}")
            self.agents = {}
    
    def _setup_task_routing(self):
        """设置任务路由规则"""
        self.task_router = {
            # 设备控制任务
            "开灯": "device_control",
            "关灯": "device_control",
            "调亮度": "device_control",
            
            # 笔记任务
            "记笔记": "note_keeper",
            "保存偏好": "note_keeper",
            "回忆记忆": "note_keeper",
            "搜索": "note_keeper",
            
            # 任务管理
            "创建提醒": "task_manager",
            "安排任务": "task_manager",
            "发送通知": "task_manager",
            
            # 安全任务
            "安全检查": "security",
            "监控": "security",
            "告警": "security"
        }
    
    def route_task(self, task: str) -> Optional[str]:
        """根据任务类型路由到合适的Agent"""
        # 精确匹配
        for keyword, agent_id in self.task_router.items():
            if keyword in task:
                return agent_id
        
        # 模糊匹配
        if "灯" in task:
            return "device_control"
        elif "笔记" in task or "记忆" in task or "搜索" in task:
            return "note_keeper"
        elif "提醒" in task or "任务" in task or "通知" in task:
            return "task_manager"
        elif "安全" in task or "监控" in task or "告警" in task:
            return "security"
        
        # 默认路由到对话Agent处理通用问题
        return "conversation"
    
    async def execute_task(self, task: str, context: Dict = None) -> Dict:
        """执行任务 - 通过集群路由"""
        # 检查是否为场景模式请求，使用工作流引擎处理
        if self.workflow_engine.is_known_scenario(task):
            result = await self.workflow_engine.execute_with_chain(task)
            # 对工作流执行结果进行反思
            reflection = await self.reflection_module.reflect_on_execution(result)
            result['reflection'] = reflection
            return result
        
        # 检查是否需要多Agent协作
        if self._needs_multiple_agents(task):
            result = await self._coordinate_multiple_agents(task, context)
            # 对多Agent协作结果进行反思
            reflection = await self.reflection_module.reflect_on_execution(result)
            result['reflection'] = reflection
            return result
        
        # 路由到合适的Agent
        agent_id = self.route_task(task)
        
        if not agent_id or agent_id not in self.agents:
            result = {
                "success": False,
                "message": "没有找到合适的Agent处理此任务"
            }
            # 对失败结果进行反思
            reflection = await self.reflection_module.reflect_on_execution(result)
            result['reflection'] = reflection
            return result
        
        # 执行任务
        try:
            agent = self.agents[agent_id]
            # 从上下文获取用户ID和session_id
            user_id = context.get("user_id", "default_user") if context else "default_user"
            session_id = context.get("session_id") if context else None
            
            # 根据Agent类型传递不同参数
            if agent_id == "conversation":
                agent_result = await agent.execute(task, user_id=user_id, session_id=session_id)
            else:
                agent_result = await agent.execute(task)
                
            result = {
                "success": True,
                "agent": agent.agent_id,
                "role": agent.role,
                "result": agent_result,
                "execution_log": [{"step": "执行任务", "agent": agent_id, "result": agent_result, "timestamp": "2026-03-17T10:00:00"}]
            }
            # 对执行结果进行反思
            reflection = await self.reflection_module.reflect_on_execution(result)
            result['reflection'] = reflection
            return result
        except Exception as e:
            result = {
                "success": False,
                "message": f"任务执行失败: {str(e)}",
                "agent": agent_id,
                "execution_log": [{"step": "执行任务", "agent": agent_id, "error": str(e), "timestamp": "2026-03-17T10:00:00"}]
            }
            # 对失败结果进行反思
            reflection = await self.reflection_module.reflect_on_execution(result)
            result['reflection'] = reflection
            return result
    
    def _needs_multiple_agents(self, task: str) -> bool:
        """判断是否需要多Agent协作"""
        # 复杂任务需要多个Agent协作
        complex_tasks = ["场景模式", "综合控制", "全屋控制"]
        task_lower = task.lower()
        return any(complex_task in task_lower for complex_task in complex_tasks)
    
    async def _coordinate_multiple_agents(self, task: str, context: Dict = None) -> Dict:
        """协调多个Agent完成复杂任务"""
        print(f"协调多个Agent处理复杂任务: {task}")
        
        # 任务分解
        subtasks = self._decompose_task(task)
        print(f"任务分解结果: {subtasks}")
        
        # 执行子任务
        results = []
        for subtask in subtasks:
            agent_id = self.route_task(subtask)
            if agent_id and agent_id in self.agents:
                try:
                    agent = self.agents[agent_id]
                    result = await agent.execute(subtask)
                    results.append({
                        "agent": agent_id,
                        "subtask": subtask,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "agent": agent_id,
                        "subtask": subtask,
                        "error": str(e)
                    })
        
        # 结果汇总
        summary = self._summarize_results(results)
        print(f"结果汇总: {summary}")
        
        return {
            "success": True,
            "message": f"复杂任务处理完成",
            "coordinated": True,
            "results": results,
            "summary": summary
        }
    
    def _decompose_task(self, task: str) -> List[str]:
        """分解复杂任务为子任务"""
        task_lower = task.lower()
        
        if "场景模式" in task_lower or "电影模式" in task_lower:
            return ["关灯", "创建提醒", "安全检查"]
        elif "综合控制" in task_lower:
            return ["开灯", "创建提醒"]
        elif "全屋控制" in task_lower:
            return ["开灯", "安全检查"]
        else:
            return [task]
    
    def _summarize_results(self, results: List[Dict]) -> str:
        """汇总多个Agent的执行结果"""
        success_count = sum(1 for r in results if "error" not in r)
        total_count = len(results)
        
        summary = f"已完成 {success_count}/{total_count} 个子任务"
        
        for result in results:
            if "error" in result:
                summary += f"\n{result['agent']} 处理 {result['subtask']} 失败: {result['error']}"
            else:
                summary += f"\n{result['agent']} 处理 {result['subtask']} 成功"
        
        return summary
    
    def get_agent_status(self) -> Dict:
        """获取所有Agent的状态"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "capabilities": agent.capabilities,
                "context_length": len(agent.context),
                "execution_log_length": len(agent.execution_log),
                "emotion_state": agent.emotion_state
            }
        return status
    
    def broadcast_message(self, message: Dict):
        """向所有Agent广播消息"""
        results = {}
        for agent_id, agent in self.agents.items():
            try:
                result = agent.handle_message(message)
                results[agent_id] = result
            except Exception as e:
                results[agent_id] = {"error": str(e)}
        return results
    
    def get_agent_by_id(self, agent_id: str) -> Optional:
        """根据ID获取Agent实例"""
        return self.agents.get(agent_id)
    
    def reload_agents(self):
        """重新加载所有Agent"""
        self._initialize_agents()
        return {"success": True, "message": "Agent集群已重新加载"}