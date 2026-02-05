import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
from src.cli.main import cli
from src.core.config import ProcessingConfig

@pytest.fixture
def mock_client_cls():
    with patch("src.cli.main.NotebookClient") as MockClass:
        mock_instance = AsyncMock()
        MockClass.return_value = mock_instance
        yield MockClass

@pytest.fixture
def mock_config():
    with patch("src.cli.main.load_config") as mock_load:
        mock_load.return_value = ProcessingConfig(
            profile_name="default",
            summary_prompt="Sum Prompt",
            presentation_prompt="Pres Prompt",
            keep_source=False
        )
        yield mock_load

@pytest.fixture
def mock_auth():
    with patch("src.cli.main.get_auth_config") as mock_get_auth:
        mock_get_auth.return_value = {"token": "t", "cookies": "c"}
        yield mock_get_auth

def test_cli_full_flow(mock_client_cls, mock_config, mock_auth):
    """测试 CLI 完整流程"""
    runner = CliRunner()
    url = "https://arxiv.org/html/2601.16206v1"
    
    # Setup mock behavior
    client_instance = mock_client_cls.return_value
    client_instance.add_source.return_value = "source_123"
    client_instance.generate_summary.return_value = "Summary"
    client_instance.generate_presentation.return_value = "Presentation"
    
    with patch("src.cli.main.save_content") as mock_save:
        mock_save.side_effect = lambda path, content, mode='w': path # return path
        
        result = runner.invoke(cli, [url])
        
        if result.exit_code != 0:
            print(result.output) # Debug info
            
        assert result.exit_code == 0
        assert "Initializing" in result.output
        assert "Done" in result.output
        
        # Verify calls
        client_instance.add_source.assert_called_once_with(url)
        client_instance.generate_summary.assert_called_once()
        client_instance.generate_presentation.assert_called_once()
        client_instance.delete_source.assert_called_once() # Default cleanup
        
        assert mock_save.call_count == 2

def test_cli_profile_flow(mock_client_cls, mock_config, mock_auth):
    """测试指定 Profile 的流程"""
    runner = CliRunner()
    url = "https://arxiv.org/html/2601.16206v1"
    
    with patch("src.cli.main.save_content"):
        result = runner.invoke(cli, [url, '--profile', 'custom'])
        
        assert result.exit_code == 0
        # Verify load_config was called with 'custom'
        # mock_config is the mock object for load_config
        # Note: fixture returns the mock object
        mock_config.assert_called_with('config.yaml', 'custom')