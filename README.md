# PaperFlow

PaperFlow 是一个基于 Python 的命令行工具，利用 [NotebookLM](https://notebooklm.google.com/) 自动化处理研究论文。

## 功能

- **自动摘要**: 输入论文 URL，自动生成 Markdown 格式的摘要。
- **自动演示文稿**: 自动生成演示文稿大纲/内容。
- **多领域支持**: 通过配置文件支持不同领域（如 CS, Bio）的定制化 Prompt。
- **历史记录**: 输出文件自动添加时间戳。

## 安装

1. 克隆仓库:
   ```bash
   git clone <repo-url>
   cd PaperFlow
   ```

2. 创建虚拟环境并安装依赖:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 配置

1. 复制 `.env.example` 为 `.env` 并填入 Google Token 和 Cookies:
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

2. (可选) 编辑 `config.yaml` 自定义 Prompt。

## 使用

```bash
# 基本使用
python -m src.cli.main https://arxiv.org/abs/2401.xxxxx

# 指定 Profile
python -m src.cli.main https://arxiv.org/abs/2401.xxxxx --profile cs

# 帮助
python -m src.cli.main --help
```
