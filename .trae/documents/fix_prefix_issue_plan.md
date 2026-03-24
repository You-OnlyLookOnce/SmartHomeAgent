# 修复智能体回复前缀问题 - 实现计划

## [x] Task 1: 定位并修复人格表达优化器中的前缀添加逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查persona_expression_optimizer.py文件中的optimize_expression方法
  - 移除自动添加"悦悦"前缀的逻辑
  - 确保其他人格优化功能不受影响
- **Success Criteria**:
  - 智能体回复内容前不再出现"悦悦"前缀
  - 其他人格优化功能（如emoji添加、情感表达等）仍然正常工作
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证修复后智能体回复中不包含"悦悦"前缀
  - `human-judgment` TR-1.2: 验证其他人格优化功能仍然正常工作
- **Notes**: 重点修改optimize_expression方法中第176-178行的代码

## [x] Task 2: 重启服务并验证修复效果
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 重启API服务器
  - 进行多轮不同场景的对话测试
  - 验证智能体回复中不再出现"悦悦"前缀
  - 验证智能体的正常功能不受影响
- **Success Criteria**:
  - 服务器重启成功
  - 智能体回复内容前不再出现"悦悦"前缀
  - 智能体的正常功能（如问答、指令执行等）不受影响
- **Test Requirements**:
  - `human-judgment` TR-2.1: 验证服务器重启成功
  - `human-judgment` TR-2.2: 验证智能体回复中不包含"悦悦"前缀
  - `human-judgment` TR-2.3: 验证智能体的正常功能不受影响
- **Notes**: 测试不同类型的对话，包括问答、指令和日常聊天

## [x] Task 3: 进行全面的功能测试
- **Priority**: P1
- **Depends On**: Task 2
- **Description**:
  - 测试智能体的各种功能，确保修复没有引入新问题
  - 测试备忘录模块的功能
  - 测试设备控制功能
  - 测试任务管理功能
- **Success Criteria**:
  - 所有功能都能正常工作
  - 修复没有引入新问题
- **Test Requirements**:
  - `human-judgment` TR-3.1: 验证智能体的所有功能都能正常工作
  - `human-judgment` TR-3.2: 验证备忘录模块的功能正常
  - `human-judgment` TR-3.3: 验证设备控制功能正常
  - `human-judgment` TR-3.4: 验证任务管理功能正常
- **Notes**: 确保所有功能都能正常工作，问题不会复现