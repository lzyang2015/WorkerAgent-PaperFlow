import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from src.core.notebook_client import NotebookClient

@pytest.fixture
def mock_notebooklm_client():
    with patch("src.core.notebook_client.NotebookLMClient") as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value = mock_instance
        
        mock_instance.refresh_auth = AsyncMock()
        mock_instance.notebooks = MagicMock()
        mock_instance.notebooks.list = AsyncMock()
        mock_instance.notebooks.create = AsyncMock()
        
        mock_instance.sources = MagicMock()
        mock_instance.sources.add_url = AsyncMock()
        mock_instance.sources.delete = AsyncMock()
        
        mock_instance.chat = MagicMock()
        mock_instance.chat.ask = AsyncMock()

        # Mock Artifacts API
        mock_instance.artifacts = MagicMock()
        mock_instance.artifacts.generate_slide_deck = AsyncMock()
        mock_instance.artifacts.wait_for_completion = AsyncMock()
        mock_instance.artifacts.list_slide_decks = AsyncMock()
        mock_instance.artifacts.download_slide_deck = AsyncMock()
        
        MockClient.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def client():
    config = {"cookies": "test_cookie", "token": "test_token"}
    return NotebookClient(config)

@pytest.mark.asyncio
async def test_add_source(client, mock_notebooklm_client):
    """测试添加 Source"""
    url = "https://arxiv.org/html/2601.16206v1"
    expected_source_id = "source_123"
    notebook_id = "nb_123"
    
    mock_notebook = MagicMock()
    mock_notebook.title = "TestPaperFlow"
    mock_notebook.id = notebook_id
    mock_notebooklm_client.notebooks.list.return_value = [mock_notebook]
    
    mock_source = MagicMock()
    mock_source.id = expected_source_id
    mock_notebooklm_client.sources.add_url.return_value = mock_source
    
    source_id = await client.add_source(url)
    assert source_id == expected_source_id
    mock_notebooklm_client.sources.add_url.assert_called_once_with(notebook_id, url, wait=True)

@pytest.mark.asyncio
async def test_generate_summary(client, mock_notebooklm_client):
    """测试生成摘要"""
    source_id = "source_123"
    notebook_id = "nb_123"
    prompt = "Summarize this"
    expected_summary = "This is a summary."
    
    mock_notebook = MagicMock()
    mock_notebook.title = "TestPaperFlow"
    mock_notebook.id = notebook_id
    mock_notebooklm_client.notebooks.list.return_value = [mock_notebook]

    mock_response = MagicMock()
    mock_response.answer = expected_summary
    mock_notebooklm_client.chat.ask.return_value = mock_response
    
    summary = await client.generate_summary(source_id, prompt)
    assert summary == expected_summary
    mock_notebooklm_client.chat.ask.assert_called_once_with(notebook_id, prompt)

@pytest.mark.asyncio
async def test_generate_presentation_binary(client, mock_notebooklm_client):
    """测试生成二进制幻灯片 (PDF)"""
    source_id = "source_123"
    notebook_id = "nb_123"
    prompt = "Create slides"
    expected_bytes = b"%PDF-1.4 binary data"
    
    mock_notebook = MagicMock()
    mock_notebook.title = "TestPaperFlow"
    mock_notebook.id = notebook_id
    mock_notebooklm_client.notebooks.list.return_value = [mock_notebook]
    
    # Mock generation steps
    mock_status = MagicMock()
    mock_status.task_id = "task_456"
    mock_notebooklm_client.artifacts.generate_slide_deck.return_value = mock_status
    
    mock_slide = MagicMock()
    mock_slide.id = "slide_789"
    mock_slide.title = "Test Slides"
    mock_notebooklm_client.artifacts.list_slide_decks.return_value = [mock_slide]
    
    # We need to mock the side effect of download_slide_deck to write to the file
    async def mock_download(notebook_id, output_path, artifact_id):
        with open(output_path, 'wb') as f:
            f.write(expected_bytes)
        return output_path
    
    mock_notebooklm_client.artifacts.download_slide_deck.side_effect = mock_download
    
    content = await client.generate_presentation(source_id, prompt, timeout=60.0)
    
    assert content == expected_bytes
    mock_notebooklm_client.artifacts.generate_slide_deck.assert_called_once()
    mock_notebooklm_client.artifacts.wait_for_completion.assert_called_once_with(notebook_id, "task_456", timeout=60.0)
    
    # Verify download called with ANY path
    mock_notebooklm_client.artifacts.download_slide_deck.assert_called_once_with(notebook_id=notebook_id, output_path=ANY, artifact_id="slide_789")

@pytest.mark.asyncio
async def test_delete_source(client, mock_notebooklm_client):
    """测试删除 Source"""
    source_id = "source_123"
    notebook_id = "nb_123"
    
    mock_notebook = MagicMock()
    mock_notebook.title = "TestPaperFlow"
    mock_notebook.id = notebook_id
    mock_notebooklm_client.notebooks.list.return_value = [mock_notebook]
    
    await client._get_or_create_notebook()
    await client.delete_source(source_id)
    mock_notebooklm_client.sources.delete.assert_called_once_with(notebook_id, source_id)
