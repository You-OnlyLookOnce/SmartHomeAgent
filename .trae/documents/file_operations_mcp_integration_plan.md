# 文件操作MCP工具整合计划

## 1. 项目概述

本计划旨在将文件操作MCP（Management Control Program）工具整合到现有的判断逻辑体系中。文件操作MCP工具作为已实现的功能组件，需要被纳入系统的工具选择与调用决策流程，确保在需要执行文件操作相关任务时，系统能够自动识别并调用此MCP工具，同时保持与其他现有工具判断逻辑的一致性和兼容性。

## 2. 任务分解与优先级

### [x] 任务 1: 注册文件操作MCP工具到资源注册表
- **优先级**: P0
- **依赖项**: None
- **描述**:
  - 在 `resource_registry.py` 中注册文件操作MCP工具
  - 为文件操作MCP工具提供清晰的描述和使用示例
  - 确保文件操作MCP工具能够被元认知路由器识别和调用
- **成功标准**:
  - 文件操作MCP工具成功注册到资源注册表
  - 资源注册表能够正确返回文件操作MCP工具的信息
  - 元认知路由器能够识别文件操作MCP工具
- **测试要求**:
  - `programmatic` TR-1.1: 资源注册表中包含文件操作MCP工具
  - `programmatic` TR-1.2: 元认知路由器能够识别文件操作相关任务
- **注意事项**:
  - 确保文件操作MCP工具的描述清晰明确，便于LLM理解
  - 提供足够的使用示例，覆盖常见的文件操作场景

### [x] 任务 2: 增强元认知路由器的决策逻辑
- **优先级**: P0
- **依赖项**: 任务 1
- **描述**:
  - 在 `meta_router.py` 中添加对文件操作相关任务的识别逻辑
  - 为文件操作相关任务设置专门的处理路径
  - 确保系统能够正确区分文件操作任务和其他类型的任务
- **成功标准**:
  - 元认知路由器能够正确识别文件操作相关任务
  - 文件操作相关任务能够触发文件操作MCP工具
  - 其他类型的任务能够继续使用现有的处理逻辑
- **测试要求**:
  - `programmatic` TR-2.1: 系统能够正确识别至少10个不同类型的文件操作任务
  - `programmatic` TR-2.2: 系统能够正确处理非文件操作任务
- **注意事项**:
  - 确保文件操作任务的识别逻辑准确可靠
  - 避免将非文件操作任务误判为文件操作任务
  - 保持与现有决策逻辑的一致性和兼容性

### [x] 任务 3: 实现文件操作MCP工具的调用逻辑
- **优先级**: P0
- **依赖项**: 任务 1, 任务 2
- **描述**:
  - 在 `meta_router.py` 中实现文件操作MCP工具的调用逻辑
  - 处理文件操作MCP工具的参数提取和传递
  - 处理文件操作MCP工具的返回结果
- **成功标准**:
  - 系统能够正确调用文件操作MCP工具
  - 文件操作MCP工具能够正确执行文件操作任务
  - 系统能够正确处理文件操作MCP工具的返回结果
- **测试要求**:
  - `programmatic` TR-3.1: 系统能够正确调用文件操作MCP工具的所有方法
  - `programmatic` TR-3.2: 文件操作MCP工具能够正确执行文件操作任务
- **注意事项**:
  - 确保文件操作MCP工具的参数提取和传递正确
  - 处理文件操作MCP工具的异步方法调用
  - 处理文件操作MCP工具的错误情况

### [x] 任务 4: 移除不存在工具的判断
- **优先级**: P1
- **依赖项**: None
- **描述**:
  - 检查并移除 `meta_router.py` 中对不存在工具的判断
  - 确保系统只对已注册的工具进行判断
- **成功标准**:
  - 系统中不存在对已删除工具的判断逻辑
  - 系统能够正确处理所有已注册的工具
- **测试要求**:
  - `programmatic` TR-4.1: 系统中不存在对不存在工具的判断
  - `programmatic` TR-4.2: 系统能够正确处理所有已注册的工具
- **注意事项**:
  - 确保移除所有对不存在工具的引用
  - 保持系统的稳定性和可靠性

### [/] 任务 5: 测试与验证
- **优先级**: P1
- **依赖项**: 任务 1, 任务 2, 任务 3, 任务 4
- **描述**:
  - 进行全面的测试，验证系统在各种文件操作场景下的表现
  - 测试文件操作MCP工具的调用和执行
  - 测试系统对不同类型任务的区分能力
- **成功标准**:
  - 系统能够正确处理各种文件操作任务
  - 系统能够正确区分文件操作任务和其他类型的任务
  - 系统能够正确处理不存在工具的情况
- **测试要求**:
  - `programmatic` TR-5.1: 系统能够正确处理至少15个不同类型的文件操作任务
  - `programmatic` TR-5.2: 系统能够正确处理至少15个不同类型的非文件操作任务
  - `human-judgement` TR-5.3: 系统的决策逻辑清晰合理
- **注意事项**:
  - 测试覆盖各种文件操作场景
  - 测试系统的边界情况
  - 确保系统的稳定性和可靠性

## 3. 技术实现细节

### 3.1 注册文件操作MCP工具

在 `src/core/resource_registry.py` 中的 `create_default_registry` 函数中添加文件操作MCP工具的注册：

```python
# 注册文件操作MCP工具
try:
    from src.skills.mcp_skills.file_operations_mcp import file_operations_mcp
    
    # 注册文件读取工具
    registry.register(
        name="read_file",
        description="读取文件内容，用于回答'读取文件'、'查看文件'等文件读取相关问题",
        tool_func=file_operations_mcp.read_file,
        examples=["读取文件 D:\\test.txt", "查看文件内容", "读取文件内容"]
    )
    
    # 注册文件创建工具
    registry.register(
        name="create_file",
        description="创建文件，用于回答'创建文件'、'写入文件'等文件创建相关问题",
        tool_func=file_operations_mcp.create_file,
        examples=["创建文件 D:\\test.txt", "写入文件内容", "创建新文件"]
    )
    
    # 注册文件搜索工具
    registry.register(
        name="search_files",
        description="搜索文件，用于回答'搜索文件'、'查找文件'等文件搜索相关问题",
        tool_func=file_operations_mcp.search_files,
        examples=["搜索文件", "查找文件", "搜索包含关键词的文件"]
    )
    
    # 注册文件改写工具
    registry.register(
        name="rewrite_file",
        description="改写文件内容，用于回答'修改文件'、'编辑文件'等文件改写相关问题",
        tool_func=file_operations_mcp.rewrite_file,
        examples=["修改文件", "编辑文件内容", "改写文件"]
    )
except Exception as e:
    print(f"注册文件操作MCP工具失败: {str(e)}")
```

### 3.2 增强元认知路由器的决策逻辑

在 `src/core/meta_router.py` 中的 `decide` 方法中添加文件操作相关任务的识别逻辑：

```python
# 具体决策规则：
# ... 现有规则 ...

# 文件操作相关规则
15. 对于文件读取相关问题（如"读取文件"、"查看文件"等），请选择 "read_file" 资源
16. 对于文件创建相关问题（如"创建文件"、"写入文件"等），请选择 "create_file" 资源
17. 对于文件搜索相关问题（如"搜索文件"、"查找文件"等），请选择 "search_files" 资源
18. 对于文件改写相关问题（如"修改文件"、"编辑文件"等），请选择 "rewrite_file" 资源
```

### 3.3 实现文件操作MCP工具的调用逻辑

在 `src/core/meta_router.py` 中的 `execute_decision` 方法中添加文件操作MCP工具的调用逻辑：

```python
# 处理文件操作MCP工具
elif selected_resource == "read_file":
    # 提取文件路径
    import re
    match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
    if match:
        file_path = match.group(0)
        result = tool_func(file_path)
    else:
        result = "请提供具体的文件路径"
elif selected_resource == "create_file":
    # 提取文件路径和内容
    import re
    path_match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
    content_match = re.search(r'内容[:：]\s*(.*)', user_input)
    if path_match:
        file_path = path_match.group(0)
        content = content_match.group(1) if content_match else ""
        result = tool_func(file_path, content)
    else:
        result = "请提供具体的文件路径"
elif selected_resource == "search_files":
    # 提取搜索目录和关键词
    import re
    dir_match = re.search(r'目录[:：]\s*([\\w\\s\\\\]+)', user_input)
    keyword_match = re.search(r'关键词[:：]\s*(.*)', user_input)
    directory = dir_match.group(1) if dir_match else "."
    content_keyword = keyword_match.group(1) if keyword_match else None
    result = tool_func(directory, content_keyword=content_keyword)
elif selected_resource == "rewrite_file":
    # 提取文件路径和新内容
    import re
    path_match = re.search(r'[a-zA-Z]:\\[\\w\\s.]+', user_input)
    content_match = re.search(r'内容[:：]\s*(.*)', user_input)
    if path_match:
        file_path = path_match.group(0)
        new_content = content_match.group(1) if content_match else ""
        result = tool_func(file_path, new_content)
    else:
        result = "请提供具体的文件路径"
```

### 3.4 移除不存在工具的判断

检查 `src/core/meta_router.py` 中的 `execute_decision` 方法，移除对不存在工具的判断，确保系统只对已注册的工具进行判断。

## 4. 测试计划

### 4.1 测试用例

1. **文件操作任务测试**:
   - 测试文件读取任务
   - 测试文件创建任务
   - 测试文件搜索任务
   - 测试文件改写任务

2. **非文件操作任务测试**:
   - 测试时间日期任务
   - 测试数学计算任务
   - 测试闲聊任务
   - 测试其他类型的任务

3. **边界情况测试**:
   - 测试不存在的文件路径
   - 测试权限不足的情况
   - 测试无效的文件操作参数

### 4.2 测试方法

1. **自动化测试**:
   - 编写测试脚本，自动测试系统的文件操作任务处理能力
   - 验证系统能够正确识别和处理文件操作任务

2. **人工测试**:
   - 手动测试系统在各种文件操作场景下的表现
   - 评估系统的决策逻辑和用户体验

## 5. 预期效果

通过本计划的实施，系统将：

1. 能够正确识别和处理文件操作相关任务
2. 能够自动调用文件操作MCP工具执行文件操作任务
3. 能够正确区分文件操作任务和其他类型的任务
4. 能够处理不存在工具的情况，保持系统的稳定性
5. 提供良好的用户体验，确保文件操作任务的执行结果准确可靠

## 6. 风险评估

1. **文件操作安全风险**:
   - 可能存在文件操作权限和路径安全问题
   - 应对措施：使用文件操作MCP工具的路径白名单机制，确保只允许操作安全的路径

2. **参数提取风险**:
   - 可能无法正确提取文件操作的参数
   - 应对措施：优化参数提取逻辑，确保能够正确提取各种格式的文件路径和内容

3. **兼容性风险**:
   - 可能与现有系统产生兼容性问题
   - 应对措施：保持与现有决策逻辑的一致性，确保系统的稳定性

4. **错误处理风险**:
   - 可能无法正确处理文件操作的错误情况
   - 应对措施：完善错误处理机制，确保系统能够优雅处理各种错误情况

## 7. 总结

本计划通过将文件操作MCP工具整合到现有的判断逻辑体系中，提升了系统的文件操作能力。通过注册文件操作MCP工具、增强元认知路由器的决策逻辑、实现文件操作MCP工具的调用逻辑、移除不存在工具的判断，系统将能够正确识别和处理文件操作相关任务，为用户提供更加全面和强大的功能。

通过本计划的实施，系统将在保持现有功能的基础上，增加文件操作能力，提升系统的实用性和用户体验。