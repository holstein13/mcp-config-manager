"""Preset list item model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class PresetType(Enum):
    """Preset types."""
    BUILTIN = "builtin"
    CUSTOM = "custom"
    IMPORTED = "imported"
    RECENT = "recent"


class PresetCategory(Enum):
    """Preset categories."""
    MINIMAL = "minimal"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    CUSTOM = "custom"


@dataclass
class PresetListItem:
    """Represents a preset in the preset list."""
    
    # Core properties
    name: str
    preset_type: PresetType = PresetType.CUSTOM
    category: PresetCategory = PresetCategory.CUSTOM
    
    # Server configuration
    enabled_servers: List[str] = field(default_factory=list)
    disabled_servers: List[str] = field(default_factory=list)
    server_count: int = 0
    
    # Display properties
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # State properties
    is_selected: bool = False
    is_active: bool = False
    is_modified: bool = False
    is_favorite: bool = False
    
    # Metadata
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    last_used_date: Optional[str] = None
    usage_count: int = 0
    author: Optional[str] = None
    version: Optional[str] = None
    
    # Mode support
    supported_modes: Set[str] = field(default_factory=lambda: {"claude", "gemini", "both"})
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Additional configuration
    config: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived properties."""
        self.server_count = len(self.enabled_servers) + len(self.disabled_servers)
        if not self.description:
            self.description = self._generate_description()
        if not self.icon:
            self.icon = self._get_default_icon()
    
    def _generate_description(self) -> str:
        """Generate default description."""
        if self.preset_type == PresetType.BUILTIN:
            descriptions = {
                "minimal": "Minimal configuration with essential servers only",
                "web-dev": "Web development preset with browser and dev tools",
                "full": "Full configuration with all available servers",
                "testing": "Testing preset with test runners and mock servers",
            }
            return descriptions.get(self.name, f"{self.name} preset configuration")
        return f"Custom preset with {self.server_count} servers"
    
    def _get_default_icon(self) -> str:
        """Get default icon based on preset type and category."""
        if self.preset_type == PresetType.BUILTIN:
            icon_map = {
                PresetCategory.MINIMAL: "minimize",
                PresetCategory.DEVELOPMENT: "code",
                PresetCategory.PRODUCTION: "rocket",
                PresetCategory.TESTING: "flask",
                PresetCategory.CUSTOM: "palette",
            }
            return icon_map.get(self.category, "bookmark")
        elif self.preset_type == PresetType.IMPORTED:
            return "download"
        elif self.preset_type == PresetType.RECENT:
            return "history"
        return "bookmark"
    
    def apply(self) -> Dict[str, List[str]]:
        """Get server configuration to apply."""
        return {
            "enabled": self.enabled_servers.copy(),
            "disabled": self.disabled_servers.copy(),
        }
    
    def update_servers(self, enabled: List[str], disabled: List[str]) -> None:
        """Update server lists."""
        self.enabled_servers = enabled.copy()
        self.disabled_servers = disabled.copy()
        self.server_count = len(enabled) + len(disabled)
        self.is_modified = True
        self.modified_date = None  # Should be set by caller
    
    def add_server(self, server_name: str, enabled: bool = True) -> None:
        """Add a server to the preset."""
        if enabled:
            if server_name not in self.enabled_servers:
                self.enabled_servers.append(server_name)
                if server_name in self.disabled_servers:
                    self.disabled_servers.remove(server_name)
        else:
            if server_name not in self.disabled_servers:
                self.disabled_servers.append(server_name)
                if server_name in self.enabled_servers:
                    self.enabled_servers.remove(server_name)
        
        self.server_count = len(self.enabled_servers) + len(self.disabled_servers)
        self.is_modified = True
    
    def remove_server(self, server_name: str) -> None:
        """Remove a server from the preset."""
        if server_name in self.enabled_servers:
            self.enabled_servers.remove(server_name)
        if server_name in self.disabled_servers:
            self.disabled_servers.remove(server_name)
        
        self.server_count = len(self.enabled_servers) + len(self.disabled_servers)
        self.is_modified = True
    
    def toggle_server(self, server_name: str) -> None:
        """Toggle a server between enabled and disabled."""
        if server_name in self.enabled_servers:
            self.enabled_servers.remove(server_name)
            self.disabled_servers.append(server_name)
        elif server_name in self.disabled_servers:
            self.disabled_servers.remove(server_name)
            self.enabled_servers.append(server_name)
        else:
            # Server not in preset, add as enabled
            self.enabled_servers.append(server_name)
        
        self.is_modified = True
    
    def has_server(self, server_name: str) -> bool:
        """Check if preset contains a server."""
        return server_name in self.enabled_servers or server_name in self.disabled_servers
    
    def is_server_enabled(self, server_name: str) -> bool:
        """Check if a server is enabled in this preset."""
        return server_name in self.enabled_servers
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the preset."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.is_modified = True
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the preset."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.is_modified = True
    
    def has_tag(self, tag: str) -> bool:
        """Check if preset has a tag."""
        return tag in self.tags
    
    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.is_modified = True
    
    def supports_mode(self, mode: str) -> bool:
        """Check if preset supports a mode."""
        return mode in self.supported_modes
    
    def add_mode_support(self, mode: str) -> None:
        """Add support for a mode."""
        self.supported_modes.add(mode)
        self.is_modified = True
    
    def remove_mode_support(self, mode: str) -> None:
        """Remove support for a mode."""
        self.supported_modes.discard(mode)
        self.is_modified = True
    
    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1
        self.last_used_date = None  # Should be set by caller
    
    def validate(self) -> bool:
        """Validate preset configuration."""
        self.validation_errors.clear()
        self.is_valid = True
        
        # Validate name
        if not self.name:
            self.validation_errors.append("Preset name is required")
            self.is_valid = False
        elif len(self.name) < 2:
            self.validation_errors.append("Preset name must be at least 2 characters")
            self.is_valid = False
        
        # Check for duplicate servers
        duplicates = set(self.enabled_servers) & set(self.disabled_servers)
        if duplicates:
            self.validation_errors.append(f"Servers in both enabled and disabled: {', '.join(duplicates)}")
            self.is_valid = False
        
        # Validate server count matches
        actual_count = len(self.enabled_servers) + len(self.disabled_servers)
        if self.server_count != actual_count:
            self.server_count = actual_count  # Fix the count
        
        # Validate supported modes
        if not self.supported_modes:
            self.validation_errors.append("Preset must support at least one mode")
            self.is_valid = False
        
        return self.is_valid
    
    def matches_filter(self, filter_text: str, case_sensitive: bool = False) -> bool:
        """Check if preset matches filter text."""
        if not filter_text:
            return True
        
        search_text = filter_text if case_sensitive else filter_text.lower()
        
        # Search in name
        name = self.name if case_sensitive else self.name.lower()
        if search_text in name:
            return True
        
        # Search in description
        if self.description:
            desc = self.description if case_sensitive else self.description.lower()
            if search_text in desc:
                return True
        
        # Search in tags
        for tag in self.tags:
            tag_text = tag if case_sensitive else tag.lower()
            if search_text in tag_text:
                return True
        
        # Search in author
        if self.author:
            author = self.author if case_sensitive else self.author.lower()
            if search_text in author:
                return True
        
        # Search in server names
        for server in self.enabled_servers + self.disabled_servers:
            server_text = server if case_sensitive else server.lower()
            if search_text in server_text:
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.preset_type.value,
            "category": self.category.value,
            "enabled_servers": self.enabled_servers,
            "disabled_servers": self.disabled_servers,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "last_used_date": self.last_used_date,
            "usage_count": self.usage_count,
            "author": self.author,
            "version": self.version,
            "supported_modes": list(self.supported_modes),
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PresetListItem":
        """Create from dictionary representation."""
        item = cls(
            name=data.get("name", ""),
            preset_type=PresetType(data.get("type", "custom")),
            category=PresetCategory(data.get("category", "custom")),
            enabled_servers=data.get("enabled_servers", []),
            disabled_servers=data.get("disabled_servers", []),
            description=data.get("description"),
            icon=data.get("icon"),
            color=data.get("color"),
            tags=data.get("tags", []),
            is_favorite=data.get("is_favorite", False),
            created_date=data.get("created_date"),
            modified_date=data.get("modified_date"),
            last_used_date=data.get("last_used_date"),
            usage_count=data.get("usage_count", 0),
            author=data.get("author"),
            version=data.get("version"),
            supported_modes=set(data.get("supported_modes", ["claude", "gemini", "both"])),
            config=data.get("config", {}),
        )
        
        return item
    
    def copy(self) -> "PresetListItem":
        """Create a copy of this preset item."""
        return PresetListItem(
            name=self.name,
            preset_type=self.preset_type,
            category=self.category,
            enabled_servers=self.enabled_servers.copy(),
            disabled_servers=self.disabled_servers.copy(),
            server_count=self.server_count,
            description=self.description,
            icon=self.icon,
            color=self.color,
            tags=self.tags.copy(),
            is_selected=self.is_selected,
            is_active=self.is_active,
            is_modified=self.is_modified,
            is_favorite=self.is_favorite,
            created_date=self.created_date,
            modified_date=self.modified_date,
            last_used_date=self.last_used_date,
            usage_count=self.usage_count,
            author=self.author,
            version=self.version,
            supported_modes=self.supported_modes.copy(),
            is_valid=self.is_valid,
            validation_errors=self.validation_errors.copy(),
            config=self.config.copy(),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on name and type."""
        if not isinstance(other, PresetListItem):
            return False
        return self.name == other.name and self.preset_type == other.preset_type
    
    def __hash__(self) -> int:
        """Hash based on name and type."""
        return hash((self.name, self.preset_type))
    
    def __str__(self) -> str:
        """String representation."""
        return f"PresetListItem(name='{self.name}', type={self.preset_type.value}, servers={self.server_count})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return self.__str__()