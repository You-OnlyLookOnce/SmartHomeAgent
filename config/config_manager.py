import json
import os

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.configs = {}
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'modules')
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                config_path = os.path.join(self.config_dir, filename)
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.configs.update(config)
    
    def get_config(self, key, default=None):
        """获取配置"""
        keys = key.split('.')
        value = self.configs
        
        for k in keys:
            if k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_qiniu_config(self):
        """获取七牛云配置"""
        return self.get_config('qiniu', {})
    
    def get_device_config(self):
        """获取设备配置"""
        return self.get_config('device', {})
    
    def get_model_config(self):
        """获取模型配置"""
        return self.get_config('model', {})

# 全局配置管理器实例
config_manager = ConfigManager()
