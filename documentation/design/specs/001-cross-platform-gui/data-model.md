# Data Model: Cross-Platform GUI for MCP Configuration Management

**Date**: 2025-01-08  
**Feature**: Cross-Platform GUI

## Overview

This document defines the data structures and models for the GUI application, building upon the existing core library models while adding GUI-specific state management.

## Core Entities (Existing - from Library)

### ServerConfiguration
```python
class ServerConfiguration:
    """Represents an MCP server configuration"""
    name: str                    # Unique server identifier
    command: str                 # Executable command
    args: List[str]             # Command arguments
    env: Dict[str, str]         # Environment variables
    enabled: bool               # Current enable/disable state
    metadata: Dict[str, Any]    # Additional server metadata
```

### Preset
```python
class Preset:
    """Saved configuration snapshot"""
    name: str                    # Preset identifier
    description: str            # User-friendly description
    servers: List[ServerConfiguration]  # Server states
    created_at: datetime        # Creation timestamp
    updated_at: datetime        # Last modification
    is_builtin: bool           # System vs user preset
```

### ConfigurationFile
```python
class ConfigurationFile:
    """Represents a configuration file (Claude/Gemini)"""
    path: Path                  # File location
    type: Literal["claude", "gemini"]  # Config type
    servers: Dict[str, ServerConfiguration]  # Server configs
    last_modified: datetime     # File modification time
    is_valid: bool             # Validation status
```

## GUI-Specific Models

### ApplicationState
```python
class ApplicationState:
    """Central application state management"""
    current_mode: ApplicationMode  # Current operation mode
    has_unsaved_changes: bool      # Dirty flag
    active_view: ViewType          # Current UI view
    selected_servers: Set[str]     # Multi-selection
    search_filter: str             # Active search term
    sort_order: SortOrder          # List sorting
    last_backup: Optional[Path]    # Recent backup location
```

### ApplicationMode
```python
class ApplicationMode(Enum):
    """Operating mode enumeration"""
    CLAUDE_ONLY = "claude"
    GEMINI_ONLY = "gemini"  
    BOTH_SYNCED = "both"
```

### ViewType
```python
class ViewType(Enum):
    """Active view enumeration"""
    SERVER_LIST = "servers"
    PRESET_MANAGER = "presets"
    SETTINGS = "settings"
    BACKUP_RESTORE = "backup"
```

### UIConfiguration
```python
class UIConfiguration:
    """User interface preferences"""
    theme: str = "system"           # Theme selection
    window_geometry: Dict[str, int] # Window size/position
    splitter_sizes: List[int]       # Panel sizes
    show_disabled_servers: bool = True
    show_status_bar: bool = True
    confirm_on_exit: bool = True
    auto_save: bool = False
    auto_backup_count: int = 10
    shortcuts: Dict[str, str]       # Keyboard shortcuts
```

### ServerListItem
```python
class ServerListItem:
    """View model for server list display"""
    server: ServerConfiguration    # Underlying server
    is_selected: bool              # Selection state
    is_modified: bool              # Changed from saved
    has_error: bool                # Validation error
    error_message: Optional[str]   # Error details
    icon: Optional[str]            # Display icon
```

### PresetListItem
```python
class PresetListItem:
    """View model for preset list display"""
    preset: Preset                 # Underlying preset
    is_active: bool               # Currently loaded
    server_count: int             # Number of servers
    can_delete: bool              # User preset flag
    can_edit: bool                # Modification allowed
```

### BackupInfo
```python
class BackupInfo:
    """Backup file metadata"""
    path: Path                     # Backup file location
    timestamp: datetime            # Creation time
    size: int                     # File size in bytes
    config_type: str              # Claude/Gemini/Both
    server_count: int             # Servers in backup
    is_restorable: bool          # Can be restored
```

## State Transitions

### Server State Machine
```
States: ENABLED → DISABLED → ENABLED
Triggers:
- User toggle action
- Preset application
- Bulk enable/disable
- Mode change (sync)
```

### Application State Machine
```
States: LOADING → READY → MODIFIED → SAVING → READY
Triggers:
- App startup (LOADING → READY)
- Any change (READY → MODIFIED)  
- Save action (MODIFIED → SAVING → READY)
- Discard changes (MODIFIED → READY)
```

### Mode Transition Rules
```
CLAUDE_ONLY ↔ BOTH_SYNCED ↔ GEMINI_ONLY

Transitions:
- Mode change prompts for unsaved changes
- Sync operation on BOTH mode activation
- Independent operation in single modes
```

## Validation Rules

### ServerConfiguration
- `name`: Required, unique within config
- `command`: Required, executable path
- `args`: Optional, valid JSON array
- `env`: Optional, valid key-value pairs

### Preset
- `name`: Required, unique, alphanumeric + spaces
- `description`: Optional, max 500 characters
- `servers`: At least one server configuration

### UIConfiguration  
- `window_geometry`: Valid screen coordinates
- `auto_backup_count`: Range 1-100
- `shortcuts`: No conflicts, valid key combinations

## Relationships

### Entity Relationships
```
ApplicationState
    ├── ConfigurationFile (1:2) [Claude, Gemini]
    ├── UIConfiguration (1:1)
    └── PresetManager (1:1)
        └── Preset (1:N)

ServerConfiguration (N:M) Preset
    Via: preset_servers junction

BackupInfo (1:1) ConfigurationFile
    Via: restoration relationship
```

### Data Flow
```
User Action → Controller → Model Update → State Change → View Update
                ↓
            Validation
                ↓
            Core Library
                ↓
            File System
```

## Persistence

### Storage Locations
```
~/.mcp_config_manager/
├── ui_config.json          # UI preferences
├── state.json              # Application state
└── backups/                # Automatic backups
    └── *.backup.json

~/.claude.json              # Claude configuration
~/.gemini/settings.json     # Gemini configuration  
~/.mcp_presets.json        # Shared presets
```

### Serialization Format
All models serialize to JSON with:
- ISO 8601 timestamps
- UTF-8 encoding
- Pretty printing for readability
- Schema version header

## Event Model

### Core Events
```python
class ConfigurationEvent:
    SERVER_ADDED = "server.added"
    SERVER_REMOVED = "server.removed"
    SERVER_TOGGLED = "server.toggled"
    SERVER_MODIFIED = "server.modified"
    
class PresetEvent:
    PRESET_CREATED = "preset.created"
    PRESET_LOADED = "preset.loaded"
    PRESET_DELETED = "preset.deleted"
    
class ApplicationEvent:
    MODE_CHANGED = "app.mode_changed"
    STATE_SAVED = "app.state_saved"
    BACKUP_CREATED = "app.backup_created"
    ERROR_OCCURRED = "app.error"
```

## Performance Considerations

### Optimization Points
- Lazy load preset contents (on-demand)
- Virtual scrolling for >100 servers
- Debounce search filtering (300ms)
- Batch UI updates for bulk operations
- Cache validation results (5 minute TTL)

### Memory Management
- Maximum 10 backups in memory
- Prune old backups on startup
- Release preset data when not active
- Limit undo history to 50 operations

## Error Handling

### Error Categories
```python
class ErrorType(Enum):
    VALIDATION_ERROR = "validation"    # Invalid data
    FILE_ERROR = "file"                # I/O issues
    PARSE_ERROR = "parse"              # JSON errors
    PERMISSION_ERROR = "permission"    # Access denied
    SYNC_ERROR = "sync"                # Mode sync failed
    NETWORK_ERROR = "network"          # Connection issues
```

### Recovery Strategies
- Validation: Show inline errors, prevent save
- File: Offer backup restoration
- Parse: Load defaults, warn user
- Permission: Request elevation or alternate path
- Sync: Retry with exponential backoff
- Network: Offline mode with queued changes

## Threading Model

### Main Thread (UI)
- All widget updates
- User input handling
- Event dispatching

### Worker Threads
- File I/O operations
- Backup creation
- Validation checks
- Network requests (future)

### Thread Safety
- Queue-based communication
- Immutable data transfer
- Signal/slot mechanism (PyQt6)
- Lock-free state updates

## Migration Path

### From CLI to GUI
1. Import existing configurations
2. Preserve all server settings
3. Convert disabled_servers.json
4. Maintain backup compatibility

### Version Upgrades
- Schema version in all files
- Automatic migration on load
- Backup before migration
- Rollback capability