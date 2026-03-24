from typing import Dict, Optional, Any, AsyncGenerator
from core.meta_router import MetaCognitionRouter
from core.resource_registry import ResourceRegistry
import asyncio
import logging

class StreamingDecisionEngine:
    """流式决策引擎 - 将智能决策系统与流式处理机制相结合"""
    
    def __init__(self, llm_client, registry: ResourceRegistry):
        """初始化流式决策引擎
        
        Args:
            llm_client: LLM客户端实例
            registry: 资源注册表实例
        """
        self.llm_client = llm_client
        self.registry = registry
        self.meta_router = MetaCognitionRouter(llm_client, registry)
        self.logger = logging.getLogger(__name__)
        self.rules = []  # 决策规则列表
        self.rules_lock = asyncio.Lock()  # 规则锁，用于并发安全
        self.cache = {}  # 缓存，用于存储决策结果
        self.cache_lock = asyncio.Lock()  # 缓存锁，用于并发安全
        self.batch_size = 10  # 批处理大小
        self.batch_data = []  # 批处理数据
        self.batch_lock = asyncio.Lock()  # 批处理锁，用于并发安全
    
    async def process_stream(self, data_stream: AsyncGenerator[Dict[str, Any], None]) -> AsyncGenerator[Dict[str, Any], None]:
        """处理流式数据
        
        Args:
            data_stream: 流式数据生成器
            
        Returns:
            决策结果的流式生成器
        """
        async for data in data_stream:
            try:
                # 检查缓存
                user_input = data.get("input", "")
                cache_key = hash(user_input)
                
                async with self.cache_lock:
                    if cache_key in self.cache:
                        self.logger.info(f"缓存命中: {user_input}")
                        yield self.cache[cache_key]
                        continue
                
                # 批处理
                async with self.batch_lock:
                    self.batch_data.append(data)
                    if len(self.batch_data) >= self.batch_size:
                        # 处理批数据
                        batch_results = await self._process_batch(self.batch_data)
                        for result in batch_results:
                            yield result
                        # 清空批数据
                        self.batch_data.clear()
                    else:
                        # 处理单个数据项
                        result = await self._process_single_data(data)
                        # 更新缓存
                        async with self.cache_lock:
                            self.cache[cache_key] = result
                        yield result
            except Exception as e:
                # 处理异常
                self.logger.error(f"处理流式数据时出错: {str(e)}")
                yield {
                    "type": "error",
                    "content": f"处理数据时出错: {str(e)}"
                }
        
        # 处理剩余的批数据
        async with self.batch_lock:
            if self.batch_data:
                batch_results = await self._process_batch(self.batch_data)
                for result in batch_results:
                    yield result
                self.batch_data.clear()
    
    async def _process_single_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个数据项
        
        Args:
            data: 单个数据项
            
        Returns:
            决策结果
        """
        # 提取用户输入
        user_input = data.get("input", "")
        
        # 记录决策过程
        decision_process = {
            "input": user_input,
            "steps": []
        }
        
        # 应用规则引擎
        rule_result = await self._apply_rules(user_input)
        if rule_result:
            decision_process["steps"].append({
                "type": "rule_engine",
                "result": "规则匹配成功",
                "output": rule_result
            })
            
            return {
                "type": "rule_based",
                "content": rule_result,
                "input": user_input,
                "decision_process": decision_process
            }
        
        # 使用元认知路由器进行决策
        decision_process["steps"].append({
            "type": "meta_router",
            "result": "开始智能决策"
        })
        
        decision_result = await self.meta_router.decide(user_input)
        
        decision_process["steps"].append({
            "type": "meta_router",
            "result": "决策完成",
            "decision": decision_result
        })
        
        # 执行决策
        execution_result = await self.meta_router.execute_decision(decision_result, user_input)
        
        decision_process["steps"].append({
            "type": "execution",
            "result": "执行完成",
            "output": execution_result
        })
        
        # 构建返回结果
        return {
            "type": "decision_based",
            "content": execution_result,
            "decision": decision_result,
            "input": user_input,
            "decision_process": decision_process
        }
    
    async def _apply_rules(self, user_input: str) -> Optional[str]:
        """应用规则引擎
        
        Args:
            user_input: 用户输入
            
        Returns:
            规则匹配结果，如果没有匹配的规则则返回None
        """
        async with self.rules_lock:
            for rule in sorted(self.rules, key=lambda r: r.get("priority", 0), reverse=True):
                condition = rule.get("condition")
                action = rule.get("action")
                
                if condition(user_input):
                    self.logger.info(f"规则匹配成功: {rule.get('name', 'unnamed')}")
                    return action(user_input)
        return None
    
    async def add_rule(self, name: str, condition: callable, action: callable, priority: int = 0):
        """添加决策规则
        
        Args:
            name: 规则名称
            condition: 条件函数，接收用户输入，返回布尔值
            action: 动作函数，接收用户输入，返回决策结果
            priority: 优先级，数值越大优先级越高
        """
        async with self.rules_lock:
            self.rules.append({
                "name": name,
                "condition": condition,
                "action": action,
                "priority": priority
            })
            self.logger.info(f"添加规则: {name}, 优先级: {priority}")
    
    async def remove_rule(self, name: str):
        """移除决策规则
        
        Args:
            name: 规则名称
        """
        async with self.rules_lock:
            self.rules = [rule for rule in self.rules if rule.get("name") != name]
            self.logger.info(f"移除规则: {name}")
    
    async def clear_rules(self):
        """清空所有决策规则"""
        async with self.rules_lock:
            self.rules.clear()
            self.logger.info("清空所有规则")
    
    async def _process_batch(self, batch_data: list) -> list:
        """处理批数据
        
        Args:
            batch_data: 批数据列表
            
        Returns:
            决策结果列表
        """
        results = []
        
        # 并发处理批数据
        tasks = []
        for data in batch_data:
            tasks.append(self._process_single_data(data))
        
        # 等待所有任务完成
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                # 处理异常
                self.logger.error(f"处理批数据时出错: {str(result)}")
                results.append({
                    "type": "error",
                    "content": f"处理数据时出错: {str(result)}",
                    "input": batch_data[i].get("input", "")
                })
            else:
                # 更新缓存
                user_input = batch_data[i].get("input", "")
                cache_key = hash(user_input)
                async with self.cache_lock:
                    self.cache[cache_key] = result
                results.append(result)
        
        return results
    
    async def get_rules(self) -> list:
        """获取所有决策规则
        
        Returns:
            规则列表
        """
        async with self.rules_lock:
            return self.rules.copy()
    
    async def clear_cache(self):
        """清空缓存"""
        async with self.cache_lock:
            self.cache.clear()
            self.logger.info("清空缓存")
    
    async def set_batch_size(self, batch_size: int):
        """设置批处理大小
        
        Args:
            batch_size: 批处理大小
        """
        self.batch_size = batch_size
        self.logger.info(f"设置批处理大小: {batch_size}")
