"""
Tests for the core ConfigManager class
"""

import pytest
from pathlib import Path
from src.mcp_config_manager.core.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager"""
    
    def test_init(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        assert manager.servers == {}
        assert manager.config_path is None
    
    def test_init_with_path(self):
        """Test ConfigManager initialization with path"""
        test_path = Path("/test/path")
        manager = ConfigManager(test_path)
        assert manager.config_path == test_path
    
    def test_list_servers_empty(self):
        """Test listing servers when none are configured"""
        manager = ConfigManager()
        assert manager.list_servers() == []
    
    # TODO: Add more tests as functionality is implemented
