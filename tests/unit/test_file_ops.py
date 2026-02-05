import pytest
import os
from pathlib import Path
from datetime import datetime
from src.utils.file_ops import generate_timestamped_name, save_content, extract_arxiv_id

def test_extract_arxiv_id():
    """测试 arXiv ID 提取"""
    # Standard format
    assert extract_arxiv_id("https://arxiv.org/abs/2601.14750") == "2601.14750"
    # Versioned format
    assert extract_arxiv_id("https://arxiv.org/abs/2601.14750v2") == "2601.14750v2"
    # HTML format
    assert extract_arxiv_id("https://arxiv.org/html/2601.14750v2") == "2601.14750v2"
    # PDF format
    assert extract_arxiv_id("https://arxiv.org/pdf/2601.14750v2.pdf") == "2601.14750v2"
    # Non-arXiv URL
    assert extract_arxiv_id("https://google.com") is None

def test_generate_timestamped_name_with_id():
    """测试带 ID 的文件名生成"""
    base_name = "summary"
    ext = ".md"
    identifier = "2601.14750v2"
    name = generate_timestamped_name(base_name, ext, identifier)
    
    # 验证格式 summary_2601.14750v2_YYYYMMDD_HHMM.md
    assert name.startswith(f"summary_{identifier}_")
    assert name.endswith(".md")

def test_generate_timestamped_name_no_id():
    """测试不带 ID 的文件名生成"""
    base_name = "summary"
    ext = ".md"
    name = generate_timestamped_name(base_name, ext)
    
    # 验证格式 summary_YYYYMMDD_HHMM.md
    assert name.startswith("summary_")
    assert "_20" in name # Check for year part of timestamp

def test_save_text_content(tmp_path):
    """测试保存文本内容"""
    content = "# Summary Content"
    file_path = tmp_path / "test.md"
    
    saved_path = save_content(str(file_path), content)
    
    assert Path(saved_path).exists()
    assert Path(saved_path).read_text(encoding='utf-8') == content

def test_save_binary_content(tmp_path):
    """测试保存二进制内容"""
    content = b"Binary Data"
    file_path = tmp_path / "test.bin"
    
    saved_path = save_content(str(file_path), content, mode='wb')
    
    assert Path(saved_path).exists()
    assert Path(saved_path).read_bytes() == content

def test_save_content_create_dirs(tmp_path):
    """测试自动创建父目录"""
    content = "test"
    file_path = tmp_path / "subdir" / "test.txt"
    
    saved_path = save_content(str(file_path), content)
    
    assert Path(saved_path).exists()
    assert Path(saved_path).parent.exists()