"""Controller for configuration load/save operations."""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import logging

from mcp_config_manager.core.config_manager import ConfigManager
from mcp_config_manager.core.config_manager import ConfigMode

logger = logging.getLogger(__name__)


class ConfigController:
    """Controller for managing configuration operations between GUI and library."""
    
    def __init__(self):
        """Initialize the config controller."""
        self.config_manager = ConfigManager()
        # No more current_mode - always work with both configs
        self.on_config_loaded_callbacks: List[Callable] = []
        self.on_config_saved_callbacks: List[Callable] = []
        self.on_config_error_callbacks: List[Callable] = []
    
    def load_config(self, mode: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration for the specified mode.

        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            force_reload: If True, force a fresh read from disk bypassing any caches

        Returns:
            Dictionary with:
                - success: bool
                - data: config data if successful
                - error: error message if failed
        """
        try:
            # Always load both configurations
            if force_reload:
                # Force fresh read from disk - clear any potential caches
                self.config_manager._claude_config = None
                self.config_manager._gemini_config = None
                # Also reload disabled servers
                self.config_manager.server_manager.disabled_servers = None

            claude_data, gemini_data, codex_data = self.config_manager.load_configs()
            logger.debug(
                "Configs loaded%s. Claude servers: %d, Gemini servers: %d, Codex servers: %d",
                ' (forced reload)' if force_reload else '',
                len(claude_data.get('mcpServers', {})),
                len(gemini_data.get('mcpServers', {})),
                len(codex_data.get('mcpServers', {})),
            )

            # Get server list with per-client states
            server_list = self._get_server_list()
            logger.debug(f"Got {len(server_list)} total servers")

            config_data = {
                'servers': server_list,
                'claude_path': str(self.config_manager.claude_path) if self.config_manager.claude_path else None,
                'gemini_path': str(self.config_manager.gemini_path) if self.config_manager.gemini_path else None,
                'codex_path': str(self.config_manager.codex_path) if self.config_manager.codex_path else None,
                'has_unsaved_changes': False
            }

            # Notify callbacks
            for callback in self.on_config_loaded_callbacks:
                callback(config_data)
            
            return {
                'success': True,
                'data': config_data
            }
            
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg)
            
            # Notify error callbacks
            for callback in self.on_config_error_callbacks:
                callback(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }

    def reload_config(self) -> Dict[str, Any]:
        """Force reload configuration from disk, clearing all caches.

        This method ensures a fresh read of all configuration files,
        bypassing any cached data. Useful when files have been modified
        externally or when user explicitly requests a refresh.

        Returns:
            Dictionary with:
                - success: bool
                - data: config data if successful (same format as load_config)
                - error: error message if failed
        """
        logger.debug("Forcing configuration reload from disk")
        return self.load_config(force_reload=True)

    def save_config(self, create_backup: bool = True, client: Optional[str] = None) -> Dict[str, Any]:
        """Save configuration with per-client state handling.

        Args:
            create_backup: Whether to create a backup before saving
            client: Optional client to save for ('claude', 'gemini', or None for both)

        Returns:
            Dictionary with:
                - success: bool
                - backup_file: path to backup if created
                - error: error message if failed
        """
        try:
            backup_file = None

            if create_backup:
                # Create backup
                backups = self.config_manager.create_backups()
                if backups:
                    backup_file = str(backups[0][1]) if backups else None

            # Save configuration - always get current data first
            claude_data, gemini_data, codex_data = self.config_manager.load_configs()
            # Save for specific client or both
            target = client if client else 'both'
            self.config_manager.save_configs(claude_data, gemini_data, codex_data, target)

            # Notify callbacks
            for callback in self.on_config_saved_callbacks:
                callback({'backup_file': backup_file, 'client': client})

            return {
                'success': True,
                'backup_file': backup_file
            }

        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logger.error(error_msg)

            # Notify error callbacks
            for callback in self.on_config_error_callbacks:
                callback(error_msg)

            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_configuration(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Validate a configuration file.

        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)

        Returns:
            Dictionary with:
                - success: bool
                - valid: whether config is valid
                - errors: list of validation errors
                - warnings: list of warnings
        """
        try:
            errors = []
            warnings = []

            # Always load and validate both configs
            claude_data, gemini_data, codex_data = self.config_manager.load_configs()

            # Validate Claude configuration
            if self.config_manager.claude_parser:
                if not self.config_manager.claude_parser.validate(claude_data):
                    errors.append("Claude configuration is invalid.")

            # Validate Gemini configuration
            if self.config_manager.gemini_parser:
                if not self.config_manager.gemini_parser.validate(gemini_data):
                    errors.append("Gemini configuration is invalid.")

            if self.config_manager.codex_parser:
                if not self.config_manager.codex_parser.validate(codex_data):
                    errors.append("Codex configuration is invalid.")

            return {
                'success': True,
                'data': {
                    'valid': len(errors) == 0,
                    'errors': errors,
                    'warnings': warnings
                }
            }

        except Exception as e:
            error_msg = f"Failed to validate configuration: {str(e)}"
            logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'data': {
                    'valid': False,
                    'errors': [error_msg],
                    'warnings': []
                }
            }
    
    def get_config_paths(self) -> Dict[str, Optional[str]]:
        """Get paths to configuration files.
        
        Returns:
            Dictionary with paths for each client
        """
        return {
            'claude': str(self.config_manager.claude_parser.config_path) if self.config_manager.claude_parser else None,
            'gemini': str(self.config_manager.gemini_parser.config_path) if self.config_manager.gemini_parser else None,
            'codex': str(self.config_manager.codex_path) if self.config_manager.codex_path else None,
            'presets': str(self.config_manager.preset_manager.presets_file) if self.config_manager.preset_manager else None
        }
    
    # Note: change_mode() method removed - no longer needed without mode concept
    
    def _get_server_list(self) -> List[Dict[str, Any]]:
        """Get list of servers from current configuration.
        
        Returns:
            List of server dictionaries
        """
        servers = []
        
        try:
            # Load current configs
            claude_data, gemini_data, codex_data = self.config_manager.load_configs()

            # Get all servers (enabled and disabled) with per-client states
            all_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data,
                gemini_data,
                'all',
                codex_data=codex_data,
            )

            # Build unified server list with per-client states
            server_dict = {}  # name -> server info

            # Process enabled servers
            for server_info in all_servers:
                name = server_info['name']
                if name not in server_dict:
                    server_dict[name] = {
                        'name': name,
                        'command': server_info['config'].get('command', ''),
                        'args': server_info['config'].get('args', []),
                        'env': server_info['config'].get('env', {}),
                        'claude_enabled': server_info.get('claude_enabled', False),
                        'gemini_enabled': server_info.get('gemini_enabled', False),
                        'codex_enabled': server_info.get('codex_enabled', False),
                        'config': server_info['config']
                    }

            # Get disabled servers and add their states
            disabled_data = self.config_manager.server_manager.load_disabled_servers()
            for name, server_info in disabled_data.items():
                if name not in server_dict:
                    # Handle new format with 'config' and 'disabled_for'
                    if isinstance(server_info, dict) and 'config' in server_info:
                        config = server_info['config']
                        disabled_for = server_info.get(
                            'disabled_for',
                            list(self.config_manager.server_manager.DEFAULT_DISABLED),
                        )
                        server_dict[name] = {
                            'name': name,
                            'command': config.get('command', ''),
                            'args': config.get('args', []),
                            'env': config.get('env', {}),
                            'claude_enabled': 'claude' not in disabled_for,
                            'gemini_enabled': 'gemini' not in disabled_for,
                            'codex_enabled': 'codex' not in disabled_for,
                            'config': config
                        }
                    else:
                        # Old format - treat as disabled for both
                        config = server_info if isinstance(server_info, dict) else {}
                        server_dict[name] = {
                            'name': name,
                            'command': config.get('command', ''),
                            'args': config.get('args', []),
                            'env': config.get('env', {}),
                            'claude_enabled': False,
                            'gemini_enabled': False,
                            'codex_enabled': False,
                            'config': config
                        }

            servers = list(server_dict.values())
            
        except Exception as e:
            logger.error(f"Failed to get server list: {str(e)}")
        
        return servers
    
    def on_config_loaded(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for config loaded event.
        
        Args:
            callback: Function to call when config is loaded
        """
        self.on_config_loaded_callbacks.append(callback)
    
    def on_config_saved(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for config saved event.
        
        Args:
            callback: Function to call when config is saved
        """
        self.on_config_saved_callbacks.append(callback)
    
    def on_config_error(self, callback: Callable[[str], None]):
        """Register callback for config error event.
        
        Args:
            callback: Function to call with error message
        """
        self.on_config_error_callbacks.append(callback)
