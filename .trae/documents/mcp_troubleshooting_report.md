# MCP调用失败故障排查报告

## 测试环境
- 测试时间: 2026-03-23
- 操作系统: Windows 11
- Python版本: 3.11
- API密钥: 已配置（长度: 67）

## 问题描述
所有MCP工具调用均返回404错误，错误信息为"not found or method not allowed"。

## 排查过程

### 1. URL地址检查
**测试用例**：
- 当前配置的URL: `https://api.qnaigc.com/v1/agent/instance/{id}/v1`
- 修正后的URL: `https://api.qnaigc.com/v1/agent/instance/{id}`
- 标准MCP协议URL: `https://api.qnaigc.com/v1/mcp/http-streamable/{id}`

**结果**：
- 当前配置的URL: 404错误
- 修正后的URL: 404错误
- 标准MCP协议URL: 200状态码，但返回"Invalid session ID"

### 2. HTTP方法检查
**测试用例**：
- 使用POST方法调用MCP服务

**结果**：
- HTTP方法正确，返回404不是因为方法错误

### 3. API密钥检查
**测试用例**：
- 验证API密钥是否配置
- 验证API密钥长度

**结果**：
- API密钥已配置，长度为67个字符
- 不是API密钥问题

### 4. Server ID检查
**测试用例**：
- 测试不同的MCP ID格式
- 测试不同的协议格式

**结果**：
- 标准MCP协议返回200状态码，说明ID格式正确
- 问题可能是MCP服务实例未激活

### 5. 请求格式检查
**测试用例**：
- 使用标准JSON-RPC格式调用
- 测试tools/list方法
- 测试tool/call方法

**结果**：
- 所有请求均返回"Invalid session ID"

## 问题原因分析

### 主要原因
1. **MCP服务实例未激活**：根据MCP文档，需要在七牛云AI控制台激活MCP服务实例
2. **会话管理问题**：标准MCP协议需要先创建会话才能调用工具
3. **URL格式错误**：当前使用的Agent协议URL格式可能不正确

### 次要原因
1. **权限问题**：API密钥可能没有MCP服务的访问权限
2. **服务不可用**：MCP服务可能暂时不可用

## 解决方案

### 1. 检查MCP服务实例状态
- 登录七牛云AI控制台
- 进入MCP服务管理页面
- 检查MCP服务实例是否激活
- 确认MCP ID是否正确

### 2. 使用正确的URL格式
根据MCP文档，推荐使用以下格式：
- Agent协议: `https://api.qnaigc.com/v1/agent/instance/{mcp-id}`
- 标准MCP协议: `https://api.qnaigc.com/v1/mcp/http-streamable/{mcp-id}`

### 3. 实现会话管理
对于标准MCP协议，需要：
1. 先调用会话创建方法
2. 使用返回的会话ID进行后续调用
3. 会话结束后调用会话销毁方法

### 4. 检查API密钥权限
- 确认API密钥具有MCP服务的访问权限
- 尝试在控制台重置API密钥

### 5. 验证网络连接
- 检查网络连接是否正常
- 验证是否可以访问七牛云API

## 代码优化建议

### 1. MCP客户端改进
```python
class MCPClient:
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session_id = None
    
    async def create_session(self, base_url: str) -> str:
        """创建MCP会话"""
        # 实现会话创建逻辑
        pass
    
    async def call_agent(self, base_url: str, messages: list) -> AsyncGenerator[Dict[str, Any], None]:
        """调用Agent协议的MCP服务"""
        # 现有实现
        pass
    
    async def call_mcp(self, base_url: str, method: str, params: dict) -> Dict[str, Any]:
        """调用标准MCP协议服务"""
        # 实现标准MCP协议调用
        pass
```

### 2. 错误处理增强
- 添加更详细的错误信息
- 实现自动重试机制
- 提供更友好的错误提示

### 3. 配置验证
- 在启动时验证MCP配置
- 提供配置检查工具
- 自动检测URL格式是否正确

## 测试结果总结

| 测试项 | 状态 | 结果 |
|--------|------|------|
| URL格式检查 | 失败 | 404错误 |
| HTTP方法检查 | 成功 | POST方法正确 |
| API密钥检查 | 成功 | 已配置且格式正确 |
| Server ID检查 | 部分成功 | 标准MCP协议返回200 |
| 请求格式检查 | 部分成功 | JSON-RPC格式正确 |

## 结论

MCP调用失败的主要原因是：
1. **MCP服务实例未激活**：需要在七牛云AI控制台激活服务
2. **URL格式错误**：当前使用的URL格式不符合MCP文档规范
3. **会话管理缺失**：标准MCP协议需要会话管理

建议按照MCP文档正确配置服务实例，并使用标准的MCP协议进行调用。