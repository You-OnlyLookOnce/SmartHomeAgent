"""日期时间工具模块

提供统一的日期时间处理功能，包括：
- 本地日期时间获取
- 日期时间格式化
- 时区处理
- 日期时间解析
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union

class DatetimeUtils:
    """日期时间工具类"""
    
    @staticmethod
    def get_local_datetime() -> datetime:
        """获取本地日期时间
        
        Returns:
            datetime: 本地日期时间对象
        """
        return datetime.now()
    
    @staticmethod
    def get_utc_datetime() -> datetime:
        """获取UTC日期时间
        
        Returns:
            datetime: UTC日期时间对象
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化日期时间
        
        Args:
            dt: 日期时间对象
            format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        return dt.strftime(format_str)
    
    @staticmethod
    def format_local_datetime(format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化当前本地日期时间
        
        Args:
            format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        return DatetimeUtils.format_datetime(DatetimeUtils.get_local_datetime(), format_str)
    
    @staticmethod
    def parse_datetime(datetime_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
        """解析日期时间字符串
        
        Args:
            datetime_str: 日期时间字符串
            format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            Optional[datetime]: 解析后的日期时间对象，解析失败返回None
        """
        try:
            return datetime.strptime(datetime_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def get_date_string(format_str: str = '%Y-%m-%d') -> str:
        """获取当前日期字符串
        
        Args:
            format_str: 格式化字符串，默认 '%Y-%m-%d'
            
        Returns:
            str: 格式化后的日期字符串
        """
        return DatetimeUtils.format_local_datetime(format_str)
    
    @staticmethod
    def get_time_string(format_str: str = '%H:%M:%S') -> str:
        """获取当前时间字符串
        
        Args:
            format_str: 格式化字符串，默认 '%H:%M:%S'
            
        Returns:
            str: 格式化后的时间字符串
        """
        return DatetimeUtils.format_local_datetime(format_str)
    
    @staticmethod
    def get_timestamp() -> float:
        """获取当前时间戳
        
        Returns:
            float: 时间戳
        """
        return DatetimeUtils.get_local_datetime().timestamp()
    
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化时间戳
        
        Args:
            timestamp: 时间戳
            format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        return datetime.fromtimestamp(timestamp).strftime(format_str)
    
    @staticmethod
    def is_valid_datetime(datetime_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> bool:
        """验证日期时间字符串是否有效
        
        Args:
            datetime_str: 日期时间字符串
            format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            bool: 是否有效
        """
        return DatetimeUtils.parse_datetime(datetime_str, format_str) is not None

# 导出常用函数
get_local_datetime = DatetimeUtils.get_local_datetime
get_utc_datetime = DatetimeUtils.get_utc_datetime
format_datetime = DatetimeUtils.format_datetime
format_local_datetime = DatetimeUtils.format_local_datetime
parse_datetime = DatetimeUtils.parse_datetime
get_date_string = DatetimeUtils.get_date_string
get_time_string = DatetimeUtils.get_time_string
get_timestamp = DatetimeUtils.get_timestamp
format_timestamp = DatetimeUtils.format_timestamp
is_valid_datetime = DatetimeUtils.is_valid_datetime
