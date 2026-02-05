import pytest
import yaml
import os
from src.core.config import ProcessingConfig, load_config, get_auth_config

# Mock YAML content
VALID_YAML = """
profiles:
  default:
    summary_prompt: "Summary Prompt"
    presentation_prompt: "Presentation Prompt"
    keep_source: false
  
  custom:
    summary_prompt: "Custom Summary"
    presentation_prompt: "Custom Presentation"
    keep_source: true
"""

@pytest.fixture
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(VALID_YAML, encoding='utf-8')
    return p

def test_processing_config_model():
    """测试配置模型的基本验证"""
    config = ProcessingConfig(
        profile_name="test",
        summary_prompt="prompt",
        presentation_prompt="prompt",
        keep_source=True
    )
    assert config.profile_name == "test"
    assert config.summary_prompt == "prompt"
    assert config.keep_source is True

def test_load_config_default(config_file):
    """测试加载默认配置"""
    config = load_config(str(config_file), "default")
    assert config.profile_name == "default"
    assert config.summary_prompt == "Summary Prompt"
    assert config.keep_source is False

def test_load_config_custom(config_file):
    """测试加载自定义配置"""
    config = load_config(str(config_file), "custom")
    assert config.profile_name == "custom"
    assert config.summary_prompt == "Custom Summary"
    assert config.keep_source is True

def test_load_config_not_found(config_file):
    """测试加载不存在的 Profile"""
    # 修正：匹配中文异常信息
    with pytest.raises(ValueError, match="在配置中未找到 Profile"):
        load_config(str(config_file), "missing")

def test_load_env_vars(monkeypatch):
    """测试从环境变量加载认证信息"""
    monkeypatch.setenv("GOOGLE_TOKEN", "token123")
    monkeypatch.setenv("COOKIES", "cookie123")
    
    auth = get_auth_config()
    assert auth["token"] == "token123"
    assert auth["cookies"] == "cookie123"

def test_missing_env_vars(monkeypatch):
    """测试缺失环境变量 (新逻辑下不应抛出异常)"""
    monkeypatch.delenv("GOOGLE_TOKEN", raising=False)
    monkeypatch.delenv("COOKIES", raising=False)
    
    auth = get_auth_config()
    assert auth["token"] is None
    assert auth["cookies"] is None