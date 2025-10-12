"""
Tests for the core ConfigManager class
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.mcp_config_manager.core.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager"""

    def test_init(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        # Check that parsers are initialized
        assert manager.claude_parser is not None
        assert manager.gemini_parser is not None
        assert manager.codex_parser is not None
        # Check that managers are initialized
        assert manager.server_manager is not None
        assert manager.preset_manager is not None
        # Check that paths are set
        assert manager.claude_path is not None
        assert manager.gemini_path is not None
        assert manager.codex_path is not None

    def test_init_with_path(self):
        """Test ConfigManager initialization with custom paths"""
        claude_path = Path("/test/claude/path")
        gemini_path = Path("/test/gemini/path")
        codex_path = Path("/test/codex/path")
        manager = ConfigManager(claude_path, gemini_path, codex_path)
        assert manager.claude_path == claude_path
        assert manager.gemini_path == gemini_path
        assert manager.codex_path == codex_path

    @patch('src.mcp_config_manager.core.config_manager.ClaudeConfigParser')
    @patch('src.mcp_config_manager.core.config_manager.GeminiConfigParser')
    @patch('src.mcp_config_manager.core.config_manager.CodexConfigParser')
    @patch('src.mcp_config_manager.core.config_manager.ServerManager')
    def test_list_servers_empty(self, mock_server_manager, mock_codex_parser,
                                mock_gemini_parser, mock_claude_parser):
        """Test listing servers when none are configured"""
        # Create mock instances
        mock_claude_instance = Mock()
        mock_gemini_instance = Mock()
        mock_codex_instance = Mock()
        mock_server_instance = Mock()

        # Configure mocks to return empty configs
        mock_claude_instance.parse.return_value = {'mcpServers': {}}
        mock_gemini_instance.parse.return_value = {'mcpServers': {}}
        mock_codex_instance.parse.return_value = {'mcpServers': {}}

        # Configure server manager to return empty lists
        mock_server_instance.list_all_servers.return_value = ([], [])

        # Set up mock constructors
        mock_claude_parser.return_value = mock_claude_instance
        mock_gemini_parser.return_value = mock_gemini_instance
        mock_codex_parser.return_value = mock_codex_instance
        mock_server_manager.return_value = mock_server_instance

        # Create manager and test
        manager = ConfigManager()
        active, disabled = manager.list_servers()
        assert active == []
        assert disabled == []

    # TODO: Add more tests as functionality is implemented
