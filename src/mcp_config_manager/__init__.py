"""
MCP Config Manager

A cross-platform GUI utility for managing Model Context Protocol (MCP) 
server configurations across Claude, Gemini, and other AI systems.
"""

__version__ = "0.1.0"
__author__ = "MCP Config Manager Contributors"
__email__ = "your-email@example.com"

from .core.config_manager import ConfigManager
from .parsers.claude_parser import ClaudeConfigParser
from .parsers.gemini_parser import GeminiConfigParser

__all__ = [
    "ConfigManager",
    "ClaudeConfigParser", 
    "GeminiConfigParser",
]
