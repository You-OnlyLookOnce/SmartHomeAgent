# 联网搜索功能深度排查计划

## [x] Task 1: 检查搜索判断逻辑触发
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查 `search_judgment.is_search_needed()` 函数是否正确触发
  - 验证日期相关查询是否被正确识别为需要搜索的查询
  - 检查日志输出，确认判断过程
- **Success Criteria**: 
  - 搜索判断函数能够正确识别日期相关查询
  - 日志中能够看到搜索判断的详细过程
  - 对于"今天是几号"等查询，返回 True
- **Test Requirements**:
  - `programmatic` TR-1.1: 测试 `is_search_needed()` 函数对日期查询的判断
  - `programmatic` TR-1.2: 检查日志输出是否包含搜索判断信息
  - `human-judgement` TR-1.3: 验证判断逻辑的正确性
- **Notes**: 重点测试"今天是几号"、"明天天气怎么样"等常见查询

## [x] Task 2: 检查API网关执行流程
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 检查 API 网关在接收到需要搜索的查询时是否正确执行搜索流程
  - 验证搜索执行逻辑是否被调用
  - 检查日志输出，确认搜索执行过程
- **Success Criteria**: 
  - API 网关能够正确识别需要搜索的查询
  - 搜索执行逻辑被正确调用
  - 日志中能够看到搜索执行的详细过程
- **Test Requirements**:
  - `programmatic` TR-2.1: 测试 API 网关的搜索执行流程
  - `programmatic` TR-2.2: 检查日志输出是否包含搜索执行信息
  - `human-judgement` TR-2.3: 验证执行流程的正确性
- **Notes**: 重点检查 `api_gateway.py` 中的搜索执行逻辑

## [x] Task 3: 检查模型配置
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查模型配置是否正确
  - 验证是否使用了正确的模型
  - 检查 API 密钥配置是否正确
- **Success Criteria**: 
  - 模型配置正确，使用预期的模型
  - API 密钥配置正确
  - 模型能够正常调用
- **Test Requirements**:
  - `programmatic` TR-3.1: 检查模型配置文件
  - `programmatic` TR-3.2: 验证 API 密钥配置
  - `human-judgement` TR-3.3: 确认模型调用正常
- **Notes**: 从日志中看到使用的是 kimi-k2.5 模型，需要确认是否正确

## [x] Task 4: 检查搜索API调用
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 检查 `web_search.execute()` 函数是否正确调用
  - 验证搜索 API 调用参数是否正确
  - 检查搜索 API 响应是否正常
- **Success Criteria**: 
  - 搜索 API 能够正确调用
  - 搜索参数设置正确
  - 能够获取到有效的搜索结果
- **Test Requirements**:
  - `programmatic` TR-4.1: 测试 `web_search.execute()` 函数
  - `programmatic` TR-4.2: 检查搜索 API 调用参数
  - `human-judgement` TR-4.3: 验证搜索结果的有效性
- **Notes**: 重点检查七牛云 Web Search API 的调用

## [x] Task 5: 检查前端状态提示
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 检查前端是否正确显示"正在联网搜索"状态
  - 验证前端是否能够正确处理搜索结果
- **Success Criteria**: 
  - 前端能够正确显示搜索状态
  - 能够正确处理和显示搜索结果
- **Test Requirements**:
  - `human-judgement` TR-5.1: 测试前端状态显示
  - `human-judgement` TR-5.2: 验证搜索结果显示
- **Notes**: 重点测试前端对搜索状态的处理

## [x] Task 6: 端到端测试
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3, Task 4
- **Description**: 
  - 进行端到端测试，验证整个搜索流程
  - 测试各种搜索场景
  - 验证搜索结果的准确性和及时性
- **Success Criteria**: 
  - 端到端流程能够正常工作
  - 搜索结果准确反映实时信息
  - 前端能够正确显示搜索状态和结果
- **Test Requirements**:
  - `programmatic` TR-6.1: 测试完整的搜索流程
  - `human-judgement` TR-6.2: 评估搜索结果质量
  - `human-judgement` TR-6.3: 验证前端用户体验
- **Notes**: 重点测试日期查询、天气查询等常见场景