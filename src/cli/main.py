import click
import asyncio
import os
from pathlib import Path
from src.core.config import load_config, get_auth_config
from src.core.notebook_client import NotebookClient
from src.utils.file_ops import generate_timestamped_name, save_content, extract_arxiv_id

# 辅助函数：运行异步协程
def run_async(coro):
    return asyncio.run(coro)

@click.command()
@click.argument('url')
@click.option('--profile', default='default', help='Configuration profile to use')
@click.option('--keep-source', is_flag=True, help='Do not delete source after processing')
@click.option('--config', default='config.yaml', help='Path to configuration file')
def cli(url, profile, keep_source, config):
    """
    PaperFlow: NotebookLM 论文处理工具
    
    命令行接口主入口。
    自动处理给定的论文 URL，利用 NotebookLM 生成摘要和演示文稿（幻灯片）。
    
    参数:
    - url: 论文的 URL (例如 arXiv 链接)
    - profile: 使用的配置预设 (默认为 'default')
    - keep-source: 标志位，如果设置，处理后不删除 NotebookLM 中的源文件
    - config: 配置文件路径 (默认为 'config.yaml')
    """
    
    # 1. 加载配置
    # 尝试加载用户指定的配置文件和认证信息
    try:
        cfg = load_config(config, profile)
        auth = get_auth_config()
    except Exception as e:
        click.echo(f"错误: 加载配置失败: {e}", err=True)
        raise click.Abort()
    
    # 清理 URL (去除空白字符)
    url = url.strip()
    click.echo(f"正在处理 URL: '{url}'")

    # 确定是否保留源文件
    # 命令行参数 keep_source 优先级高于配置文件中的 keep_source
    should_keep_source = keep_source or cfg.keep_source
    
    # 2. 尝试从 URL 中提取 ArXiv ID
    # 用于后续生成文件名时作为标识符
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        click.echo(f"检测到 ArXiv ID: {arxiv_id}")
        # 为了提高稳定性，强制将其转换为 PDF 链接
        # NotebookLM 处理 PDF 通常比处理 ArXiv 的 HTML 页面更稳定
        new_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if url != new_url:
             click.echo(f"自动转换为 PDF 链接: {new_url}")
             url = new_url
    else:
        # 如果无法提取 ID，使用 'unknown'
        arxiv_id = "unknown"

    # 定义输出目录: {cfg.output_dir}/{arxiv_id}/
    output_dir = Path(cfg.output_dir) / arxiv_id

    # 定义异步处理流程
    async def process():
        click.echo(f"正在初始化 NotebookClient (Profile: {profile})...")
        client = NotebookClient(auth)
        
        source_id = None
        artifact_id = None
        try:
            # 3. 添加资源 (Source)
            click.echo(f"正在添加资源: {url}...")
            source_id = await client.add_source(url)
            click.echo(f"资源已添加 (ID: {source_id})")
            
            # 4. 生成摘要 (Summary)
            click.echo("正在生成摘要...")
            # 使用配置中的提示词生成摘要
            summary_text = await client.generate_summary(source_id, cfg.summary_prompt)
            
            # 保存摘要到 Markdown 文件
            # 路径: {output_dir}/summary_{arxiv_id}_{timestamp}.md
            summary_filename = generate_timestamped_name("summary", ".md", identifier=arxiv_id)
            summary_path = output_dir / summary_filename
            saved_summary = save_content(summary_path, summary_text)
            click.echo(f"摘要已保存至: {saved_summary}")
            
            # 5. 生成演示文稿 (Presentation/Slide Deck)
            click.echo("正在生成演示文稿 (这可能需要几分钟)...")
            # 调用耗时的生成接口，返回 PDF 二进制内容和生成的 artifact ID
            presentation_bytes, artifact_id = await client.generate_presentation(
                source_id, 
                cfg.presentation_prompt,
                timeout=cfg.timeout,
                max_retries=cfg.max_retries
            )
            
            # 保存演示文稿为 PDF 文件
            # 路径: {output_dir}/presentation_{arxiv_id}_{timestamp}.pdf
            presentation_filename = generate_timestamped_name("presentation", ".pdf", identifier=arxiv_id)
            presentation_path = output_dir / presentation_filename
            saved_pres = save_content(presentation_path, presentation_bytes, mode='wb')
            click.echo(f"演示文稿已保存至: {saved_pres}")
            
        except Exception as e:
            click.echo(f"处理过程中出错: {e}", err=True)
            # 如果出错，退出码设为 1，以便 batch 脚本感知
            import sys
            sys.exit(1)
        finally:
            # 6. 清理资源 (Cleanup)
            
            # 清理上传的源文件 (Source)
            if source_id and not should_keep_source:
                click.echo("正在清理资源...")
                try:
                    await client.delete_source(source_id)
                    click.echo("资源已删除。")
                except Exception as e:
                    click.echo(f"删除资源失败: {e}", err=True)
            elif source_id:
                click.echo("跳过资源清理。")

            # 清理生成的 Artifact (如幻灯片对象)
            # 只有在成功生成了 artifact_id 且不保留源时才清理
            if artifact_id and not should_keep_source:
                click.echo("正在清理生成物...")
                try:
                    await client.delete_artifact(artifact_id)
                    click.echo("生成物已删除。")
                except Exception as e:
                    click.echo(f"删除生成物失败: {e}", err=True)
            elif artifact_id:
                click.echo("跳过生成物清理。")
                
            # 关闭客户端连接
            await client.close()
            
        click.echo("完成。")

    # 运行异步主循环
    run_async(process())

if __name__ == '__main__':
    cli()