import os
import subprocess
import sys
import argparse
from src.gateway.api_gateway import APIGateway

# 解析命令行参数
parser = argparse.ArgumentParser(description='启动智能家居智能体API服务器')
parser.add_argument('--port', type=int, default=8005, help='服务器端口')
args = parser.parse_args()

# 检查并释放端口
port = args.port

def check_and_release_port(port):
    """检查端口是否被占用，并尝试释放"""
    try:
        # 使用netstat命令查找占用端口的进程
        if sys.platform == 'win32':
            # Windows系统
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"发现端口 {port} 被占用，尝试释放...")
                # 解析输出，获取PID
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[4]
                            print(f"终止占用端口 {port} 的进程 PID: {pid}")
                            try:
                                subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                                print(f"进程 {pid} 已终止")
                            except Exception as e:
                                print(f"终止进程失败: {e}")
        else:
            # 其他系统（Linux/Mac）
            cmd = f'lsof -i :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"发现端口 {port} 被占用，尝试释放...")
                # 解析输出，获取PID
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过表头
                    if line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            print(f"终止占用端口 {port} 的进程 PID: {pid}")
                            try:
                                subprocess.run(f'kill -9 {pid}', shell=True, capture_output=True)
                                print(f"进程 {pid} 已终止")
                            except Exception as e:
                                print(f"终止进程失败: {e}")
    except Exception as e:
        print(f"检查端口时出错: {e}")

# 检查并释放端口
check_and_release_port(port)

# 创建API网关实例
gateway = APIGateway()

# 导出FastAPI应用实例
app = gateway.app

if __name__ == "__main__":
    # 启动API服务器
    url = f"http://localhost:{port}"
    print(f"启动服务在 {url}...")
    print(f"请点击以下链接进入网页: {url}")
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 使用uvicorn启动FastAPI应用
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=port, reload=False)