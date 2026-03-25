import json
import os
import time
import uuid
from typing import Dict, List, Optional

from tools.datetime_utils import format_local_datetime
from agent.langchain_memory_manager import LangChainMemoryManager

# 简化版日志配置
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndependentSessionManager:
    """独立会话管理器 - 负责对话的创建、管理和持久化"""
    
    def __init__(self):
        """初始化会话管理器"""
        # 会话存储目录 - 使用项目内部的数据目录
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "conversations")
        self.chats_file = os.path.join(self.base_dir, "chats.json")
        self.sessions_dir = os.path.join(self.base_dir, "sessions")
        
        # 确保目录存在
        self._ensure_directories()
        
        # 会话数据
        self.chats = self._load_chats()
        self.active_sessions = {}
    
    def _ensure_directories(self):
        """确保存储目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        # 确保日志目录存在
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    
    def _load_chats(self) -> Dict:
        """加载chats.json文件"""
        if not os.path.exists(self.chats_file):
            # 创建默认的chats.json文件
            default_chats = {
                "version": 1,
                "chats": []
            }
            self._save_chats(default_chats)
            return default_chats
        
        try:
            with open(self.chats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载chats.json失败: {e}")
            return {"version": 1, "chats": []}
    
    def _save_chats(self, chats: Dict):
        """保存chats.json文件"""
        try:
            with open(self.chats_file, "w", encoding="utf-8") as f:
                json.dump(chats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存chats.json失败: {e}")
    
    def create_session(self, name: str = "New Chat", user_id: str = "default") -> Dict:
        """创建新会话"""
        # 生成唯一的session_id
        session_id = str(time.time_ns())
        
        # 创建会话对象
        now = format_local_datetime('%Y-%m-%dT%H:%M:%S')
        chat = {
            "channel": "Yueyue",
            "created_at": now,
            "id": str(uuid.uuid4()),
            "meta": {},
            "name": name,
            "session_id": session_id,
            "updated_at": now,
            "user_id": user_id
        }
        
        # 添加到chats列表
        self.chats["chats"].append(chat)
        self._save_chats(self.chats)
        
        # 初始化会话上下文
        context = {
            "session_id": session_id,
            "conversation_history": [],
            "tool_states": {},
            "variables": {},
            "memory_manager": None
        }
        self.active_sessions[session_id] = context
        # 初始化记忆管理器
        self._init_memory_manager(session_id)
        # 保存会话上下文到文件
        self.save_session_context(session_id, context)
        
        return chat
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        for chat in self.chats["chats"]:
            if chat["session_id"] == session_id:
                return chat
        return None
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话"""
        return self.chats["chats"]
    
    def update_session_name(self, session_id: str, name: str) -> bool:
        """更新会话名称"""
        for chat in self.chats["chats"]:
            if chat["session_id"] == session_id:
                chat["name"] = name
                chat["updated_at"] = format_local_datetime('%Y-%m-%dT%H:%M:%S')
                self._save_chats(self.chats)
                return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        # 从chats列表中移除
        new_chats = [chat for chat in self.chats["chats"] if chat["session_id"] != session_id]
        if len(new_chats) < len(self.chats["chats"]):
            self.chats["chats"] = new_chats
            self._save_chats(self.chats)
            
            # 从活跃会话中移除
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # 删除会话文件
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                except Exception as e:
                    print(f"删除会话文件失败: {e}")
            
            return True
        return False
    
    def save_session_context(self, session_id: str, context: Dict):
        """保存会话上下文"""
        try:
            # 更新内存中的上下文
            self.active_sessions[session_id] = context
            
            # 确保目录存在
            os.makedirs(self.sessions_dir, exist_ok=True)
            
            # 创建一个可序列化的上下文副本，排除memory_manager
            serializable_context = {k: v for k, v in context.items() if k != "memory_manager"}
            
            # 保存到文件
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            # 先写入临时文件，再重命名，确保原子性
            temp_file = session_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(serializable_context, f, ensure_ascii=False, indent=2)
            
            # 原子性重命名
            os.replace(temp_file, session_file)
            
            logger.info(f"会话上下文保存成功，文件: {session_file}")
            return True
        except PermissionError as e:
            logger.error(f"保存会话上下文失败 - 权限错误: {e}")
            logger.error(f"请检查目录权限: {self.sessions_dir}")
            return False
        except IOError as e:
            logger.error(f"保存会话上下文失败 - IO错误: {e}")
            return False
        except TypeError as e:
            logger.error(f"保存会话上下文失败 - 类型错误（可能是JSON序列化问题）: {e}")
            # 尝试序列化部分数据，找出问题所在
            try:
                test_data = {k: v for k, v in serializable_context.items() if k != "conversation_history"}
                json.dumps(test_data)
                logger.error("问题可能出在conversation_history字段")
            except Exception as inner_e:
                logger.error(f"测试序列化失败: {inner_e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"保存会话上下文失败 - JSON解码错误: {e}")
            return False
        except Exception as e:
            logger.error(f"保存会话上下文失败 - 未知错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _init_memory_manager(self, session_id: str):
        """初始化记忆管理器"""
        context = self.active_sessions.get(session_id)
        if context:
            # 创建记忆管理器实例
            memory_manager = LangChainMemoryManager()
            # 尝试从文件加载记忆
            memory_file = os.path.join(self.sessions_dir, f"{session_id}_memory.json")
            memory_manager.load_from_file(memory_file)
            context["memory_manager"] = memory_manager
    
    def load_session_context(self, session_id: str) -> Dict:
        """加载会话上下文"""
        # 先检查内存中是否存在
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 从文件加载
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    context = json.load(f)
                    self.active_sessions[session_id] = context
                    # 初始化记忆管理器
                    self._init_memory_manager(session_id)
                    # 确保memory_manager被添加到上下文中
                    context["memory_manager"] = self.active_sessions[session_id].get("memory_manager")
                    return context
            except Exception as e:
                logger.error(f"加载会话上下文失败: {e}")
        
        # 返回默认上下文
        context = {
            "session_id": session_id,
            "conversation_history": [],
            "tool_states": {},
            "variables": {},
            "memory_manager": None
        }
        self.active_sessions[session_id] = context
        # 初始化记忆管理器
        self._init_memory_manager(session_id)
        # 确保memory_manager被添加到上下文中
        context["memory_manager"] = self.active_sessions[session_id].get("memory_manager")
        return context
    
    def update_conversation_history(self, session_id: str, user_message: str, assistant_message: str, process_info: Optional[List[Dict]] = None):
        """更新对话历史"""
        try:
            context = self.load_session_context(session_id)
            
            # 添加用户消息
            user_entry = {
                "user": user_message,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S'),
                "importance": self._calculate_message_importance(user_message, assistant_message)
            }
            context["conversation_history"].append(user_entry)
            
            # 添加过程信息
            if process_info:
                for process in process_info:
                    process_entry = {
                        "process": process,
                        "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
                    }
                    context["conversation_history"].append(process_entry)
            
            # 添加助手消息
            assistant_entry = {
                "assistant": assistant_message,
                "timestamp": format_local_datetime('%Y-%m-%dT%H:%M:%S')
            }
            context["conversation_history"].append(assistant_entry)
            
            # 优化对话历史长度限制，基于重要性保留消息
            if len(context["conversation_history"]) > 40:  # 20轮对话
                # 按照重要性排序，保留重要的消息
                important_messages = []
                recent_messages = context["conversation_history"][-20:]  # 保留最近的10轮对话
                
                # 从剩余消息中选择重要的消息
                for i in range(0, len(context["conversation_history"]) - 20, 2):
                    if i + 1 < len(context["conversation_history"]):
                        user_msg = context["conversation_history"][i]
                        importance = user_msg.get("importance", 5)
                        if importance >= 7:  # 保留重要性高的消息
                            important_messages.append(user_msg)
                            important_messages.append(context["conversation_history"][i + 1])
                
                # 合并重要消息和最近消息
                context["conversation_history"] = important_messages + recent_messages
                # 确保不超过限制
                if len(context["conversation_history"]) > 40:
                    context["conversation_history"] = context["conversation_history"][-40:]
            
            # 更新记忆管理器
            memory_manager = context.get("memory_manager")
            if memory_manager:
                memory_manager.add_message(user_message, assistant_message)
                # 保存记忆到文件
                memory_file = os.path.join(self.sessions_dir, f"{session_id}_memory.json")
                memory_manager.save_to_file(memory_file)
                logger.debug(f"记忆保存成功，文件: {memory_file}")
            
            # 保存上下文
            success = self.save_session_context(session_id, context)
            if success:
                logger.info(f"对话历史更新成功，会话ID: {session_id}")
            else:
                logger.error(f"对话历史更新失败，会话ID: {session_id}")
            return success
        except IOError as e:
            logger.error(f"更新对话历史失败 - IO错误: {e}")
            return False
        except TypeError as e:
            logger.error(f"更新对话历史失败 - 类型错误（可能是JSON序列化问题）: {e}")
            return False
        except Exception as e:
            logger.error(f"更新对话历史失败 - 未知错误: {e}")
            return False
    
    def _calculate_message_importance(self, user_message: str, assistant_message: str) -> int:
        """计算消息重要性
        
        Args:
            user_message: 用户消息
            assistant_message: 助手消息
            
        Returns:
            重要性级别（0-10）
        """
        importance = 5  # 默认重要性
        
        # 关键词权重
        important_keywords = {
            "名字": 8,
            "姓名": 8,
            "职业": 7,
            "工作": 7,
            "爱好": 6,
            "喜欢": 6,
            "讨厌": 6,
            "需求": 9,
            "要求": 9,
            "问题": 8,
            "困难": 8,
            "计划": 7,
            "目标": 7,
            "时间": 6,
            "日期": 6,
            "地点": 6,
            "地址": 6
        }
        
        # 分析用户消息
        for keyword, weight in important_keywords.items():
            if keyword in user_message:
                importance = max(importance, weight)
        
        # 分析助手消息
        for keyword, weight in important_keywords.items():
            if keyword in assistant_message:
                importance = max(importance, weight)
        
        # 消息长度也是重要性的一个指标
        total_length = len(user_message) + len(assistant_message)
        if total_length > 100:
            importance += 1
        if total_length > 200:
            importance += 1
        
        # 确保重要性在0-10之间
        return min(max(importance, 0), 10)
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        context = self.load_session_context(session_id)
        return context.get("conversation_history", [])
    
    def save_conversation_history(self, session_id: str, user_message: str, assistant_message: str, process_info: Optional[List[Dict]] = None) -> bool:
        """
        全新的对话历史保存函数
        用于将用户发送的前端信息和AI生成的新回答完整保存到历史聊天记录JSON文件中
        
        Args:
            session_id (str): 会话ID
            user_message (str): 用户输入文本
            assistant_message (str): AI响应内容
            process_info (Optional[List[Dict]]): 过程信息列表，包含思考、搜索、工具调用等过程
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            logger.info(f"开始保存对话历史，会话ID: {session_id}")
            
            # 加载现有会话上下文
            context = self.load_session_context(session_id)
            logger.debug(f"加载会话上下文成功，当前对话历史长度: {len(context.get('conversation_history', []))}")
            
            # 检查是否存在相同的消息组合，避免重复添加
            conversation_history = context.get('conversation_history', [])
            has_duplicate = False
            
            # 检查最近的对话，避免重复
            for i in range(len(conversation_history) - 2, -1, -2):
                if i >= 0 and i + 1 < len(conversation_history):
                    user_entry = conversation_history[i]
                    assistant_entry = conversation_history[i + 1]
                    if user_entry.get('user') == user_message and assistant_entry.get('assistant') == assistant_message:
                        logger.info(f"发现重复的消息组合，跳过保存: {user_message[:50]}...")
                        has_duplicate = True
                        break
            
            if has_duplicate:
                return True
            
            # 获取当前时间戳
            timestamp = format_local_datetime('%Y-%m-%dT%H:%M:%S')
            
            # 计算消息重要性
            importance = self._calculate_message_importance(user_message, assistant_message)
            
            # 添加用户消息
            user_entry = {
                "user": user_message,
                "timestamp": timestamp,
                "importance": importance
            }
            context["conversation_history"].append(user_entry)
            logger.debug(f"添加用户消息成功: {user_message[:50]}...")
            
            # 添加过程信息
            if process_info:
                for process in process_info:
                    process_entry = {
                        "process": process,
                        "timestamp": timestamp
                    }
                    context["conversation_history"].append(process_entry)
                logger.debug(f"添加过程信息成功，共{len(process_info)}条")
            
            # 添加助手消息
            assistant_entry = {
                "assistant": assistant_message,
                "timestamp": timestamp
            }
            context["conversation_history"].append(assistant_entry)
            logger.debug(f"添加助手消息成功: {assistant_message[:50]}...")
            
            # 优化对话历史长度限制，基于重要性保留消息
            if len(context["conversation_history"]) > 40:  # 20轮对话
                # 按照重要性排序，保留重要的消息
                important_messages = []
                recent_messages = context["conversation_history"][-20:]  # 保留最近的10轮对话
                
                # 从剩余消息中选择重要的消息
                for i in range(0, len(context["conversation_history"]) - 20, 2):
                    if i + 1 < len(context["conversation_history"]):
                        user_msg = context["conversation_history"][i]
                        importance = user_msg.get("importance", 5)
                        if importance >= 7:  # 保留重要性高的消息
                            important_messages.append(user_msg)
                            important_messages.append(context["conversation_history"][i + 1])
                
                # 合并重要消息和最近消息
                context["conversation_history"] = important_messages + recent_messages
                # 确保不超过限制
                if len(context["conversation_history"]) > 40:
                    context["conversation_history"] = context["conversation_history"][-40:]
                logger.debug("对话历史长度超过限制，已基于重要性截断")
            
            # 确保目录存在
            os.makedirs(self.sessions_dir, exist_ok=True)
            logger.debug(f"确保目录存在: {self.sessions_dir}")
            
            # 更新记忆管理器
            memory_manager = context.get("memory_manager")
            if memory_manager:
                memory_manager.add_message(user_message, assistant_message)
                # 保存记忆到文件
                memory_file = os.path.join(self.sessions_dir, f"{session_id}_memory.json")
                memory_manager.save_to_file(memory_file)
                logger.debug(f"记忆保存成功，文件: {memory_file}")
            
            # 创建一个可序列化的上下文副本，排除memory_manager
            serializable_context = {k: v for k, v in context.items() if k != "memory_manager"}
            
            # 保存到文件
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            logger.debug(f"准备保存到文件: {session_file}")
            
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(serializable_context, f, ensure_ascii=False, indent=2)
            
            logger.info(f"对话历史保存成功，文件: {session_file}")
            return True
        except PermissionError as e:
            logger.error(f"保存对话历史失败 - 权限错误: {e}")
            logger.error(f"请检查目录权限: {self.sessions_dir}")
            return False
        except IOError as e:
            logger.error(f"保存对话历史失败 - IO错误: {e}")
            return False
        except TypeError as e:
            logger.error(f"保存对话历史失败 - 类型错误（可能是JSON序列化问题）: {e}")
            logger.error(f"用户消息: {user_message[:100]}...")
            logger.error(f"助手消息: {assistant_message[:100]}...")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"保存对话历史失败 - JSON解码错误: {e}")
            return False
        except Exception as e:
            logger.error(f"保存对话历史失败 - 未知错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def clear_conversation_history(self, session_id: str):
        """清空对话历史"""
        context = self.load_session_context(session_id)
        context["conversation_history"] = []
        self.save_session_context(session_id, context)
    
    def backup_session(self, session_id: str) -> bool:
        """备份会话状态"""
        try:
            # 加载会话上下文
            context = self.load_session_context(session_id)
            
            # 确保备份目录存在
            backup_dir = os.path.join(self.base_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = format_local_datetime('%Y-%m-%d_%H-%M-%S')
            backup_file = os.path.join(backup_dir, f"{session_id}_{timestamp}.json")
            
            # 创建可序列化的上下文副本
            serializable_context = {k: v for k, v in context.items() if k != "memory_manager"}
            
            # 保存备份
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(serializable_context, f, ensure_ascii=False, indent=2)
            
            # 备份记忆
            memory_manager = context.get("memory_manager")
            if memory_manager:
                memory_backup_file = os.path.join(backup_dir, f"{session_id}_{timestamp}_memory.json")
                memory_manager.save_to_file(memory_backup_file)
            
            logger.info(f"会话备份成功，文件: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"会话备份失败: {e}")
            return False
    
    def restore_session(self, session_id: str, backup_file: str) -> bool:
        """从备份恢复会话状态"""
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 加载备份文件
            with open(backup_file, "r", encoding="utf-8") as f:
                context = json.load(f)
            
            # 更新会话ID
            context["session_id"] = session_id
            
            # 保存上下文
            success = self.save_session_context(session_id, context)
            if not success:
                logger.error("恢复会话上下文失败")
                return False
            
            # 恢复记忆
            memory_backup_file = backup_file.replace(".json", "_memory.json")
            if os.path.exists(memory_backup_file):
                context = self.load_session_context(session_id)
                memory_manager = context.get("memory_manager")
                if memory_manager:
                    memory_manager.load_from_file(memory_backup_file)
                    # 保存记忆
                    memory_file = os.path.join(self.sessions_dir, f"{session_id}_memory.json")
                    memory_manager.save_to_file(memory_file)
            
            logger.info(f"会话恢复成功，文件: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"会话恢复失败: {e}")
            return False
    
    def list_session_backups(self, session_id: str) -> List[str]:
        """列出会话的所有备份"""
        try:
            backup_dir = os.path.join(self.base_dir, "backups")
            if not os.path.exists(backup_dir):
                return []
            
            backups = []
            for filename in os.listdir(backup_dir):
                if filename.startswith(f"{session_id}_") and filename.endswith(".json") and "_memory" not in filename:
                    backups.append(os.path.join(backup_dir, filename))
            
            # 按时间排序，最新的在前
            backups.sort(reverse=True)
            return backups
        except Exception as e:
            logger.error(f"列出会话备份失败: {e}")
            return []
