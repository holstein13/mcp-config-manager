"""Application state model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


# Mode enum deprecated - we now track per-LLM states directly
# class Mode(Enum) removed in favor of per-client tracking


class ViewType(Enum):
    """UI view types."""
    SERVER_LIST = "server_list"
    PRESET_MANAGER = "preset_manager"
    BACKUP_RESTORE = "backup_restore"
    SETTINGS = "settings"


@dataclass
class ApplicationState:
    """Represents the current state of the application."""
    
    # Mode property removed - we now track per-LLM states
    current_view: ViewType = ViewType.SERVER_LIST

    # Server state - now tracked per LLM
    claude_servers: Dict[str, bool] = field(default_factory=dict)  # server_name: enabled
    gemini_servers: Dict[str, bool] = field(default_factory=dict)  # server_name: enabled
    selected_servers: Set[str] = field(default_factory=set)

    # Legacy lists for backward compatibility during transition
    active_servers: List[str] = field(default_factory=list)
    disabled_servers: List[str] = field(default_factory=list)
    
    # Preset state
    available_presets: List[str] = field(default_factory=list)
    current_preset: Optional[str] = None
    custom_presets: Dict[str, List[str]] = field(default_factory=dict)
    
    # File state
    config_loaded: bool = False
    has_unsaved_changes: bool = False
    config_path_claude: Optional[str] = None
    config_path_gemini: Optional[str] = None
    
    # Backup state
    available_backups: List[str] = field(default_factory=list)
    last_backup: Optional[str] = None
    auto_backup_enabled: bool = True
    
    # UI state
    search_filter: str = ""
    show_disabled_servers: bool = True
    sort_alphabetically: bool = True
    
    # Error state
    last_error: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    
    # Operation state
    is_loading: bool = False
    is_saving: bool = False
    current_operation: Optional[str] = None
    
    def reset(self) -> None:
        """Reset application state to defaults."""
        self.current_view = ViewType.SERVER_LIST
        self.claude_servers.clear()
        self.gemini_servers.clear()
        self.active_servers.clear()
        self.disabled_servers.clear()
        self.selected_servers.clear()
        self.available_presets.clear()
        self.current_preset = None
        self.custom_presets.clear()
        self.config_loaded = False
        self.has_unsaved_changes = False
        self.config_path_claude = None
        self.config_path_gemini = None
        self.available_backups.clear()
        self.last_backup = None
        self.search_filter = ""
        self.last_error = None
        self.validation_errors.clear()
        self.is_loading = False
        self.is_saving = False
        self.current_operation = None
    
    # Mode setter removed - no longer needed with per-LLM tracking

    def get_server_enabled(self, server_name: str, client: str) -> bool:
        """Check if a server is enabled for a specific client."""
        if client == "claude":
            return self.claude_servers.get(server_name, False)
        elif client == "gemini":
            return self.gemini_servers.get(server_name, False)
        return False

    def set_server_enabled(self, server_name: str, client: str, enabled: bool) -> None:
        """Set server enabled state for a specific client."""
        if client == "claude":
            self.claude_servers[server_name] = enabled
        elif client == "gemini":
            self.gemini_servers[server_name] = enabled
        self.has_unsaved_changes = True
    
    def toggle_server(self, server_name: str, client: Optional[str] = None) -> None:
        """Toggle server enabled state for a specific client or both."""
        if client == "claude":
            current = self.claude_servers.get(server_name, False)
            self.claude_servers[server_name] = not current
        elif client == "gemini":
            current = self.gemini_servers.get(server_name, False)
            self.gemini_servers[server_name] = not current
        elif client is None:
            # Toggle both when no client specified
            claude_state = self.claude_servers.get(server_name, False)
            gemini_state = self.gemini_servers.get(server_name, False)
            # If either is enabled, disable both; otherwise enable both
            new_state = not (claude_state or gemini_state)
            self.claude_servers[server_name] = new_state
            self.gemini_servers[server_name] = new_state
        self.has_unsaved_changes = True
    
    def add_server(self, server_name: str, enabled_claude: bool = True, enabled_gemini: bool = True) -> None:
        """Add a new server with per-LLM enabled states."""
        self.claude_servers[server_name] = enabled_claude
        self.gemini_servers[server_name] = enabled_gemini
        # Update legacy lists for compatibility
        if enabled_claude or enabled_gemini:
            if server_name not in self.active_servers:
                self.active_servers.append(server_name)
            if server_name in self.disabled_servers:
                self.disabled_servers.remove(server_name)
        else:
            if server_name not in self.disabled_servers:
                self.disabled_servers.append(server_name)
            if server_name in self.active_servers:
                self.active_servers.remove(server_name)
        self.has_unsaved_changes = True
    
    def remove_server(self, server_name: str) -> None:
        """Remove a server from all tracking."""
        # Remove from per-LLM tracking
        self.claude_servers.pop(server_name, None)
        self.gemini_servers.pop(server_name, None)
        # Remove from legacy lists
        if server_name in self.active_servers:
            self.active_servers.remove(server_name)
        if server_name in self.disabled_servers:
            self.disabled_servers.remove(server_name)
        if server_name in self.selected_servers:
            self.selected_servers.discard(server_name)
        self.has_unsaved_changes = True
    
    def enable_all_servers(self, client: Optional[str] = None) -> None:
        """Enable all servers for a specific client or both."""
        all_servers = set(self.claude_servers.keys()) | set(self.gemini_servers.keys())
        if client == "claude":
            for server in all_servers:
                self.claude_servers[server] = True
        elif client == "gemini":
            for server in all_servers:
                self.gemini_servers[server] = True
        elif client is None:
            # Enable for both
            for server in all_servers:
                self.claude_servers[server] = True
                self.gemini_servers[server] = True
        # Update legacy lists
        self.active_servers = list(all_servers)
        self.disabled_servers.clear()
        self.has_unsaved_changes = True
    
    def disable_all_servers(self, client: Optional[str] = None) -> None:
        """Disable all servers for a specific client or both."""
        all_servers = set(self.claude_servers.keys()) | set(self.gemini_servers.keys())
        if client == "claude":
            for server in all_servers:
                self.claude_servers[server] = False
        elif client == "gemini":
            for server in all_servers:
                self.gemini_servers[server] = False
        elif client is None:
            # Disable for both
            for server in all_servers:
                self.claude_servers[server] = False
                self.gemini_servers[server] = False
        # Update legacy lists
        self.disabled_servers = list(all_servers)
        self.active_servers.clear()
        self.has_unsaved_changes = True
    
    def apply_preset(self, preset_name: str, servers: List[str]) -> None:
        """Apply a preset configuration."""
        self.active_servers = servers.copy()
        self.disabled_servers.clear()
        self.current_preset = preset_name
        self.has_unsaved_changes = True
    
    def save_custom_preset(self, name: str, servers: List[str]) -> None:
        """Save current configuration as a custom preset."""
        self.custom_presets[name] = servers.copy()
        self.available_presets.append(name)
    
    def delete_custom_preset(self, name: str) -> None:
        """Delete a custom preset."""
        if name in self.custom_presets:
            del self.custom_presets[name]
            self.available_presets.remove(name)
    
    def mark_saved(self) -> None:
        """Mark state as saved."""
        self.has_unsaved_changes = False
        self.config_loaded = True
    
    def set_operation(self, operation: Optional[str]) -> None:
        """Set current operation being performed."""
        self.current_operation = operation
        if operation:
            if "load" in operation.lower():
                self.is_loading = True
            elif "save" in operation.lower():
                self.is_saving = True
        else:
            self.is_loading = False
            self.is_saving = False
    
    def add_validation_error(self, error: str) -> None:
        """Add a validation error."""
        if error not in self.validation_errors:
            self.validation_errors.append(error)
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()
    
    def get_all_servers(self) -> List[str]:
        """Get all servers (active and disabled)."""
        return self.active_servers + self.disabled_servers
    
    def get_filtered_servers(self) -> List[str]:
        """Get servers filtered by search term."""
        if not self.search_filter:
            return self.get_all_servers() if self.show_disabled_servers else self.active_servers
        
        filter_lower = self.search_filter.lower()
        all_servers = self.get_all_servers() if self.show_disabled_servers else self.active_servers
        return [s for s in all_servers if filter_lower in s.lower()]
    
    def is_server_active(self, server_name: str, client: Optional[str] = None) -> bool:
        """Check if a server is active for any or specific client."""
        if client == "claude":
            return self.claude_servers.get(server_name, False)
        elif client == "gemini":
            return self.gemini_servers.get(server_name, False)
        else:
            # Check if active for either client
            return (self.claude_servers.get(server_name, False) or
                    self.gemini_servers.get(server_name, False))
    
    def is_server_selected(self, server_name: str) -> bool:
        """Check if a server is selected."""
        return server_name in self.selected_servers
    
    def toggle_server_selection(self, server_name: str) -> None:
        """Toggle server selection state."""
        if server_name in self.selected_servers:
            self.selected_servers.discard(server_name)
        else:
            self.selected_servers.add(server_name)
    
    def clear_selection(self) -> None:
        """Clear all selected servers."""
        self.selected_servers.clear()
    
    def select_all(self) -> None:
        """Select all visible servers."""
        filtered = self.get_filtered_servers()
        self.selected_servers = set(filtered)

    def get_all_server_states(self) -> Dict[str, Dict[str, bool]]:
        """Get all server states for both clients."""
        all_servers = set(self.claude_servers.keys()) | set(self.gemini_servers.keys())
        states = {}
        for server in all_servers:
            states[server] = {
                "claude": self.claude_servers.get(server, False),
                "gemini": self.gemini_servers.get(server, False)
            }
        return states

    def get_servers_for_client(self, client: str, enabled_only: bool = True) -> List[str]:
        """Get servers for a specific client."""
        if client == "claude":
            servers = self.claude_servers
        elif client == "gemini":
            servers = self.gemini_servers
        else:
            return []

        if enabled_only:
            return [name for name, enabled in servers.items() if enabled]
        else:
            return list(servers.keys())

    def sync_from_legacy_lists(self) -> None:
        """Sync per-LLM states from legacy active/disabled lists."""
        # Enable servers in active list for both clients
        for server in self.active_servers:
            self.claude_servers[server] = True
            self.gemini_servers[server] = True
        # Disable servers in disabled list for both clients
        for server in self.disabled_servers:
            self.claude_servers[server] = False
            self.gemini_servers[server] = False