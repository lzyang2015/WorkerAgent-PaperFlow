import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional, Union

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

def get_arxiv_title(arxiv_id: str) -> str:
    """通过 arXiv API 获取论文标题"""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('utf-8')

    root = ET.fromstring(data)
    # arXiv API 返回的 XML 使用 Atom 命名空间
    # 需要找到 entry 下的 title
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entry = root.find('atom:entry', ns)
    if entry is not None:
        title_elem = entry.find('atom:title', ns)
        if title_elem is not None and title_elem.text:
            # 标题中可能有换行符，需要清理
            return ' '.join(title_elem.text.strip().split())

    return "Unknown"

def sanitize_folder_name(name: str) -> str:
    """清理字符串作为文件夹名称，移除非法字符"""
    # 移除 Windows/macOS/Linux 非法文件名字符
    # 包括: \ / : * ? " < > |
    illegal_chars = r'[\\/:*?"<>|]'
    name = re.sub(illegal_chars, '', name)
    # 移除其他可能导致问题的特殊字符
    # 保留: 字母、数字、中文、空格、括号()[]、连字符-、下划线_、英文句号.
    name = re.sub(r'[^\w\s\u4e00-\u9fff()\[\].-]', '', name, flags=re.UNICODE)
    # 去除首尾空格和点
    name = name.strip().strip('.')
    # 限制长度（防止文件系统限制）
    max_length = 100
    if len(name) > max_length:
        name = name[:max_length].strip()
    # 移除多余的连续空格
    name = re.sub(r'\s+', ' ', name)
    return name
