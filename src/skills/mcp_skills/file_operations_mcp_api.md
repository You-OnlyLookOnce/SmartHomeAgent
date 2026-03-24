# 文件操作管理控制程序(MCP) - API文档

## 概述
文件操作管理控制程序(MCP)是一个本地文件操作工具，提供文件读取、文件创建、文件查找和文件内容改写等核心功能。该MCP完全独立于外部管理控制程序，仅依赖七牛云的模型推理能力进行决策支持。

## 功能列表

### 1. 文件读取
- **功能**: 读取指定路径文件内容，返回文本格式数据
- **方法**: `read_file(file_path)`
- **参数**: 
  - `file_path` (str): 文件路径
- **返回值**: 文件内容（文本格式）或错误信息
- **异步方法**: `read_file_async(file_path)`

### 2. 文件创建
- **功能**: 创建新文件并写入内容，处理文件已存在情况
- **方法**: `create_file(file_path, content, overwrite=False)`
- **参数**: 
  - `file_path` (str): 文件路径
  - `content` (str): 文件内容
  - `overwrite` (bool): 是否覆盖已存在的文件，默认为False
- **返回值**: 操作结果（成功或错误信息）
- **异步方法**: `create_file_async(file_path, content, overwrite=False)`

### 3. 文件查找
- **功能**: 按文件名、文件类型或内容关键词搜索文件
- **方法**: `search_files(directory, filename_pattern=None, file_extension=None, content_keyword=None)`
- **参数**: 
  - `directory` (str): 搜索目录
  - `filename_pattern` (str, 可选): 文件名模式（支持通配符）
  - `file_extension` (str, 可选): 文件扩展名
  - `content_keyword` (str, 可选): 内容关键词
- **返回值**: 符合条件的文件列表
- **异步方法**: `search_files_async(directory, filename_pattern=None, file_extension=None, content_keyword=None)`

### 4. 文件改写
- **功能**: 替换文件内容，保留文件元数据
- **方法**: `rewrite_file(file_path, new_content, start_line=None, end_line=None)`
- **参数**: 
  - `file_path` (str): 文件路径
  - `new_content` (str): 新内容
  - `start_line` (int, 可选): 开始行（从1开始）
  - `end_line` (int, 可选): 结束行（从1开始）
- **返回值**: 操作结果（成功或错误信息）
- **异步方法**: `rewrite_file_async(file_path, new_content, start_line=None, end_line=None)`

## 错误处理

| 错误类型 | 错误信息 | 原因 |
|---------|---------|------|
| 路径不允许 | 路径不允许操作: {path} | 操作的路径不在允许范围内 |
| 文件不存在 | 文件不存在: {path} | 指定的文件不存在 |
| 路径不是文件 | 路径不是文件: {path} | 指定的路径不是文件 |
| 权限不足 | 权限不足，无法{operation}文件: {path} | 没有足够的权限执行操作 |
| 文件已存在 | 文件已存在: {path} | 文件已存在且未设置覆盖选项 |
| 目录不存在 | 目录不存在: {path} | 搜索的目录不存在 |
| 路径不是目录 | 路径不是目录: {path} | 搜索的路径不是目录 |
| 无效的行范围 | 无效的行范围: 开始行 {start}, 结束行 {end}, 文件总行数 {total} | 指定的行范围超出文件范围 |

## 安全限制

- **路径限制**: 仅允许操作项目根目录、用户主目录和临时目录内的文件
- **权限检查**: 会检查文件操作的权限，无权限时会返回错误信息
- **异常处理**: 所有操作都有异常处理机制，防止程序崩溃

## 调用示例

### 同步调用示例

```python
from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp

# 1. 读取文件
content = file_operations_mcp.read_file("path/to/file.txt")
print(content)

# 2. 创建文件
result = file_operations_mcp.create_file("path/to/new_file.txt", "Hello, world!")
print(result)

# 3. 搜索文件
files = file_operations_mcp.search_files("path/to/directory", filename_pattern="*.txt")
print(files)

# 4. 改写文件
result = file_operations_mcp.rewrite_file("path/to/file.txt", "New content")
print(result)
```

### 异步调用示例

```python
import asyncio
from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp

async def main():
    # 1. 异步读取文件
    content = await file_operations_mcp.read_file_async("path/to/file.txt")
    print(content)
    
    # 2. 异步创建文件
    result = await file_operations_mcp.create_file_async("path/to/new_file.txt", "Hello, world!")
    print(result)
    
    # 3. 异步搜索文件
    files = await file_operations_mcp.search_files_async("path/to/directory", filename_pattern="*.txt")
    print(files)
    
    # 4. 异步改写文件
    result = await file_operations_mcp.rewrite_file_async("path/to/file.txt", "New content")
    print(result)

asyncio.run(main())
```

## 智能体集成示例

```python
# 智能体调用文件操作MCP的示例

def call_file_operations_mcp(action, **kwargs):
    """调用文件操作MCP
    
    Args:
        action: 操作类型 (read_file, create_file, search_files, rewrite_file)
        **kwargs: 操作参数
        
    Returns:
        操作结果
    """
    from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp
    
    if action == "read_file":
        return file_operations_mcp.read_file(kwargs.get("file_path"))
    elif action == "create_file":
        return file_operations_mcp.create_file(
            kwargs.get("file_path"),
            kwargs.get("content"),
            kwargs.get("overwrite", False)
        )
    elif action == "search_files":
        return file_operations_mcp.search_files(
            kwargs.get("directory"),
            kwargs.get("filename_pattern"),
            kwargs.get("file_extension"),
            kwargs.get("content_keyword")
        )
    elif action == "rewrite_file":
        return file_operations_mcp.rewrite_file(
            kwargs.get("file_path"),
            kwargs.get("new_content"),
            kwargs.get("start_line"),
            kwargs.get("end_line")
        )
    else:
        return "错误: 无效的操作类型"

# 示例调用
result = call_file_operations_mcp("read_file", file_path="path/to/file.txt")
print(result)
```

## 跨平台兼容性

- **路径处理**: 自动处理不同操作系统的路径分隔符差异
- **权限处理**: 处理不同操作系统的文件权限差异
- **编码处理**: 使用UTF-8编码读取和写入文件，确保跨平台兼容性

## 性能考虑

- **大文件处理**: 对于大文件，建议使用异步方法进行操作，避免阻塞主线程
- **搜索性能**: 内容搜索可能会比较耗时，特别是在大型目录中，建议限制搜索范围
- **并发操作**: 支持多个并发操作，但应注意文件锁定和并发写入的问题
