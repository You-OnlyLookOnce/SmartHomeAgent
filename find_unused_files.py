import os
import re
import sys

# 项目根目录
PROJECT_ROOT = "d:\\PythonProject\\Home-AI-Agent"

# 排除的目录和文件
EXCLUDE_DIRS = [".git", ".pytest_cache", ".trae", "backup-", "__pycache__", "data", "logs"]
EXCLUDE_FILES = ["find_unused_files.py"]

# 获取所有Python文件
def get_python_files():
    python_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if not any(exclude in d for exclude in EXCLUDE_DIRS)]
        
        for file in files:
            if file.endswith(".py") and file not in EXCLUDE_FILES:
                python_files.append(os.path.relpath(os.path.join(root, file), PROJECT_ROOT))
    return python_files

# 分析文件中的import语句
def analyze_imports(file_path):
    imports = []
    try:
        with open(os.path.join(PROJECT_ROOT, file_path), 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 匹配import语句
            import_patterns = [
                r'^import\s+([\w\.]+)',
                r'^from\s+([\w\.]+)\s+import',
                r'^from\s+\.([\w\.]+)\s+import',  # 相对导入
                r'^from\s+\.\.([\w\.]+)\s+import',  # 相对导入
                r'^from\s+\.\.\.([\w\.]+)\s+import'  # 相对导入
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    # 处理相对导入
                    if pattern.startswith('^from\s+\.'):
                        # 计算相对路径
                        levels = pattern.count('.') - 1
                        file_dir = os.path.dirname(file_path)
                        for _ in range(levels):
                            file_dir = os.path.dirname(file_dir)
                        if match:
                            import_path = os.path.join(file_dir, *match.split('.'))
                        else:
                            import_path = file_dir
                    else:
                        # 处理绝对导入
                        import_path = os.path.join(*match.split('.'))
                    
                    # 检查是否存在对应的.py文件或__init__.py文件
                    py_file = os.path.join(PROJECT_ROOT, f"{import_path}.py")
                    init_file = os.path.join(PROJECT_ROOT, import_path, "__init__.py")
                    
                    if os.path.exists(py_file):
                        module_name = py_file.replace(PROJECT_ROOT + os.sep, "").replace(".py", "").replace(os.sep, ".")
                        imports.append(module_name)
                    elif os.path.exists(init_file):
                        module_name = init_file.replace(PROJECT_ROOT + os.sep, "").replace("\__init__.py", "").replace(os.sep, ".")
                        imports.append(module_name)
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    return imports

# 主函数
def main():
    print("Finding unused Python files...")
    python_files = get_python_files()
    print(f"Found {len(python_files)} Python files")
    
    # 构建文件路径到模块名的映射
    file_to_module = {}
    for file_path in python_files:
        # 转换为模块名
        module_name = file_path.replace(".py", "").replace(os.sep, ".")
        file_to_module[file_path] = module_name
    
    # 收集所有被引用的模块
    referenced_modules = set()
    for file_path in python_files:
        imports = analyze_imports(file_path)
        referenced_modules.update(imports)
    
    # 找出未被引用的文件
    unused_files = []
    for file_path, module_name in file_to_module.items():
        if module_name not in referenced_modules:
            # 检查是否是主入口文件
            if file_path == "app.py":
                continue
            unused_files.append(file_path)
    
    print("\nUnused Python files:")
    for file in unused_files:
        print(f"- {file}")
    
    print(f"\nTotal unused files: {len(unused_files)}")
    
    # 保存结果到文件
    with open("unused_files.txt", "w", encoding="utf-8") as f:
        for file in unused_files:
            f.write(f"{file}\n")
    print("\nResults saved to unused_files.txt")

if __name__ == "__main__":
    main()