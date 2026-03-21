import os
import shutil

# 项目根目录
PROJECT_ROOT = "d:\\PythonProject\\Home-AI-Agent"

# 读取未引用的文件列表
def read_unused_files():
    with open("unused_files.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# 读取空文件夹列表
def read_empty_folders():
    with open("empty_folders.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# 执行清理操作
def main():
    print("Starting cleanup operation...")
    
    # 1. 移除未引用的文件
    unused_files = read_unused_files()
    print(f"Removing {len(unused_files)} unused files...")
    for file_path in unused_files:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # 2. 移除空文件夹
    empty_folders = read_empty_folders()
    print(f"\nRemoving {len(empty_folders)} empty folders...")
    for folder_path in empty_folders:
        full_path = os.path.join(PROJECT_ROOT, folder_path)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            try:
                shutil.rmtree(full_path)
                print(f"Removed: {folder_path}")
            except Exception as e:
                print(f"Error removing {folder_path}: {e}")
    
    # 3. 移除冗余配置文件
    redundant_configs = [
        "config\modules\qiniu_config.json",
        "config\config_manager.py"
    ]
    print(f"\nRemoving {len(redundant_configs)} redundant configuration files...")
    for config_path in redundant_configs:
        full_path = os.path.join(PROJECT_ROOT, config_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Removed: {config_path}")
            except Exception as e:
                print(f"Error removing {config_path}: {e}")
    
    print("\nCleanup operation completed!")

if __name__ == "__main__":
    main()