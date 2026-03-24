from typing import Dict, Any
import logging
import os
import httpx
from datetime import datetime

class SimpleLocalWeatherTool:
    """简单本地天气工具 - 使用和风天气API获取天气信息"""
    
    def __init__(self):
        """初始化简单本地天气工具"""
        self.api_key = os.getenv("HEFENG_WEATHER_API_KEY", "")
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://devapi.qweather.com/v7"
    
    async def get_weather(self, location: str) -> str:
        """获取指定位置的天气信息
        
        Args:
            location: 位置信息
            
        Returns:
            格式化的天气信息
        """
        try:
            # 检查API密钥
            if not self.api_key:
                return "获取天气信息失败: 未配置和风天气API密钥"
            
            # 获取位置ID
            self.logger.info(f"正在获取{location}的天气信息")
            location_id = await self._get_location_id(location)
            if not location_id:
                return f"获取天气信息失败: 无法找到位置 {location}"
            
            # 获取实时天气
            realtime_weather = await self._get_realtime_weather(location_id)
            if not realtime_weather:
                return f"获取天气信息失败: 无法获取{location}的实时天气"
            
            # 获取天气预报
            forecast_weather = await self._get_forecast_weather(location_id)
            
            # 格式化天气信息
            weather_info = self._format_weather_info(location, realtime_weather, forecast_weather)
            
            self.logger.info(f"成功获取{location}的天气信息")
            return weather_info
            
        except Exception as e:
            self.logger.error(f"天气工具执行失败: {str(e)}")
            return f"获取天气信息失败: {str(e)}"
    
    async def _get_location_id(self, location: str) -> str:
        """获取位置ID
        
        Args:
            location: 位置名称
            
        Returns:
            位置ID
        """
        try:
            url = f"{self.base_url}/city/lookup"
            params = {
                "key": self.api_key,
                "location": location
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                data = response.json()
                
                if data.get("code") == "200" and data.get("location"):
                    return data["location"][0]["id"]
                return None
        except Exception as e:
            self.logger.error(f"获取位置ID失败: {str(e)}")
            return None
    
    async def _get_realtime_weather(self, location_id: str) -> Dict[str, Any]:
        """获取实时天气
        
        Args:
            location_id: 位置ID
            
        Returns:
            实时天气数据
        """
        try:
            url = f"{self.base_url}/weather/now"
            params = {
                "key": self.api_key,
                "location": location_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                data = response.json()
                
                if data.get("code") == "200" and data.get("now"):
                    return data["now"]
                return None
        except Exception as e:
            self.logger.error(f"获取实时天气失败: {str(e)}")
            return None
    
    async def _get_forecast_weather(self, location_id: str) -> Dict[str, Any]:
        """获取天气预报
        
        Args:
            location_id: 位置ID
            
        Returns:
            天气预报数据
        """
        try:
            url = f"{self.base_url}/weather/7d"
            params = {
                "key": self.api_key,
                "location": location_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                data = response.json()
                
                if data.get("code") == "200" and data.get("daily"):
                    return data["daily"]
                return None
        except Exception as e:
            self.logger.error(f"获取天气预报失败: {str(e)}")
            return None
    
    def _format_weather_info(self, location: str, realtime: Dict[str, Any], forecast: Dict[str, Any]) -> str:
        """格式化天气信息
        
        Args:
            location: 位置名称
            realtime: 实时天气数据
            forecast: 天气预报数据
            
        Returns:
            格式化的天气信息
        """
        try:
            # 构建实时天气信息
            realtime_info = f"{location}的实时天气：\n"
            realtime_info += f"- 天气状况: {realtime.get('text', '未知')}\n"
            realtime_info += f"- 温度: {realtime.get('temp', '未知')}°C\n"
            realtime_info += f"- 体感温度: {realtime.get('feelsLike', '未知')}°C\n"
            realtime_info += f"- 湿度: {realtime.get('humidity', '未知')}%\n"
            realtime_info += f"- 风力: {realtime.get('windDir', '未知')} {realtime.get('windScale', '未知')}级\n"
            realtime_info += f"- 气压: {realtime.get('pressure', '未知')}hPa\n"
            realtime_info += f"- 能见度: {realtime.get('vis', '未知')}km\n"
            realtime_info += f"- 更新时间: {datetime.fromtimestamp(int(realtime.get('obsTime', '0'))).strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 构建天气预报信息
            if forecast:
                realtime_info += "\n7天天气预报：\n"
                for day in forecast[:7]:
                    date = day.get('fxDate', '未知')
                    textDay = day.get('textDay', '未知')
                    textNight = day.get('textNight', '未知')
                    tempMax = day.get('tempMax', '未知')
                    tempMin = day.get('tempMin', '未知')
                    windDirDay = day.get('windDirDay', '未知')
                    windScaleDay = day.get('windScaleDay', '未知')
                    
                    realtime_info += f"{date}: {textDay} / {textNight}，温度 {tempMin}°C ~ {tempMax}°C，{windDirDay} {windScaleDay}级\n"
            
            return realtime_info
        except Exception as e:
            self.logger.error(f"格式化天气信息失败: {str(e)}")
            return str(realtime)

# 创建简单本地天气工具实例
simple_local_weather_tool = SimpleLocalWeatherTool()
