from typing import Dict, List, Optional
import datetime

class WorkflowStep:
    """工作流步骤"""
    
    def __init__(self, name: str, agent_role: str, task: str):
        self.name = name
        self.agent_role = agent_role
        self.task = task

class WorkflowChain:
    """工作流链"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
    
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)

class SmartHomeWorkflowEngine:
    """智能家居工作流引擎 - Chat Chain 上层封装"""
    
    def __init__(self, agent_cluster):
        self.agent_cluster = agent_cluster
        self.chain_templates = self._load_chain_templates()
    
    def _load_chain_templates(self) -> Dict[str, WorkflowChain]:
        """加载预定义的工作流模板"""
        templates = {}
        
        # 睡前模式
        sleep_mode = WorkflowChain("睡前模式")
        sleep_mode.add_step(WorkflowStep("关灯", "device_control", "关灯"))
        sleep_mode.add_step(WorkflowStep("创建提醒", "task_manager", "创建明天早上的提醒"))
        sleep_mode.add_step(WorkflowStep("安全检查", "security", "安全检查"))
        templates["睡前模式"] = sleep_mode
        
        # 起床模式
        wakeup_mode = WorkflowChain("起床模式")
        wakeup_mode.add_step(WorkflowStep("开灯", "device_control", "开灯"))
        wakeup_mode.add_step(WorkflowStep("创建提醒", "task_manager", "创建今天的日程提醒"))
        templates["起床模式"] = wakeup_mode
        
        # 离家模式
        leave_home_mode = WorkflowChain("离家模式")
        leave_home_mode.add_step(WorkflowStep("关灯", "device_control", "关灯"))
        leave_home_mode.add_step(WorkflowStep("安全检查", "security", "安全检查"))
        templates["离家模式"] = leave_home_mode
        
        # 回家模式
        return_home_mode = WorkflowChain("回家模式")
        return_home_mode.add_step(WorkflowStep("开灯", "device_control", "开灯"))
        return_home_mode.add_step(WorkflowStep("安全检查", "security", "安全检查"))
        templates["回家模式"] = return_home_mode
        
        return templates
    
    def is_known_scenario(self, request: str) -> bool:
        """判断是否为已知场景"""
        for template_name in self.chain_templates:
            if template_name in request:
                return True
        return False
    
    def load_template_chain(self, request: str) -> WorkflowChain:
        """加载模板工作流"""
        for template_name, chain in self.chain_templates.items():
            if template_name in request:
                return chain
        return None
    
    async def plan_dynamic_chain(self, request: str) -> WorkflowChain:
        """动态规划工作流"""
        # 这里可以根据用户请求动态生成工作流
        # 暂时返回一个默认的工作流
        chain = WorkflowChain("动态工作流")
        
        # 简单的动态规划逻辑
        if "灯" in request:
            chain.add_step(WorkflowStep("控制灯光", "device_control", request))
        if "提醒" in request:
            chain.add_step(WorkflowStep("创建提醒", "task_manager", request))
        if "安全" in request:
            chain.add_step(WorkflowStep("安全检查", "security", request))
        
        return chain
    
    def build_context(self, execution_log: List[Dict]) -> Dict:
        """构建上下文"""
        context = {}
        for log in execution_log:
            if "result" in log:
                context[f"{log['step']}_result"] = log['result']
        return context
    
    async def recovery_strategy(self, step: WorkflowStep, result: Dict) -> Dict:
        """失败恢复策略"""
        # 简单的恢复策略：记录失败并继续
        return {
            'step': f"{step.name}_recovery",
            'agent': step.agent_role,
            'result': {'success': False, 'message': f"{step.name}失败，已记录"},
            'timestamp': datetime.datetime.now()
        }
    
    def generate_final_response(self, execution_log: List[Dict]) -> str:
        """生成最终响应"""
        success_count = sum(1 for log in execution_log if 'result' in log and log['result'].get('success', False))
        total_count = len(execution_log)
        
        response = f"已完成 {success_count}/{total_count} 个步骤\n"
        for log in execution_log:
            if 'error' in log:
                response += f"{log['step']}: 失败 - {log['error']}\n"
            elif 'result' in log:
                response += f"{log['step']}: 成功 - {log['result'].get('message', '操作完成')}\n"
        
        return response
    
    async def execute_with_chain(self, request: str) -> Dict:
        """使用工作流执行任务"""
        # Step 1: 判断是否使用预定义 Chain 或动态生成
        if self.is_known_scenario(request):
            chain = self.load_template_chain(request)
        else:
            chain = await self.plan_dynamic_chain(request)
        
        if not chain or not chain.steps:
            return {
                "success": False,
                "message": "无法生成工作流"
            }
        
        # Step 2: 按照 Chain 顺序执行
        execution_log = []
        for step in chain.steps:
            # 每个步骤调用对应的 Agent
            agent_id = step.agent_role
            
            # 传入前一步的结果作为上下文
            context = self.build_context(execution_log)
            
            try:
                result = await self.agent_cluster.execute_task(step.task, context)
                execution_log.append({
                    'step': step.name,
                    'agent': agent_id,
                    'result': result,
                    'timestamp': datetime.datetime.now()
                })
                
                # 失败则触发恢复（不是简单的重试）
                if not result.get('success', False):
                    recovery_result = await self.recovery_strategy(step, result)
                    execution_log.append(recovery_result)
            except Exception as e:
                execution_log.append({
                    'step': step.name,
                    'agent': agent_id,
                    'error': str(e),
                    'timestamp': datetime.datetime.now()
                })
        
        # Step 3: 汇总结果
        final_response = self.generate_final_response(execution_log)
        
        return {
            "success": True,
            "message": "工作流执行完成",
            "execution_log": execution_log,
            "final_response": final_response
        }
    
    def get_available_templates(self) -> List[str]:
        """获取可用的工作流模板"""
        return list(self.chain_templates.keys())