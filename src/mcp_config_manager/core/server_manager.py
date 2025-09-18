"""
Server management functionality
Extracted from mcp_toggle.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional, Iterable, Mapping
from ..utils.file_utils import get_disabled_servers_path
from .project_discovery import ProjectDiscoveryService, ProjectServer


class ServerManager:
    """Manages MCP server enabling/disabling and storage"""
    SUPPORTED_CLIENTS: Tuple[str, ...] = ("claude", "gemini", "codex")
    DEFAULT_DISABLED: Tuple[str, ...] = SUPPORTED_CLIENTS

    def __init__(self, disabled_path: Path = None):
        self.disabled_path = disabled_path or get_disabled_servers_path()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_client_map(
        self,
        claude_data: Optional[Dict[str, Any]] = None,
        gemini_data: Optional[Dict[str, Any]] = None,
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Create a mapping of client identifier to config dict."""

        client_map: Dict[str, Dict[str, Any]] = {}
        if claude_data is not None:
            client_map["claude"] = claude_data
        if gemini_data is not None:
            client_map["gemini"] = gemini_data
        if codex_data is not None:
            client_map["codex"] = codex_data
        return client_map

    def _resolve_clients(self, mode: Optional[str], available: Iterable[str]) -> List[str]:
        """Resolve mode string into concrete client list."""

        available_set = set(available)
        if not available_set:
            return []

        if not mode or mode.lower() in {"all", "any"}:
            return [c for c in self.SUPPORTED_CLIENTS if c in available_set]

        mode_lower = mode.lower()
        if mode_lower == "both":
            base = ["claude", "gemini"]
            return [c for c in base if c in available_set]

        if mode_lower in available_set:
            return [mode_lower]

        # Fallback: return all available clients that we support
        return [c for c in self.SUPPORTED_CLIENTS if c in available_set]

    def _get_server_table(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return the mutable server table from a config dict."""

        if not config:
            return {}
        if "mcpServers" in config and isinstance(config["mcpServers"], dict):
            return config["mcpServers"]
        if "mcp_servers" in config and isinstance(config["mcp_servers"], dict):
            return config["mcp_servers"]
        return {}

    def _ensure_server_table(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the config has a mutable mcpServers dict and return it."""

        if "mcpServers" not in config or not isinstance(config.get("mcpServers"), dict):
            config["mcpServers"] = {}
        return config["mcpServers"]

    def _set_server_table(self, config: Dict[str, Any], table: Dict[str, Any]) -> None:
        """Persist table back onto config in internal format."""

        config["mcpServers"] = table
    
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
    
    def disable_server(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Move a server from active configs into disabled storage."""

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        clients_to_disable = self._resolve_clients(mode, client_map.keys())
        if not clients_to_disable:
            return False

        disabled = self.load_disabled_servers()

        # Find the latest server config from any active client
        server_config = None
        for client in self.SUPPORTED_CLIENTS:
            table = self._get_server_table(client_map.get(client))
            if server_name in table:
                server_config = table[server_name]
                break

        # Fall back to existing disabled entry config
        if server_config is None and server_name in disabled:
            entry = disabled.get(server_name)
            if isinstance(entry, dict):
                server_config = entry.get("config")

        if server_config is None:
            # Without a config snapshot we cannot safely disable
            return False

        entry = disabled.get(server_name, {"config": server_config, "disabled_for": []})
        if not isinstance(entry, dict):
            entry = {"config": server_config, "disabled_for": list(self.DEFAULT_DISABLED)}

        entry["config"] = server_config
        disabled_for = set(entry.get("disabled_for", []))
        disabled_for.update(clients_to_disable)
        entry["disabled_for"] = sorted(disabled_for)
        disabled[server_name] = entry

        # Remove from each active config as requested
        for client in clients_to_disable:
            table = self._get_server_table(client_map.get(client))
            if server_name in table:
                del table[server_name]

        self.save_disabled_servers(disabled)
        return True
    
    def enable_server(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Move a server from disabled storage back into active configs."""

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        clients_to_enable = self._resolve_clients(mode, client_map.keys())
        if not clients_to_enable:
            return False

        disabled = self.load_disabled_servers()
        if server_name not in disabled:
            return False

        entry = disabled[server_name]
        if not isinstance(entry, dict):
            return False

        server_config = entry.get("config")
        if not isinstance(server_config, dict):
            return False

        current_disabled = set(entry.get("disabled_for", []))

        for client in clients_to_enable:
            table = self._ensure_server_table(client_map[client])
            table[server_name] = server_config.copy()

        remaining_disabled = current_disabled - set(clients_to_enable)

        if remaining_disabled:
            entry["disabled_for"] = sorted(remaining_disabled)
            disabled[server_name] = entry
        else:
            disabled.pop(server_name, None)

        self.save_disabled_servers(disabled)
        return True
    
    def get_enabled_servers(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return enabled server records with per-client flags."""

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        server_states: Dict[str, Dict[str, Any]] = {}

        for client, config in client_map.items():
            table = self._get_server_table(config)
            for name, server_config in table.items():
                entry = server_states.setdefault(
                    name,
                    {
                        'name': name,
                        'config': server_config,
                        'enabled': False,
                        'per_client': {c: False for c in self.SUPPORTED_CLIENTS},
                    },
                )
                entry['per_client'][client] = True
                entry[f'{client}_enabled'] = True
                entry['enabled'] = entry['enabled'] or True
                # Prefer existing config unless missing
                if 'config' not in entry or not entry['config']:
                    entry['config'] = server_config

        # Ensure missing client flags default to False for backward compatibility
        for entry in server_states.values():
            for client in self.SUPPORTED_CLIENTS:
                key = f'{client}_enabled'
                if key not in entry:
                    entry[key] = False
                    entry['per_client'][client] = False

        target_clients = set(self._resolve_clients(mode, client_map.keys())) or set(client_map.keys())

        filtered = [
            entry
            for entry in server_states.values()
            if any(entry.get(f'{client}_enabled', False) for client in target_clients)
        ]

        return sorted(filtered, key=lambda x: x['name'])
    
    def list_all_servers(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        mode: str = 'both',
        include_project_servers: bool = False,
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """List active/disabled servers with per-client metadata."""

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        all_servers: Dict[str, Dict[str, Any]] = {}

        def ensure_entry(name: str) -> Dict[str, Any]:
            return all_servers.setdefault(
                name,
                {
                    'name': name,
                    'config': {},
                    'per_client': {c: False for c in self.SUPPORTED_CLIENTS},
                    'location': 'global',
                    'is_active': False,
                },
            )

        # Populate active global servers
        for client, config in client_map.items():
            table = self._get_server_table(config)
            for name, server_config in table.items():
                entry = ensure_entry(name)
                entry['config'] = entry['config'] or server_config
                entry[f'{client}_enabled'] = True
                entry['per_client'][client] = True
                entry['is_active'] = True

        # Merge disabled storage state
        disabled_storage = self.load_disabled_servers()
        for name, raw_entry in disabled_storage.items():
            entry = ensure_entry(name)
            if isinstance(raw_entry, dict):
                config_snapshot = raw_entry.get('config', {})
                disabled_for = set(raw_entry.get('disabled_for', []))
            else:
                config_snapshot = raw_entry
                disabled_for = set(self.DEFAULT_DISABLED)

            if config_snapshot and not entry['config']:
                entry['config'] = config_snapshot

            for client in self.SUPPORTED_CLIENTS:
                enabled_key = f'{client}_enabled'
                currently_enabled = entry.get(enabled_key, False)
                if client in disabled_for:
                    entry[enabled_key] = False
                    entry['per_client'][client] = False
                else:
                    entry[enabled_key] = currently_enabled or entry['per_client'][client]
                    entry['per_client'][client] = entry[enabled_key]

            entry['is_active'] = any(
                entry.get(f'{client}_enabled', False) for client in self.SUPPORTED_CLIENTS
            )

        # Ensure all expected flags exist
        for entry in all_servers.values():
            for client in self.SUPPORTED_CLIENTS:
                key = f'{client}_enabled'
                if key not in entry:
                    entry[key] = False
                    entry['per_client'][client] = False

        # Add project-specific servers if requested (Codex not yet supported)
        if include_project_servers:
            try:
                project_servers = self.get_project_servers(use_cache=True)
                for project_path, servers in project_servers.items():
                    for server in servers:
                        is_duplicate = server.name in all_servers
                        key = f"{server.name}@{project_path}" if is_duplicate else server.name
                        entry = ensure_entry(key)
                        entry.update(
                            {
                                'name': server.name,
                                'config': server.config,
                                'location': str(project_path),
                                'is_project_server': True,
                                'is_duplicate': is_duplicate,
                            }
                        )
                        for client in self.SUPPORTED_CLIENTS:
                            enabled = client in {"claude", "gemini"}
                            entry[f'{client}_enabled'] = enabled
                            entry['per_client'][client] = enabled
                        entry['is_active'] = True
            except Exception as exc:
                import logging

                logging.getLogger(__name__).debug(
                    "Could not include project servers: %s", exc
                )

        target_clients = set(self._resolve_clients(mode, client_map.keys()))
        if not target_clients:
            target_clients = set(client_map.keys()) or set(self.SUPPORTED_CLIENTS)

        active: List[Dict[str, Any]] = []
        disabled: List[Dict[str, Any]] = []

        for entry in all_servers.values():
            is_active_for_mode = any(
                entry.get(f'{client}_enabled', False) for client in target_clients
            )
            is_disabled_for_mode = any(
                not entry.get(f'{client}_enabled', False) for client in target_clients
            )

            if is_active_for_mode:
                active.append(entry)
            if is_disabled_for_mode:
                disabled.append(entry)

        active.sort(key=lambda x: x['name'])
        disabled.sort(key=lambda x: x['name'])

        return active, disabled
    
    def disable_all_servers(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Disable all active servers"""
        active, _ = self.list_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        count = 0

        for server in active:
            if self.disable_server(
                claude_data,
                gemini_data,
                server['name'],
                mode,
                codex_data=codex_data,
            ):
                count += 1

        return count

    def enable_all_servers(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Enable all disabled servers"""
        _, disabled = self.list_all_servers(
            claude_data,
            gemini_data,
            mode,
            codex_data=codex_data,
        )
        count = 0

        for server in disabled:
            if self.enable_server(
                claude_data,
                gemini_data,
                server['name'],
                mode,
                codex_data=codex_data,
            ):
                count += 1

        return count
    
    def add_new_server_from_json(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        json_text: str,
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
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
                            self._add_server_to_configs(
                                claude_data,
                                gemini_data,
                                server_name,
                                server_config,
                                mode,
                                codex_data=codex_data,
                            )
                    return True, f"Added {len(parsed)} servers"
            else:
                return False, "Invalid JSON structure"
                
        except json.JSONDecodeError as e:
            return False, f"JSON parsing failed: {e}"

    def add_server_with_name(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        server_config: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a server with a specific name"""
        return self._add_server_to_configs(
            claude_data,
            gemini_data,
            server_name,
            server_config,
            mode,
            codex_data=codex_data,
        )


    def _add_server_to_configs(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        server_config: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Internal method to add server to appropriate configs"""
        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        targets = self._resolve_clients(mode, client_map.keys())
        if not targets:
            return False

        for client in targets:
            table = self._ensure_server_table(client_map[client])
            table[server_name] = server_config.copy()

        return True
    
    def update_server_config(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        new_config: Dict[str, Any],
        mode: str = 'both',
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing server's configuration.

        Updates the config in active configs and/or disabled storage as appropriate.
        """
        updated = False

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        targets = self._resolve_clients(mode, client_map.keys())

        for client in targets:
            table = self._get_server_table(client_map.get(client))
            if server_name in table:
                self._ensure_server_table(client_map[client])[server_name] = new_config.copy()
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
                    "disabled_for": list(self.DEFAULT_DISABLED)
                }
            self.save_disabled_servers(disabled)
            updated = True

        return updated
    
    def delete_server(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        server_name: str,
        mode: str = 'both',
        from_disabled: bool = False,
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
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
        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        clients_to_delete = self._resolve_clients(mode, client_map.keys())

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
            for client in clients_to_delete:
                table = self._get_server_table(client_map.get(client))
                if server_name in table:
                    del table[server_name]
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

    def bulk_enable_for_client(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        client: str,
        server_names: List[str],
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Enable multiple servers for a specific client.

        Args:
            client: 'claude' or 'gemini' - the client to enable servers for
            server_names: List of server names to enable

        Returns:
            Number of servers successfully enabled
        """
        count = 0
        for server_name in server_names:
            if self.enable_server(
                claude_data,
                gemini_data,
                server_name,
                mode=client,
                codex_data=codex_data,
            ):
                count += 1
        return count

    def bulk_disable_for_client(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        client: str,
        server_names: List[str],
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Disable multiple servers for a specific client.

        Args:
            client: 'claude' or 'gemini' - the client to disable servers for
            server_names: List of server names to disable

        Returns:
            Number of servers successfully disabled
        """
        count = 0
        for server_name in server_names:
            if self.disable_server(
                claude_data,
                gemini_data,
                server_name,
                mode=client,
                codex_data=codex_data,
            ):
                count += 1
        return count

    def sync_server_states(
        self,
        claude_data: Dict[str, Any],
        gemini_data: Dict[str, Any],
        source_client: str,
        target_client: str,
        server_names: List[str] = None,
        codex_data: Optional[Dict[str, Any]] = None,
    ) -> int:
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

        client_map = self._build_client_map(claude_data, gemini_data, codex_data)
        if source_client not in client_map or target_client not in client_map:
            return 0

        # Get all servers if none specified
        if server_names is None:
            active, disabled = self.list_all_servers(
                claude_data,
                gemini_data,
                mode='all',
                codex_data=codex_data,
            )
            all_servers = active + disabled
            server_names = [s['name'] for s in all_servers]

        count = 0
        disabled_store = self.load_disabled_servers()
        disabled_modified = False

        for server_name in server_names:
            # Determine source state and config
            source_table = self._get_server_table(client_map.get(source_client))
            target_table = self._get_server_table(client_map.get(target_client))

            source_enabled = server_name in source_table
            target_enabled = server_name in target_table

            server_config = source_table.get(server_name)

            if not server_config:
                entry = disabled_store.get(server_name)
                if isinstance(entry, dict):
                    server_config = entry.get('config')

            # Skip if we don't have a config for this server
            if not server_config:
                continue

            # Sync if different
            if source_enabled != target_enabled:
                if source_enabled:
                    target_table = self._ensure_server_table(client_map[target_client])
                    target_table[server_name] = server_config.copy()

                    entry = disabled_store.get(server_name)
                    if isinstance(entry, dict):
                        disabled_for = set(entry.get('disabled_for', []))
                        if target_client in disabled_for:
                            disabled_for.remove(target_client)
                            if disabled_for:
                                entry['disabled_for'] = sorted(disabled_for)
                                disabled_store[server_name] = entry
                            else:
                                disabled_store.pop(server_name, None)
                            disabled_modified = True
                    count += 1
                else:
                    # Disable for target
                    if self.disable_server(
                        claude_data,
                        gemini_data,
                        server_name,
                        mode=target_client,
                        codex_data=codex_data,
                    ):
                        disabled_store = self.load_disabled_servers()
                        count += 1

        if disabled_modified:
            self.save_disabled_servers(disabled_store)

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
                        "disabled_for": list(self.DEFAULT_DISABLED),
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
                        "disabled_for": list(self.DEFAULT_DISABLED),
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
