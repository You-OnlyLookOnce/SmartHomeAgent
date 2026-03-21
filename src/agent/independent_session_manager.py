import json
import os
import time
import uuid
from typing import Dict, List, Optional

from src.tools.datetime_utils import format_local_datetime

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
            "variables": {}
        }
        self.active_sessions[session_id] = context
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
            
            # 保存到文件
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
            logger.info(f"会话上下文保存成功，文件: {session_file}")
            return True
        except IOError as e:
            logger.error(f"保存会话上下文失败 - IO错误: {e}")
            return False
        except TypeError as e:
            logger.error(f"保存会话上下文失败 - 类型错误（可能是JSON序列化问题）: {e}")
            return False
        except Exception as e:
            logger.error(f"保存会话上下文失败 - 未知错误: {e}")
            return False
    
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
                    return context
            except Exception as e:
                print(f"加载会话上下文失败: {e}")
        
        # 返回默认上下文
        return {
            "session_id": session_id,
            "conversation_history": [],
            "tool_states": {},
            "variables": {}
        }
    
    def update_conversation_history(self, session_id: str, user_message: str, assistant_message: str):
        """更新对话历史"""
        try:
            context = self.load_session_context(session_id)
            
            # 添加用户消息
            context["conversation_history"].append({"user": user_message})
            # 添加助手消息
            context["conversation_history"].append({"assistant": assistant_message})
            
            # 限制对话历史长度
            if len(context["conversation_history"]) > 40:  # 20轮对话
                # 保留最近的20轮对话
                context["conversation_history"] = context["conversation_history"][-40:]
            
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
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        context = self.load_session_context(session_id)
        return context.get("conversation_history", [])
    
    def save_conversation_history(self, session_id: str, user_message: str, assistant_message: str) -> bool:
        """
        全新的对话历史保存函数
        用于将用户发送的前端信息和AI生成的新回答完整保存到历史聊天记录JSON文件中
        
        Args:
            session_id (str): 会话ID
            user_message (str): 用户输入文本
            assistant_message (str): AI响应内容
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            logger.info(f"开始保存对话历史，会话ID: {session_id}")
            
            # 加载现有会话上下文
            context = self.load_session_context(session_id)
            logger.debug(f"加载会话上下文成功，当前对话历史长度: {len(context.get('conversation_history', []))}")
            
            # 获取当前时间戳
            timestamp = format_local_datetime('%Y-%m-%dT%H:%M:%S')
            
            # 添加用户消息
            user_entry = {
                "user": user_message,
                "timestamp": timestamp
            }
            context["conversation_history"].append(user_entry)
            logger.debug(f"添加用户消息成功: {user_message[:50]}...")
            
            # 添加助手消息
            assistant_entry = {
                "assistant": assistant_message,
                "timestamp": timestamp
            }
            context["conversation_history"].append(assistant_entry)
            logger.debug(f"添加助手消息成功: {assistant_message[:50]}...")
            
            # 限制对话历史长度，保留最近的20轮对话（40条消息）
            if len(context["conversation_history"]) > 40:
                context["conversation_history"] = context["conversation_history"][-40:]
                logger.debug("对话历史长度超过限制，已截断")
            
            # 确保目录存在
            os.makedirs(self.sessions_dir, exist_ok=True)
            logger.debug(f"确保目录存在: {self.sessions_dir}")
            
            # 保存到文件
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            logger.debug(f"准备保存到文件: {session_file}")
            
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
            
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
