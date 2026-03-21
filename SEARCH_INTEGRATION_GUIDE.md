# 🔗 悦悦 - 实时推理 + 全网搜索联合使用指南

> **"让悦悦既能深度思考，又能实时联网获取最新信息！"** 🌐🧠💕

---

## 🎯 核心概念辨析

### ❓ 这两个 API 有什么区别？

| API | 定位 | 类比 | 负责 |
|-----|------|------|------|
| **实时推理 API** | LLM 对话接口 | 🧠 **大脑** | 理解、推理、生成回复 |
| **全网搜索 API** | 网络搜索工具 | 📡 **眼睛** | 获取最新网络信息 |

**本质**: 它们是**互补关系**,不是竞争关系!

```
┌─────────────┐      ┌─────────────┐
│  实时推理    │ ◄──► │  全网搜索   │
│  (Qwen Max) │      │  (Bing/Google)│
│   思考决策   │      │   获取信息   │
└─────────────┘      └─────────────┘
       ↓                    ↑
       └────────────────────┘
          互相配合，协同工作
```

---

## ✅ 结论先行

### 会不会相互干涉？

**❌ 不会！**

- ✅ 两个 API 独立调用，互不影响
- ✅ 实时推理只管「怎么回答」
- ✅ 全网搜索只管「去哪里找信息」
- ✅ 它们像「左脑 + 右脑」一样配合工作

### 怎么结合起来？

**✅ 三种主流方案:**

| 方案 | 原理 | 难度 | 推荐度 |
|------|------|------|--------|
| **Tool Call 模式** | LLM 自动判断何时搜索 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **规则触发模式** | 根据关键词主动搜索 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **固定流程模式** | 每次都先搜索再回答 | ⭐⭐ | ⭐⭐ |

---

## 🏗️ 方案 A: Tool Call 模式 (⭐⭐⭐⭐⭐ 最智能)

### 核心思想

让 LLM 自己决定什么时候需要搜索!

```
用户："今天北京的天气怎么样？"
        ↓
    LLM 思考："这个问题需要实时数据，我应该用搜索工具"
        ↓
    Action: web_search({"query": "北京今日天气"})
        ↓
    搜索结果：[{"title": "北京天气预报", "snippet": "晴天，25°C..."}]
        ↓
    LLM 整合："今天北京是晴天，气温 25°C 左右哦～☀️"
        ↓
    回复给用户
```

### 实现代码

```python
# yueyue/tools/search_tool.py

import httpx
from typing import List, Dict, Optional


class WebSearchAPI:
    """
    七牛云全网搜索 API 客户端
    
    文档：https://developer.qiniu.com/aitokenapi/13192/web-search-api
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.qnaigc.com/v1"
        
        # 搜索参数配置
        self.max_results = 5          # 最多返回几个结果
        self.search_depth = "standard"  # search_depth / advanced
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def close(self):
        await self.client.aclose()
    
    async def search(
        self,
        query: str,
        num_results: int = None,
        search_type: str = "web"  # web / news / images
    ) -> List[Dict]:
        """
        执行网络搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            search_type: 搜索类型
            
        Returns:
            [{"title": "...", "url": "...", "snippet": "..."}, ...]
        """
        params = {
            "q": query,
            "num": num_results or self.max_results,
            "type": search_type
        }
        
        try:
            response = await self.client.post("/web/search", json=params)
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "date": item.get("date", "")
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 搜索失败：{e}")
            return []
    
    def search_sync(self, query: str, num_results: int = None) -> List[Dict]:
        """同步版本"""
        import asyncio
        return asyncio.run(self.search(query, num_results))


# ──────────────────────────────────────────
# ReAct 引擎集成
# ──────────────────────────────────────────


class ReactEngineWithSearch:
    """增强版 ReAct 引擎 - 集成了搜索能力"""
    
    def __init__(self, llm_client, search_client: WebSearchAPI):
        self.llm = llm_client
        self.search = search_client
    
    async def run(self, user_query: str) -> str:
        """执行完整的 ReAct 流程"""
        
        # 步骤 1: 告诉 LLM 有哪些工具可用
        system_prompt = """你是一个智能助手，拥有以下工具:

【工具列表】
1. web_search(query) - 搜索网络获取最新信息
2. read_file(path) - 读取本地文件
3. write_file(path, content) - 写入文件

【工作流程】
如果遇到需要最新信息的问题 (如新闻、天气、价格等),请先调用 web_search,然后用搜索结果回答问题。

【输出格式】
如果需要搜索:
Thought: 我需要搜索一下最新信息
Action: TOOL:web_search({"query": "关键词"})
Observation: (等待搜索结果后填写)
Thought: (继续分析)
...
Final Answer: 最终回复

如果不需要搜索:
直接给出 Final Answer: xxx
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        max_iterations = 5
        search_results = []
        
        for iteration in range(max_iterations):
            # 调用 LLM
            response = self.llm.chat(messages=messages, temperature=0.7)
            
            # 检查是否要调用搜索工具
            if "TOOL:web_search" in response:
                # 提取搜索词
                import re
                match = re.search(r'web_search\(\{"query": "(.*?)"\}\)', response)
                
                if match:
                    search_query = match.group(1)
                    
                    # 执行搜索
                    print(f"🔍 正在搜索：{search_query}")
                    results = await self.search.search(search_query)
                    search_results.extend(results)
                    
                    # 将搜索结果格式化并加入上下文
                    observation = self._format_search_results(results)
                    
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "system", "content": f"Observation: {observation}"})
                    continue
            
            # 没有工具调用，直接回复
            if "Final Answer:" in response:
                answer = response.split("Final Answer:")[-1].strip()
                
                # 如果有过搜索，进行总结
                if search_results:
                    summary_prompt = f"""基于以下搜索结果，整理成一个简洁的回答:

搜索结果:
{self._format_search_results(search_results)}

原始问题：{user_query}

请用温柔亲切的语气回复，适当加 emoji～"""
                    
                    final_response = self.llm.chat([{"role": "user", "content": summary_prompt}])
                    return self._add_personality(final_response)
                else:
                    return self._add_personality(answer)
            
            # 继续下一轮思考
            messages.append({"role": "assistant", "content": response})
        
        return "抱歉，我暂时无法回答这个问题🤔"
    
    def _format_search_results(self, results: List[Dict], max_snippet: int = 200) -> str:
        """格式化搜索结果供 LLM 使用"""
        formatted = []
        
        for i, r in enumerate(results[:5], 1):  # 最多前 5 个
            snippet = r["snippet"][:max_snippet] + "..." if len(r["snippet"]) > max_snippet else r["snippet"]
            
            formatted.append(
                f"[{i]] 标题：{r['title']}\n"
                f"    摘要：{snippet}\n"
                f"    URL: {r['url']}"
            )
        
        return "\n\n".join(formatted)
    
    def _add_personality(self, text: str) -> str:
        """添加悦悦风格"""
        # 简单的 emoji 增强
        emoji_map = {
            "好": "好哒😊",
            "是的": "没错呢～😘",
            "不知道": "这个我还不太清楚哦🤔",
            "谢谢": "不客气呀～💕"
        }
        
        for k, v in emoji_map.items():
            if k in text:
                text = text.replace(k, v)
        
        return text
```

---

## 🏗️ 方案 B: 规则触发模式 (⭐⭐⭐⭐ 简单实用)

### 核心思想

不用 LLM 判断，直接根据关键词触发搜索:

```python
# yueyue/core/message_router.py

from .tools.search_tool import WebSearchAPI


class MessageRouter:
    """消息路由器 - 判断是否需要搜索"""
    
    # 触发搜索的关键词
    SEARCH_KEYWORDS = {
        "时间类": ["今天", "明天", "现在", "实时", "当前"],
        "新闻类": ["新闻", "热搜", "头条", "最新消息", "最近"],
        "天气类": ["天气", "温度", "下雨", "晴", "预报"],
        "价格类": ["多少钱", "价格", "报价", "售价", "多少钱"],
        "体育类": ["比分", "比赛", "进球", "冠军", "奖牌"],
        "股市类": ["股票", "涨跌", "指数", "行情"],
    }
    
    def __init__(self, search_client: WebSearchAPI):
        self.search = search_client
    
    def needs_search(self, message: str) -> bool:
        """判断消息是否需要搜索"""
        message_lower = message.lower()
        
        for category, keywords in self.SEARCH_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                return True
        
        return False
    
    def build_search_query(self, message: str) -> str:
        """从用户消息构建搜索词"""
        # 简化版：直接使用原话
        # 进阶：可以用 LLM 优化搜索词
        return message
    
    async def handle_message(self, message: str) -> str:
        """
        统一入口 - 自动判断是否搜索
        
        Args:
            message: 用户输入
            
        Returns:
            回复内容
        """
        # 判断是否需要搜索
        if self.needs_search(message):
            # 执行搜索
            search_query = self.build_search_query(message)
            print(f"🔍 检测到需要搜索：{search_query}")
            results = await self.search.search(search_query)
            
            if not results:
                return "抱歉，我没有找到相关信息呢🤔"
            
            # 组合成搜索结果的 prompt
            search_context = self._format_search_results(results)
            
            # 交给 LLM 生成最终回复
            final_prompt = f"""下面是关于"{message}"的搜索结果:

{search_context}

请根据这些信息，以悦悦的风格回复用户～记得温柔可爱一点，加些 emoji 哦!💕"""
            
            from ..clients.qiniu_llm_client import QiniuLLMClient
            llm = QiniuLLMClient(api_key=os.getenv("QINIU_API_KEY"))
            
            response = llm.chat([{"role": "user", "content": final_prompt}])
            return response
        
        else:
            # 不需要搜索，直接对话
            from ..clients.qiniu_llm_client import QiniuLLMClient
            llm = QiniuLLMClient(api_key=os.getenv("QINIU_API_KEY"))
            
            response = llm.chat([{"role": "user", "content": message}])
            return response
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """格式化搜索结果"""
        lines = []
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   {r['snippet']}")
            lines.append("")
        
        return "\n".join(lines)
```

### 使用示例

```python
router = MessageRouter(WebSearchAPI(api_key="xxx"))

# 测试不同场景
print(await router.handle_message("今天北京的天气怎么样？"))
# → 会触发搜索

print(await router.handle_message("你知道太阳系有多少颗行星吗？"))
# → 不会触发搜索，直接用已有知识回答
```

---

## 🏗️ 方案 C: 固定流程模式 (⭐⭐ 最简单)

### 核心思想

每次收到特定类型的问题，都先搜索再回答

```python
async def handle_time_related_question(query: str) -> str:
    """处理时间相关问题 - 固定搜索流程"""
    
    # 1. 构造搜索词
    search_queries = [
        f"{query}",
        f"{query} 2026 年",
        f"最新 {query}"
    ]
    
    all_results = []
    for q in search_queries:
        results = await search_api.search(q)
        all_results.extend(results)
    
    # 2. 合并去重
    unique_results = {}
    for r in all_results:
        unique_results[r["url"]] = r
    top_results = list(unique_results.values())[:10]
    
    # 3. 交给 LLM 总结
    prompt = f"""用户问的问题是：{query}

我已经搜索了网络，以下是相关结果:

{self._format_results(top_results)}

请帮我将这些结果整理成一个清晰、准确的回答。语气要友好，用中文回复。"""
    
    response = llm.chat([{"role": "user", "content": prompt}])
    return response
```

---

## 📊 三种方案对比

| 维度 | Tool Call 模式 | 规则触发模式 | 固定流程模式 |
|------|--------------|-------------|-------------|
| **智能程度** | ⭐⭐⭐⭐⭐ LLM 自己决定 | ⭐⭐⭐⭐ 规则判断 | ⭐⭐⭐ 固定触发 |
| **开发难度** | ⭐⭐⭐ 需要解析 | ⭐⭐⭐⭐ 简单 | ⭐⭐⭐⭐⭐ 最简单 |
| **灵活性** | ⭐⭐⭐⭐⭐ 动态调整 | ⭐⭐⭐⭐ 可改规则 | ⭐⭐⭐ 硬编码 |
| **响应速度** | ⭐⭐⭐ 可能多轮 | ⭐⭐⭐⭐ 一次搜索 | ⭐⭐⭐⭐⭐ 直接搜索 |
| **准确性** | ⭐⭐⭐⭐⭐ 最优 | ⭐⭐⭐⭐ 较好 | ⭐⭐⭐ 一般 |
| **推荐场景** | 生产环境 | MVP 验证 | 简单 demo |

---

## 🚀 完整集成示例

这是最终的集成代码，可以直接复制使用:

```python
# main.py - 悦悦主程序

import os
import asyncio
from dotenv import load_dotenv
from yueyue.clients.qiniu_llm_client import QiniuLLMClient
from yueyue.tools.search_tool import WebSearchAPI
from yueyue.core.message_router import MessageRouter

load_dotenv()


async def main():
    # 初始化组件
    llm = QiniuLLMClient(api_key=os.getenv("QINIU_API_KEY"))
    search = WebSearchAPI(api_key=os.getenv("QINIU_API_KEY"))
    router = MessageRouter(search)
    
    print("=" * 60)
    print("  💕 悦悦 - 支持实时搜索的智能家居 AI 管家")
    print("  「有我在，家永远温暖如春~」✨")
    print("=" * 60)
    print("\n试试这些问题:")
    print("  • \"今天的天气怎么样？\"  ← 会触发搜索")
    print("  • \"昨天北京下暴雨了吗？\" ← 会触发搜索")
    print("  • \"太阳系有多少颗行星？\" ← 直接回答")
    print("  • \"帮我列出 D:\\CoWorks 目录下的文件\" ← 文件操作")
    print("\n输入 'quit' 退出\n")
    
    while True:
        try:
            user_input = input("你：").strip()
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("悦悦：再见啦～下次见!💕")
                break
            
            if not user_input:
                continue
            
            # 统一路由到处理函数
            response = await router.handle_message(user_input)
            print(f"\n悦悦：{response}\n")
            
        except KeyboardInterrupt:
            print("\n\n悦悦：拜拜～💕")
            break
    
    await search.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔍 实际对话演示

### 示例 1: 触发搜索的问题

```
你：今天北京的天气怎么样？

[后端日志]
🔍 检测到需要搜索：今天北京的天气怎么样？
🔍 正在搜索：北京 今日 天气

[搜索结果]
1. [中国天气网] 北京天气预报 - 今天多云转晴，最高 25°C
2. [墨迹天气] 北京实时空气质量优，体感温度舒适
3. ...

悦悦：今天北京是多云转晴的天气呢～☀️ 
最高气温大概 25°C 左右，空气质量也很好哦！
适合出门走走，记得带件薄外套～🧥💕
```

### 示例 2: 不触发搜索的问题

```
你：你知道太阳系有几颗行星吗？

[后端日志]
ℹ️ 不需要搜索，使用已有知识回答

悦悦：当然知道啦～🌌
太阳系一共有 8 颗行星呢！
从小到大分别是：水星、金星、地球、火星、木星、土星、天王星、海王星～
你还对天文感兴趣吗？我可以帮你找找更多有趣的知识点哦!🔭✨💕
```

### 示例 3: 混合场景

```
你：帮我看看昨天深圳是不是下雨了

[后端日志]
🔍 检测到需要搜索：昨天深圳是不是下雨了
🔍 正在搜索：深圳 昨天 天气 降雨

悦悦：查到了呢～🌧️
昨天深圳确实有下雨哦!
大部分地区是阵雨天气，雨量不大，
但是还是有点湿哒哒的呢～
今天要不要提醒你带伞出门呀？☔💕
```

---

## 🎯 最佳实践建议

### ✅ DO

- ✅ 优先使用 **规则触发模式** 开始验证 (简单可靠)
- ✅ 搜索词尽量简洁明确 ("北京天气" > "我今天想知道北京的天气情况")
- ✅ 限制搜索结果数量 (5-10 条足够)
- ✅ 对搜索结果做摘要处理 (避免超出 token)
- ✅ 添加错误处理 (搜索失败时给友好提示)

### ❌ DON'T

- ❌ 不要在每次对话都搜索 (浪费且没必要)
- ❌ 不要把整个网页内容传给 LLM (只传摘要)
- ❌ 不要忽略搜索结果的可信度评估
- ❌ 不要暴露内部搜索词和用户看到的内容差异

---

## 📋 常见场景对照表

| 用户问题 | 是否需要搜索 | 推荐方案 |
|---------|-------------|---------|
| "今天北京天气" | ✅ 是 | 规则触发 |
| "太阳为什么发光" | ❌ 否 | 直接回答 |
| "最新 AI 新闻" | ✅ 是 | 规则触发 |
| "苹果多少钱一斤" | ✅ 是 | 规则触发 |
| "Python 怎么写循环" | ❌ 否 | 直接回答 |
| "昨天沪深指数多少" | ✅ 是 | 规则触发 |
| "如何泡方便面" | ❌ 否 | 直接回答 |
| "附近的餐厅推荐" | ✅ 是 | 工具调用 |

---

## 🛠️ 故障排查 FAQ

### Q1: 搜索 API 返回 403?
**A**: 检查 API Key 是否有效，是否有搜索功能的权限

### Q2: 搜索结果是空的?
**A**: 可能是搜索词太生僻，换个通俗的表达试试

### Q3: LLM 重复引用同一来源?
**A**: 搜索结果去重，确保每个 URL 只出现一次

### Q4: 响应时间太长?
**A**: 减少搜索结果数，或用缓存机制

---

*让悦悦既有智慧的大脑，又有敏锐的眼睛～🧠👀💕✨*

**版本**: V1.0  
**最后更新**: 2026-03-09  
**Related**: [实时推理 API](https://developer.qiniu.com/aitokenapi/12882/ai-inference-api) | [全网搜索 API](https://developer.qiniu.com/aitokenapi/13192/web-search-api)
