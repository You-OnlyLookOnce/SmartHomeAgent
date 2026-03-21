import os

# 项目根目录
PROJECT_ROOT = "d:\\PythonProject\\Home-AI-Agent"

# 排除的目录
EXCLUDE_DIRS = [".git", ".pytest_cache", ".trae", "backup-", "__pycache__"]

# 递归检查空文件夹
def find_empty_folders(root):
    empty_folders = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        # 排除不需要检查的目录
        dirnames[:] = [d for d in dirnames if not any(exclude in d for exclude in EXCLUDE_DIRS)]
        
        # 检查当前目录是否为空
        # 忽略 .gitkeep 等占位文件
        valid_files = [f for f in filenames if not f.startswith('.') or f not in ['.gitkeep']]
        if not valid_files and not dirnames:
            empty_folders.append(os.path.relpath(dirpath, PROJECT_ROOT))
    
    return empty_folders

# 主函数
def main():
    print("Finding empty folders...")
    empty_folders = find_empty_folders(PROJECT_ROOT)
    
    print("\nEmpty folders:")
    for folder in empty_folders:
        print(f"- {folder}")
    
    print(f"\nTotal empty folders: {len(empty_folders)}")
    
    # 保存结果到文件
    with open("empty_folders.txt", "w", encoding="utf-8") as f:
        for folder in empty_folders:
            f.write(f"{folder}\n")
    print("\nResults saved to empty_folders.txt")

if __name__ == "__main__":
    main()