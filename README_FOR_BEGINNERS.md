# 智能家居助手 - 小白操作指南

## 项目简介

这是一个智能家居助手系统，你可以通过它控制家里的智能设备，管理任务，和AI助手聊天。即使你是代码零基础，也能轻松上手！

## 所需工具

1. **电脑**：Windows、Mac或Linux系统都可以
2. **网络连接**：需要连接互联网
3. **Python**：需要安装Python 3.11或更高版本

## 第一步：安装Python

如果你还没有安装Python，请按照以下步骤操作：

### Windows用户
1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击"Download Python 3.11.x"按钮（x是版本号，如3.11.9）
3. 下载完成后，双击安装文件
4. **重要**：在安装界面勾选"Add Python to PATH"选项
5. 点击"Install Now"完成安装
6. 安装完成后，关闭安装窗口

### Mac用户
1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击"Download Python 3.11.x"按钮
3. 下载完成后，双击安装文件
4. 按照提示完成安装

### 验证Python安装
1. 打开命令提示符（Windows）或终端（Mac/Linux）
2. 输入 `python --version` 并按Enter键
3. 如果看到类似 "Python 3.11.x" 的输出，说明安装成功

## 第二步：下载项目文件

1. 下载项目压缩包到你的电脑
2. 右键点击压缩包，选择"解压到当前文件夹"
3. 记住解压后的文件夹位置（比如桌面）

## 第三步：安装依赖

1. 打开命令提示符（Windows）或终端（Mac/Linux）
2. 导航到项目文件夹（比如解压到桌面，输入 `cd Desktop/Home-AI-Agent`）
3. 输入以下命令并按Enter键：
   ```
   conda create -n Home_Agent python=3.11
   ```
4. 激活虚拟环境：
   - Windows：输入 `conda activate Home_Agent`
   - Mac/Linux：输入 `conda activate Home_Agent`
5. 安装依赖：输入 `pip install -r requirements.txt`
6. 等待安装完成（可能需要几分钟）

## 第四步：配置API密钥

1. 在项目文件夹中找到 `.env` 文件
2. 用记事本打开它
3. 填写七牛云API密钥：
   ```
   # 七牛云API密钥
   QINIU_ACCESS_KEY=你的访问密钥
   QINIU_SECRET_KEY=你的 secret 密钥
   
   # 其他配置
   SECRET_KEY=随便写一些字符
   ```
4. 保存并关闭文件

## 第五步：启动服务

1. 在命令提示符或终端中，确保虚拟环境已激活（前面有 `(Home_Agent)` 字样）
2. 输入 `python app.py` 并按Enter键
3. 看到类似 "Uvicorn running on http://0.0.0.0:8000" 的消息，说明服务启动成功
4. 不要关闭这个窗口！

## 第六步：打开网页界面

1. 打开浏览器（Chrome、Edge、Firefox等）
2. 在地址栏输入 `http://localhost:8000` 并按Enter键
3. 你应该能看到智能家居助手的界面了！

## 如何使用

### 与AI助手聊天
1. 在聊天输入框中输入你想说的话，比如"你好"
2. 点击"发送"按钮或按Enter键
3. 等待AI助手的回复

### 控制设备
1. 在设备控制面板中，你可以看到"客厅灯"
2. 点击"开"按钮打开灯
3. 点击"关"按钮关闭灯
4. 拖动滑块调节灯光亮度

## 常见问题及解决方法

### 问题1：命令提示符显示"python不是内部或外部命令"
- 解决方法：重新安装Python，确保勾选了"Add Python to PATH"

### 问题2：安装依赖时出错
- 解决方法：确保网络连接正常，重试命令

### 问题3：服务启动后浏览器无法访问
- 解决方法：检查服务是否正在运行，地址是否正确输入

### 问题4：API密钥配置错误
- 解决方法：确保正确填写了七牛云的API密钥

## 停止服务

当你想停止服务时：
1. 回到启动服务的命令提示符或终端窗口
2. 按 `Ctrl+C` 组合键
3. 服务会停止运行

## 联系我们

如果遇到问题，可以联系项目维护者寻求帮助。

---

**智能家居助手 - 让生活更智能，更便捷！** 🚀