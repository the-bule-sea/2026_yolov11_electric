"""
路径转换工具
用于Windows路径和WSL路径的相互转换
"""
import os


def convert_path_to_wsl(win_path: str) -> str:
    """
    将Windows路径转换为WSL路径
    
    Args:
        win_path: Windows路径, 例如: D:\\data\\img.jpg
        
    Returns:
        WSL路径, 例如: /mnt/d/data/img.jpg
        
    Examples:
        >>> convert_path_to_wsl('D:\\data\\img.jpg')
        '/mnt/d/data/img.jpg'
        >>> convert_path_to_wsl('D:/data/img.jpg')
        '/mnt/d/data/img.jpg'
    """
    # 确保是绝对路径
    abs_path = os.path.abspath(win_path)
    
    # 替换反斜杠为正斜杠
    linux_path = abs_path.replace('\\', '/')
    
    # 处理盘符 (C: -> /mnt/c, D: -> /mnt/d)
    if ':' in linux_path:
        drive, tail = linux_path.split(':', 1)
        return f"/mnt/{drive.lower()}{tail}"
    
    return linux_path


def convert_path_to_windows(wsl_path: str) -> str:
    """
    将WSL路径转换为Windows路径 (可选功能)
    
    Args:
        wsl_path: WSL路径, 例如: /mnt/d/data/img.jpg
        
    Returns:
        Windows路径, 例如: D:\\data\\img.jpg
        
    Examples:
        >>> convert_path_to_windows('/mnt/d/data/img.jpg')
        'D:\\\\data\\\\img.jpg'
    """
    if wsl_path.startswith('/mnt/'):
        # 移除 /mnt/ 前缀
        path_without_mnt = wsl_path[5:]
        
        # 提取盘符
        drive = path_without_mnt[0].upper()
        tail = path_without_mnt[1:]
        
        # 转换为Windows路径
        win_path = f"{drive}:{tail}".replace('/', '\\')
        return win_path
    
    return wsl_path


def ensure_directory_exists(path: str) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


if __name__ == '__main__':
    # 测试代码
    test_win_path = r'D:\Document\test\image.jpg'
    wsl_path = convert_path_to_wsl(test_win_path)
    print(f"Windows: {test_win_path}")
    print(f"WSL: {wsl_path}")
    
    win_path_back = convert_path_to_windows(wsl_path)
    print(f"Back to Windows: {win_path_back}")
