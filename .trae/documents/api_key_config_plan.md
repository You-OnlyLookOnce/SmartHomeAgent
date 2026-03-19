# API密钥配置与大模型调用测试 - 实施计划

## [x] Task 1: 修改 .env 文件添加 API 密钥
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在 .env 文件中添加 QINIU_AI_API_KEY 环境变量
  - 设置为用户提供的 API 密钥
- **Success Criteria**:
  - .env 文件中正确配置了 QINIU_AI_API_KEY
  - 密钥值正确设置为用户提供的 API 密钥
- **Test Requirements**:
  - `programmatic` TR-1.1: 检查 .env 文件中 QINIU_AI_API_KEY 是否存在且非空
  - `programmatic` TR-1.2: 验证 QINIU_AI_API_KEY 的值是否正确
- **Notes**: 确保密钥格式正确，长度符合要求

## [x] Task 2: 重启服务
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 停止当前运行的服务
  - 启动服务以加载新的 API 密钥配置
- **Success Criteria**:
  - 服务成功启动
  - 日志显示 API 密钥已正确配置
- **Test Requirements**:
  - `programmatic` TR-2.1: 服务启动成功，无错误
  - `programmatic` TR-2.2: 日志显示 API 密钥配置状态
- **Notes**: 确保服务正常启动，没有端口冲突

## [x] Task 3: 测试大模型调用
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 发送测试请求到 /api/chat 接口
  - 验证是否能正确调用大模型并返回响应
- **Success Criteria**:
  - API 调用成功
  - 返回有效的大模型响应
  - 无认证错误
- **Test Requirements**:
  - `programmatic` TR-3.1: API 调用返回 200 状态码
  - `programmatic` TR-3.2: 响应包含大模型生成的文本
  - `human-judgment` TR-3.3: 响应内容符合预期，不是错误消息
- **Notes**: 测试时使用简单的问候语，如"你好"

## [x] Task 4: 验证系统状态
- **Priority**: P1
- **Depends On**: Task 3
- **Description**:
  - 检查系统日志
  - 确认大模型调用过程无错误
  - 验证系统是否正常运行
- **Success Criteria**:
  - 日志显示大模型调用成功
  - 系统运行正常
  - 无异常错误
- **Test Requirements**:
  - `programmatic` TR-4.1: 日志中无认证错误
  - `programmatic` TR-4.2: 系统运行状态正常
- **Notes**: 重点关注大模型调用的日志信息