# 对话历史持久化问题分析 - 产品需求文档

## Overview
- **Summary**: 分析并修复前端与后端交互中导致对话历史未能正确写入JSON文件的问题，确保每次新对话生成后，相关内容能被完整、准确地追加到指定的JSON文件中。
- **Purpose**: 解决对话历史数据持久化失败的问题，确保用户与AI的对话内容能够可靠存储，避免刷新页面或切换窗口后对话内容丢失。
- **Target Users**: 使用智能家居智能体系统的用户，需要能够保存和查看历史对话记录。

## Goals
- 定位对话历史数据写入失败的具体原因
- 修复数据持久化问题，确保对话历史能够正确保存到JSON文件
- 验证修复后在多场景下的可靠性

## Non-Goals (Out of Scope)
- 重构整个会话管理系统
- 更改数据存储格式（仍然使用JSON文件）
- 增加新的对话功能

## Background & Context
- 系统使用独立会话管理器（IndependentSessionManager）来管理对话历史
- 对话历史存储在项目内部的data/conversations/sessions目录下的JSON文件中
- 前端通过API与后端交互，获取和更新对话历史
- 后端在流式响应结束后更新对话历史并保存到文件

## Functional Requirements
- **FR-1**: 确保每次新对话生成后，用户消息和AI回复能够正确追加到对话历史JSON文件中
- **FR-2**: 确保JSON文件格式的完整性和数据的一致性
- **FR-3**: 确保在网络中断恢复后，对话历史仍然能够正确保存
- **FR-4**: 确保在输入特殊字符时，对话历史仍然能够正确保存

## Non-Functional Requirements
- **NFR-1**: 数据持久化操作应该在1秒内完成
- **NFR-2**: 错误处理机制应该能够捕获并记录所有可能的异常
- **NFR-3**: 系统应该能够处理并发的对话历史写入操作

## Constraints
- **Technical**: 使用Python 3.11，FastAPI框架，JSON文件存储
- **Business**: 修复应在不影响现有功能的前提下进行
- **Dependencies**: 依赖于文件系统权限和JSON库的正常工作

## Assumptions
- 服务器具有写入JSON文件的权限
- 网络连接正常
- 用户输入的内容符合JSON格式要求

## Acceptance Criteria

### AC-1: 正常对话流程
- **Given**: 用户在前端发送一条消息，AI生成回复
- **When**: 流式响应结束后
- **Then**: 对话历史应该被正确保存到JSON文件中，刷新页面后对话内容仍然可见
- **Verification**: `programmatic`
- **Notes**: 检查JSON文件内容是否包含新的对话记录

### AC-2: 特殊字符输入
- **Given**: 用户在前端发送包含特殊字符的消息，如引号、反斜杠等
- **When**: 流式响应结束后
- **Then**: 对话历史应该被正确保存到JSON文件中，特殊字符应该被正确转义
- **Verification**: `programmatic`
- **Notes**: 检查JSON文件是否包含正确转义的特殊字符

### AC-3: 网络中断恢复
- **Given**: 用户在前端发送消息，网络临时中断后恢复
- **When**: 网络恢复后，流式响应继续
- **Then**: 对话历史应该被正确保存到JSON文件中
- **Verification**: `human-judgment`
- **Notes**: 模拟网络中断场景，检查对话历史是否仍然能够保存

### AC-4: 多次连续对话
- **Given**: 用户在前端连续发送多条消息，AI生成多条回复
- **When**: 每次流式响应结束后
- **Then**: 所有对话历史应该被正确保存到JSON文件中，顺序应该正确
- **Verification**: `programmatic`
- **Notes**: 检查JSON文件是否包含所有对话记录，顺序是否正确

## Open Questions
- [ ] 前端与后端的会话ID传递是否正确？
- [ ] JSON文件写入权限是否足够？
- [ ] 流式响应结束后，后端是否正确调用了update_conversation_history方法？
- [ ] 前端是否正确处理了会话ID的更新？