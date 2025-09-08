"""
MCP Config Manager

A cross-platform GUI utility for managing Model Context Protocol (MCP) 
server configurations across Claude, Gemini, and other AI systems.

Enhanced with functionality from the original mcp_toggle.py script.
"""

__version__ = "0.1.0"
__author__ = "MCP Config Manager Contributors"
__email__ = "your-email@example.com"

from .core.config_manager import ConfigManager
from .core.server_manager import ServerManager
from .core.presets import PresetManager
from .parsers.claude_parser import ClaudeConfigParser
from .parsers.gemini_parser import GeminiConfigParser
from .utils.backup import backup_all_configs, create_backup
from .utils.sync import sync_server_configs
from .utils.file_utils import (
    get_claude_config_path, 
    get_gemini_config_path, 
    get_presets_path,
    ensure_config_directories
)

__all__ = [
    "ConfigManager",
    "ServerManager", 
    "PresetManager",
    "ClaudeConfigParser", 
    "GeminiConfigParser",
    "backup_all_configs",
    "create_backup",
    "sync_server_configs",
    "get_claude_config_path",
    "get_gemini_config_path", 
    "get_presets_path",
    "ensure_config_directories",
]
