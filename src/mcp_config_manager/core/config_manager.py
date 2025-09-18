"""
Core configuration management functionality
Enhanced with functionality from mcp_toggle.py
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from enum import Enum

from ..parsers.claude_parser import ClaudeConfigParser
from ..parsers.gemini_parser import GeminiConfigParser
from ..utils.file_utils import (
    get_claude_config_path, get_gemini_config_path, get_codex_config_path,
    ensure_config_directories
)
from ..utils.backup import backup_all_configs
from ..utils.sync import sync_server_configs
from .server_manager import ServerManager
from .presets import PresetManager
from ..auth.google_auth import GoogleAuthManager
from ..parsers.codex_parser import CodexConfigParser
from .cli_detector import CLIDetector


class ConfigMode(Enum):
    """Configuration mode for the application."""

    CLAUDE = "claude"
    GEMINI = "gemini"
    CODEX = "codex"
    BOTH = "both"  # legacy alias for Claude + Gemini
    ALL = "all"


class ConfigManager:
    """
    Main configuration manager class
    Enhanced with functionality from original mcp_toggle.py
    """
    
    SUPPORTED_CLIENTS = ("claude", "gemini", "codex")

    def __init__(
        self,
        claude_path: Optional[Path] = None,
        gemini_path: Optional[Path] = None,
        codex_path: Optional[Path] = None,
    ):
        self.claude_path = claude_path or get_claude_config_path()
        self.gemini_path = gemini_path or get_gemini_config_path()
        self.codex_path = codex_path or get_codex_config_path()

        self.claude_parser = ClaudeConfigParser()
        self.gemini_parser = GeminiConfigParser()
        self.codex_parser = CodexConfigParser()

        self.server_manager = ServerManager()
        self.preset_manager = PresetManager()
        self.cli_detector = CLIDetector()

        # Initialize Google auth (project_id can be set later)
        self.google_auth = GoogleAuthManager()

        # Ensure all directories exist
        ensure_config_directories()
    
    def load_configs(self) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Load Claude, Gemini, and Codex configurations."""

        claude_data = self.claude_parser.parse(self.claude_path)
        gemini_data = self.gemini_parser.parse(self.gemini_path)
        codex_data = self.codex_parser.parse(self.codex_path)
        return claude_data, gemini_data, codex_data

    def _build_config_map(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        codex_data: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Bundle individual config dicts into a client-keyed map."""

        return {
            "claude": claude_data,
            "gemini": gemini_data,
            "codex": codex_data,
        }

    def _resolve_mode_clients(self, mode: Optional[str]) -> List[str]:
        """Translate configuration mode string into client list."""

        if not mode or mode.lower() in {ConfigMode.ALL.value, "all"}:
            return list(self.SUPPORTED_CLIENTS)

        mode = mode.lower()
        if mode == ConfigMode.BOTH.value:
            return [ConfigMode.CLAUDE.value, ConfigMode.GEMINI.value]

        if mode in self.SUPPORTED_CLIENTS:
            return [mode]

        # Fallback for unknown modes: treat as all
        return list(self.SUPPORTED_CLIENTS)

    def get_cli_availability(self, force_refresh: bool = False) -> Dict[str, bool]:
        """Expose cached CLI availability information to callers."""

        return self.cli_detector.detect_all(force_refresh=force_refresh)
    
    def save_configs(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        codex_data: Dict[str, Any],
        mode: str = "all",
    ) -> None:
        """Persist configuration changes for selected clients."""

        clients = set(self._resolve_mode_clients(mode))

        if "claude" in clients:
            self.claude_parser.write(claude_data, self.claude_path)

        if "gemini" in clients:
            self.gemini_parser.write(gemini_data, self.gemini_path)

        if "codex" in clients:
            self.codex_parser.write(codex_data, self.codex_path)
    
    def create_backups(self) -> List[Tuple[str, Path]]:
        """Create timestamped backups of all config files"""
        return backup_all_configs(self.claude_path, self.gemini_path)
    
    def create_backup(self) -> Dict[str, Any]:
        """Create timestamped backups of all config files and return GUI-compatible result"""
        try:
            backups = backup_all_configs(self.claude_path, self.gemini_path)
            if backups:
                # Return the first backup file path for compatibility
                return {
                    'success': True,
                    'backup_file': str(backups[0][1]),  # First backup file path as string
                    'all_backups': [(name, str(path)) for name, path in backups]
                }
            else:
                return {
                    'success': False,
                    'error': 'No backup files were created'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create backup: {str(e)}'
            }
    
    def sync_configurations(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Synchronize servers between Claude and Gemini configs"""
        return sync_server_configs(claude_data, gemini_data)
    
    def list_servers(self, mode: str = 'both') -> Tuple[List[str], List[str]]:
        """List all servers (active and disabled)"""
        claude_data, gemini_data, codex_data = self.load_configs()
        return self.server_manager.list_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )

    def disable_server(self, server_name: str, mode: str = 'both') -> bool:
        """Disable a server (move to storage)"""
        claude_data, gemini_data, codex_data = self.load_configs()
        success = self.server_manager.disable_server(
            claude_data,
            gemini_data,
            server_name,
            mode,
            codex_data=codex_data,
        )
        if success:
            self.save_configs(claude_data, gemini_data, codex_data, mode)
        return success

    def enable_server(self, server_name: str, mode: str = 'both') -> bool:
        """Enable a server (move from storage)"""
        claude_data, gemini_data, codex_data = self.load_configs()
        success = self.server_manager.enable_server(
            claude_data,
            gemini_data,
            server_name,
            mode,
            codex_data=codex_data,
        )
        if success:
            self.save_configs(claude_data, gemini_data, codex_data, mode)
        return success

    def disable_all_servers(self, mode: str = 'both') -> int:
        """Disable all active servers"""
        claude_data, gemini_data, codex_data = self.load_configs()
        count = self.server_manager.disable_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        self.save_configs(claude_data, gemini_data, codex_data, mode)
        return count

    def enable_all_servers(self, mode: str = 'both') -> int:
        """Enable all disabled servers"""
        claude_data, gemini_data, codex_data = self.load_configs()
        count = self.server_manager.enable_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        self.save_configs(claude_data, gemini_data, codex_data, mode)
        return count

    def apply_preset_mode(self, preset_mode: str, mode: str = 'both') -> List[str]:
        """Apply a preset mode (minimal, webdev, etc.)"""
        claude_data, gemini_data, codex_data = self.load_configs()
        
        # Get servers to keep active for this preset
        keep_active = self.preset_manager.get_default_servers(preset_mode)
        
        # Get current server lists
        active, disabled = self.server_manager.list_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        
        # Disable servers not in the preset
        for server in active:
            name = server['name'] if isinstance(server, dict) else server
            if name not in keep_active:
                self.server_manager.disable_server(
                    claude_data,
                    gemini_data,
                    name,
                    mode,
                    codex_data=codex_data,
                )
        
        # Enable servers that should be active
        for server in keep_active:
            disabled_names = {s['name'] if isinstance(s, dict) else s for s in disabled}
            if server in disabled_names:
                self.server_manager.enable_server(
                    claude_data,
                    gemini_data,
                    server,
                    mode,
                    codex_data=codex_data,
                )
        
        self.save_configs(claude_data, gemini_data, codex_data, mode)
        return keep_active
    
    def add_server_from_json(self, json_text: str, server_name: str = None, 
                           mode: str = 'both') -> Tuple[bool, str]:
        """Add a new server from JSON configuration"""
        claude_data, gemini_data, codex_data = self.load_configs()
        
        if server_name:
            # Single server with provided name
            try:
                server_config = json.loads(json_text.strip())
                success = self.server_manager.add_server_with_name(
                    claude_data,
                    gemini_data,
                    server_name,
                    server_config,
                    mode,
                    codex_data=codex_data,
                )
                if success:
                    self.save_configs(claude_data, gemini_data, codex_data, mode)
                    return True, f"Added server: {server_name}"
                else:
                    return False, "Failed to add server"
            except json.JSONDecodeError as e:
                return False, f"JSON parsing failed: {e}"
        else:
            # Multiple servers or single server needing name
            success, message = self.server_manager.add_new_server_from_json(
                claude_data,
                gemini_data,
                json_text,
                mode,
                codex_data=codex_data,
            )
            if success:
                self.save_configs(claude_data, gemini_data, codex_data, mode)
            return success, message

    def validate_configs(self) -> Tuple[bool, bool, bool]:
        """Validate both configuration files"""
        claude_data, gemini_data, codex_data = self.load_configs()
        claude_valid = self.claude_parser.validate(claude_data)
        gemini_valid = self.gemini_parser.validate(gemini_data)
        codex_valid = self.codex_parser.validate(codex_data)
        return claude_valid, gemini_valid, codex_valid
    
    # Preset management methods
    def list_presets(self) -> List[str]:
        """List all available presets"""
        return self.preset_manager.list_presets()
    
    def load_preset(self, preset_name: str, mode: str = 'both') -> bool:
        """Load a specific preset configuration"""
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            return False
        
        claude_data, gemini_data, codex_data = self.load_configs()
        
        # First disable all servers
        self.server_manager.disable_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        
        # Then add servers from preset
        preset_servers = preset.get('servers', {})
        for server_name, server_config in preset_servers.items():
            self.server_manager.add_server_with_name(
                claude_data,
                gemini_data,
                server_name,
                server_config,
                mode,
                codex_data=codex_data,
            )
        
        self.save_configs(claude_data, gemini_data, codex_data, mode)
        return True
    
    def save_current_as_preset(self, preset_name: str, description: str, 
                              mode: str = 'both') -> None:
        """Save current active configuration as a preset"""
        claude_data, gemini_data, codex_data = self.load_configs()
        
        # Get currently active servers
        if mode == 'claude':
            servers = claude_data.get('mcpServers', {})
        elif mode == 'gemini':
            servers = gemini_data.get('mcpServers', {})
        elif mode == 'codex':
            servers = codex_data.get('mcpServers', {})
        else:  # both
            # Merge servers from both configs
            servers = {}
            servers.update(claude_data.get('mcpServers', {}))
            servers.update(gemini_data.get('mcpServers', {}))
            if mode in {'all', 'codex'}:
                servers.update(codex_data.get('mcpServers', {}))
        
        self.preset_manager.save_preset(preset_name, description, servers)

    def add_server(self, server_name: str, server_config: Dict[str, Any], 
                   mode: str = 'both') -> Dict[str, Any]:
        """Add a server - interface expected by ServerController
        
        Args:
            server_name: Name of the server to add
            server_config: Server configuration dictionary
            mode: Which configs to add to ('claude', 'gemini', or 'both')
            
        Returns:
            Dictionary with 'success' and 'error' keys
        """
        try:
            claude_data, gemini_data, codex_data = self.load_configs()
            success = self.server_manager.add_server_with_name(
                claude_data,
                gemini_data,
                server_name,
                server_config,
                mode,
                codex_data=codex_data,
            )
            
            if success:
                self.save_configs(claude_data, gemini_data, codex_data, mode)
                return {
                    'success': True,
                    'server_name': server_name,
                    'message': f"Added server: {server_name}"
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to add server: {server_name}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error adding server: {str(e)}"
            }

    def get_google_cloud_project(self) -> Optional[str]:
        """Get the configured Google Cloud Project ID

        Returns:
            Project ID from config or environment variable
        """
        gemini_data = self.gemini_parser.parse(self.gemini_path)
        project_id = self.gemini_parser.get_google_cloud_project(gemini_data)

        # Fall back to environment variable if not in config
        if not project_id:
            import os
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

        return project_id

    def set_google_cloud_project(self, project_id: str) -> Dict[str, Any]:
        """Set the Google Cloud Project ID

        Args:
            project_id: Google Cloud Project ID to use

        Returns:
            Dictionary with 'success' and optional 'error' keys
        """
        try:
            # Load config
            gemini_data = self.gemini_parser.parse(self.gemini_path)

            # Set project ID
            gemini_data = self.gemini_parser.set_google_cloud_project(gemini_data, project_id)

            # Save config
            self.gemini_parser.write(gemini_data, self.gemini_path)

            # Update auth manager
            self.google_auth.set_project_id(project_id)

            return {
                'success': True,
                'project_id': project_id,
                'message': f"Google Cloud Project set to: {project_id}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to set Google Cloud Project: {str(e)}"
            }

    def authenticate_google(self, client_id: str, client_secret: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate with Google OAuth

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret (optional)

        Returns:
            Dictionary with 'success' and 'message' or 'error' keys
        """
        # Ensure project ID is set
        project_id = self.get_google_cloud_project()
        if not project_id:
            return {
                'success': False,
                'error': 'Google Cloud Project ID not configured. Set GOOGLE_CLOUD_PROJECT environment variable or use set_google_cloud_project()'
            }

        self.google_auth.set_project_id(project_id)

        # Perform authentication
        success, message = self.google_auth.authenticate(client_id, client_secret)

        return {
            'success': success,
            'message': message if success else None,
            'error': message if not success else None
        }

    def is_google_authenticated(self) -> bool:
        """Check if Google authentication is valid"""
        return self.google_auth.is_authenticated()

    def get_google_credentials(self) -> Optional[Dict[str, str]]:
        """Get cached Google credentials if available"""
        return self.google_auth.get_credentials()

    def clear_google_credentials(self) -> Dict[str, Any]:
        """Clear cached Google credentials"""
        try:
            self.google_auth.clear_credentials()
            return {
                'success': True,
                'message': 'Google credentials cleared successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear credentials: {str(e)}'
            }
