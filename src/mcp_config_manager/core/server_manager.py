"""
Server management functionality
Extracted from mcp_toggle.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional
from ..utils.file_utils import get_disabled_servers_path
from .project_discovery import ProjectDiscoveryService, ProjectServer


class ServerManager:
    """Manages MCP server enabling/disabling and storage"""
    
    def __init__(self, disabled_path: Path = None):
        self.disabled_path = disabled_path or get_disabled_servers_path()
    
    def load_disabled_servers(self) -> Dict[str, Any]:
        """Load disabled servers from storage file with migration support.

        New format:
        {
            "server_name": {
                "config": {...server config...},
                "disabled_for": ["claude", "gemini"]  # or just ["claude"] or ["gemini"]
            }
        }

        Old format (auto-migrated):
        {
            "server_name": {...server config...}
        }
        """
        if not self.disabled_path.exists():
            return {}

        try:
            with open(self.disabled_path, 'r') as f:
                data = json.load(f)

            # Migrate old format to new format if needed
            migrated = self._migrate_disabled_format(data)
            if migrated != data:
                # Save the migrated format
                self.save_disabled_servers(migrated)

            return migrated
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_disabled_servers(self, disabled: Dict[str, Any]) -> None:
        """Save disabled servers to storage file in new format.

        Ensures all entries follow the new format with 'config' and 'disabled_for' keys.
        """
        # Ensure new format before saving
        normalized = self._normalize_to_new_format(disabled)

        self.disabled_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.disabled_path, 'w') as f:
            json.dump(normalized, f, indent=2)
    
    def disable_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                      server_name: str, mode: str = 'both') -> bool:
        """Move a server from active to disabled storage with per-LLM tracking.

        Args:
            mode: 'claude', 'gemini', or 'both' - which LLM(s) to disable the server for
        """
        disabled = self.load_disabled_servers()
        server_config = None
        clients_to_disable = []

        # Determine which clients to disable for
        if mode in ['claude', 'both']:
            clients_to_disable.append('claude')
        if mode in ['gemini', 'both']:
            clients_to_disable.append('gemini')

        # Get server config from active configs
        if 'mcpServers' in claude_data and server_name in claude_data['mcpServers']:
            server_config = claude_data['mcpServers'][server_name]
        elif 'mcpServers' in gemini_data and server_name in gemini_data['mcpServers']:
            server_config = gemini_data['mcpServers'][server_name]

        # Handle existing disabled entry or create new one
        if server_name in disabled:
            # Server already has a disabled entry - update it
            entry = disabled[server_name]
            if isinstance(entry, dict) and 'disabled_for' in entry:
                # New format - update the disabled_for list
                current_disabled = set(entry.get('disabled_for', []))
                current_disabled.update(clients_to_disable)
                entry['disabled_for'] = sorted(list(current_disabled))
                # Update config if we have a newer one
                if server_config:
                    entry['config'] = server_config
            else:
                # Old format - shouldn't happen after migration, but handle it
                disabled[server_name] = {
                    "config": server_config or entry,
                    "disabled_for": clients_to_disable
                }
        else:
            # New disabled entry
            if server_config:
                disabled[server_name] = {
                    "config": server_config,
                    "disabled_for": clients_to_disable
                }

        # Remove from active configs as specified
        if 'claude' in clients_to_disable and 'mcpServers' in claude_data:
            if server_name in claude_data['mcpServers']:
                del claude_data['mcpServers'][server_name]

        if 'gemini' in clients_to_disable and 'mcpServers' in gemini_data:
            if server_name in gemini_data['mcpServers']:
                del gemini_data['mcpServers'][server_name]

        # Save updated disabled servers
        if server_name in disabled:
            self.save_disabled_servers(disabled)
            return True

        return False
    
    def enable_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                     server_name: str, mode: str = 'both') -> bool:
        """Move a server from disabled storage to active with per-LLM tracking.

        Args:
            mode: 'claude', 'gemini', or 'both' - which LLM(s) to enable the server for
        """
        disabled = self.load_disabled_servers()

        if server_name not in disabled:
            return False

        entry = disabled[server_name]
        server_config = None
        clients_to_enable = []

        # Determine which clients to enable for
        if mode in ['claude', 'both']:
            clients_to_enable.append('claude')
        if mode in ['gemini', 'both']:
            clients_to_enable.append('gemini')

        # Extract config from new or old format
        if isinstance(entry, dict):
            if 'config' in entry:
                # New format
                server_config = entry['config']
                current_disabled = set(entry.get('disabled_for', []))
            else:
                # Old format (shouldn't happen after migration)
                server_config = entry
                current_disabled = {'claude', 'gemini'}
        else:
            return False

        # Add to appropriate active configs
        if 'claude' in clients_to_enable:
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            if server_name not in claude_data['mcpServers']:
                claude_data['mcpServers'][server_name] = server_config.copy()

        if 'gemini' in clients_to_enable:
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            if server_name not in gemini_data['mcpServers']:
                gemini_data['mcpServers'][server_name] = server_config.copy()

        # Update or remove from disabled list
        remaining_disabled = current_disabled - set(clients_to_enable)

        if remaining_disabled:
            # Still disabled for some clients - update the entry
            entry['disabled_for'] = sorted(list(remaining_disabled))
            disabled[server_name] = entry
        else:
            # No longer disabled for any client - remove entirely
            del disabled[server_name]

        self.save_disabled_servers(disabled)
        return True
    
    def get_enabled_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                           mode: str = 'both') -> List[Dict[str, Any]]:
        """Get list of enabled servers with their configurations and per-client states.

        Returns servers with 'claude_enabled' and 'gemini_enabled' flags.
        """
        # Build a unified view of all servers
        server_states = {}

        # Process Claude servers
        for name, config in claude_data.get('mcpServers', {}).items():
            if name not in server_states:
                server_states[name] = {
                    'name': name,
                    'config': config,
                    'enabled': True,  # Legacy field for backward compatibility
                    'claude_enabled': True,
                    'gemini_enabled': False
                }
            else:
                server_states[name]['claude_enabled'] = True

        # Process Gemini servers
        for name, config in gemini_data.get('mcpServers', {}).items():
            if name not in server_states:
                server_states[name] = {
                    'name': name,
                    'config': config,
                    'enabled': True,  # Legacy field for backward compatibility
                    'claude_enabled': False,
                    'gemini_enabled': True
                }
            else:
                server_states[name]['gemini_enabled'] = True
                # Update config if not already set (Gemini takes precedence if only in Gemini)
                if 'config' not in server_states[name]:
                    server_states[name]['config'] = config

        # Filter based on mode
        servers = []
        for server_data in server_states.values():
            if mode == 'claude' and server_data['claude_enabled']:
                servers.append(server_data)
            elif mode == 'gemini' and server_data['gemini_enabled']:
                servers.append(server_data)
            elif mode == 'both':
                servers.append(server_data)

        return sorted(servers, key=lambda x: x['name'])
    
    def list_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                        mode: str = 'both', include_project_servers: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """List all servers (active and disabled) with per-client state information.

        Args:
            claude_data: Claude configuration dict
            gemini_data: Gemini configuration dict
            mode: 'claude', 'gemini', or 'both'
            include_project_servers: Whether to include project-specific servers in the list

        Returns:
            Tuple of (active_servers, disabled_servers) where each is a list of dicts containing:
            - name: server name
            - claude_enabled: bool
            - gemini_enabled: bool
            - config: server configuration (if available)
            - location: 'global' or project path if from a project
        """
        # Build complete server state map
        all_servers = {}

        # Add active Claude servers (global)
        for name, config in claude_data.get('mcpServers', {}).items():
            if name not in all_servers:
                all_servers[name] = {
                    'name': name,
                    'config': config,
                    'claude_enabled': True,
                    'gemini_enabled': False,
                    'is_active': True,
                    'location': 'global'
                }
            else:
                all_servers[name]['claude_enabled'] = True
                all_servers[name]['is_active'] = True

        # Add active Gemini servers (global)
        for name, config in gemini_data.get('mcpServers', {}).items():
            if name not in all_servers:
                all_servers[name] = {
                    'name': name,
                    'config': config,
                    'claude_enabled': False,
                    'gemini_enabled': True,
                    'is_active': True,
                    'location': 'global'
                }
            else:
                all_servers[name]['gemini_enabled'] = True
                all_servers[name]['is_active'] = True
                if 'config' not in all_servers[name]:
                    all_servers[name]['config'] = config

        # Add disabled servers
        disabled_servers = self.load_disabled_servers()
        for server_name, entry in disabled_servers.items():
            if isinstance(entry, dict) and 'disabled_for' in entry:
                disabled_for = entry.get('disabled_for', [])
                config = entry.get('config', {})

                if server_name not in all_servers:
                    all_servers[server_name] = {
                        'name': server_name,
                        'config': config,
                        'claude_enabled': 'claude' not in disabled_for,
                        'gemini_enabled': 'gemini' not in disabled_for,
                        'is_active': False,
                        'location': 'global'
                    }
                else:
                    # Server exists in active - update disabled states
                    if 'claude' in disabled_for:
                        all_servers[server_name]['claude_enabled'] = False
                    if 'gemini' in disabled_for:
                        all_servers[server_name]['gemini_enabled'] = False

        # Add project-specific servers if requested
        if include_project_servers:
            try:
                project_servers = self.get_project_servers(use_cache=True)
                for project_path, servers in project_servers.items():
                    for server in servers:
                        # Check if this is a duplicate (same name exists in global)
                        is_duplicate = server.name in all_servers

                        # Create a unique key for project servers to avoid conflicts
                        # If duplicate, use project-specific key; otherwise use server name
                        server_key = f"{server.name}@{project_path}" if is_duplicate else server.name

                        all_servers[server_key] = {
                            'name': server.name,
                            'config': server.config,
                            'claude_enabled': True,  # Project servers are enabled by default
                            'gemini_enabled': True,
                            'is_active': True,
                            'location': str(project_path),
                            'is_project_server': True,
                            'is_duplicate': is_duplicate
                        }
            except Exception as e:
                # If project discovery fails, just continue without project servers
                import logging
                logging.getLogger(__name__).debug(f"Could not include project servers: {e}")

        # Separate active and disabled based on mode
        active = []
        disabled = []

        for server_data in all_servers.values():
            # Determine if server is active or disabled for requested mode
            is_active_for_mode = False
            is_disabled_for_mode = False

            if mode == 'claude':
                is_active_for_mode = server_data['claude_enabled']
                is_disabled_for_mode = not server_data['claude_enabled']
            elif mode == 'gemini':
                is_active_for_mode = server_data['gemini_enabled']
                is_disabled_for_mode = not server_data['gemini_enabled']
            elif mode == 'both':
                is_active_for_mode = server_data['claude_enabled'] or server_data['gemini_enabled']
                is_disabled_for_mode = not server_data['claude_enabled'] or not server_data['gemini_enabled']

            if is_active_for_mode:
                active.append(server_data)
            if is_disabled_for_mode:
                disabled.append(server_data)

        # Sort by name
        active.sort(key=lambda x: x['name'])
        disabled.sort(key=lambda x: x['name'])

        return active, disabled
    
    def disable_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                           mode: str = 'both') -> int:
        """Disable all active servers"""
        active, _ = self.list_all_servers(claude_data, gemini_data, mode)
        count = 0

        for server in active:
            if self.disable_server(claude_data, gemini_data, server['name'], mode):
                count += 1

        return count

    def enable_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                          mode: str = 'both') -> int:
        """Enable all disabled servers"""
        _, disabled = self.list_all_servers(claude_data, gemini_data, mode)
        count = 0

        for server in disabled:
            if self.enable_server(claude_data, gemini_data, server['name'], mode):
                count += 1

        return count
    
    def add_new_server_from_json(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                                json_text: str, mode: str = 'both') -> Tuple[bool, str]:
        """Add a new server from JSON configuration"""
        try:
            parsed = json.loads(json_text.strip())
            
            if isinstance(parsed, dict):
                if 'command' in parsed or 'args' in parsed or 'type' in parsed:
                    # Single server config, need server name
                    return False, "Server name required for single server config"
                else:
                    # Multiple servers
                    for server_name, server_config in parsed.items():
                        if isinstance(server_config, dict):
                            self._add_server_to_configs(claude_data, gemini_data, 
                                                       server_name, server_config, mode)
                    return True, f"Added {len(parsed)} servers"
            else:
                return False, "Invalid JSON structure"
                
        except json.JSONDecodeError as e:
            return False, f"JSON parsing failed: {e}"
    
    def add_server_with_name(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                            server_name: str, server_config: Dict[str, Any], 
                            mode: str = 'both') -> bool:
        """Add a server with a specific name"""
        return self._add_server_to_configs(claude_data, gemini_data, server_name, server_config, mode)
    
    
    def _add_server_to_configs(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                              server_name: str, server_config: Dict[str, Any], 
                              mode: str = 'both') -> bool:
        """Internal method to add server to appropriate configs"""
        if mode in ['claude', 'both']:
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            claude_data['mcpServers'][server_name] = server_config
        
        if mode in ['gemini', 'both']:
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            gemini_data['mcpServers'][server_name] = server_config
        
        return True
    
    def update_server_config(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                            server_name: str, new_config: Dict[str, Any],
                            mode: str = 'both') -> bool:
        """Update an existing server's configuration.

        Updates the config in active configs and/or disabled storage as appropriate.
        """
        updated = False

        # Check if server exists in enabled servers
        if mode in ['claude', 'both'] and 'mcpServers' in claude_data:
            if server_name in claude_data['mcpServers']:
                claude_data['mcpServers'][server_name] = new_config
                updated = True

        if mode in ['gemini', 'both'] and 'mcpServers' in gemini_data:
            if server_name in gemini_data['mcpServers']:
                gemini_data['mcpServers'][server_name] = new_config
                updated = True

        # Also check disabled servers
        disabled = self.load_disabled_servers()
        if server_name in disabled:
            entry = disabled[server_name]
            if isinstance(entry, dict) and 'config' in entry:
                # New format - update the config
                entry['config'] = new_config
            else:
                # Old format - convert to new format
                disabled[server_name] = {
                    "config": new_config,
                    "disabled_for": ["claude", "gemini"]
                }
            self.save_disabled_servers(disabled)
            updated = True

        return updated
    
    def delete_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                     server_name: str, mode: str = 'both', from_disabled: bool = False) -> bool:
        """Permanently delete a server from configurations and/or storage.

        Args:
            claude_data: Claude configuration dictionary
            gemini_data: Gemini configuration dictionary
            server_name: Name of the server to delete
            mode: Which configs to delete from ('claude', 'gemini', or 'both')
            from_disabled: If True, only delete from disabled storage.
                          If False, delete from active configs and disabled storage.

        Returns:
            True if server was found and deleted, False otherwise
        """
        deleted = False
        clients_to_delete = []

        # Determine which clients to delete for
        if mode in ['claude', 'both']:
            clients_to_delete.append('claude')
        if mode in ['gemini', 'both']:
            clients_to_delete.append('gemini')

        if from_disabled:
            # Handle disabled storage with per-client awareness
            disabled = self.load_disabled_servers()
            if server_name in disabled:
                entry = disabled[server_name]
                if isinstance(entry, dict) and 'disabled_for' in entry:
                    # New format - update the disabled_for list
                    current_disabled = set(entry.get('disabled_for', []))
                    remaining = current_disabled - set(clients_to_delete)
                    if remaining:
                        # Still disabled for some clients
                        entry['disabled_for'] = sorted(list(remaining))
                        disabled[server_name] = entry
                    else:
                        # No longer disabled for any client
                        del disabled[server_name]
                else:
                    # Old format or full delete
                    del disabled[server_name]
                self.save_disabled_servers(disabled)
                deleted = True
        else:
            # Remove from active configs
            if 'claude' in clients_to_delete and 'mcpServers' in claude_data:
                if server_name in claude_data['mcpServers']:
                    del claude_data['mcpServers'][server_name]
                    deleted = True

            if 'gemini' in clients_to_delete and 'mcpServers' in gemini_data:
                if server_name in gemini_data['mcpServers']:
                    del gemini_data['mcpServers'][server_name]
                    deleted = True

            # Also update disabled storage
            disabled = self.load_disabled_servers()
            if server_name in disabled:
                entry = disabled[server_name]
                if isinstance(entry, dict) and 'disabled_for' in entry:
                    # New format - update based on mode
                    current_disabled = set(entry.get('disabled_for', []))
                    remaining = current_disabled - set(clients_to_delete)
                    if remaining:
                        entry['disabled_for'] = sorted(list(remaining))
                        disabled[server_name] = entry
                    else:
                        del disabled[server_name]
                else:
                    # Old format - delete entirely
                    del disabled[server_name]
                self.save_disabled_servers(disabled)
                deleted = True

        return deleted

    def bulk_enable_for_client(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                               client: str, server_names: List[str]) -> int:
        """Enable multiple servers for a specific client.

        Args:
            client: 'claude' or 'gemini' - the client to enable servers for
            server_names: List of server names to enable

        Returns:
            Number of servers successfully enabled
        """
        count = 0
        for server_name in server_names:
            if self.enable_server(claude_data, gemini_data, server_name, mode=client):
                count += 1
        return count

    def bulk_disable_for_client(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                                client: str, server_names: List[str]) -> int:
        """Disable multiple servers for a specific client.

        Args:
            client: 'claude' or 'gemini' - the client to disable servers for
            server_names: List of server names to disable

        Returns:
            Number of servers successfully disabled
        """
        count = 0
        for server_name in server_names:
            if self.disable_server(claude_data, gemini_data, server_name, mode=client):
                count += 1
        return count

    def sync_server_states(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                          source_client: str, target_client: str,
                          server_names: List[str] = None) -> int:
        """Synchronize server states from one client to another.

        Args:
            source_client: 'claude' or 'gemini' - the client to copy states from
            target_client: 'claude' or 'gemini' - the client to copy states to
            server_names: Optional list of specific servers to sync. If None, syncs all servers.

        Returns:
            Number of servers synchronized
        """
        if source_client == target_client:
            return 0

        # Get all servers if none specified
        if server_names is None:
            active, disabled = self.list_all_servers(claude_data, gemini_data, mode='both')
            all_servers = active + disabled
            server_names = [s['name'] for s in all_servers]

        count = 0
        for server_name in server_names:
            # Determine source state and config
            source_enabled = False
            server_config = None

            if source_client == 'claude':
                source_enabled = server_name in claude_data.get('mcpServers', {})
                if source_enabled:
                    server_config = claude_data['mcpServers'][server_name]
            elif source_client == 'gemini':
                source_enabled = server_name in gemini_data.get('mcpServers', {})
                if source_enabled:
                    server_config = gemini_data['mcpServers'][server_name]

            # If not in source active, check disabled storage
            if not source_enabled:
                disabled_servers = self.load_disabled_servers()
                if server_name in disabled_servers:
                    entry = disabled_servers[server_name]
                    if isinstance(entry, dict) and 'config' in entry:
                        server_config = entry['config']

            # Determine target state
            target_enabled = False
            if target_client == 'claude':
                target_enabled = server_name in claude_data.get('mcpServers', {})
                if not server_config and target_enabled:
                    server_config = claude_data['mcpServers'][server_name]
            elif target_client == 'gemini':
                target_enabled = server_name in gemini_data.get('mcpServers', {})
                if not server_config and target_enabled:
                    server_config = gemini_data['mcpServers'][server_name]

            # Skip if we don't have a config for this server
            if not server_config:
                continue

            # Sync if different
            if source_enabled != target_enabled:
                if source_enabled:
                    # Enable for target - first ensure it's in disabled storage if not already
                    if not target_enabled:
                        # Add to appropriate config
                        if target_client == 'claude':
                            if 'mcpServers' not in claude_data:
                                claude_data['mcpServers'] = {}
                            claude_data['mcpServers'][server_name] = server_config.copy()
                        elif target_client == 'gemini':
                            if 'mcpServers' not in gemini_data:
                                gemini_data['mcpServers'] = {}
                            gemini_data['mcpServers'][server_name] = server_config.copy()
                        count += 1
                else:
                    # Disable for target
                    if self.disable_server(claude_data, gemini_data, server_name, mode=target_client):
                        count += 1

        return count

    def _migrate_disabled_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old disabled servers format to new format.

        Old format: {"server_name": {...config...}}
        New format: {"server_name": {"config": {...}, "disabled_for": ["claude", "gemini"]}}
        """
        migrated = {}

        for server_name, value in data.items():
            if isinstance(value, dict):
                # Check if already in new format
                if 'config' in value and 'disabled_for' in value:
                    migrated[server_name] = value
                else:
                    # Old format - migrate it
                    # Assume disabled for both by default (preserves existing behavior)
                    migrated[server_name] = {
                        "config": value,
                        "disabled_for": ["claude", "gemini"]
                    }
            else:
                # Shouldn't happen, but handle gracefully
                migrated[server_name] = value

        return migrated

    def _normalize_to_new_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all entries in disabled servers follow the new format."""
        normalized = {}

        for server_name, value in data.items():
            if isinstance(value, dict):
                if 'config' in value and 'disabled_for' in value:
                    # Already in new format
                    normalized[server_name] = value
                else:
                    # Old format or bare config - normalize it
                    normalized[server_name] = {
                        "config": value,
                        "disabled_for": ["claude", "gemini"]
                    }
            else:
                # Shouldn't happen, but preserve it
                normalized[server_name] = value

        return normalized

    def _get_disabled_for_client(self, disabled: Dict[str, Any], client: str) -> Dict[str, Any]:
        """Get servers disabled for a specific client.

        Args:
            disabled: The full disabled servers dict
            client: "claude" or "gemini"

        Returns:
            Dict of server_name -> config for servers disabled for this client
        """
        result = {}
        for server_name, entry in disabled.items():
            if isinstance(entry, dict) and 'disabled_for' in entry:
                if client in entry.get('disabled_for', []):
                    result[server_name] = entry.get('config', {})
        return result

    def get_project_servers(self, base_paths: List[Path] = None, max_depth: int = 3,
                           use_cache: bool = True) -> Dict[str, List[ProjectServer]]:
        """
        Get all project-specific MCP servers.

        Args:
            base_paths: List of paths to scan for project configs
            max_depth: Maximum directory depth to scan
            use_cache: Whether to use cached results if available

        Returns:
            Dict mapping project path to list of ProjectServer objects
        """
        # Create discovery service if needed
        if not hasattr(self, '_discovery_service'):
            from ..parsers.claude_parser import ClaudeConfigParser
            parser = ClaudeConfigParser()
            self._discovery_service = ProjectDiscoveryService(claude_parser=parser)

        return self._discovery_service.scan_projects(
            base_paths=base_paths,
            max_depth=max_depth,
            use_cache=use_cache
        )

    def promote_project_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                               server_name: str, from_project: str,
                               to_global: bool = True) -> bool:
        """
        Promote a project server to global configuration.

        Args:
            claude_data: Claude configuration dict
            gemini_data: Gemini configuration dict
            server_name: Name of the server to promote
            from_project: Project path where server is currently defined
            to_global: Whether to promote to global (True) or just copy (False)

        Returns:
            True if promotion successful, False otherwise
        """
        # Get project servers
        project_servers = self.get_project_servers()

        # Find the specific server
        if from_project not in project_servers:
            return False

        server_to_promote = None
        for server in project_servers[from_project]:
            if server.name == server_name:
                server_to_promote = server
                break

        if not server_to_promote:
            return False

        # Add to both Claude and Gemini configs by default
        if 'mcpServers' not in claude_data:
            claude_data['mcpServers'] = {}
        if 'mcpServers' not in gemini_data:
            gemini_data['mcpServers'] = {}

        claude_data['mcpServers'][server_name] = server_to_promote.config.copy()
        gemini_data['mcpServers'][server_name] = server_to_promote.config.copy()

        # If to_global is True, also remove from project (requires claude_parser)
        if to_global and hasattr(self, '_discovery_service') and self._discovery_service.claude_parser:
            try:
                self._discovery_service.claude_parser.promote_to_global(
                    server_name, from_project
                )
            except Exception as e:
                # Log but don't fail - server is already added to global
                import logging
                logging.getLogger(__name__).warning(
                    f"Could not remove server from project after promotion: {e}"
                )

        return True

    def merge_duplicate_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                               server_name: str, strategy: str = 'keep_global') -> Dict[str, Any]:
        """
        Merge duplicate servers found in multiple locations.

        Args:
            claude_data: Claude configuration dict
            gemini_data: Gemini configuration dict
            server_name: Name of the server to merge
            strategy: Merge strategy - 'keep_global', 'keep_project', or 'merge'

        Returns:
            Dict with merge results including affected locations and final config
        """
        result = {
            'merged': False,
            'affected_projects': [],
            'final_config': None,
            'strategy_used': strategy
        }

        # Check if server exists in global configs
        global_config = None
        if 'mcpServers' in claude_data and server_name in claude_data['mcpServers']:
            global_config = claude_data['mcpServers'][server_name]
        elif 'mcpServers' in gemini_data and server_name in gemini_data['mcpServers']:
            global_config = gemini_data['mcpServers'][server_name]

        # Get project servers with this name
        project_servers = self.get_project_servers()
        project_configs = []

        for project_path, servers in project_servers.items():
            for server in servers:
                if server.name == server_name:
                    project_configs.append({
                        'project': project_path,
                        'config': server.config
                    })
                    result['affected_projects'].append(project_path)

        # Apply merge strategy
        if strategy == 'keep_global':
            if global_config:
                result['final_config'] = global_config
                result['merged'] = len(project_configs) > 0
        elif strategy == 'keep_project':
            if project_configs:
                # Use the first project config found
                result['final_config'] = project_configs[0]['config']
                # Update global configs
                if 'mcpServers' not in claude_data:
                    claude_data['mcpServers'] = {}
                if 'mcpServers' not in gemini_data:
                    gemini_data['mcpServers'] = {}
                claude_data['mcpServers'][server_name] = result['final_config'].copy()
                gemini_data['mcpServers'][server_name] = result['final_config'].copy()
                result['merged'] = True
        elif strategy == 'merge':
            # Merge configs - start with global if it exists
            merged_config = global_config.copy() if global_config else {}

            # Merge each project config
            for proj_cfg in project_configs:
                config = proj_cfg['config']
                # Deep merge - for simplicity, just update top-level keys
                # In a real implementation, you might want a more sophisticated merge
                for key, value in config.items():
                    if key not in merged_config:
                        merged_config[key] = value
                    elif isinstance(value, dict) and isinstance(merged_config[key], dict):
                        merged_config[key].update(value)
                    elif isinstance(value, list) and isinstance(merged_config[key], list):
                        # Combine lists, removing duplicates
                        merged_config[key] = list(set(merged_config[key] + value))

            result['final_config'] = merged_config
            if merged_config:
                # Update global configs
                if 'mcpServers' not in claude_data:
                    claude_data['mcpServers'] = {}
                if 'mcpServers' not in gemini_data:
                    gemini_data['mcpServers'] = {}
                claude_data['mcpServers'][server_name] = merged_config
                gemini_data['mcpServers'][server_name] = merged_config
                result['merged'] = True

        return result

    def consolidate_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                           strategy: str = 'keep_global') -> Dict[str, Any]:
        """
        Consolidate all project servers to global configuration.

        Args:
            claude_data: Claude configuration dict
            gemini_data: Gemini configuration dict
            strategy: Strategy for handling duplicates - 'keep_global', 'keep_project', or 'merge'

        Returns:
            Dict with consolidation results including count and conflicts
        """
        result = {
            'total_promoted': 0,
            'conflicts_resolved': 0,
            'errors': [],
            'promoted_servers': []
        }

        # Get all project servers
        project_servers = self.get_project_servers()

        # Track all unique server names across projects
        all_server_names = set()
        for servers in project_servers.values():
            for server in servers:
                all_server_names.add(server.name)

        # Process each unique server
        for server_name in all_server_names:
            # Check if it already exists in global
            exists_in_global = (
                ('mcpServers' in claude_data and server_name in claude_data['mcpServers']) or
                ('mcpServers' in gemini_data and server_name in gemini_data['mcpServers'])
            )

            if exists_in_global:
                # Handle conflict using merge strategy
                merge_result = self.merge_duplicate_servers(
                    claude_data, gemini_data, server_name, strategy
                )
                if merge_result['merged']:
                    result['conflicts_resolved'] += 1
            else:
                # Find first occurrence and promote it
                for project_path, servers in project_servers.items():
                    for server in servers:
                        if server.name == server_name:
                            if self.promote_project_server(
                                claude_data, gemini_data,
                                server_name, project_path, to_global=True
                            ):
                                result['total_promoted'] += 1
                                result['promoted_servers'].append({
                                    'name': server_name,
                                    'from_project': project_path
                                })
                            else:
                                result['errors'].append(
                                    f"Failed to promote {server_name} from {project_path}"
                                )
                            break
                    else:
                        continue
                    break

        return result
