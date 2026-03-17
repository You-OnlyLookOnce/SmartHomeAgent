# 核心参数配置

# 导入配置管理器
from config.config_manager import config_manager

# 硬件配置
HARDWARE_UART_BAUDRATE = 115200
HARDWARE_LED_PIN = "GPIO_Pin_13"
HARDWARE_STM32_FREQ = 72000000

# 模型配置
model_config = config_manager.get_model_config()
MODEL_DECISION_PROVIDER = model_config.get("decision", {}).get("provider", "qiniu")
MODEL_DECISION_NAME = model_config.get("decision", {}).get("name", "qwen-max")
MODEL_EXPERT_PROVIDER = model_config.get("expert", {}).get("provider", "qiniu")
MODEL_EXPERT_NAME = model_config.get("expert", {}).get("name", "qwen-turbo")
MODEL_TEMPERATURE = model_config.get("decision", {}).get("temperature", 0.7)
MODEL_MAX_TOKENS = model_config.get("decision", {}).get("max_tokens", 2048)

# Agent配置
AGENT_MAX_CONTEXT = 10
AGENT_TIMEOUT_SECONDS = 30
AGENT_RETRY_COUNT = 3

# 检索配置
LANCEDB_DIMENSION = 1536
HYBRID_SEARCH_TOP_K = 5
MEMORY_DISTRILL_INTERVAL = "02:00"  # 每日凌晨2点

# 前端配置
UI_THEME_COLOR = "#FFF5E6"  # 晨光色
UI_THEME_WARMTH = 0.85

# 系统配置
HEALTH_CHECK_INTERVAL = 30  # 健康检查间隔（秒）
MAX_RESTART_ATTEMPTS = 3  # 最大重启尝试次数
SELF_HEALING_ENABLED = True  # 自修复功能

# 路径配置
DATA_DIR = "data"
LANCEDB_PATH = "data/lancedb"
LOG_DIR = "data/logs"
