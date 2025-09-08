"""Application state model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class Mode(Enum):
    """Application operation mode."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    BOTH = "both"


class ViewType(Enum):
    """UI view types."""
    SERVER_LIST = "server_list"
    PRESET_MANAGER = "preset_manager"
    BACKUP_RESTORE = "backup_restore"
    SETTINGS = "settings"


@dataclass
class ApplicationState:
    """Represents the current state of the application."""
    
    mode: Mode = Mode.BOTH
    current_view: ViewType = ViewType.SERVER_LIST
    
    # Server state
    active_servers: List[str] = field(default_factory=list)
    disabled_servers: List[str] = field(default_factory=list)
    selected_servers: Set[str] = field(default_factory=set)
    
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
        self.mode = Mode.BOTH
        self.current_view = ViewType.SERVER_LIST
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
    
    def set_mode(self, mode: Mode) -> None:
        """Change application mode."""
        if mode != self.mode:
            self.mode = mode
            self.has_unsaved_changes = True
    
    def toggle_server(self, server_name: str) -> None:
        """Toggle server between active and disabled."""
        if server_name in self.active_servers:
            self.active_servers.remove(server_name)
            self.disabled_servers.append(server_name)
        elif server_name in self.disabled_servers:
            self.disabled_servers.remove(server_name)
            self.active_servers.append(server_name)
        self.has_unsaved_changes = True
    
    def add_server(self, server_name: str, enabled: bool = True) -> None:
        """Add a new server."""
        if enabled:
            if server_name not in self.active_servers:
                self.active_servers.append(server_name)
        else:
            if server_name not in self.disabled_servers:
                self.disabled_servers.append(server_name)
        self.has_unsaved_changes = True
    
    def remove_server(self, server_name: str) -> None:
        """Remove a server."""
        if server_name in self.active_servers:
            self.active_servers.remove(server_name)
        if server_name in self.disabled_servers:
            self.disabled_servers.remove(server_name)
        if server_name in self.selected_servers:
            self.selected_servers.discard(server_name)
        self.has_unsaved_changes = True
    
    def enable_all_servers(self) -> None:
        """Enable all disabled servers."""
        self.active_servers.extend(self.disabled_servers)
        self.disabled_servers.clear()
        self.has_unsaved_changes = True
    
    def disable_all_servers(self) -> None:
        """Disable all active servers."""
        self.disabled_servers.extend(self.active_servers)
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
    
    def is_server_active(self, server_name: str) -> bool:
        """Check if a server is active."""
        return server_name in self.active_servers
    
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