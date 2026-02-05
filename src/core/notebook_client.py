import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Union, Tuple
from notebooklm.client import NotebookLMClient
from notebooklm.auth import AuthTokens
from notebooklm.types import GenerationStatus

class NotebookClient:
    """
    NotebookLM 客户端封装类。
    负责与 Google NotebookLM API 进行交互，处理认证、资源管理和内容生成。
    """
    
    def __init__(self, auth_config: dict):
        """
        初始化 NotebookClient。
        
        Args:
            auth_config (dict): 包含 'token' 和 'cookies' 的字典。
                                如果为空，将尝试使用本地存储的认证状态。
        """
        self.cookies_raw = auth_config.get("cookies")
        self.token = auth_config.get("token")
        self.client: Optional[NotebookLMClient] = None
        self.notebook_id: Optional[str] = None
        self.notebook_title = "TestPaperFlow" # 默认使用的笔记本标题

    async def _get_client(self) -> NotebookLMClient:
        """
        获取或初始化内部的 NotebookLMClient 实例。
        
        策略:
        1. 如果已有连接的 client，直接返回。
        2. 如果提供了环境变量 (cookies 和 token)，尝试使用它们登录。
        3. 如果环境变量缺失或失败，尝试加载本地存储 (~/.notebooklm/storage_state.json)。
        
        Returns:
            NotebookLMClient: 已连接的客户端实例
        """
        if self.client and self.client.is_connected:
            return self.client
            
        # 尝试使用环境变量认证
        if self.cookies_raw and self.token:
            cookie_dict = {}
            # 解析 cookie 字符串
            for item in self.cookies_raw.split(';'):
                if '=' in item:
                    k, v = item.strip().split('=', 1)
                    cookie_dict[k] = v
            
            auth = AuthTokens(cookies=cookie_dict, csrf_token="", session_id="")
            client = NotebookLMClient(auth)
            try:
                await client.__aenter__()
                await client.refresh_auth()
                self.client = client
                return self.client
            except Exception as e:
                # 如果认证失败，清理并尝试备选方案
                if client: await client.__aexit__(None, None, None)
                print(f"警告: 环境变量认证失败，尝试备选方案: {e}")

        # 尝试使用本地存储认证
        storage_path = Path.home() / ".notebooklm" / "storage_state.json"
        if storage_path.exists():
            try:
                client = await NotebookLMClient.from_storage(str(storage_path))
                await client.__aenter__()
                self.client = client
                return self.client
            except Exception as e:
                print(f"错误: 无法从存储文件加载状态: {e}")
        
        raise ValueError("未找到有效的认证信息。请运行 'notebooklm login' 完成登录。")

    async def _get_or_create_notebook(self) -> str:
        """
        获取当前工作用的笔记本 ID，如果不存在则创建。
        
        Returns:
            str: Notebook ID
        """
        if self.notebook_id:
            return self.notebook_id
            
        client = await self._get_client()
        notebooks = await client.notebooks.list()
        
        # 查找匹配标题的笔记本
        for nb in notebooks:
            if nb.title == self.notebook_title:
                self.notebook_id = nb.id
                return nb.id
        
        # 未找到则新建
        new_nb = await client.notebooks.create(title=self.notebook_title)
        self.notebook_id = new_nb.id
        return new_nb.id

    async def add_source(self, url: str) -> str:
        """
        向笔记本添加资源 (URL)。
        
        Args:
            url (str): 资源的 URL (如 PDF 链接或网页)
            
        Returns:
            str: 新添加资源的 Source ID
        """
        client = await self._get_client()
        notebook_id = await self._get_or_create_notebook()
        # wait=True 确保资源处理完成后再返回
        source = await client.sources.add_url(notebook_id, url, wait=True)
        return source.id

    async def generate_summary(self, source_id: str, prompt: str) -> str:
        """
        生成摘要。实际是通过 Chat 接口发送 Prompt。
        
        Args:
            source_id (str): 资源 ID (虽然 Chat 是针对整个 Notebook，但逻辑上关联)
            prompt (str): 提示词
            
        Returns:
            str: 生成的摘要文本
        """
        client = await self._get_client()
        notebook_id = await self._get_or_create_notebook()
        
        max_retries = 3
        current_delay = 5.0
        
        for attempt in range(max_retries):
            try:
                response = await client.chat.ask(notebook_id, prompt)
                return response.answer
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"生成摘要失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    print(f"等待 {current_delay:.1f} 秒后重试...")
                    await asyncio.sleep(current_delay)
                    current_delay *= 1.5
                else:
                    print(f"生成摘要失败，已达到最大重试次数。")
                    raise e
        return "" # Should not be reached

    async def generate_presentation(self, source_id: str, prompt: str, timeout: float = 1800.0, max_retries: int = 5) -> Tuple[bytes, str]:
        """
        生成演示文稿 (幻灯片)。
        
        流程:
        1. 提交生成 Slide Deck 的任务。
        2. 等待任务完成。
        3. 查找生成的 Slide Deck Artifact。
        4. 下载 Artifact 为 PDF 格式。
        
        Args:
            source_id (str): 资源 ID
            prompt (str): 指导生成的指令
            timeout (float): 等待生成的超时时间 (秒)
            max_retries (int): 列出幻灯片的重试次数
            
        Returns:
            Tuple[bytes, str]: (PDF文件内容的二进制数据, Artifact ID)
        """
        client = await self._get_client()
        notebook_id = await self._get_or_create_notebook()
        
        print("正在提交 Slide Deck 生成任务...")
        status = await client.artifacts.generate_slide_deck(
            notebook_id=notebook_id,
            instructions=prompt,
            language="zh" # 强制指定中文
        )
        
        print(f"任务已提交 (ID: {status.task_id})，等待完成 (超时: {timeout}s)...")
        # 轮询等待任务完成
        await client.artifacts.wait_for_completion(
            notebook_id, 
            status.task_id, 
            timeout=timeout
        )

        # 任务完成后等待几秒，确保服务器状态同步
        await asyncio.sleep(3)
        
        # 获取最新的幻灯片列表 (增加重试机制和指数退避)
        slides = None
        current_delay = 5.0
        for attempt in range(max_retries):
            try:
                slides = await client.artifacts.list_slide_decks(notebook_id)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"列出幻灯片失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    print(f"等待 {current_delay:.1f} 秒后重试...")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 1.5, 60.0) # 指数退避，上限 60秒
                else:
                    print(f"列出幻灯片失败，已达到最大重试次数。")
                    raise e
                    
        if not slides:
            raise RuntimeError("未找到生成的幻灯片文件")
            
        # 假设列表是按时间倒序排列的，取最新的一个
        latest_slide = slides[0]
        print(f"正在下载幻灯片: {latest_slide.title} (ID: {latest_slide.id})")
        
        # 使用临时文件下载 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            await client.artifacts.download_slide_deck(
                notebook_id=notebook_id, 
                output_path=tmp_path, 
                artifact_id=latest_slide.id
            )
            # 读取下载的文件内容
            with open(tmp_path, 'rb') as f:
                content = f.read()
            return content, latest_slide.id
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def delete_source(self, source_id: str) -> None:
        """
        删除资源。
        """
        client = await self._get_client()
        if self.notebook_id:
             await client.sources.delete(self.notebook_id, source_id)

    async def delete_artifact(self, artifact_id: str) -> None:
        """
        删除生成物 (如幻灯片)。
        """
        client = await self._get_client()
        if self.notebook_id:
             await client.artifacts.delete(self.notebook_id, artifact_id)
        
    async def close(self):
        """
        关闭客户端连接。
        """
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None