"""Server list item model for MCP Config Manager GUI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ServerStatus(Enum):
    """Server status states."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    LOADING = "loading"
    UNKNOWN = "unknown"


class ServerType(Enum):
    """Server types."""
    MCP = "mcp"
    STDIO = "stdio"
    SSE = "sse"
    CUSTOM = "custom"


@dataclass
class ServerCommand:
    """Server command configuration."""
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ServerCommand":
        """Create from dictionary."""
        return cls(
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
        )


@dataclass
class ServerListItem:
    """Represents a server in the server list."""
    
    # Core properties
    name: str
    status: ServerStatus = ServerStatus.UNKNOWN
    server_type: ServerType = ServerType.MCP
    
    # Command configuration
    command: Optional[ServerCommand] = None
    
    # Display properties
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # State properties
    is_selected: bool = False
    is_expanded: bool = False
    is_modified: bool = False
    is_new: bool = False
    
    # Validation state
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    
    # Metadata
    source_mode: Optional[str] = None  # "claude", "gemini", "both"
    last_modified: Optional[str] = None
    version: Optional[str] = None
    
    # Runtime info
    is_running: bool = False
    pid: Optional[int] = None
    port: Optional[int] = None
    error_message: Optional[str] = None
    
    # Additional configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived properties."""
        if not self.description:
            self.description = f"{self.name} server"
        if not self.icon:
            self.icon = self._get_default_icon()
    
    def _get_default_icon(self) -> str:
        """Get default icon based on server type."""
        icon_map = {
            ServerType.MCP: "server",
            ServerType.STDIO: "terminal",
            ServerType.SSE: "cloud",
            ServerType.CUSTOM: "puzzle",
        }
        return icon_map.get(self.server_type, "server")
    
    def enable(self) -> None:
        """Enable the server."""
        if self.status != ServerStatus.ERROR:
            self.status = ServerStatus.ENABLED
            self.is_modified = True
    
    def disable(self) -> None:
        """Disable the server."""
        self.status = ServerStatus.DISABLED
        self.is_modified = True
        self.is_running = False
        self.pid = None
        self.port = None
    
    def toggle(self) -> None:
        """Toggle server status."""
        if self.status == ServerStatus.ENABLED:
            self.disable()
        elif self.status == ServerStatus.DISABLED:
            self.enable()
    
    def set_error(self, error_message: str) -> None:
        """Set server to error state."""
        self.status = ServerStatus.ERROR
        self.error_message = error_message
        self.is_running = False
        self.pid = None
        self.port = None
    
    def clear_error(self) -> None:
        """Clear error state."""
        if self.status == ServerStatus.ERROR:
            self.status = ServerStatus.DISABLED
            self.error_message = None
    
    def set_loading(self) -> None:
        """Set server to loading state."""
        self.status = ServerStatus.LOADING
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the server."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.is_modified = True
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the server."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.is_modified = True
    
    def has_tag(self, tag: str) -> bool:
        """Check if server has a tag."""
        return tag in self.tags
    
    def validate(self) -> bool:
        """Validate server configuration."""
        self.validation_errors.clear()
        self.validation_warnings.clear()
        self.is_valid = True
        
        # Validate name
        if not self.name:
            self.validation_errors.append("Server name is required")
            self.is_valid = False
        elif len(self.name) < 2:
            self.validation_errors.append("Server name must be at least 2 characters")
            self.is_valid = False
        
        # Validate command
        if self.command:
            if not self.command.command:
                self.validation_errors.append("Server command is required")
                self.is_valid = False
            elif not self._is_valid_command(self.command.command):
                self.validation_warnings.append(f"Command '{self.command.command}' may not be available")
        
        # Validate port if specified
        if self.port is not None:
            if not 1 <= self.port <= 65535:
                self.validation_errors.append(f"Invalid port number: {self.port}")
                self.is_valid = False
        
        return self.is_valid
    
    def _is_valid_command(self, command: str) -> bool:
        """Check if command appears valid."""
        # Basic validation - could be extended
        return bool(command and not command.startswith(" "))
    
    def matches_filter(self, filter_text: str, case_sensitive: bool = False) -> bool:
        """Check if server matches filter text."""
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
        
        # Search in category
        if self.category:
            cat = self.category if case_sensitive else self.category.lower()
            if search_text in cat:
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "type": self.server_type.value,
            "command": self.command.to_dict() if self.command else None,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "tags": self.tags,
            "source_mode": self.source_mode,
            "version": self.version,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ServerListItem":
        """Create from dictionary representation."""
        item = cls(
            name=data.get("name", ""),
            status=ServerStatus(data.get("status", "unknown")),
            server_type=ServerType(data.get("type", "mcp")),
            description=data.get("description"),
            icon=data.get("icon"),
            category=data.get("category"),
            tags=data.get("tags", []),
            source_mode=data.get("source_mode"),
            version=data.get("version"),
            config=data.get("config", {}),
        )
        
        if data.get("command"):
            item.command = ServerCommand.from_dict(data["command"])
        
        return item
    
    def copy(self) -> "ServerListItem":
        """Create a copy of this server item."""
        return ServerListItem(
            name=self.name,
            status=self.status,
            server_type=self.server_type,
            command=ServerCommand(
                command=self.command.command,
                args=self.command.args.copy(),
                env=self.command.env.copy(),
            ) if self.command else None,
            description=self.description,
            icon=self.icon,
            category=self.category,
            tags=self.tags.copy(),
            is_selected=self.is_selected,
            is_expanded=self.is_expanded,
            is_modified=self.is_modified,
            is_new=self.is_new,
            is_valid=self.is_valid,
            validation_errors=self.validation_errors.copy(),
            validation_warnings=self.validation_warnings.copy(),
            source_mode=self.source_mode,
            last_modified=self.last_modified,
            version=self.version,
            is_running=self.is_running,
            pid=self.pid,
            port=self.port,
            error_message=self.error_message,
            config=self.config.copy(),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on name."""
        if not isinstance(other, ServerListItem):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        """Hash based on name."""
        return hash(self.name)
    
    def __str__(self) -> str:
        """String representation."""
        return f"ServerListItem(name='{self.name}', status={self.status.value}, type={self.server_type.value})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return self.__str__()