from src.gateway.api_gateway import APIGateway

# 创建API网关实例
gateway = APIGateway()

# 导出FastAPI应用实例
app = gateway.app

if __name__ == "__main__":
    # 启动API服务器
    gateway.run(host="0.0.0.0", port=8000)