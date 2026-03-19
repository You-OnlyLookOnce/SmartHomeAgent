import os
import json
import logging
from typing import Dict, Optional, List, Any
from src.ai.qiniu_llm import QiniuLLM

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReasoningEngine:
    """推理引擎 - 负责分析任务并制定执行计划"""
    
    def __init__(self):
        """初始化推理引擎"""
        self.llm = QiniuLLM(model_type="decision")
        self.tools = self._load_tools()
    
    def _load_tools(self) -> List[Dict[str, Any]]:
        """加载可用工具列表"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "browser_use",
                    "description": "控制浏览器，用于打开网页、抓取数据、截图等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "操作类型，如 open, screenshot, extract"
                            },
                            "url": {
                                "type": "string",
                                "description": "网页URL"
                            },
                            "params": {
                                "type": "object",
                                "description": "其他参数"
                            }
                        },
                        "required": ["action", "url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell_command",
                    "description": "执行命令行指令，用于运行脚本、检查磁盘空间、配置任务等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的命令"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "命令执行超时时间（秒）"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文本文件，用于打开记忆文件、查看代码等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "写入/创建文本文件，用于保存报告、更新配置文件等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "content": {
                                "type": "string",
                                "description": "文件内容"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "memory_search",
                    "description": "语义搜索记忆，用于查找历史信息、恢复上下文等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大返回结果数"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        return tools
    
    async def analyze_task(self, task: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """分析任务并制定执行计划
        
        Args:
            task: 用户的任务描述
            context: 对话上下文
            
        Returns:
            分析结果，包含执行计划和工具调用建议
        """
        logger.info(f"Analyzing task: {task}")
        
        # 构建提示词
        prompt = ("你是一个智能推理引擎，负责分析用户任务并制定执行计划。\n\n" 
                 "任务：" + task + "\n\n" 
                 "请按照以下步骤分析：\n" 
                 "1. 理解任务的具体需求\n" 
                 "2. 分析完成任务需要的步骤\n" 
                 "3. 确定是否需要使用工具\n" 
                 "4. 如果需要工具，选择合适的工具并说明使用理由\n" 
                 "5. 制定详细的执行计划\n\n" 
                 "请以JSON格式输出分析结果：\n" 
                 "{\n" 
                 "    \"task_analysis\": \"任务分析\",\n" 
                 "    \"execution_plan\": [\"步骤1\", \"步骤2\", ...],\n" 
                 "    \"tool_usage\": [\n" 
                 "        {\n" 
                 "            \"tool_name\": \"工具名称\",\n" 
                 "            \"reason\": \"使用理由\",\n" 
                 "            \"parameters\": {\"参数1\": \"值1\", ...}\n" 
                 "        }\n" 
                 "    ],\n" 
                 "    \"confidence\": 0.0-1.0\n" 
                 "}\n")
        
        # 调用LLM进行任务分析
        result = await self.llm.generate_text(prompt, context)
        
        if not result.get("success"):
            logger.error(f"Failed to analyze task: {result.get('error')}")
            # 返回默认分析结果
            return {
                "task_analysis": "无法分析任务",
                "execution_plan": ["直接回答用户"],
                "tool_usage": [],
                "confidence": 0.5
            }
        
        # 解析LLM返回的结果
        try:
            analysis_result = json.loads(result.get("text", "{}"))
            logger.info(f"Task analysis result: {analysis_result}")
            return analysis_result
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            # 返回默认分析结果
            return {
                "task_analysis": result.get("text", "无法分析任务"),
                "execution_plan": ["直接回答用户"],
                "tool_usage": [],
                "confidence": 0.5
            }
    
    async def make_decision(self, task: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """做出决策，决定如何处理任务
        
        Args:
            task: 用户的任务描述
            context: 对话上下文
            
        Returns:
            决策结果，包含执行计划和工具调用
        """
        logger.info(f"Making decision for task: {task}")
        
        # 分析任务
        analysis_result = await self.analyze_task(task, context)
        
        # 构建决策结果
        decision_result = {
            "task": task,
            "analysis": analysis_result,
            "action": "execute_plan",
            "timestamp": os.path.getmtime(__file__)
        }
        
        # 如果需要工具调用，生成工具调用请求
        if analysis_result.get("tool_usage"):
            tool_calls = []
            for tool_info in analysis_result["tool_usage"]:
                tool_calls.append({
                    "id": f"tool_{len(tool_calls) + 1}",
                    "type": "function",
                    "function": {
                        "name": tool_info["tool_name"],
                        "arguments": json.dumps(tool_info.get("parameters", {}), ensure_ascii=False)
                    }
                })
            decision_result["tool_calls"] = tool_calls
        
        logger.info(f"Decision result: {decision_result}")
        return decision_result
    
    async def execute_plan(self, plan: List[str], tool_usage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行计划
        
        Args:
            plan: 执行计划步骤
            tool_usage: 工具使用信息
            
        Returns:
            执行结果
        """
        logger.info(f"Executing plan: {plan}")
        logger.info(f"Tool usage: {tool_usage}")
        
        # 这里需要与工具调用系统集成
        # 暂时返回执行状态
        return {
            "success": True,
            "message": f"执行计划完成，共 {len(plan)} 个步骤",
            "steps": plan,
            "tool_usage": tool_usage
        }
