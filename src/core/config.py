import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量 (.env 文件)
load_dotenv()

class ProcessingConfig(BaseModel):
    """
    处理流程配置模型。
    对应配置文件中的 profiles 部分。
    """
    profile_name: str           # 配置名称 (如 'default')
    summary_prompt: str         # 生成摘要的提示词
    presentation_prompt: str    # 生成演示文稿的提示词
    keep_source: bool = False   # 是否保留源文件 (默认 False)
    timeout: float = 1800.0     # 操作超时时间 (默认 30 分钟)
    max_retries: int = 5        # 最大重试次数 (默认 5 次)
    output_dir: str = "output"  # 输出目录 (默认 'output')

def get_auth_config() -> dict:
    """
    获取认证配置信息。
    
    优先从环境变量中读取认证所需的 Token 和 Cookie。
    如果环境变量缺失，返回对应值为 None 的字典。
    NotebookClient 后续会据此判断是否使用本地存储的认证状态。
    
    Returns:
        dict: 包含 'token' 和 'cookies' 的字典
    """
    return {
        "token": os.getenv("GOOGLE_TOKEN"),
        "cookies": os.getenv("COOKIES")
    }

def load_config(config_path: str, profile_name: str = "default") -> ProcessingConfig:
    """
    加载并解析配置文件。

    Args:
        config_path (str): 配置文件路径
        profile_name (str): 要使用的配置 Profile 名称 (默认 "default")

    Returns:
        ProcessingConfig: 解析后的配置对象

    Raises:
        FileNotFoundError: 如果配置文件不存在
        ValueError: 如果配置文件格式错误或指定的 profile 不存在
    """
    path = Path(config_path)
    
    # 如果指定路径不存在，尝试在当前目录查找默认文件名
    if not path.exists():
        path = Path("config.yaml")
        
    if not path.exists():
        raise FileNotFoundError(f"未找到配置文件: {config_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    if not data or "profiles" not in data:
        raise ValueError("配置文件格式错误：缺失 'profiles' 键")
        
    profiles = data["profiles"]
    if profile_name not in profiles:
        raise ValueError(f"在配置中未找到 Profile: '{profile_name}'")
        
    profile_data = profiles[profile_name]
    
    # 构建并返回配置对象
    return ProcessingConfig(
        profile_name=profile_name,
        summary_prompt=profile_data.get("summary_prompt", ""),
        presentation_prompt=profile_data.get("presentation_prompt", ""),
        keep_source=profile_data.get("keep_source", False),
        timeout=float(profile_data.get("timeout", 1800.0)),
        max_retries=int(profile_data.get("max_retries", 5)),
        output_dir=profile_data.get("output_dir", "output")
    )
