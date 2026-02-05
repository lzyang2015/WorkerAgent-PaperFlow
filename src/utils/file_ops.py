import os
import re
from pathlib import Path
from datetime import datetime
from typing import Union, Optional

def extract_arxiv_id(url: str) -> Optional[str]:
    """
    从 arXiv URL 中提取论文 ID。
    
    支持的 URL 格式示例:
    - https://arxiv.org/abs/2601.14750v2
    - https://arxiv.org/html/2601.14750v2
    - https://arxiv.org/pdf/2601.14750v2.pdf
    
    Args:
        url (str): 输入的 URL 字符串
        
    Returns:
        Optional[str]: 成功提取则返回 ID (如 '2601.14750v2')，否则返回 None
    """
    # 匹配常见的 arXiv URL 模式
    # capturing group 1: ID part
    pattern = r"arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+(?:v\d+)?)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def generate_timestamped_name(base_name: str, extension: str, identifier: Optional[str] = None) -> str:
    """
    生成带时间戳的文件名。
    
    Args:
        base_name (str): 基础文件名前缀 (如 'summary')
        extension (str): 文件扩展名 (如 '.md')
        identifier (Optional[str]): 可选的标识符 (如论文ID)，用于增加文件名辨识度
        
    Returns:
        str: 生成的文件名
             格式: {base_name}_{identifier}_{timestamp}{extension} 
             或    {base_name}_{timestamp}{extension}
    """
    # 生成当前时间戳，格式: YYYYMMDD_HHMM
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # 确保扩展名以 '.' 开头
    if not extension.startswith('.'):
        extension = f".{extension}"
        
    if identifier:
        return f"{base_name}_{identifier}_{timestamp}{extension}"
    else:
        return f"{base_name}_{timestamp}{extension}"

def save_content(file_path: Union[str, Path], content: Union[str, bytes], mode: str = 'w') -> str:
    """
    保存内容到文件，如果父目录不存在则自动创建。
    
    Args:
        file_path (Union[str, Path]): 目标文件路径
        content (Union[str, bytes]): 要写入的内容
        mode (str): 文件打开模式 ('w' for text, 'wb' for binary). 默认为 'w'。
        
    Returns:
        str: 保存后的文件绝对路径
    """
    path = Path(file_path)
    
    # 确保父目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 二进制模式下不需要 encoding
    encoding = 'utf-8' if 'b' not in mode else None
    
    with open(path, mode, encoding=encoding) as f:
        f.write(content)
        
    return str(path.absolute())
