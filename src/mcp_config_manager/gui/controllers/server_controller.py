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
        """Get list of all servers with per-client enable flags.

        Args:
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)

        Returns:
            Dictionary with:
                - success: bool
                - data: {'servers': list of ServerListItem objects with claude_enabled and gemini_enabled flags}
                - error: error message if failed
        """
        try:
            # Get current mode from config manager if not specified
            if not mode:
                mode = 'both'  # Default to both

            # Load configs once
            claude_data, gemini_data = self.config_manager.load_configs()

            # Build unified server list with per-client states
            server_dict = {}  # name -> ServerListItem

            # Get enabled servers - now includes per-client state info
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data, gemini_data, mode
            )

            # Process enabled servers
            for server_info in enabled_servers:
                name = server_info['name']
                config = server_info['config']

                if name not in server_dict:
                    command_obj = ServerCommand(
                        command=config.get('command', ''),
                        args=config.get('args', []),
                        env=config.get('env', {})
                    )

                    server_item = ServerListItem(
                        name=name,
                        status=ServerStatus.ENABLED,
                        command=command_obj,
                        source_mode=server_info['mode'],
                        config=config
                    )

                    # Set per-client flags based on the returned data
                    server_item.claude_enabled = server_info.get('claude_enabled', False)
                    server_item.gemini_enabled = server_info.get('gemini_enabled', False)

                    server_dict[name] = server_item

            # Get disabled servers and update their states
            try:
                disabled_data = self.config_manager.server_manager.load_disabled_servers()

                for server_name, server_info in disabled_data.items():
                    # New format has 'config' and 'disabled_for'
                    if isinstance(server_info, dict) and 'config' in server_info:
                        config = server_info['config']
                        disabled_for = server_info.get('disabled_for', ['claude', 'gemini'])

                        if server_name not in server_dict:
                            command_obj = ServerCommand(
                                command=config.get('command', ''),
                                args=config.get('args', []),
                                env=config.get('env', {})
                            )

                            server_item = ServerListItem(
                                name=server_name,
                                status=ServerStatus.DISABLED,
                                command=command_obj,
                                source_mode='both',
                                config=config
                            )

                            # Set per-client flags based on disabled_for
                            server_item.claude_enabled = 'claude' not in disabled_for
                            server_item.gemini_enabled = 'gemini' not in disabled_for

                            server_dict[server_name] = server_item
                    else:
                        # Old format - treat as disabled for both
                        config = server_info if isinstance(server_info, dict) else {}

                        if server_name not in server_dict:
                            command_obj = ServerCommand(
                                command=config.get('command', ''),
                                args=config.get('args', []),
                                env=config.get('env', {})
                            )

                            server_item = ServerListItem(
                                name=server_name,
                                status=ServerStatus.DISABLED,
                                command=command_obj,
                                source_mode='both',
                                config=config
                            )

                            # Old format means disabled for both
                            server_item.claude_enabled = False
                            server_item.gemini_enabled = False

                            server_dict[server_name] = server_item
            except:
                # No disabled servers file yet, that's OK
                pass

            # Convert to list
            server_items = list(server_dict.values())

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
    
    def set_server_enabled(self, server_name: str, client: str, enabled: bool) -> Dict[str, Any]:
        """Set a server's enabled state for a specific client.

        Args:
            server_name: Name of the server
            client: Client to set state for ('claude' or 'gemini')
            enabled: Whether to enable or disable

        Returns:
            Dictionary with:
                - success: bool
                - enabled: new enabled state
                - error: error message if failed
        """
        try:
            # Load current configs
            claude_data, gemini_data = self.config_manager.load_configs()

            if enabled:
                # Enable the server for the specific client
                success = self.config_manager.server_manager.enable_server(
                    claude_data, gemini_data, server_name, client
                )
            else:
                # Disable the server for the specific client
                success = self.config_manager.server_manager.disable_server(
                    claude_data, gemini_data, server_name, client
                )

            if success:
                # Save the configs
                self.config_manager.save_configs(claude_data, gemini_data, client)

                # Notify callbacks
                for callback in self.on_server_toggled_callbacks:
                    callback({
                        'server': server_name,
                        'client': client,
                        'enabled': enabled
                    })

                return {
                    'success': True,
                    'enabled': enabled
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to set server state'
                }

        except Exception as e:
            error_msg = f"Failed to set server state: {str(e)}"
            logger.error(error_msg)

            return {
                'success': False,
                'error': error_msg
            }

    def toggle_server(self, server_name: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """Toggle a server's enabled/disabled state (backward compatibility).

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
                result = self.config_manager.add_server(
                    server_name,
                    config,
                    config_mode.value
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
                       mode: Optional[str] = None, client: Optional[str] = None) -> Dict[str, Any]:
        """Perform bulk operations on servers.

        Args:
            operation: Operation to perform ('enable_all', 'disable_all', 'enable', 'disable')
            server_names: List of server names (for 'enable' and 'disable' operations)
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current) - backward compat
            client: Target client ('claude', 'gemini', or None for both) - new parameter

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
            
            # Use client if provided, otherwise fall back to mode for backward compatibility
            target = client or mode or 'both'

            if operation == 'enable_all':
                # Enable all disabled servers
                # Load current configs
                claude_data, gemini_data = self.config_manager.load_configs()

                # If targeting specific client, use bulk_enable_for_client
                if target in ['claude', 'gemini']:
                    # Get all disabled servers for this client
                    disabled_servers = self.config_manager.server_manager.load_disabled_servers()
                    servers_to_enable = []

                    for server_name, server_info in disabled_servers.items():
                        if isinstance(server_info, dict) and 'disabled_for' in server_info:
                            if target in server_info['disabled_for']:
                                servers_to_enable.append(server_name)
                        else:
                            # Old format - treat as disabled for both
                            servers_to_enable.append(server_name)

                    # Use bulk enable method
                    result = self.config_manager.server_manager.bulk_enable_for_client(
                        claude_data, gemini_data, target, servers_to_enable
                    )
                    affected_servers = servers_to_enable if result else []
                else:
                    # Enable for both clients
                    disabled_servers = self.config_manager.server_manager.load_disabled_servers()
                    for server_name in disabled_servers.keys():
                        success = self.config_manager.server_manager.enable_server(
                            claude_data, gemini_data, server_name, 'both'
                        )
                        if success:
                            affected_servers.append(server_name)

                # Save the updated configs
                if affected_servers:
                    self.config_manager.save_configs(claude_data, gemini_data, target)
            
            elif operation == 'disable_all':
                # Disable all enabled servers
                # Load current configs
                claude_data, gemini_data = self.config_manager.load_configs()
                enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                    claude_data, gemini_data, target
                )

                # If targeting specific client, use bulk_disable_for_client
                if target in ['claude', 'gemini']:
                    servers_to_disable = [server['name'] for server in enabled_servers]

                    # Use bulk disable method
                    result = self.config_manager.server_manager.bulk_disable_for_client(
                        claude_data, gemini_data, target, servers_to_disable
                    )
                    affected_servers = servers_to_disable if result else []
                else:
                    # Disable for both clients
                    for server in enabled_servers:
                        server_name = server['name']
                        success = self.config_manager.server_manager.disable_server(
                            claude_data, gemini_data, server_name, 'both'
                        )
                        if success:
                            affected_servers.append(server_name)

                # Save the updated configs
                if affected_servers:
                    self.config_manager.save_configs(claude_data, gemini_data, target)
            
            elif operation == 'enable' and server_names:
                # Enable specific servers
                # Load current configs
                claude_data, gemini_data = self.config_manager.load_configs()

                # If targeting specific client, use bulk_enable_for_client
                if target in ['claude', 'gemini']:
                    result = self.config_manager.server_manager.bulk_enable_for_client(
                        claude_data, gemini_data, target, server_names
                    )
                    affected_servers = server_names if result else []
                else:
                    # Enable for both clients
                    for server_name in server_names:
                        success = self.config_manager.server_manager.enable_server(
                            claude_data, gemini_data, server_name, 'both'
                        )
                        if success:
                            affected_servers.append(server_name)

                # Save the updated configs
                self.config_manager.save_configs(claude_data, gemini_data, target)
            
            elif operation == 'disable' and server_names:
                # Disable specific servers
                # Load current configs
                claude_data, gemini_data = self.config_manager.load_configs()

                # If targeting specific client, use bulk_disable_for_client
                if target in ['claude', 'gemini']:
                    result = self.config_manager.server_manager.bulk_disable_for_client(
                        claude_data, gemini_data, target, server_names
                    )
                    affected_servers = server_names if result else []
                else:
                    # Disable for both clients
                    for server_name in server_names:
                        success = self.config_manager.server_manager.disable_server(
                            claude_data, gemini_data, server_name, 'both'
                        )
                        if success:
                            affected_servers.append(server_name)

                # Save the updated configs
                self.config_manager.save_configs(claude_data, gemini_data, target)
            
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
                    'mode': mode,  # Keep for backward compat
                    'client': client  # New field
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
    
    def update_server(self, server_name: str, config: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
        """Update a server's configuration.
        
        Args:
            server_name: Name of the server to update
            config: New configuration for the server
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Load current configs
            claude_data, gemini_data = self.config_manager.load_configs()
            
            # Determine mode
            if not mode:
                mode = 'both'
            
            # Update the server configuration
            success = self.config_manager.server_manager.update_server_config(
                claude_data, gemini_data, server_name, config, mode
            )
            
            if success:
                # Save the updated configs
                self.config_manager.save_configs(claude_data, gemini_data, mode)
                
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': 'Failed to update server configuration'
                }
                
        except Exception as e:
            error_msg = f"Failed to update server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_server_states(self) -> Dict[str, Dict[str, bool]]:
        """Get per-client enabled states for all servers.

        Returns:
            Dictionary mapping server_name -> {'claude_enabled': bool, 'gemini_enabled': bool}
        """
        try:
            # Load configs once
            claude_data, gemini_data = self.config_manager.load_configs()

            server_states = {}

            # Get enabled servers - includes per-client state info
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                claude_data, gemini_data, 'both'
            )

            # Process enabled servers
            for server_info in enabled_servers:
                name = server_info['name']
                server_states[name] = {
                    'claude_enabled': server_info.get('claude_enabled', False),
                    'gemini_enabled': server_info.get('gemini_enabled', False)
                }

            # Add disabled servers
            try:
                disabled_data = self.config_manager.server_manager.load_disabled_servers()

                for server_name, server_info in disabled_data.items():
                    if server_name not in server_states:
                        if isinstance(server_info, dict) and 'disabled_for' in server_info:
                            disabled_for = server_info.get('disabled_for', ['claude', 'gemini'])
                            server_states[server_name] = {
                                'claude_enabled': 'claude' not in disabled_for,
                                'gemini_enabled': 'gemini' not in disabled_for
                            }
                        else:
                            # Old format - treat as disabled for both
                            server_states[server_name] = {
                                'claude_enabled': False,
                                'gemini_enabled': False
                            }
            except:
                # No disabled servers file yet, that's OK
                pass

            return server_states

        except Exception as e:
            logger.error(f"Failed to get server states: {str(e)}")
            return {}

    def on_servers_bulk(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for bulk operation event.

        Args:
            callback: Function to call when bulk operation is performed
        """
        self.on_servers_bulk_callbacks.append(callback)
    
    def delete_server(self, server_name: str, mode: Optional[str] = None, from_disabled: Optional[bool] = None) -> Dict[str, Any]:
        """Permanently delete a server from configurations.
        
        Args:
            server_name: Name of the server to delete
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            from_disabled: If provided, explicitly states whether to delete from disabled list.
                          If None, will auto-detect based on server status.
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Load current configs
            claude_data, gemini_data = self.config_manager.load_configs()
            
            # Determine mode
            if not mode:
                mode = 'both'
            
            # If from_disabled is not explicitly provided, auto-detect
            if from_disabled is None:
                # Check if server is currently disabled
                from_disabled = False
                enabled_servers = self.config_manager.server_manager.get_enabled_servers(
                    claude_data, gemini_data, mode
                )
                is_enabled = any(s['name'] == server_name for s in enabled_servers)
                
                # If not in enabled servers, check if it's in disabled storage
                if not is_enabled:
                    disabled_servers = self.config_manager.server_manager.load_disabled_servers()
                    if server_name in disabled_servers:
                        from_disabled = True
            
            # Delete the server with appropriate flag
            success = self.config_manager.server_manager.delete_server(
                claude_data, gemini_data, server_name, mode, from_disabled
            )
            
            if success:
                # Only save configs if we deleted from active configs
                if not from_disabled:
                    self.config_manager.save_configs(claude_data, gemini_data, mode)
                
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
                    'error': f"Server '{server_name}' not found"
                }
                
        except Exception as e:
            error_msg = f"Failed to delete server: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }