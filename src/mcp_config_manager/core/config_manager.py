"""
Core configuration management functionality
Enhanced with functionality from mcp_toggle.py
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

from ..parsers.claude_parser import ClaudeConfigParser
from ..parsers.gemini_parser import GeminiConfigParser
from ..utils.file_utils import (
    get_claude_config_path, get_gemini_config_path, 
    ensure_config_directories
)
from ..utils.backup import backup_all_configs
from ..utils.sync import sync_server_configs
from .server_manager import ServerManager
from .presets import PresetManager


class ConfigManager:
    """
    Main configuration manager class
    Enhanced with functionality from original mcp_toggle.py
    """
    
    def __init__(self, claude_path: Optional[Path] = None, gemini_path: Optional[Path] = None):
        self.claude_path = claude_path or get_claude_config_path()
        self.gemini_path = gemini_path or get_gemini_config_path()
        
        self.claude_parser = ClaudeConfigParser()
        self.gemini_parser = GeminiConfigParser()
        self.server_manager = ServerManager()
        self.preset_manager = PresetManager()
        
        # Ensure all directories exist
        ensure_config_directories()
    
    def load_configs(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load both Claude and Gemini configurations"""
        claude_data = self.claude_parser.parse(self.claude_path)
        gemini_data = self.gemini_parser.parse(self.gemini_path)
        return claude_data, gemini_data
    
    def save_configs(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                    mode: str = 'both') -> None:
        """Save configurations based on mode"""
        if mode in ['claude', 'both']:
            self.claude_parser.write(claude_data, self.claude_path)
        
        if mode in ['gemini', 'both']:
            self.gemini_parser.write(gemini_data, self.gemini_path)
    
    def create_backups(self) -> List[Tuple[str, Path]]:
        """Create timestamped backups of all config files"""
        return backup_all_configs(self.claude_path, self.gemini_path)
    
    def sync_configurations(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Synchronize servers between Claude and Gemini configs"""
        return sync_server_configs(claude_data, gemini_data)
    
    def list_servers(self, mode: str = 'both') -> Tuple[List[str], List[str]]:
        """List all servers (active and disabled)"""
        claude_data, gemini_data = self.load_configs()
        return self.server_manager.list_all_servers(claude_data, gemini_data, mode)
    
    def disable_server(self, server_name: str, mode: str = 'both') -> bool:
        """Disable a server (move to storage)"""
        claude_data, gemini_data = self.load_configs()
        success = self.server_manager.disable_server(claude_data, gemini_data, server_name, mode)
        if success:
            self.save_configs(claude_data, gemini_data, mode)
        return success
    
    def enable_server(self, server_name: str, mode: str = 'both') -> bool:
        """Enable a server (move from storage)"""
        claude_data, gemini_data = self.load_configs()
        success = self.server_manager.enable_server(claude_data, gemini_data, server_name, mode)
        if success:
            self.save_configs(claude_data, gemini_data, mode)
        return success
    
    def disable_all_servers(self, mode: str = 'both') -> int:
        """Disable all active servers"""
        claude_data, gemini_data = self.load_configs()
        count = self.server_manager.disable_all_servers(claude_data, gemini_data, mode)
        self.save_configs(claude_data, gemini_data, mode)
        return count
    
    def enable_all_servers(self, mode: str = 'both') -> int:
        """Enable all disabled servers"""
        claude_data, gemini_data = self.load_configs()
        count = self.server_manager.enable_all_servers(claude_data, gemini_data, mode)
        self.save_configs(claude_data, gemini_data, mode)
        return count
    
    def apply_preset_mode(self, preset_mode: str, mode: str = 'both') -> List[str]:
        """Apply a preset mode (minimal, webdev, etc.)"""
        claude_data, gemini_data = self.load_configs()
        
        # Get servers to keep active for this preset
        keep_active = self.preset_manager.get_default_servers(preset_mode)
        
        # Get current server lists
        active, disabled = self.server_manager.list_all_servers(claude_data, gemini_data, mode)
        
        # Disable servers not in the preset
        for server in active:
            if server not in keep_active:
                self.server_manager.disable_server(claude_data, gemini_data, server, mode)
        
        # Enable servers that should be active
        for server in keep_active:
            if server in disabled:
                self.server_manager.enable_server(claude_data, gemini_data, server, mode)
        
        self.save_configs(claude_data, gemini_data, mode)
        return keep_active
    
    def add_server_from_json(self, json_text: str, server_name: str = None, 
                           mode: str = 'both') -> Tuple[bool, str]:
        """Add a new server from JSON configuration"""
        claude_data, gemini_data = self.load_configs()
        
        if server_name:
            # Single server with provided name
            try:
                server_config = json.loads(json_text.strip())
                success = self.server_manager.add_server_with_name(
                    claude_data, gemini_data, server_name, server_config, mode)
                if success:
                    self.save_configs(claude_data, gemini_data, mode)
                    return True, f"Added server: {server_name}"
                else:
                    return False, "Failed to add server"
            except json.JSONDecodeError as e:
                return False, f"JSON parsing failed: {e}"
        else:
            # Multiple servers or single server needing name
            success, message = self.server_manager.add_new_server_from_json(
                claude_data, gemini_data, json_text, mode)
            if success:
                self.save_configs(claude_data, gemini_data, mode)
            return success, message
    
    def validate_configs(self) -> Tuple[bool, bool]:
        """Validate both configuration files"""
        claude_data, gemini_data = self.load_configs()
        claude_valid = self.claude_parser.validate(claude_data)
        gemini_valid = self.gemini_parser.validate(gemini_data)
        return claude_valid, gemini_valid
    
    # Preset management methods
    def list_presets(self) -> List[str]:
        """List all available presets"""
        return self.preset_manager.list_presets()
    
    def load_preset(self, preset_name: str, mode: str = 'both') -> bool:
        """Load a specific preset configuration"""
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            return False
        
        claude_data, gemini_data = self.load_configs()
        
        # First disable all servers
        self.server_manager.disable_all_servers(claude_data, gemini_data, mode)
        
        # Then add servers from preset
        preset_servers = preset.get('servers', {})
        for server_name, server_config in preset_servers.items():
            self.server_manager.add_server_with_name(
                claude_data, gemini_data, server_name, server_config, mode)
        
        self.save_configs(claude_data, gemini_data, mode)
        return True
    
    def save_current_as_preset(self, preset_name: str, description: str, 
                              mode: str = 'both') -> None:
        """Save current active configuration as a preset"""
        claude_data, gemini_data = self.load_configs()
        
        # Get currently active servers
        if mode == 'claude':
            servers = claude_data.get('mcpServers', {})
        elif mode == 'gemini':
            servers = gemini_data.get('mcpServers', {})
        else:  # both
            # Merge servers from both configs
            servers = {}
            servers.update(claude_data.get('mcpServers', {}))
            servers.update(gemini_data.get('mcpServers', {}))
        
        self.preset_manager.save_preset(preset_name, description, servers)
