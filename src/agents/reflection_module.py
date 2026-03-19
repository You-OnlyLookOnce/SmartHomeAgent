from typing import Dict, List
import datetime

class ExecutionReflectionModule:
    """任务执行反思模块 - ChatDev 思想"""
    
    def __init__(self):
        pass
    
    def format_execution_timeline(self, execution_log: List[Dict]) -> str:
        """格式化执行时间线"""
        timeline = []
        for i, log in enumerate(execution_log):
            step = log.get('step', f'Step {i+1}')
            agent = log.get('agent', 'Unknown')
            timestamp = log.get('timestamp', datetime.datetime.now())
            if 'result' in log:
                status = '成功' if log['result'].get('success', False) else '失败'
                message = log['result'].get('message', '')
                timeline.append(f"{timestamp}: {step} (由 {agent} 执行) - {status}: {message}")
            elif 'error' in log:
                timeline.append(f"{timestamp}: {step} (由 {agent} 执行) - 失败: {log['error']}")
        return '\n'.join(timeline)
    
    async def reflect_on_execution(self, task_result: dict) -> dict:
        """对整个任务执行过程进行反思
        
        用于发现潜在问题和优化机会
        
        Args:
            task_result: 包含完整执行日志的结果对象
            
        Returns:
            反思结果
        """
        # 构建反思提示
        reflection_prompt = f"""
        请对以下智能家居任务执行过程进行反思：
        
        任务目标：{task_result.get('message', '未知')}
        
        执行步骤时序:
        {self.format_execution_timeline(task_result.get('execution_log', []))}
        
        最终结果: {'成功' if task_result.get('success', False) else '失败'}
        
        请分析:
        1. 是否完全达成了用户的目标？(Y/N)
        2. 是否有中间步骤出现异常或犹豫？
        3. 如果重做一次，哪些地方可以改进？
        4. 是否需要向用户确认某些状态以避免误会？
        """
        
        # 这里可以使用LLM进行反思
        # 暂时使用模拟结果
        reflection = {
            "confidence": 0.95,
            "summary": "任务执行过程整体良好，所有步骤都成功完成。",
            "suggestions": [
                "可以考虑在执行前向用户确认详细需求",
                "可以优化执行顺序以提高效率"
            ],
            "issues_found": []
        }
        
        # 分析执行日志，寻找潜在问题
        execution_log = task_result.get('execution_log', [])
        for log in execution_log:
            if 'error' in log:
                reflection['issues_found'].append(f"{log.get('step', 'Unknown')} 执行失败: {log['error']}")
            elif 'result' in log and not log['result'].get('success', False):
                reflection['issues_found'].append(f"{log.get('step', 'Unknown')} 执行结果失败: {log['result'].get('message', '未知错误')}")
        
        # 如果发现问题，调整反思结果
        if reflection['issues_found']:
            reflection['confidence'] = 0.7
            reflection['summary'] = f"任务执行过程中发现 {len(reflection['issues_found'])} 个问题，需要改进。"
            return {
                "status": "uncertain",
                "reflection": reflection['summary'],
                "recommendation": "请向用户确认执行结果",
                "should_notify_user": True,
                "issues": reflection['issues_found'],
                "suggestions": reflection['suggestions']
            }
        
        return {
            "status": "success",
            "reflection": reflection['summary'],
            "optimizations": reflection['suggestions'],
            "should_notify_user": False,
            "should_retry": False
        }
    
    def apply_optimizations(self, task: str, suggestions: List[str]) -> str:
        """应用优化建议到任务中
        
        Args:
            task: 原始任务
            suggestions: 优化建议
            
        Returns:
            优化后的任务
        """
        # 简单的优化逻辑
        optimized_task = task
        for suggestion in suggestions:
            if "确认" in suggestion:
                optimized_task += " (请确认详细需求)"
            elif "优化顺序" in suggestion:
                optimized_task += " (优化执行顺序)"
        return optimized_task