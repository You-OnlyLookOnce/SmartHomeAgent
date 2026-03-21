import os
import re

# 项目根目录
PROJECT_ROOT = "d:\\PythonProject\\Home-AI-Agent"

# 排除的目录和文件
EXCLUDE_DIRS = [".git", ".pytest_cache", ".trae", "backup-", "__pycache__", "data", "logs"]
EXCLUDE_FILES = ["find_unused_files.py", "find_unused_code.py"]

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

# 分析文件中的函数、类和变量定义
def analyze_definitions(file_path):
    definitions = {
        "functions": [],
        "classes": [],
        "variables": []
    }
    
    try:
        with open(os.path.join(PROJECT_ROOT, file_path), 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 匹配函数定义
            function_pattern = r'^\s*def\s+([a-zA-Z_]\w*)\s*\('  # 简单匹配函数定义
            function_matches = re.findall(function_pattern, content, re.MULTILINE)
            definitions["functions"] = function_matches
            
            # 匹配类定义
            class_pattern = r'^\s*class\s+([a-zA-Z_]\w*)\s*'  # 简单匹配类定义
            class_matches = re.findall(class_pattern, content, re.MULTILINE)
            definitions["classes"] = class_matches
            
            # 匹配变量定义（简单匹配）
            variable_pattern = r'^\s*([a-zA-Z_]\w*)\s*='  # 简单匹配变量定义
            variable_matches = re.findall(variable_pattern, content, re.MULTILINE)
            # 过滤掉函数和类名
            variable_matches = [var for var in variable_matches if var not in function_matches and var not in definitions["classes"]]
            # 过滤掉内置变量和特殊变量
            variable_matches = [var for var in variable_matches if not var.startswith('__') and not var.endswith('__')]
            definitions["variables"] = variable_matches
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return definitions

# 分析文件中的函数、类和变量引用
def analyze_references(file_path):
    references = {
        "functions": [],
        "classes": [],
        "variables": []
    }
    
    try:
        with open(os.path.join(PROJECT_ROOT, file_path), 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 匹配函数调用
            function_call_pattern = r'([a-zA-Z_]\w*)\s*\('  # 简单匹配函数调用
            function_call_matches = re.findall(function_call_pattern, content)
            references["functions"] = function_call_matches
            
            # 匹配类实例化
            class_instantiation_pattern = r'([a-zA-Z_]\w*)\s*\('  # 与函数调用相同
            class_instantiation_matches = re.findall(class_instantiation_pattern, content)
            references["classes"] = class_instantiation_matches
            
            # 匹配变量引用（简单匹配）
            variable_reference_pattern = r'\b([a-zA-Z_]\w*)\b'  # 简单匹配变量引用
            variable_reference_matches = re.findall(variable_reference_pattern, content)
            # 过滤掉函数和类名
            variable_reference_matches = [var for var in variable_reference_matches if var not in function_call_matches and var not in class_instantiation_matches]
            # 过滤掉关键字
            keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'return', 'print', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'pass', 'break', 'continue', 'try', 'except', 'finally', 'with', 'as', 'lambda']
            variable_reference_matches = [var for var in variable_reference_matches if var not in keywords]
            references["variables"] = variable_reference_matches
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return references

# 主函数
def main():
    print("Finding unused functions, classes, and variables...")
    python_files = get_python_files()
    print(f"Found {len(python_files)} Python files")
    
    # 收集所有定义和引用
    all_definitions = {}
    all_references = {}
    
    for file_path in python_files:
        all_definitions[file_path] = analyze_definitions(file_path)
        all_references[file_path] = analyze_references(file_path)
    
    # 收集所有引用的函数、类和变量
    referenced_functions = set()
    referenced_classes = set()
    referenced_variables = set()
    
    for file_path, refs in all_references.items():
        referenced_functions.update(refs["functions"])
        referenced_classes.update(refs["classes"])
        referenced_variables.update(refs["variables"])
    
    # 找出未使用的函数、类和变量
    unused_code = {}
    
    for file_path, defs in all_definitions.items():
        unused_functions = [func for func in defs["functions"] if func not in referenced_functions]
        unused_classes = [cls for cls in defs["classes"] if cls not in referenced_classes]
        unused_variables = [var for var in defs["variables"] if var not in referenced_variables]
        
        if unused_functions or unused_classes or unused_variables:
            unused_code[file_path] = {
                "functions": unused_functions,
                "classes": unused_classes,
                "variables": unused_variables
            }
    
    # 输出结果
    print("\nUnused code elements:")
    total_unused_functions = 0
    total_unused_classes = 0
    total_unused_variables = 0
    
    for file_path, unused in unused_code.items():
        print(f"\nFile: {file_path}")
        if unused["functions"]:
            print("  Unused functions:")
            for func in unused["functions"]:
                print(f"    - {func}")
            total_unused_functions += len(unused["functions"])
        if unused["classes"]:
            print("  Unused classes:")
            for cls in unused["classes"]:
                print(f"    - {cls}")
            total_unused_classes += len(unused["classes"])
        if unused["variables"]:
            print("  Unused variables:")
            for var in unused["variables"]:
                print(f"    - {var}")
            total_unused_variables += len(unused["variables"])
    
    print(f"\nTotal unused functions: {total_unused_functions}")
    print(f"Total unused classes: {total_unused_classes}")
    print(f"Total unused variables: {total_unused_variables}")
    
    # 保存结果到文件
    with open("unused_code.txt", "w", encoding="utf-8") as f:
        f.write("Unused code elements:\n\n")
        for file_path, unused in unused_code.items():
            f.write(f"File: {file_path}\n")
            if unused["functions"]:
                f.write("  Unused functions:\n")
                for func in unused["functions"]:
                    f.write(f"    - {func}\n")
            if unused["classes"]:
                f.write("  Unused classes:\n")
                for cls in unused["classes"]:
                    f.write(f"    - {cls}\n")
            if unused["variables"]:
                f.write("  Unused variables:\n")
                for var in unused["variables"]:
                    f.write(f"    - {var}\n")
            f.write("\n")
    print("\nResults saved to unused_code.txt")

if __name__ == "__main__":
    main()