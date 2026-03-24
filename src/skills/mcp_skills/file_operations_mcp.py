from typing import Dict, Any, List, Optional
import logging
import os
import re
import fnmatch
import asyncio
import tempfile

class FileOperationsMCP:
    """文件操作管理控制程序(MCP) - 实现文件读取、创建、查找和改写功能"""
    
    def __init__(self):
        """初始化文件操作MCP"""
        self.logger = logging.getLogger(__name__)
        # 定义允许操作的路径范围（白名单）
        self.allowed_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),  # 项目根目录
            os.path.expanduser("~"),  # 用户主目录
            tempfile.gettempdir(),  # 临时目录
        ]
        self.logger.info("文件操作MCP初始化完成")
    
    def _is_path_allowed(self, path: str) -> bool:
        """检查路径是否在允许的范围内
        
        Args:
            path: 要检查的文件路径
            
        Returns:
            bool: 路径是否在允许范围内
        """
        try:
            abs_path = os.path.abspath(path)
            for allowed_path in self.allowed_paths:
                if abs_path.startswith(allowed_path):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"路径检查失败: {str(e)}")
            return False
    
    def read_file(self, file_path: str) -> str:
        """读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容或错误信息
        """
        try:
            # 检查路径是否允许
            if not self._is_path_allowed(file_path):
                error_msg = f"路径不允许操作: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查是否是文件
            if not os.path.isfile(file_path):
                error_msg = f"路径不是文件: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 读取文件内容
            self.logger.info(f"正在读取文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.logger.info(f"文件读取成功: {file_path}")
            return content
            
        except PermissionError:
            error_msg = f"权限不足，无法读取文件: {file_path}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
    
    async def read_file_async(self, file_path: str) -> str:
        """异步读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容或错误信息
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_file, file_path)
    
    def create_file(self, file_path: str, content: str, overwrite: bool = False) -> str:
        """创建文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            str: 操作结果
        """
        try:
            # 检查路径是否允许
            if not self._is_path_allowed(file_path):
                error_msg = f"路径不允许操作: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                if not overwrite:
                    error_msg = f"文件已存在: {file_path}"
                    self.logger.warning(error_msg)
                    return f"错误: {error_msg}"
                else:
                    self.logger.info(f"覆盖已存在的文件: {file_path}")
            
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                self.logger.info(f"创建目录: {directory}")
                os.makedirs(directory, exist_ok=True)
            
            # 写入文件内容
            self.logger.info(f"正在创建文件: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"文件创建成功: {file_path}")
            return f"文件创建成功: {file_path}"
            
        except PermissionError:
            error_msg = f"权限不足，无法创建文件: {file_path}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"创建文件失败: {str(e)}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
    
    async def create_file_async(self, file_path: str, content: str, overwrite: bool = False) -> str:
        """异步创建文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            str: 操作结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_file, file_path, content, overwrite)
    
    def search_files(self, directory: str, filename_pattern: Optional[str] = None, 
                     file_extension: Optional[str] = None, 
                     content_keyword: Optional[str] = None) -> List[str]:
        """搜索文件
        
        Args:
            directory: 搜索目录
            filename_pattern: 文件名模式（支持通配符）
            file_extension: 文件扩展名
            content_keyword: 内容关键词
            
        Returns:
            List[str]: 符合条件的文件列表
        """
        try:
            # 检查路径是否允许
            if not self._is_path_allowed(directory):
                error_msg = f"路径不允许操作: {directory}"
                self.logger.warning(error_msg)
                return [f"错误: {error_msg}"]
            
            # 检查目录是否存在
            if not os.path.exists(directory):
                error_msg = f"目录不存在: {directory}"
                self.logger.warning(error_msg)
                return [f"错误: {error_msg}"]
            
            # 检查是否是目录
            if not os.path.isdir(directory):
                error_msg = f"路径不是目录: {directory}"
                self.logger.warning(error_msg)
                return [f"错误: {error_msg}"]
            
            self.logger.info(f"正在搜索文件，目录: {directory}, 文件名模式: {filename_pattern}, \
                           文件扩展名: {file_extension}, 内容关键词: {content_keyword}")
            
            result = []
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查路径是否允许
                    if not self._is_path_allowed(file_path):
                        continue
                    
                    # 检查文件名模式
                    if filename_pattern and not fnmatch.fnmatch(file, filename_pattern):
                        continue
                    
                    # 检查文件扩展名
                    if file_extension:
                        ext = os.path.splitext(file)[1].lstrip('.')
                        if ext != file_extension:
                            continue
                    
                    # 检查内容关键词
                    if content_keyword:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            if content_keyword not in content:
                                continue
                        except Exception:
                            # 无法读取文件内容，跳过
                            continue
                    
                    result.append(file_path)
            
            self.logger.info(f"搜索完成，找到 {len(result)} 个文件")
            return result
            
        except PermissionError:
            error_msg = f"权限不足，无法搜索目录: {directory}"
            self.logger.error(error_msg)
            return [f"错误: {error_msg}"]
        except Exception as e:
            error_msg = f"搜索文件失败: {str(e)}"
            self.logger.error(error_msg)
            return [f"错误: {error_msg}"]
    
    async def search_files_async(self, directory: str, filename_pattern: Optional[str] = None, 
                                file_extension: Optional[str] = None, 
                                content_keyword: Optional[str] = None) -> List[str]:
        """异步搜索文件
        
        Args:
            directory: 搜索目录
            filename_pattern: 文件名模式（支持通配符）
            file_extension: 文件扩展名
            content_keyword: 内容关键词
            
        Returns:
            List[str]: 符合条件的文件列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_files, directory, 
                                         filename_pattern, file_extension, content_keyword)
    
    def rewrite_file(self, file_path: str, new_content: str, 
                    start_line: Optional[int] = None, 
                    end_line: Optional[int] = None) -> str:
        """改写文件内容
        
        Args:
            file_path: 文件路径
            new_content: 新内容
            start_line: 开始行（从1开始）
            end_line: 结束行（从1开始）
            
        Returns:
            str: 操作结果
        """
        try:
            # 检查路径是否允许
            if not self._is_path_allowed(file_path):
                error_msg = f"路径不允许操作: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查是否是文件
            if not os.path.isfile(file_path):
                error_msg = f"路径不是文件: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            self.logger.info(f"正在改写文件: {file_path}, 开始行: {start_line}, 结束行: {end_line}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 处理行范围
            if start_line is not None and end_line is not None:
                # 替换指定行范围
                if start_line < 1 or end_line > len(lines) or start_line > end_line:
                    error_msg = f"无效的行范围: 开始行 {start_line}, 结束行 {end_line}, 文件总行数 {len(lines)}"
                    self.logger.warning(error_msg)
                    return f"错误: {error_msg}"
                
                # 替换指定行
                lines[start_line-1:end_line] = [new_content + '\n']
            else:
                # 替换整个文件
                lines = [new_content + '\n']
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.logger.info(f"文件改写成功: {file_path}")
            return f"文件改写成功: {file_path}"
            
        except PermissionError:
            error_msg = f"权限不足，无法改写文件: {file_path}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"改写文件失败: {str(e)}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
    
    async def rewrite_file_async(self, file_path: str, new_content: str, 
                                start_line: Optional[int] = None, 
                                end_line: Optional[int] = None) -> str:
        """异步改写文件内容
        
        Args:
            file_path: 文件路径
            new_content: 新内容
            start_line: 开始行（从1开始）
            end_line: 结束行（从1开始）
            
        Returns:
            str: 操作结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.rewrite_file, file_path, 
                                         new_content, start_line, end_line)
    
    def delete_file(self, file_path: str) -> str:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 操作结果
        """
        try:
            # 检查路径是否允许
            if not self._is_path_allowed(file_path):
                error_msg = f"路径不允许操作: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 检查是否是文件
            if not os.path.isfile(file_path):
                error_msg = f"路径不是文件: {file_path}"
                self.logger.warning(error_msg)
                return f"错误: {error_msg}"
            
            # 删除文件
            self.logger.info(f"正在删除文件: {file_path}")
            os.remove(file_path)
            
            self.logger.info(f"文件删除成功: {file_path}")
            return f"文件删除成功: {file_path}"
            
        except PermissionError:
            error_msg = f"权限不足，无法删除文件: {file_path}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"删除文件失败: {str(e)}"
            self.logger.error(error_msg)
            return f"错误: {error_msg}"
    
    async def delete_file_async(self, file_path: str) -> str:
        """异步删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 操作结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete_file, file_path)

# 创建文件操作MCP实例
file_operations_mcp = FileOperationsMCP()
