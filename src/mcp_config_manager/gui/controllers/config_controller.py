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
        self.current_mode = ConfigMode.CLAUDE
        self.on_config_loaded_callbacks: List[Callable] = []
        self.on_config_saved_callbacks: List[Callable] = []
        self.on_config_error_callbacks: List[Callable] = []
    
    def load_config(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration for the specified mode.
        
        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - data: config data if successful
                - error: error message if failed
        """
        try:
            if mode:
                # Convert string to ConfigMode
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                self.current_mode = mode_map.get(mode.lower(), self.current_mode)
            
            # Load configuration
            claude_data, gemini_data = self.config_manager.load_configs()
            
            # Get current configuration
            config_data = {
                'mode': self.current_mode.value,
                'servers': self._get_server_list(),
                'claude_path': str(self.config_manager.claude_parser.config_path) if self.config_manager.claude_parser else None,
                'gemini_path': str(self.config_manager.gemini_parser.config_path) if self.config_manager.gemini_parser else None,
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
    
    def save_config(self, create_backup: bool = True) -> Dict[str, Any]:
        """Save the current configuration.
        
        Args:
            create_backup: Whether to create a backup before saving
            
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
            
            # Save configuration - need to get current data first
            claude_data, gemini_data = self.config_manager.load_configs()
            self.config_manager.save_configs(claude_data, gemini_data, self.current_mode.value)
            
            # Notify callbacks
            for callback in self.on_config_saved_callbacks:
                callback({'backup_file': backup_file})
            
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
    
    def validate_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate a configuration file.
        
        Args:
            config_path: Path to config file to validate (None for current)
            
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
            
            if config_path:
                # Validate specific file
                path = Path(config_path)
                if not path.exists():
                    errors.append(f"File not found: {config_path}")
                else:
                    # Use appropriate parser based on file
                    if 'claude' in str(path).lower():
                        result = self.config_manager.claude_parser.validate_config(path)
                    elif 'gemini' in str(path).lower():
                        result = self.config_manager.gemini_parser.validate_config(path)
                    else:
                        errors.append("Unknown configuration file type")
                        result = {'valid': False}
                    
                    if not result.get('valid'):
                        errors.extend(result.get('errors', []))
                    warnings.extend(result.get('warnings', []))
            else:
                # Validate current configuration
                if self.current_mode in [ConfigMode.CLAUDE, ConfigMode.BOTH]:
                    if self.config_manager.claude_parser:
                        result = self.config_manager.claude_parser.validate_current()
                        if not result.get('valid'):
                            errors.extend(result.get('errors', []))
                        warnings.extend(result.get('warnings', []))
                
                if self.current_mode in [ConfigMode.GEMINI, ConfigMode.BOTH]:
                    if self.config_manager.gemini_parser:
                        result = self.config_manager.gemini_parser.validate_current()
                        if not result.get('valid'):
                            errors.extend(result.get('errors', []))
                        warnings.extend(result.get('warnings', []))
            
            return {
                'success': True,
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            error_msg = f"Failed to validate configuration: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'valid': False,
                'errors': [error_msg],
                'warnings': []
            }
    
    def get_config_paths(self) -> Dict[str, Optional[str]]:
        """Get paths to configuration files.
        
        Returns:
            Dictionary with paths for each client
        """
        return {
            'claude': str(self.config_manager.claude_parser.config_path) if self.config_manager.claude_parser else None,
            'gemini': str(self.config_manager.gemini_parser.config_path) if self.config_manager.gemini_parser else None,
            'presets': str(self.config_manager.preset_manager.presets_file) if self.config_manager.preset_manager else None
        }
    
    def change_mode(self, mode: str) -> Dict[str, Any]:
        """Change the configuration mode.
        
        Args:
            mode: New mode ('claude', 'gemini', or 'both')
            
        Returns:
            Dictionary with:
                - success: bool
                - previous_mode: previous mode value
                - error: error message if failed
        """
        try:
            previous_mode = self.current_mode.value
            
            # Convert string to ConfigMode
            mode_map = {
                'claude': ConfigMode.CLAUDE,
                'gemini': ConfigMode.GEMINI,
                'both': ConfigMode.BOTH
            }
            
            new_mode = mode_map.get(mode.lower())
            if not new_mode:
                return {
                    'success': False,
                    'error': f"Invalid mode: {mode}"
                }
            
            self.current_mode = new_mode
            
            # Reload configuration for new mode
            result = self.load_config(mode)
            
            return {
                'success': result['success'],
                'previous_mode': previous_mode,
                'error': result.get('error')
            }
            
        except Exception as e:
            error_msg = f"Failed to change mode: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def _get_server_list(self) -> List[Dict[str, Any]]:
        """Get list of servers from current configuration.
        
        Returns:
            List of server dictionaries
        """
        servers = []
        
        try:
            # Get enabled servers
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(self.current_mode)
            for name, config in enabled_servers.items():
                servers.append({
                    'name': name,
                    'enabled': True,
                    'command': config.get('command', ''),
                    'args': config.get('args', []),
                    'env': config.get('env', {}),
                    'mode': self.current_mode.value
                })
            
            # Get disabled servers
            disabled_servers = self.config_manager.server_manager.get_disabled_servers(self.current_mode)
            for name, config in disabled_servers.items():
                servers.append({
                    'name': name,
                    'enabled': False,
                    'command': config.get('command', ''),
                    'args': config.get('args', []),
                    'env': config.get('env', {}),
                    'mode': self.current_mode.value
                })
            
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