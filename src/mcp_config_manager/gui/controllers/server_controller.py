"""Controller for server management operations."""

from typing import Dict, Any, List, Optional, Callable
import logging

from mcp_config_manager.core.config_manager import ConfigManager
from mcp_config_manager.core.config_manager import ConfigMode
from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus, ServerCommand

logger = logging.getLogger(__name__)


class ServerController:
    """Controller for managing server operations between GUI and library."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the server controller.
        
        Args:
            config_manager: Optional ConfigManager instance to use
        """
        self.config_manager = config_manager or ConfigManager()
        self.on_server_toggled_callbacks: List[Callable] = []
        self.on_server_added_callbacks: List[Callable] = []
        self.on_server_removed_callbacks: List[Callable] = []
        self.on_servers_bulk_callbacks: List[Callable] = []
    
    def get_servers(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Get list of all servers as ServerListItem objects.
        
        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - data: {'servers': list of ServerListItem objects}
                - error: error message if failed
        """
        try:
            # Get current mode from config manager if not specified
            if not mode:
                mode = 'both'  # Default to both
            
            # Load configs once
            claude_data, gemini_data = self.config_manager.load_configs()
            
            server_items = []
            
            # Get enabled servers using the same method as ConfigController
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data, gemini_data, mode
            )
            
            # Add enabled servers
            for server_info in enabled_servers:
                config = server_info['config']
                command_obj = ServerCommand(
                    command=config.get('command', ''),
                    args=config.get('args', []),
                    env=config.get('env', {})
                )
                
                server_item = ServerListItem(
                    name=server_info['name'],
                    status=ServerStatus.ENABLED,
                    command=command_obj,
                    source_mode=server_info['mode'],
                    config=config
                )
                server_items.append(server_item)
            
            # Get disabled servers if they exist
            try:
                disabled_servers = self.config_manager.server_manager.load_disabled_servers()
                for server_name, config in disabled_servers.items():
                    command_obj = ServerCommand(
                        command=config.get('command', ''),
                        args=config.get('args', []),
                        env=config.get('env', {})
                    )
                    
                    server_item = ServerListItem(
                        name=server_name,
                        status=ServerStatus.DISABLED,
                        command=command_obj,
                        source_mode=mode,
                        config=config
                    )
                    server_items.append(server_item)
            except:
                # No disabled servers file yet, that's OK
                pass
            
            return {
                'success': True,
                'data': {'servers': server_items}
            }
            
        except Exception as e:
            error_msg = f"Failed to get servers: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'data': {'servers': []},  # Keep consistent structure
                'error': error_msg
            }
    
    def get_server_list(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Get list of all servers.
        
        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - servers: list of server dictionaries
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            servers = []
            
            # Load current configs
            claude_data, gemini_data = self.config_manager.load_configs()
            
            # Get enabled servers using the new method
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data, gemini_data, mode.lower() if mode else 'both'
            )
            
            for server_info in enabled_servers:
                servers.append({
                    'name': server_info['name'],
                    'enabled': True,
                    'command': server_info['config'].get('command', ''),
                    'args': server_info['config'].get('args', []),
                    'env': server_info['config'].get('env', {}),
                    'status': 'enabled'
                })
            
            # Get disabled servers
            try:
                disabled_servers = self.config_manager.server_manager.load_disabled_servers()
                for name, config in disabled_servers.items():
                    servers.append({
                        'name': name,
                        'enabled': False,
                        'command': config.get('command', ''),
                        'args': config.get('args', []),
                        'env': config.get('env', {}),
                        'status': 'disabled'
                    })
            except:
                # No disabled servers file yet, that's OK
                pass
            
            return {
                'success': True,
                'servers': servers
            }
            
        except Exception as e:
            error_msg = f"Failed to get server list: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'servers': [],
                'error': error_msg
            }
    
    def toggle_server(self, server_name: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """Toggle a server's enabled/disabled state.
        
        Args:
            server_name: Name of the server to toggle
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - enabled: new enabled state
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            # Check current state
            claude_data, gemini_data = self.config_manager.load_configs()
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data, gemini_data, mode.lower() if mode else 'both'
            )
            is_currently_enabled = any(s['name'] == server_name for s in enabled_servers)
            
            if is_currently_enabled:
                # Disable the server
                success = self.config_manager.server_manager.disable_server(
                    claude_data, gemini_data, server_name, mode.lower() if mode else 'both'
                )
                new_state = False
            else:
                # Enable the server
                success = self.config_manager.server_manager.enable_server(
                    claude_data, gemini_data, server_name, mode.lower() if mode else 'both'
                )
                new_state = True
            
            if success:
                # Save the configs
                self.config_manager.save_configs(claude_data, gemini_data, mode.lower() if mode else 'both')
                
                # Notify callbacks
                for callback in self.on_server_toggled_callbacks:
                    callback({
                        'server': server_name,
                        'enabled': new_state,
                        'mode': mode
                    })
                
                return {
                    'success': True,
                    'enabled': new_state
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to toggle server'
                }
            
        except Exception as e:
            error_msg = f"Failed to toggle server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def add_server(self, server_config: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
        """Add a new server.
        
        Args:
            server_config: Dictionary with server configuration
                          Should have format: {"server_name": {"command": "...", ...}}
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - server_names: list of added server names
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            added_servers = []
            
            # Add each server in the config
            for server_name, config in server_config.items():
                result = self.config_manager.server_manager.add_server(
                    server_name,
                    config,
                    config_mode
                )
                
                if result.get('success'):
                    added_servers.append(server_name)
                else:
                    # If any server fails, return error
                    return {
                        'success': False,
                        'error': f"Failed to add server '{server_name}': {result.get('error')}"
                    }
            
            # Notify callbacks
            for callback in self.on_server_added_callbacks:
                callback({
                    'servers': added_servers,
                    'mode': mode
                })
            
            return {
                'success': True,
                'server_names': added_servers
            }
            
        except Exception as e:
            error_msg = f"Failed to add server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def remove_server(self, server_name: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """Remove a server completely.
        
        Args:
            server_name: Name of the server to remove
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            result = self.config_manager.server_manager.remove_server(server_name, config_mode)
            
            if result.get('success'):
                # Notify callbacks
                for callback in self.on_server_removed_callbacks:
                    callback({
                        'server': server_name,
                        'mode': mode
                    })
                
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to remove server')
                }
            
        except Exception as e:
            error_msg = f"Failed to remove server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def bulk_operation(self, operation: str, server_names: Optional[List[str]] = None,
                       mode: Optional[str] = None) -> Dict[str, Any]:
        """Perform bulk operations on servers.
        
        Args:
            operation: Operation to perform ('enable_all', 'disable_all', 'enable', 'disable')
            server_names: List of server names (for 'enable' and 'disable' operations)
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - affected_servers: list of affected server names
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            affected_servers = []
            
            if operation == 'enable_all':
                # Enable all disabled servers
                disabled_servers = self.config_manager.server_manager.get_disabled_servers(config_mode)
                for server_name in disabled_servers:
                    result = self.config_manager.server_manager.enable_server(server_name, config_mode)
                    if result.get('success'):
                        affected_servers.append(server_name)
            
            elif operation == 'disable_all':
                # Disable all enabled servers
                enabled_servers = self.config_manager.server_manager.get_enabled_servers(config_mode)
                for server_name in enabled_servers:
                    result = self.config_manager.server_manager.disable_server(server_name, config_mode)
                    if result.get('success'):
                        affected_servers.append(server_name)
            
            elif operation == 'enable' and server_names:
                # Enable specific servers
                for server_name in server_names:
                    result = self.config_manager.server_manager.enable_server(server_name, config_mode)
                    if result.get('success'):
                        affected_servers.append(server_name)
            
            elif operation == 'disable' and server_names:
                # Disable specific servers
                for server_name in server_names:
                    result = self.config_manager.server_manager.disable_server(server_name, config_mode)
                    if result.get('success'):
                        affected_servers.append(server_name)
            
            else:
                return {
                    'success': False,
                    'error': f"Invalid operation: {operation}"
                }
            
            # Notify callbacks
            for callback in self.on_servers_bulk_callbacks:
                callback({
                    'operation': operation,
                    'servers': affected_servers,
                    'mode': mode
                })
            
            return {
                'success': True,
                'affected_servers': affected_servers
            }
            
        except Exception as e:
            error_msg = f"Failed to perform bulk operation: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_server(self, server_name: str, server_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a server configuration.
        
        Args:
            server_name: Name of the server
            server_config: Optional server configuration to validate
                          If not provided, validates existing server
            
        Returns:
            Dictionary with:
                - success: bool
                - valid: whether server is valid
                - errors: list of validation errors
                - warnings: list of warnings
        """
        try:
            errors = []
            warnings = []
            
            if server_config:
                # Validate provided config
                if not server_config.get('command'):
                    errors.append("Server must have a 'command' field")
                
                if not isinstance(server_config.get('args', []), list):
                    errors.append("Server 'args' must be a list")
                
                if not isinstance(server_config.get('env', {}), dict):
                    errors.append("Server 'env' must be a dictionary")
                
                # Check for environment variables
                env_vars = server_config.get('env', {})
                for key, value in env_vars.items():
                    if not isinstance(value, str):
                        warnings.append(f"Environment variable '{key}' should be a string")
            else:
                # Validate existing server
                all_servers = self.get_server_list()
                if all_servers['success']:
                    server = next((s for s in all_servers['servers'] if s['name'] == server_name), None)
                    if not server:
                        errors.append(f"Server '{server_name}' not found")
                    else:
                        # Validate the found server
                        if not server.get('command'):
                            errors.append("Server has no command specified")
                else:
                    errors.append("Failed to retrieve server list")
            
            return {
                'success': True,
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            error_msg = f"Failed to validate server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'valid': False,
                'errors': [error_msg],
                'warnings': []
            }
    
    def on_server_toggled(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for server toggled event.
        
        Args:
            callback: Function to call when server is toggled
        """
        self.on_server_toggled_callbacks.append(callback)
    
    def on_server_added(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for server added event.
        
        Args:
            callback: Function to call when server is added
        """
        self.on_server_added_callbacks.append(callback)
    
    def on_server_removed(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for server removed event.
        
        Args:
            callback: Function to call when server is removed
        """
        self.on_server_removed_callbacks.append(callback)
    
    def on_servers_bulk(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for bulk operation event.
        
        Args:
            callback: Function to call when bulk operation is performed
        """
        self.on_servers_bulk_callbacks.append(callback)