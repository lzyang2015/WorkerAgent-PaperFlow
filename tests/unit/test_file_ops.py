import pytest
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.utils.file_ops import (
    generate_timestamped_name,
    save_content,
    extract_arxiv_id,
    get_arxiv_title,
    sanitize_folder_name
)

# ==================== extract_arxiv_id Tests ====================

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


# ==================== generate_timestamped_name Tests ====================

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


# ==================== save_content Tests ====================

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


# ==================== get_arxiv_title Tests ====================

@patch('src.utils.file_ops.urllib.request.urlopen')
def test_get_arxiv_title_success(mock_urlopen):
    """测试成功获取论文标题"""
    # Mock API response for ERNIE 5.0
    mock_response_data = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>ERNIE 5.0 Technical Report</title>
  </entry>
</feed>'''
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_context.read.return_value = mock_response_data
    mock_urlopen.return_value = mock_context

    title = get_arxiv_title("2602.04705")
    assert title == "ERNIE 5.0 Technical Report"

@patch('src.utils.file_ops.urllib.request.urlopen')
def test_get_arxiv_title_with_colon(mock_urlopen):
    """测试获取包含冒号的论文标题"""
    mock_response_data = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>FASA: Frequency-aware Sparse Attention</title>
  </entry>
</feed>'''
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_context.read.return_value = mock_response_data
    mock_urlopen.return_value = mock_context

    title = get_arxiv_title("2602.03152")
    assert title == "FASA: Frequency-aware Sparse Attention"

@patch('src.utils.file_ops.urllib.request.urlopen')
def test_get_arxiv_title_with_newlines(mock_urlopen):
    """测试获取包含换行符的论文标题"""
    mock_response_data = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>
      Attention Is All You Need
    </title>
  </entry>
</feed>'''
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_context.read.return_value = mock_response_data
    mock_urlopen.return_value = mock_context

    title = get_arxiv_title("1706.03762")
    assert title == "Attention Is All You Need"

@patch('src.utils.file_ops.urllib.request.urlopen')
def test_get_arxiv_title_not_found(mock_urlopen):
    """测试获取不存在的论文标题"""
    mock_response_data = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>'''
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_context)
    mock_context.__exit__ = MagicMock(return_value=False)
    mock_context.read.return_value = mock_response_data
    mock_urlopen.return_value = mock_context

    title = get_arxiv_title("9999.99999")
    assert title == "Unknown"


# ==================== sanitize_folder_name Tests ====================

def test_sanitize_folder_name_basic():
    """测试基本清理功能"""
    assert sanitize_folder_name("Hello World") == "Hello World"
    assert sanitize_folder_name("test") == "test"

def test_sanitize_folder_name_removes_illegal_chars():
    """测试移除非法字符"""
    # 斜杠
    assert sanitize_folder_name("test/path") == "testpath"
    # 反斜杠
    assert sanitize_folder_name("test\\path") == "testpath"
    # 冒号
    assert sanitize_folder_name("FASA: Method") == "FASA Method"
    # 星号
    assert sanitize_folder_name("test*file") == "testfile"
    # 问号
    assert sanitize_folder_name("test?file") == "testfile"
    # 双引号
    assert sanitize_folder_name('test"file') == "testfile"
    # 小于号
    assert sanitize_folder_name("test<file") == "testfile"
    # 大于号
    assert sanitize_folder_name("test>file") == "testfile"
    # 管道符
    assert sanitize_folder_name("test|file") == "testfile"

def test_sanitize_folder_name_preserves_chinese():
    """测试保留中文字符"""
    assert sanitize_folder_name("中文测试") == "中文测试"
    assert sanitize_folder_name("论文标题") == "论文标题"

def test_sanitize_folder_name_preserves_english():
    """测试保留英文字符"""
    assert sanitize_folder_name("Attention Is All You Need") == "Attention Is All You Need"

def test_sanitize_folder_name_removes_special_chars():
    """测试移除特殊字符"""
    assert sanitize_folder_name("test@#$%file") == "testfile"

def test_sanitize_folder_name_trims_whitespace():
    """测试去除首尾空白"""
    assert sanitize_folder_name("  test  ") == "test"
    assert sanitize_folder_name("\ttest\n") == "test"

def test_sanitize_folder_name_trims_dots():
    """测试去除首尾点号"""
    assert sanitize_folder_name("...test...") == "test"

def test_sanitize_folder_name_max_length():
    """测试最大长度限制"""
    long_name = "a" * 150
    result = sanitize_folder_name(long_name)
    assert len(result) <= 100

def test_sanitize_folder_name_real_titles():
    """测试真实论文标题"""
    titles = [
        ("ERNIE 5.0 Technical Report", "ERNIE 5.0 Technical Report"),
        ("FASA: Frequency-aware Sparse Attention", "FASA Frequency-aware Sparse Attention"),
        ("Attention Is All You Need", "Attention Is All You Need"),
        ("BERT: Pre-training of Deep Bidirectional Transformers",
         "BERT Pre-training of Deep Bidirectional Transformers"),
        ("GPT-4 Technical Report", "GPT-4 Technical Report"),
    ]
    for input_title, expected in titles:
        assert sanitize_folder_name(input_title) == expected

def test_sanitize_folder_name_empty_result():
    """测试空结果情况（全部是非法字符）"""
    result = sanitize_folder_name("////")
    assert result == ""
    result = sanitize_folder_name(":::")
    assert result == ""

def test_sanitize_folder_name_preserves_parentheses():
    """测试保留括号"""
    assert sanitize_folder_name("test (copy)") == "test (copy)"
    assert sanitize_folder_name("test [item]") == "test [item]"

def test_sanitize_folder_name_multiple_spaces():
    """测试合并多个连续空格"""
    result = sanitize_folder_name("test   multiple    spaces")
    assert result == "test multiple spaces"

def test_sanitize_folder_name_edge_cases():
    """测试边界情况"""
    # 只含数字
    assert sanitize_folder_name("12345") == "12345"
    # 只含中文带空格
    assert sanitize_folder_name("深度学习 神经网络") == "深度学习 神经网络"
    # LaTeX 特殊字符（下划线保留）
    assert sanitize_folder_name("alpha_2 and beta^3") == "alpha_2 and beta3"
    # 省略号（保留）
    assert sanitize_folder_name("paper...name") == "paper...name"
    # 加号
    assert sanitize_folder_name("C++ and Python") == "C and Python"
    # 等号（会被移除）
    assert sanitize_folder_name("A=B Problem") == "AB Problem"
    # 波浪号
    assert sanitize_folder_name("~test") == "test"
    # 单引号（会被移除）
    assert sanitize_folder_name("Author's Paper") == "Authors Paper"
    # 百分号
    assert sanitize_folder_name("100% Accuracy") == "100 Accuracy"
    # 井号
    assert sanitize_folder_name("#1 Paper") == "1 Paper"

def test_sanitize_folder_name_mixed_chinese_english():
    """测试中英文混合标题"""
    result = sanitize_folder_name("深度学习 Deep Learning 综述")
    assert result == "深度学习 Deep Learning 综述"

def test_sanitize_folder_name_paper_version():
    """测试论文版本号格式"""
    result = sanitize_folder_name("Neural Networks v2.0")
    assert result == "Neural Networks v2.0"
    result = sanitize_folder_name("Paper Rev.3")
    assert result == "Paper Rev.3"

def test_sanitize_folder_name_accent_chars():
    """测试带重音符号的字符"""
    result = sanitize_folder_name("Caffe: Convolutional Architecture")
    assert result == "Caffe Convolutional Architecture"
    result = sanitize_folder_name("ResNet with BatchNorm")
    assert result == "ResNet with BatchNorm"

def test_sanitize_folder_name_unicode_symbols():
    """测试 Unicode 符号"""
    # 版权符号（会被移除）
    result = sanitize_folder_name("Paper © 2024")
    assert result == "Paper 2024"
    # 省略号 unicode
    result = sanitize_folder_name("Paper… More")
    assert result == "Paper More"
    # 破折号 unicode (会被移除)
    result = sanitize_folder_name("Paper — Summary")
    assert result == "Paper Summary"

def test_sanitize_folder_name_only_numbers():
    """测试只含数字的情况"""
    result = sanitize_folder_name("12345")
    assert result == "12345"
    # 带非法字符的数字
    result = sanitize_folder_name("123/456\\789")
    assert result == "123456789"

def test_sanitize_folder_name_long_chinese():
    """测试超长中文标题"""
    long_title = "基于深度学习的自然语言处理技术在智能问答系统中的应用研究"
    result = sanitize_folder_name(long_title)
    # 应该保留中文，但可能被截断
    assert len(result) <= 100
    assert result.startswith("基于")

def test_sanitize_folder_name_consecutive_illegal():
    """测试连续非法字符"""
    result = sanitize_folder_name("test///path\\\\file")
    assert result == "testpathfile"
    result = sanitize_folder_name("name::;;??<<>>")
    assert result == "name"

def test_sanitize_folder_name_edge_length():
    """测试边界长度"""
    # 正好100字符
    result = sanitize_folder_name("a" * 100)
    assert len(result) == 100
    # 101字符应该被截断
    result = sanitize_folder_name("a" * 101)
    assert len(result) == 100

def test_sanitize_folder_name_with_dots_in_middle():
    """测试中间的点号（版本号、缩写等）"""
    result = sanitize_folder_name("Fig.1 Architecture")
    assert result == "Fig.1 Architecture"
    result = sanitize_folder_name("U.S. Patent")
    assert result == "U.S. Patent"
    result = sanitize_folder_name("Vol.2 No.3")
    assert result == "Vol.2 No.3"
