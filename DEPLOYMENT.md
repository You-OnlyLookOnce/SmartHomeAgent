# 智能家居智能体部署指南

## 系统要求

### 硬件要求
- 处理器: 至少 2 核 CPU
- 内存: 至少 4GB RAM
- 存储空间: 至少 10GB 可用空间

### 软件要求
- Python 3.11 或更高版本
- pip 包管理工具
- 操作系统: Windows 10/11, Linux, macOS

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/home-ai-agent.git
cd home-ai-agent
```

### 2. 创建conda虚拟环境

```bash
# 创建名为Home_Agent的conda虚拟环境，使用Python 3.10
conda create -n Home_Agent python=3.10

# 激活虚拟环境
conda activate Home_Agent
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置系统

#### 4.1 配置文件

编辑 `src/config/config.py` 文件，根据实际情况修改配置参数：

- 硬件配置：根据实际硬件设备修改
- 模型配置：设置七牛云API密钥和模型参数
- 路径配置：确保数据存储路径正确

#### 4.2 环境变量

设置以下环境变量：

```bash
# Windows
set QINIU_ACCESS_KEY=your_access_key
set QINIU_SECRET_KEY=your_secret_key

# Linux/macOS
export QINIU_ACCESS_KEY=your_access_key
export QINIU_SECRET_KEY=your_secret_key
```

## 运行系统

### 1. 启动后端服务

```bash
python main.py
```

### 2. 启动前端服务

```bash
# 使用内置的HTTP服务器
cd src/frontend
python -m http.server 8000
```

### 3. 访问系统

在浏览器中访问：`http://localhost:8000/templates/index.html`

## 目录结构

```
home-ai-agent/
├── src/
│   ├── agent/          # Agent核心模块
│   ├── skills/         # 技能系统
│   ├── config/         # 配置文件
│   ├── utils/          # 工具函数
│   └── frontend/       # 前端界面
├── data/              # 数据存储
├── test_*.py          # 测试脚本
├── main.py            # 主入口
└── DEPLOYMENT.md      # 部署指南
```

## 故障排除

### 1. 依赖安装失败

如果安装依赖时遇到问题，可以尝试：

```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 2. 端口占用

如果端口 8000 被占用，可以使用其他端口：

```bash
python -m http.server 8080
```

### 3. 模型调用失败

检查七牛云API密钥是否正确配置，网络连接是否正常。

### 4. 前端无法访问

检查前端服务是否正常运行，防火墙是否允许访问。

## 生产环境部署

### 1. 使用 Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### 2. 使用 Nginx 反向代理

配置 Nginx 作为反向代理，将请求转发到应用服务器。

### 3. 监控与日志

配置系统监控和日志系统，确保系统稳定运行。

## 升级系统

### 1. 拉取最新代码

```bash
git pull origin main
```

### 2. 更新依赖

```bash
pip install -r requirements.txt --upgrade
```

### 3. 重启服务

重启后端和前端服务，应用更新。

## 联系方式

如果遇到问题，请联系系统管理员或查看项目文档。
