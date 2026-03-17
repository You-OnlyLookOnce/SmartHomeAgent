from src.agent.agent_base import AgentBase
from src.agent.model_router import ModelRouter
import asyncio

async def test_agent_architecture():
    """测试Agent架构"""
    print("=== 测试核心架构 ===")
    
    # 测试Agent基类
    agent = AgentBase("test_agent", "智能家居助手")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Agent Role: {agent.role}")
    print(f"Capabilities: {agent.capabilities}")
    print(f"Permissions: {agent.permissions}")
    print(f"Knowledge Base: {agent.knowledge_base}")
    print(f"Context: {agent.context}")
    print(f"Session Summary: {agent.session_summary}")
    print(f"Temp Variables: {agent.temp_variables}")
    print(f"Emotion State: {agent.emotion_state}")
    print(f"Skills: {agent.skills}")
    print(f"Execution Log: {agent.execution_log}")
    print(f"Output Buffer: {agent.output_buffer}")
    
    # 测试模型路由器
    router = ModelRouter()
    
    # 测试普通任务
    normal_task = {"type": "简单任务", "content": "打开客厅灯"}
    normal_model = await router.route(normal_task)
    print(f"\n普通任务模型: {normal_model['name']}")
    
    # 测试复杂任务
    complex_task = {"type": "复杂推理", "content": "分析家庭能耗模式"}
    complex_model = await router.route(complex_task)
    print(f"复杂任务模型: {complex_model['name']}")
    
    # 测试模型调用
    response = await router.call("你好，我是智能家居助手", normal_task)
    print(f"\n模型响应: {response}")
    
    print("\n=== 核心架构测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_agent_architecture())
