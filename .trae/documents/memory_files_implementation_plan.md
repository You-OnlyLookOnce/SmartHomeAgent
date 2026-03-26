# 记忆文件和人格文件前端展示实现计划

## 问题分析
- 前端代码中存在记忆管理功能，尝试调用 `/api/memory/soul` 和 `/api/memory/long-term` 端点
- 后端 API 网关中缺少这些端点的实现
- 人格文件 (`YUEYUE/Soul.md`) 已存在，但前端无法读取
- 记忆文件需要实现存储和读取功能

## 实现计划

### [x] 任务 1: 实现后端 API 端点
- **Priority**: P0
- **Depends On**: None
- **Description**: 在 `api_gateway.py` 中添加以下端点：
  - GET `/api/memory/soul` - 读取人格文件内容（只读）
  - GET `/api/memory/long-term` - 读取记忆文件内容
  - POST `/api/memory/long-term` - 保存记忆文件内容
- **Success Criteria**: 端点能够正确返回文件内容，人格文件无法通过 API 修改
- **Test Requirements**:
  - `programmatic` TR-1.1: GET `/api/memory/soul` 返回 200 状态码和文件内容
  - `programmatic` TR-1.2: GET `/api/memory/long-term` 返回 200 状态码和文件内容
  - `programmatic` TR-1.3: POST `/api/memory/long-term` 成功保存内容并返回 200 状态码
  - `programmatic` TR-1.4: POST `/api/memory/soul` 返回 403 状态码（禁止修改）
- **Notes**: 人格文件路径为 `YUEYUE/Soul.md`，记忆文件路径需要创建

### [x] 任务 2: 实现记忆文件存储功能
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**: 创建记忆文件存储机制，包括：
  - 定义记忆文件路径（建议 `data/memory/long_term_memory.md`）
  - 实现文件读写功能
  - 确保文件格式正确
- **Success Criteria**: 记忆文件能够被正确读取和保存
- **Test Requirements**:
  - `programmatic` TR-2.1: 记忆文件不存在时创建默认文件
  - `programmatic` TR-2.2: 记忆文件能够被正确写入和读取
- **Notes**: 记忆文件应该使用 Markdown 格式，与人格文件保持一致

### [x] 任务 3: 修改前端代码
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**: 修改前端代码，确保：
  - 人格文件内容显示为只读
  - 记忆文件内容可编辑
  - 保存按钮只对记忆文件有效
  - 加载和保存操作有适当的错误处理
- **Success Criteria**: 前端能够正确显示和编辑记忆文件，人格文件显示为只读
- **Test Requirements**:
  - `human-judgement` TR-3.1: 人格文件显示为只读状态，无法编辑
  - `human-judgement` TR-3.2: 记忆文件可以编辑并保存
  - `human-judgement` TR-3.3: 保存操作后显示成功提示
- **Notes**: 需要修改 `app.js` 中的相关函数

### [x] 任务 4: 测试和验证
- **Priority**: P2
- **Depends On**: 任务 1, 2, 3
- **Description**: 测试整个功能流程，包括：
  - 启动服务器
  - 访问记忆管理页面
  - 验证人格文件显示正确且只读
  - 验证记忆文件可以编辑和保存
  - 验证保存后内容持久化
- **Success Criteria**: 所有功能正常工作，前端能够正确显示和操作文件
- **Test Requirements**:
  - `human-judgement` TR-4.1: 前端页面加载后正确显示人格文件和记忆文件内容
  - `human-judgement` TR-4.2: 记忆文件编辑后保存成功，刷新页面后内容保持
  - `programmatic` TR-4.3: 所有 API 端点返回正确的状态码
- **Notes**: 确保测试过程中没有错误发生

## 预期成果
- 前端能够显示人格文件内容（只读）
- 前端能够显示和编辑记忆文件内容
- 记忆文件的修改能够持久化到后端
- 所有操作都有适当的错误处理和用户反馈