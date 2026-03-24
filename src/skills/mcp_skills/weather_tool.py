from typing import Dict, Any
import logging
import os
from src.skills.mcp_skills.simple_local_weather_tool import simple_local_weather_tool

class WeatherTool:
    """天气调用工具 - 使用本地和风天气API获取天气信息"""
    
    def __init__(self, api_key: str):
        """初始化天气工具
        
        Args:
            api_key: API密钥
        """
        # 保存API密钥（实际使用的是环境变量中的密钥）
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        # 使用简单本地天气工具
        self.local_weather_tool = simple_local_weather_tool
    
    async def get_weather(self, location: str) -> str:
        """获取指定位置的天气信息
        
        Args:
            location: 位置信息
            
        Returns:
            格式化的天气信息
        """
        try:
            # 使用本地天气工具获取天气信息
            self.logger.info(f"正在获取{location}的天气信息")
            weather_info = await self.local_weather_tool.get_weather(location)
            
            self.logger.info(f"成功获取{location}的天气信息")
            return weather_info
            
        except Exception as e:
            self.logger.error(f"天气工具执行失败: {str(e)}")
            return f"获取天气信息失败: {str(e)}"

# 创建天气工具实例
# 注意：实际使用时需要从配置中获取API密钥
# weather_tool = WeatherTool(api_key="your-api-key")
