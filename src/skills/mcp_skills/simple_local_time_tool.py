from typing import Dict, Any
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

class SimpleLocalTimeTool:
    """简单本地时间工具 - 使用Python内置datetime模块获取时间信息"""
    
    def __init__(self):
        """初始化简单本地时间工具"""
        self.logger = logging.getLogger(__name__)
    
    async def get_time(self, timezone: str = "Asia/Shanghai") -> str:
        """获取当前时间和日期信息
        
        Args:
            timezone: 时区，默认为Asia/Shanghai
            
        Returns:
            格式化的时间信息
        """
        try:
            # 获取当前时间
            self.logger.info(f"正在获取当前时间信息 (时区: {timezone})")
            
            # 获取指定时区的当前时间
            try:
                tz = ZoneInfo(timezone)
                current_time = datetime.now(tz)
            except Exception as e:
                self.logger.error(f"无效的时区: {timezone}, 使用本地时区")
                current_time = datetime.now()
                timezone = "本地时区"
            
            # 格式化时间信息
            datetime_str = current_time.isoformat(timespec="seconds")
            day_of_week = current_time.strftime("%A")
            
            # 检查是否是夏令时
            is_dst = False
            try:
                is_dst = bool(current_time.dst())
            except Exception:
                pass
            
            # 构建返回信息
            time_info = f"当前时间（{timezone}）: {datetime_str}，{day_of_week}，{'夏令时' if is_dst else '标准时间'}"
            
            self.logger.info(f"成功获取当前时间信息: {time_info}")
            return time_info
            
        except Exception as e:
            self.logger.error(f"时间工具执行失败: {str(e)}")
            return f"获取时间信息失败: {str(e)}"

# 创建简单本地时间工具实例
simple_local_time_tool = SimpleLocalTimeTool()
