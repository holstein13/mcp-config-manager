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
    HTTP = "http"
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

    # Per-LLM enablement state
    claude_enabled: bool = False
    gemini_enabled: bool = False
    codex_enabled: bool = False
    
    # Validation state
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    
    # Metadata
    source_mode: Optional[str] = None  # "claude", "gemini", "codex", "all", etc.
    last_modified: Optional[str] = None
    version: Optional[str] = None
    location: Optional[str] = None  # "global" or project path
    is_project_server: bool = False  # True if from project-specific config
    
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
            ServerType.HTTP: "cloud",
            ServerType.CUSTOM: "puzzle",
        }
        return icon_map.get(self.server_type, "server")
    
    def enable(self, client: Optional[str] = None) -> None:
        """Enable the server for a specific client or all."""
        if client == "claude":
            self.claude_enabled = True
        elif client == "gemini":
            self.gemini_enabled = True
        elif client == "codex":
            self.codex_enabled = True
        elif client is None:
            # Enable for all if no client specified
            self.claude_enabled = True
            self.gemini_enabled = True
            self.codex_enabled = True

        # Update overall status based on enablement
        if self.claude_enabled or self.gemini_enabled or self.codex_enabled:
            if self.status != ServerStatus.ERROR:
                self.status = ServerStatus.ENABLED
        self.is_modified = True

    def disable(self, client: Optional[str] = None) -> None:
        """Disable the server for a specific client or all."""
        if client == "claude":
            self.claude_enabled = False
        elif client == "gemini":
            self.gemini_enabled = False
        elif client == "codex":
            self.codex_enabled = False
        elif client is None:
            # Disable for all if no client specified
            self.claude_enabled = False
            self.gemini_enabled = False
            self.codex_enabled = False

        # Update overall status based on enablement
        if not self.claude_enabled and not self.gemini_enabled and not self.codex_enabled:
            self.status = ServerStatus.DISABLED
            self.is_running = False
            self.pid = None
            self.port = None
        self.is_modified = True

    def toggle(self, client: Optional[str] = None) -> None:
        """Toggle server status for a specific client."""
        if client == "claude":
            if self.claude_enabled:
                self.disable("claude")
            else:
                self.enable("claude")
        elif client == "gemini":
            if self.gemini_enabled:
                self.disable("gemini")
            else:
                self.enable("gemini")
        elif client == "codex":
            if self.codex_enabled:
                self.disable("codex")
            else:
                self.enable("codex")
        elif client is None:
            # Toggle all when no client specified
            if self.claude_enabled or self.gemini_enabled or self.codex_enabled:
                self.disable()
            else:
                self.enable()
    
    def get_enabled_state(self, client: str) -> bool:
        """Get the enabled state for a specific client."""
        if client == "claude":
            return self.claude_enabled
        elif client == "gemini":
            return self.gemini_enabled
        elif client == "codex":
            return self.codex_enabled
        else:
            return False

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
        
        # Validate command based on server type
        # HTTP and SSE servers don't require a command (they use URL)
        if self.server_type in (ServerType.STDIO, ServerType.MCP):
            if self.command:
                if not self.command.command:
                    self.validation_errors.append("Server command is required")
                    self.is_valid = False
                elif not self._is_valid_command(self.command.command):
                    self.validation_warnings.append(f"Command '{self.command.command}' may not be available")
        elif self.server_type in (ServerType.HTTP, ServerType.SSE):
            # For HTTP/SSE servers, validate URL if present in config
            if "url" not in self.config or not self.config.get("url"):
                self.validation_errors.append(f"{self.server_type.value.upper()} server requires a URL")
                self.is_valid = False
            # Command is optional for HTTP/SSE
            if self.command and self.command.command:
                if not self._is_valid_command(self.command.command):
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
            "claude_enabled": self.claude_enabled,
            "gemini_enabled": self.gemini_enabled,
            "codex_enabled": self.codex_enabled,
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
            claude_enabled=data.get("claude_enabled", False),
            gemini_enabled=data.get("gemini_enabled", False),
            codex_enabled=data.get("codex_enabled", False),
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
            claude_enabled=self.claude_enabled,
            gemini_enabled=self.gemini_enabled,
            codex_enabled=self.codex_enabled,
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