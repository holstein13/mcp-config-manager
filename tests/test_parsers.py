"""
Tests for configuration parsers
"""

import pytest
from pathlib import Path
import tempfile
import json
from src.mcp_config_manager.parsers.claude_parser import ClaudeConfigParser
from src.mcp_config_manager.parsers.gemini_parser import GeminiConfigParser


class TestClaudeConfigParser:
    """Test cases for Claude configuration parser"""
    
    def test_parse_valid_config(self):
        """Test parsing a valid Claude configuration"""
        parser = ClaudeConfigParser()
        
        # Create a temporary config file
        test_config = {
            "mcpServers": {
                "test-server": {
                    "command": "test-command",
                    "args": ["--test"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            assert result == test_config
        finally:
            temp_path.unlink()  # Clean up
    
    # TODO: Add more parser tests


class TestGeminiConfigParser:
    """Test cases for Gemini configuration parser"""
    
    def test_validate_returns_true(self):
        """Test that validation returns True (placeholder)"""
        parser = GeminiConfigParser()
        assert parser.validate({}) is True
    
    # TODO: Add more parser tests
