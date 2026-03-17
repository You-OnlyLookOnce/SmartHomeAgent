# 配置系统使用说明

## 配置文件结构

本项目使用模块化的配置系统，将不同模块的配置分为不同的JSON文件存储在 `config/modules/` 目录中：

```
config/
├── modules/
│   ├── qiniu_config.json     # 七牛云API配置
│   ├── device_config.json     # 设备控制配置
│   └── model_config.json      # 模型配置
├── config_manager.py          # 配置管理器
└── README.md                  # 本说明文件
```

## 填写七牛云API密钥

七牛云API密钥需要在 `config/modules/qiniu_config.json` 文件中填写：

```json
{
  "qiniu": {
    "access_key": "你的七牛云Access Key",
    "secret_key": "你的七牛云Secret Key",
    "bucket_name": "你的存储空间名称",
    "domain": "你的域名"
  }
}
```

### 获取七牛云API密钥的步骤：

1. 登录七牛云控制台 (https://portal.qiniu.com/)
2. 进入 "个人中心" -> "密钥管理"
3. 复制 "Access Key" 和 "Secret Key"
4. 将复制的密钥粘贴到 `qiniu_config.json` 文件中对应的字段
5. 保存文件

## 其他配置文件说明

### 设备配置 (`device_config.json`)

```json
{
  "device": {
    "led": {
      "default_brightness": 100,  // 默认亮度
      "max_brightness": 100,      // 最大亮度
      "min_brightness": 0         // 最小亮度
    },
    "supported_devices": [         // 支持的设备类型
      "led"
    ]
  }
}
```

### 模型配置 (`model_config.json`)

```json
{
  "model": {
    "decision": {                  // 决策层模型配置
      "provider": "qiniu",
      "name": "qwen-max",
      "temperature": 0.7,
      "max_tokens": 2048
    },
    "expert": {                    // 执行层模型配置
      "provider": "qiniu",
      "name": "qwen-turbo",
      "temperature": 0.7,
      "max_tokens": 1024
    }
  }
}
```

## 在代码中使用配置

### 方法一：通过配置管理器获取

```python
from config.config_manager import config_manager

# 获取七牛云配置
qiniu_config = config_manager.get_qiniu_config()
access_key = qiniu_config.get('access_key')

# 获取设备配置
device_config = config_manager.get_device_config()

# 获取模型配置
model_config = config_manager.get_model_config()

# 获取具体配置项
decision_model = config_manager.get_config('model.decision.name')
```

### 方法二：通过核心配置模块获取

```python
from src.config.config import MODEL_DECISION_PROVIDER, MODEL_DECISION_NAME

# 使用配置
print(f"决策层模型: {MODEL_DECISION_PROVIDER}/{MODEL_DECISION_NAME}")
```

## 注意事项

1. 配置文件中的敏感信息（如API密钥）不要提交到版本控制系统
2. 确保配置文件格式正确，使用有效的JSON格式
3. 如果添加新的配置文件，确保它遵循相同的模块化结构
4. 配置文件修改后，需要重启应用才能生效
