# 大模型连接问题排查 - 产品需求文档

## Overview
- **Summary**: 针对用户提问后系统无响应的问题进行全面排查，确保系统正确调用大模型而非运行虚拟演示模式。
- **Purpose**: 解决用户与智能助手对话时无响应的问题，恢复正常的大模型调用功能。
- **Target Users**: 使用智能家庭助手的用户，以及系统维护人员。

## Goals
- 验证 API 密钥配置是否正确
- 检查前后端交互流程是否正常
- 验证大模型调用是否成功
- 分析日志定位问题根源
- 确认系统运行模式并修复问题

## Non-Goals (Out of Scope)
- 优化大模型性能或响应速度
- 开发新功能或界面改进
- 修改系统架构或技术栈

## Background & Context
- 系统使用七牛云大模型 API 提供智能对话功能
- 目前用户提问后系统返回"抱歉，我暂时无法处理你的请求"的错误信息
- 系统可能运行在演示模式或存在配置问题

## Functional Requirements
- **FR-1**: 验证 API 密钥配置的正确性
- **FR-2**: 检查前后端交互流程的完整性
- **FR-3**: 验证大模型调用的有效性
- **FR-4**: 分析日志定位问题根源
- **FR-5**: 确认系统运行模式并修复问题

## Non-Functional Requirements
- **NFR-1**: 系统应能正确调用大模型 API
- **NFR-2**: 排查过程应记录详细日志
- **NFR-3**: 修复方案应不影响其他系统功能

## Constraints
- **Technical**: 依赖七牛云大模型 API
- **Business**: 需要保持系统稳定性
- **Dependencies**: 七牛云 API 服务可用性

## Assumptions
- 系统已正确部署并运行
- 网络连接正常
- 七牛云 API 服务正常

## Acceptance Criteria

### AC-1: API 密钥配置验证
- **Given**: 系统已配置 AK 和 SK
- **When**: 检查配置文件和环境变量
- **Then**: 确认 AK 和 SK 正确设置且具有有效权限
- **Verification**: `programmatic`

### AC-2: 前后端交互验证
- **Given**: 用户发送提问
- **When**: 检查网络请求和响应
- **Then**: 确认前端请求成功到达后端，后端正确处理并返回响应
- **Verification**: `programmatic`

### AC-3: 大模型调用验证
- **Given**: 后端接收到用户请求
- **When**: 检查大模型 API 调用
- **Then**: 确认 API 调用成功，参数格式正确，无频率限制或配额问题
- **Verification**: `programmatic`

### AC-4: 日志分析验证
- **Given**: 系统运行中
- **When**: 分析前后端及大模型调用日志
- **Then**: 定位请求处理过程中的异常点或错误信息
- **Verification**: `human-judgment`

### AC-5: 功能模式确认
- **Given**: 系统运行中
- **When**: 检查系统配置
- **Then**: 确认系统运行在正式环境而非演示/测试模式
- **Verification**: `programmatic`

### AC-6: 功能恢复验证
- **Given**: 问题已修复
- **When**: 用户发送提问
- **Then**: 系统正确调用大模型并返回有效响应
- **Verification**: `programmatic`

## Open Questions
- [ ] AK 和 SK 是否具有调用大模型 API 的权限？
- [ ] 系统是否存在演示模式的配置开关？
- [ ] 大模型 API 是否有调用频率限制？
- [ ] 网络连接是否稳定？