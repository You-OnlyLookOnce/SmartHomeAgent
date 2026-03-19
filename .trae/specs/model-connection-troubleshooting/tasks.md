# 大模型连接问题排查 - 实施计划

## [x] Task 1: 验证 API 密钥配置
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 检查 .env 文件中的 AK 和 SK 配置
  - 验证密钥格式是否正确
  - 确认密钥是否具有调用大模型 API 的权限
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: 检查 .env 文件中 QINIU_ACCESS_KEY 和 QINIU_SECRET_KEY 是否存在且非空
  - `programmatic` TR-1.2: 验证密钥格式是否符合七牛云要求
- **Notes**: 确保密钥没有过期，且具有调用大模型 API 的权限

## [x] Task 2: 检查前端代码和交互流程
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 检查前端代码如何捕获用户输入并发送请求
  - 验证网络请求格式和目标地址
  - 确认前端是否正确处理响应
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 检查前端 JS 代码中的请求发送逻辑
  - `programmatic` TR-2.2: 验证网络请求是否成功发送到后端
- **Notes**: 使用浏览器开发者工具检查网络请求

## [x] Task 3: 检查后端 API 处理逻辑
- **Priority**: P0
- **Depends On**: Task 1, Task 2
- **Description**:
  - 检查后端 API 路由和处理函数
  - 验证请求参数解析和处理
  - 确认后端是否正确调用大模型服务
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 检查后端 API 路由配置
  - `programmatic` TR-3.2: 验证请求处理逻辑是否正确
- **Notes**: 检查 API 网关和路由配置

## [x] Task 4: 验证大模型调用实现
- **Priority**: P0
- **Depends On**: Task 3
- **Description**:
  - 检查 QiniuLLM 类的实现
  - 验证 API 调用参数和格式
  - 测试大模型 API 调用是否成功
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 检查 QiniuLLM 类的初始化和调用方法
  - `programmatic` TR-4.2: 验证 API 调用参数是否符合七牛云要求
- **Notes**: 检查 API URL、模型 ID 和请求格式

## [x] Task 5: 分析系统日志
- **Priority**: P1
- **Depends On**: Task 4
- **Description**:
  - 收集系统运行日志
  - 分析前后端交互和大模型调用日志
  - 定位错误信息和异常点
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `human-judgment` TR-5.1: 分析日志中的错误信息
  - `human-judgment` TR-5.2: 定位请求处理过程中的异常点
- **Notes**: 重点关注大模型 API 调用的错误信息

## [x] Task 6: 检查系统运行模式
- **Priority**: P1
- **Depends On**: Task 5
- **Description**:
  - 检查系统是否运行在演示模式
  - 验证相关配置开关
  - 确认系统环境设置
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-6.1: 检查系统配置文件中的模式设置
  - `programmatic` TR-6.2: 验证环境变量中的模式配置
- **Notes**: 查找可能存在的演示模式开关

## [x] Task 7: 实施修复措施
- **Priority**: P0
- **Depends On**: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6
- **Description**:
  - 根据排查结果实施修复
  - 验证修复效果
  - 确保系统正常运行
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic` TR-7.1: 验证系统是否能正确调用大模型
  - `programmatic` TR-7.2: 测试用户提问是否能得到有效响应
- **Notes**: 修复后进行全面测试