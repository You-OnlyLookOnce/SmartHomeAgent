# 智能家居智能体新手使用指南

## 快速开始

### 1. 环境搭建

1. **安装Python 3.11**
   - 从[Python官网](https://www.python.org/downloads/)下载并安装Python 3.11
   - 确保勾选"Add Python to PATH"

2. **创建虚拟环境**
   ```bash
   # 在项目根目录执行
   python -m venv venv
   
   # 激活虚拟环境
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置API密钥**
   - 在项目根目录创建 `.env` 文件
   - 添加以下配置（替换为实际的API密钥）：
   ```env
   # 七牛云API密钥
   QINIU_ACCESS_KEY=your_access_key
   QINIU_SECRET_KEY=your_secret_key
   
   # 其他配置
   SECRET_KEY=your_secret_key_for_encryption
   ```

### 2. 启动服务

```bash
# 启动API网关
python app.py

# 服务将在 http://localhost:8005 运行
```

### 3. 访问前端

在浏览器中打开：
```
http://localhost:8005/
```

## 基本功能使用

### 1. 设备控制

**示例命令**：
- "打开客厅灯"
- "关闭卧室灯"
- "调整厨房灯亮度为50%"
- "打开客厅风扇"

### 2. 任务管理

**示例命令**：
- "明天早上8点提醒我开会"
- "安排下周三天的购物任务"
- "发送通知给家人"

### 3. AI笔记

**示例命令**：
- "记笔记：今天买了牛奶"
- "查看我之前的笔记"
- "搜索关于购物的笔记"

### 4. 记忆管理

**示例命令**：
- "查看我的人格设置"
- "编辑我的记忆"
- "执行记忆蒸馏"

### 5. 安全监控

**示例命令**：
- "检查家里的安全状态"
- "开始监控"
- "发送安全告警"

## 常见问题

### 1. 服务启动失败
- 检查端口是否被占用（默认8005）
- 检查依赖是否安装正确
- 检查API密钥配置是否正确

### 2. 设备控制无响应
- 检查设备是否在线
- 检查设备ID是否正确
- 检查网络连接

### 3. 前端页面无法访问
- 检查后端服务是否启动
- 检查浏览器缓存
- 检查网络连接

### 4. 智能体不响应
- 检查API密钥是否有效
- 检查网络连接是否正常
- 检查七牛云服务是否可用

## 进阶功能

### 1. 添加新设备
1. 在 `src/tools/mcp_tools/device_control_tool.py` 中添加设备控制逻辑
2. 重启服务

### 2. 自定义智能体人格
1. 编辑 `YUEYUE/` 目录下的人格文件
2. 重启服务

### 3. 扩展功能
1. 在 `src/tools/mcp_tools/` 目录下创建新的工具模块
2. 在 `src/core/mcp_tool_registry.py` 中注册新工具
3. 重启服务

## 技术支持

如有问题，请参考：
- [架构文档](ARCHITECTURE_V2.md)
- 项目README.md
- 七牛云API文档

---

**智能家居智能体 - 让生活更智能，更便捷！** 🚀