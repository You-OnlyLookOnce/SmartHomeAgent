import requests
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp

class WebSearchSkill:
    """网络搜索技能 - 调用七牛云全网搜索API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 七牛云Web Search API的正确路径
        self.base_url = "https://api.qnaigc.com/v1/search/web"
    
    def get_current_date(self) -> str:
        """获取当前日期"""
        now = datetime.now()
        return now.strftime("%Y年%m月%d日 %H:%M:%S")
    
    def get_current_weekday(self) -> str:
        """获取当前星期几"""
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[now.weekday()]
    
    def search(self, query: str, max_results: int = 5, search_type: str = "web", time_filter: Optional[str] = None, site_filter: Optional[List[str]] = None, max_retries: int = 3) -> Dict:
        """执行网络搜索
        
        Args:
            query: 搜索关键词
            max_results: 返回结果数量
            search_type: 搜索类型 (web, image, video)
            time_filter: 时间过滤，可选值：week（一周内）、month（一月内）、year（一年内）、semiyear(半年内)
            site_filter: 站点过滤，指定搜索特定网站的内容（最多20个）
            max_retries: 最大重试次数
            
        Returns:
            搜索结果
        """
        import time
        
        # 根据搜索类型设置默认结果数量
        if search_type == "web" and max_results > 50:
            max_results = 50  # 网页搜索最大50
        elif search_type == "video" and max_results > 10:
            max_results = 10  # 视频搜索最大10
        elif search_type == "image" and max_results > 30:
            max_results = 30  # 图片搜索最大30
        
        print(f"[搜索API] 开始搜索: {query}")
        print(f"[搜索API] 搜索类型: {search_type}")
        print(f"[搜索API] 时间过滤: {time_filter}")
        print(f"[搜索API] API Key: {'***' + self.api_key[-8:] if self.api_key else '未配置'}")
        
        # 检查API密钥
        if not self.api_key:
            print("[搜索API] API密钥未配置")
            return {
                "success": False,
                "error_code": "API_KEY_MISSING",
                "error_message": "搜索服务未配置，请联系管理员",
                "message": "抱歉，搜索服务暂时不可用"
            }
        
        for retry in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "query": query,
                    "max_results": max_results,
                    "search_type": search_type
                }
                
                # 添加可选参数
                if time_filter:
                    payload["time_filter"] = time_filter
                if site_filter:
                    # 限制站点数量不超过20个
                    payload["site_filter"] = site_filter[:20]
                
                print(f"[搜索API] 发送请求: {self.base_url}")
                print(f"[搜索API] 请求参数: {payload}")
                
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
                
                print(f"[搜索API] 响应状态: {response.status_code}")
                print(f"[搜索API] 响应内容: {response.text[:500]}...")
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    print(f"[搜索API] 搜索成功: {result}")
                    # 确保返回格式一致
                    if "success" not in result:
                        result["success"] = True
                    return result
                elif response.status_code == 429:  # 限流错误，需要重试
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry  # 指数退避
                        print(f"搜索API限流，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[搜索API] 限流错误，已达到最大重试次数")
                        return {
                            "success": False,
                            "error_code": "API_RATE_LIMITED",
                            "error_message": "搜索请求过于频繁，请稍后再试",
                            "message": "抱歉，当前搜索请求过于频繁，请稍后再试"
                        }
                elif response.status_code == 401:
                    print("[搜索API] API密钥无效")
                    return {
                        "success": False,
                        "error_code": "INVALID_API_KEY",
                        "error_message": "API密钥无效，请检查配置",
                        "message": "抱歉，搜索服务配置有误，请联系管理员"
                    }
                elif response.status_code == 400:
                    print(f"[搜索API] 请求参数错误: {response.text}")
                    return {
                        "success": False,
                        "error_code": "INVALID_REQUEST",
                        "error_message": f"请求参数错误 - {response.text}",
                        "message": "抱歉，搜索请求参数错误"
                    }
                elif response.status_code == 403:
                    print("[搜索API] 权限不足")
                    return {
                        "success": False,
                        "error_code": "PERMISSION_DENIED",
                        "error_message": "API权限不足",
                        "message": "抱歉，搜索服务权限不足，请联系管理员"
                    }
                elif response.status_code == 404:
                    print("[搜索API] 接口不存在")
                    return {
                        "success": False,
                        "error_code": "API_NOT_FOUND",
                        "error_message": "搜索接口不存在",
                        "message": "抱歉，搜索服务暂时不可用"
                    }
                elif response.status_code >= 500:
                    print(f"[搜索API] 服务器错误: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error_code": "API_SERVER_ERROR",
                        "error_message": f"搜索服务内部错误 - {response.text}",
                        "message": "抱歉，搜索服务暂时不可用"
                    }
                else:
                    # 其他错误
                    print(f"[搜索API] HTTP错误: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error_code": "HTTP_ERROR",
                        "error_message": f"HTTP {response.status_code} - {response.text}",
                        "message": "抱歉，搜索服务暂时不可用"
                    }
            except requests.exceptions.Timeout:
                if retry < max_retries - 1:
                    wait_time = 2 ** retry
                    print(f"搜索超时，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print("[搜索API] 请求超时，已达到最大重试次数")
                    return {
                        "success": False,
                        "error_code": "REQUEST_TIMEOUT",
                        "error_message": "请求超时，已达到最大重试次数",
                        "message": "抱歉，网络连接超时，请检查网络后重试"
                    }
            except requests.exceptions.ConnectionError:
                if retry < max_retries - 1:
                    wait_time = 2 ** retry
                    print(f"网络连接错误，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print("[搜索API] 网络连接错误，已达到最大重试次数")
                    return {
                        "success": False,
                        "error_code": "CONNECTION_ERROR",
                        "error_message": "网络连接错误，已达到最大重试次数",
                        "message": "抱歉，网络连接失败，请检查网络后重试"
                    }
            except requests.exceptions.RequestException as e:
                print(f"[搜索API] 请求异常: {str(e)}")
                return {
                    "success": False,
                    "error_code": "REQUEST_EXCEPTION",
                    "error_message": f"请求异常: {str(e)}",
                    "message": "抱歉，搜索请求失败，请稍后重试"
                }
            except Exception as e:
                print(f"[搜索API] 未知异常: {str(e)}")
                return {
                    "success": False,
                    "error_code": "UNKNOWN_ERROR",
                    "error_message": f"未知异常: {str(e)}",
                    "message": "抱歉，搜索服务暂时不可用"
                }
        
        print("[搜索API] 未知错误")
        return {
            "success": False,
            "error_code": "UNKNOWN_ERROR",
            "error_message": "未知错误",
            "message": "抱歉，搜索服务暂时不可用"
        }
    
    async def async_search(self, query: str, max_results: int = 5, search_type: str = "web", time_filter: Optional[str] = None, site_filter: Optional[List[str]] = None, max_retries: int = 3) -> Dict:
        """异步执行网络搜索
        
        Args:
            query: 搜索关键词
            max_results: 返回结果数量
            search_type: 搜索类型 (web, image, video)
            time_filter: 时间过滤，可选值：week（一周内）、month（一月内）、year（一年内）、semiyear(半年内)
            site_filter: 站点过滤，指定搜索特定网站的内容（最多20个）
            max_retries: 最大重试次数
            
        Returns:
            搜索结果
        """
        import time
        
        # 根据搜索类型设置默认结果数量
        if search_type == "web" and max_results > 50:
            max_results = 50  # 网页搜索最大50
        elif search_type == "video" and max_results > 10:
            max_results = 10  # 视频搜索最大10
        elif search_type == "image" and max_results > 30:
            max_results = 30  # 图片搜索最大30
        
        print(f"[搜索API] 开始搜索: {query}")
        print(f"[搜索API] 搜索类型: {search_type}")
        print(f"[搜索API] 时间过滤: {time_filter}")
        print(f"[搜索API] API Key: {'***' + self.api_key[-8:] if self.api_key else '未配置'}")
        
        # 检查API密钥
        if not self.api_key:
            print("[搜索API] API密钥未配置")
            return {
                "success": False,
                "error_code": "API_KEY_MISSING",
                "error_message": "搜索服务未配置，请联系管理员",
                "message": "抱歉，搜索服务暂时不可用"
            }
        
        for retry in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "query": query,
                    "max_results": max_results,
                    "search_type": search_type
                }
                
                # 添加可选参数
                if time_filter:
                    payload["time_filter"] = time_filter
                if site_filter:
                    # 限制站点数量不超过20个
                    payload["site_filter"] = site_filter[:20]
                
                print(f"[搜索API] 发送请求: {self.base_url}")
                print(f"[搜索API] 请求参数: {payload}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        print(f"[搜索API] 响应状态: {response.status}")
                        response_text = await response.text()
                        print(f"[搜索API] 响应内容: {response_text[:500]}...")
                        
                        # 检查响应状态
                        if response.status == 200:
                            result = await response.json()
                            print(f"[搜索API] 搜索成功: {result}")
                            # 确保返回格式一致
                            if "success" not in result:
                                result["success"] = True
                            return result
                        elif response.status == 429:  # 限流错误，需要重试
                            if retry < max_retries - 1:
                                wait_time = 2 ** retry  # 指数退避
                                print(f"搜索API限流，{wait_time}秒后重试...")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print("[搜索API] 限流错误，已达到最大重试次数")
                                return {
                                    "success": False,
                                    "error_code": "API_RATE_LIMITED",
                                    "error_message": "搜索请求过于频繁，请稍后再试",
                                    "message": "抱歉，当前搜索请求过于频繁，请稍后再试"
                                }
                        elif response.status == 401:
                            print("[搜索API] API密钥无效")
                            return {
                                "success": False,
                                "error_code": "INVALID_API_KEY",
                                "error_message": "API密钥无效，请检查配置",
                                "message": "抱歉，搜索服务配置有误，请联系管理员"
                            }
                        elif response.status == 400:
                            print(f"[搜索API] 请求参数错误: {response_text}")
                            return {
                                "success": False,
                                "error_code": "INVALID_REQUEST",
                                "error_message": f"请求参数错误 - {response_text}",
                                "message": "抱歉，搜索请求参数错误"
                            }
                        elif response.status == 403:
                            print("[搜索API] 权限不足")
                            return {
                                "success": False,
                                "error_code": "PERMISSION_DENIED",
                                "error_message": "API权限不足",
                                "message": "抱歉，搜索服务权限不足，请联系管理员"
                            }
                        elif response.status == 404:
                            print("[搜索API] 接口不存在")
                            return {
                                "success": False,
                                "error_code": "API_NOT_FOUND",
                                "error_message": "搜索接口不存在",
                                "message": "抱歉，搜索服务暂时不可用"
                            }
                        elif response.status >= 500:
                            print(f"[搜索API] 服务器错误: {response.status} - {response_text}")
                            return {
                                "success": False,
                                "error_code": "API_SERVER_ERROR",
                                "error_message": f"搜索服务内部错误 - {response_text}",
                                "message": "抱歉，搜索服务暂时不可用"
                            }
                        else:
                            # 其他错误
                            print(f"[搜索API] HTTP错误: {response.status} - {response_text}")
                            return {
                                "success": False,
                                "error_code": "HTTP_ERROR",
                                "error_message": f"HTTP {response.status} - {response_text}",
                                "message": "抱歉，搜索服务暂时不可用"
                            }
            except aiohttp.ClientTimeout:
                if retry < max_retries - 1:
                    wait_time = 2 ** retry
                    print(f"搜索超时，{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print("[搜索API] 请求超时，已达到最大重试次数")
                    return {
                        "success": False,
                        "error_code": "REQUEST_TIMEOUT",
                        "error_message": "请求超时，已达到最大重试次数",
                        "message": "抱歉，网络连接超时，请检查网络后重试"
                    }
            except aiohttp.ClientConnectionError:
                if retry < max_retries - 1:
                    wait_time = 2 ** retry
                    print(f"网络连接错误，{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print("[搜索API] 网络连接错误，已达到最大重试次数")
                    return {
                        "success": False,
                        "error_code": "CONNECTION_ERROR",
                        "error_message": "网络连接错误，已达到最大重试次数",
                        "message": "抱歉，网络连接失败，请检查网络后重试"
                    }
            except aiohttp.ClientError as e:
                print(f"[搜索API] 请求异常: {str(e)}")
                return {
                    "success": False,
                    "error_code": "REQUEST_EXCEPTION",
                    "error_message": f"请求异常: {str(e)}",
                    "message": "抱歉，搜索请求失败，请稍后重试"
                }
            except Exception as e:
                print(f"[搜索API] 未知异常: {str(e)}")
                return {
                    "success": False,
                    "error_code": "UNKNOWN_ERROR",
                    "error_message": f"未知异常: {str(e)}",
                    "message": "抱歉，搜索服务暂时不可用"
                }
        
        print("[搜索API] 未知错误")
        return {
            "success": False,
            "error_code": "UNKNOWN_ERROR",
            "error_message": "未知错误",
            "message": "抱歉，搜索服务暂时不可用"
        }
    
    def is_search_needed(self, query: str) -> bool:
        """判断是否需要网络搜索
        
        Args:
            query: 用户查询
            
        Returns:
            是否需要网络搜索
        """
        # 关键词列表，包含需要实时信息的查询类型
        search_keywords = [
            "今天", "明天", "后天", "最近",
            "新闻", "最新", "今日", "现在",
            "假期", "放假", "安排", "时间",
            "比赛", "比分", "结果", "直播",
            "股票", "价格", "行情", "汇率",
            "电影", "上映", "票房", "评价",
            "航班", "高铁", "交通", "路况"
        ]
        
        # 检查查询是否包含需要实时信息的关键词
        query_lower = query.lower()
        for keyword in search_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def format_search_results(self, search_result: Dict) -> str:
        """格式化搜索结果为自然语言
        
        Args:
            search_result: 搜索结果
            
        Returns:
            格式化后的自然语言回答
        """
        if not search_result.get("success", True):
            return f"抱歉，搜索失败: {search_result.get('message', '未知错误')}"
        
        data = search_result.get("data", {})
        results = data.get("results", [])
        
        if not results:
            return "抱歉，未找到相关信息。"
        
        formatted_results = []
        for i, result in enumerate(results[:3], 1):  # 只取前3个结果
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            source = result.get("source", "")
            date = result.get("date", "")
            
            result_text = []
            if title:
                result_text.append(f"{i}. {title}")
            if content:
                # 限制内容长度，避免过长
                if len(content) > 200:
                    content = content[:200] + "..."
                result_text.append(content)
            if source:
                result_text.append(f"来源: {source}")
            if date:
                result_text.append(f"发布时间: {date}")
            if url:
                result_text.append(f"链接: {url}")
            
            if result_text:
                formatted_results.append("\n".join(result_text) + "\n")
        
        if formatted_results:
            return "\n".join(formatted_results)
        else:
            return "抱歉，未找到相关信息。"
    
    def execute(self, query: str, search_type: str = "web", time_filter: Optional[str] = None, site_filter: Optional[List[str]] = None, max_retries: int = 3) -> Dict:
        """执行搜索并返回结果
        
        Args:
            query: 用户查询
            search_type: 搜索类型 (web, image, video)
            time_filter: 时间过滤，可选值：week（一周内）、month（一月内）、year（一年内）、semiyear(半年内)
            site_filter: 站点过滤，指定搜索特定网站的内容（最多20个）
            max_retries: 最大重试次数
            
        Returns:
            搜索结果
        """
        try:
            # 直接执行搜索，不做本地判断（由search_judgment模块负责判断）
            print(f"[搜索] 执行搜索: {query}, 类型: {search_type}, 时间过滤: {time_filter}")
            search_result = self.search(query, search_type=search_type, time_filter=time_filter, site_filter=site_filter, max_retries=max_retries)
            print(f"[搜索] 搜索结果: {search_result}")
            
            if search_result.get("success", True):
                formatted_result = self.format_search_results(search_result)
                return {
                    "success": True,
                    "message": formatted_result,
                    "result": formatted_result
                }
            else:
                # 获取错误信息
                error_code = search_result.get("error_code", "UNKNOWN_ERROR")
                error_message = search_result.get("error_message", "搜索失败")
                friendly_message = search_result.get("message", "抱歉，搜索服务暂时不可用")
                
                print(f"[搜索] 搜索失败: {error_code} - {error_message}")
                
                # 对于日期相关查询，使用本地日期获取
                query_lower = query.lower()
                date_related_keywords = ["今天是几号", "现在几点了", "几点了", "今天日期", "当前时间", "现在时间", "今天星期几", "今年是哪一年"]
                if any(keyword in query_lower for keyword in date_related_keywords):
                    current_date = self.get_current_date()
                    current_weekday = self.get_current_weekday()
                    if "星期" in query_lower:
                        result = f"今天是{current_weekday}，{current_date}"
                    else:
                        result = f"今天是{current_date}，{current_weekday}"
                    return {
                        "success": True,
                        "message": result,
                        "result": result
                    }
                else:
                    # 返回统一格式的错误响应
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error_message": error_message,
                        "message": friendly_message,
                        "result": friendly_message
                    }
        except Exception as e:
            error_message = f"搜索执行失败: {str(e)}"
            print(f"[搜索] 执行异常: {error_message}")
            
            # 对于日期相关查询，使用本地日期获取
            query_lower = query.lower()
            date_related_keywords = ["今天是几号", "现在几点了", "几点了", "今天日期", "当前时间", "现在时间", "今天星期几", "今年是哪一年"]
            if any(keyword in query_lower for keyword in date_related_keywords):
                current_date = self.get_current_date()
                current_weekday = self.get_current_weekday()
                if "星期" in query_lower:
                    result = f"今天是{current_weekday}，{current_date}"
                else:
                    result = f"今天是{current_date}，{current_weekday}"
                return {
                    "success": True,
                    "message": result,
                    "result": result
                }
            else:
                # 返回统一格式的错误响应
                return {
                    "success": False,
                    "error_code": "EXECUTION_ERROR",
                    "error_message": error_message,
                    "message": "抱歉，搜索服务暂时不可用。我将基于我的知识库为您提供信息。",
                    "result": "抱歉，搜索服务暂时不可用。我将基于我的知识库为您提供信息。"
                }