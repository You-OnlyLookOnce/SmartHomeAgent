#!/usr/bin/env python3
"""
API调用示例

本文件展示了如何使用Home-AI-Agent系统的API
"""

import asyncio
from src.ai.qiniu_llm import QiniuLLM
from src.agent.reasoning_engine import ReasoningEngine
from src.tools.tool_manager import ToolManager
from src.agent.memory_manager import MemoryManager
from src.communication.communication_manager import communication_manager, Message

async def example_basic_chat():
    """基本聊天示例"""
    print("=== 基本聊天示例 ===")
    
    # 初始化LLM
    llm = QiniuLLM()
    
    # 发送简单的聊天请求
    prompt = "你好，我是一个开发者，正在测试智能体系统。"
    result = await llm.generate_text(prompt)
    
    print(f"用户: {prompt}")
    if result.get("success"):
        print(f"助手: {result.get('text')}")
    else:
        print(f"错误: {result.get('error')}")

async def example_reasoning():
    """推理引擎示例"""
    print("\n=== 推理引擎示例 ===")
    
    # 初始化推理引擎
    engine = ReasoningEngine()
    
    # 分析任务
    task = "打开百度首页并搜索Python教程"
    analysis = await engine.analyze_task(task)
    print(f"任务分析: {analysis}")
    
    # 制定决策
    decision = await engine.make_decision(task)
    print(f"决策结果: {decision}")

async def example_tool_usage():
    """工具使用示例"""
    print("\n=== 工具使用示例 ===")
    
    # 初始化工具管理器
    tool_manager = ToolManager()
    
    # 执行命令行工具
    result = await tool_manager.execute_tool(
        "execute_shell_command",
        command="dir",
        timeout=10
    )
    print(f"执行命令结果: {result}")
    
    # 执行时间查询工具
    result = await tool_manager.execute_tool("get_time")
    print(f"当前时间: {result}")

async def example_memory_management():
    """记忆管理示例"""
    print("\n=== 记忆管理示例 ===")
    
    # 初始化记忆管理器
    memory_manager = MemoryManager()
    
    # 更新记忆
    memory_manager.update_memory({"user": "我在学习Python", "assistant": "Python是一种非常流行的编程语言，用途广泛。"})
    
    # 搜索记忆
    results = memory_manager.memory_search("学习")
    print(f"记忆搜索结果: {results}")

async def example_communication():
    """通信示例"""
    print("\n=== 通信示例 ===")
    
    # 定义消息处理回调
    def handle_message(message):
        print(f"收到消息: {message}")
    
    # 订阅消息
    communication_manager.subscribe("test_module", handle_message)
    
    # 发送消息
    message = Message.create_message("test", "sender1", "test_module", {"key": "value"})
    await communication_manager.send_message(message)
    
    # 启动消息处理
    task = asyncio.create_task(communication_manager.process_messages())
    
    # 等待消息处理
    await asyncio.sleep(1)
    
    # 取消任务
    task.cancel()

async def main():
    """主函数"""
    await example_basic_chat()
    await example_reasoning()
    await example_tool_usage()
    await example_memory_management()
    await example_communication()

if __name__ == "__main__":
    asyncio.run(main())
