# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Config Manager is a cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems. Built from the battle-tested `mcp_toggle.py` script, now with modular architecture.

## Current Project: MCP Config Manager

### Active Specification
- **Spec**: `specs/001-cross-platform-gui/spec.md`
- **Plan**: `specs/001-cross-platform-gui/plan.md` 
- **Tasks**: `specs/001-cross-platform-gui/tasks.md`

### Implementation Status
- Current phase: GUI Development Complete (Phase 2 & 3.4)
- Active branch: master
- Next phase: Polish & Platform Testing (Phase 3.5)

## Current Status

### ✅ Phase 1 Complete: Core Functionality
- Interactive CLI interface (fully functional)
- Multi-client support (Claude + Gemini with syncing)
- Server enable/disable with separate storage
- Automatic configuration backups
- Preset management system
- JSON server addition by paste
- Command line interface for automation
- Configuration validation
- Cross-platform file handling

### ✅ Phase 2 Complete: GUI Development

#### ✅ Phase 3.1 Complete: Project Setup
- GUI module structure created at `src/gui/`
- PyQt6 dependencies configured with tkinter fallback
- pytest-qt testing framework configured
- Resource directories established
- GUI entry point configured in `__main__.py`

#### ✅ Phase 3.2 Complete: TDD Contract Tests (25/25 tasks)
**All tests written and intentionally failing with `ModuleNotFoundError`:**
- ✅ 14 Contract tests for GUI-Library integration (config, servers, presets, backups, validation)
- ✅ 5 Event contract tests (config, server, preset, app, UI events)
- ✅ 5 Integration tests covering complete user workflows:
  - `test_toggle_workflow.py` - Server enable/disable operations
  - `test_preset_workflow.py` - Preset management (list, apply, save, delete)
  - `test_add_server_workflow.py` - Adding servers via JSON paste
  - `test_mode_switch_workflow.py` - Mode switching and synchronization
  - `test_backup_workflow.py` - Backup creation and restoration

**Key Decisions Made:**
1. **Contract-First Development**: All 25 test files define exact API before implementation
2. **Event-Driven Architecture**: Tests expect loosely coupled event system
3. **Request/Response Pattern**: All operations follow `{success: bool, data/error: {...}}`
4. **Mode Abstraction**: GUI unaware of Claude/Gemini specifics, uses unified interface
5. **Comprehensive Workflows**: Integration tests cover real user stories end-to-end

#### ✅ Phase 3.3 Complete: Core Implementation

##### ✅ Data Models Complete (T030-T034)
All five core data models have been implemented in `src/gui/models/`:

1. **ApplicationState** (`app_state.py`) - Central state management
   - Tracks mode (Claude/Gemini/Both), active/disabled servers, presets
   - Manages UI state: current view, selection, search filters
   - Handles unsaved changes, validation errors, operation states
   - Methods for server toggling, preset application, state reset

2. **UIConfiguration** (`ui_config.py`) - UI preferences and settings
   - Theme system (Light/Dark/System) with custom colors
   - Window geometry persistence and layout preferences
   - Keyboard shortcuts configuration (fully customizable)
   - Animation settings, notification preferences, search options
   - Validation and serialization support

3. **ServerListItem** (`server_list_item.py`) - Server representation
   - Status tracking (Enabled/Disabled/Error/Loading)
   - Command configuration with args and environment variables
   - Validation with error/warning messages
   - Tag and category support for organization
   - Filter matching for search functionality

4. **PresetListItem** (`preset_list_item.py`) - Preset configuration
   - Types: Builtin/Custom/Imported/Recent
   - Separate enabled/disabled server lists
   - Mode support (Claude/Gemini/Both) per preset
   - Usage tracking and favorites
   - Full CRUD operations for server management

5. **BackupInfo** (`backup_info.py`) - Backup file management
   - Backup types: Manual/Auto/Scheduled/Pre-change
   - File validation and integrity checking
   - Metadata tracking (server counts, versions)
   - Age calculation and human-readable formatting
   - Restore history tracking

##### ✅ Main Window & Core Widgets Complete (T035-T039)
Successfully implemented the main window and essential UI components:

1. **MainWindow** (`main_window.py`) - Primary application window
   - Complete menu system (File, Edit, Presets, Tools, Help)
   - Toolbar with quick access buttons for common operations
   - Status bar with save indicator and status messages
   - Window state persistence (geometry, maximized state)
   - Unsaved changes tracking with visual indicators
   - Dual framework support (PyQt6 and tkinter)

2. **ServerListWidget** (`widgets/server_list.py`) - Server management UI
   - Tree view with columns: Enabled, Server, Status, Mode
   - Individual server toggle checkboxes
   - Enable All/Disable All bulk operations
   - Context menu for server operations
   - Server count status display
   - Search/filter capability foundation
   - Visual status indicators with color coding

3. **ModeSelectorWidget** (`widgets/mode_selector.py`) - Client mode selection
   - Radio buttons for Claude Only/Gemini Only/Both modes
   - Compact combo box alternative for space-constrained layouts
   - Status indicator with mode-specific color coding
   - Callback system for mode change notifications
   - Enable/disable support for configuration locking

##### ✅ Dialogs Complete (T040-T044)
Successfully implemented all dialog components in `src/gui/dialogs/`:

1. **AddServerDialog** (`add_server_dialog.py`) - JSON server addition
   - Live JSON validation with syntax highlighting
   - Placeholder text showing expected format
   - Error messages for invalid configurations
   - Support for environment variables and arguments

2. **PresetManagerDialog** (`preset_manager_dialog.py`) - Preset management
   - List view with built-in/custom preset distinction
   - Apply, save, delete operations with confirmations
   - Favorite marking and server count display
   - Details panel showing preset configuration

3. **SettingsDialog** (`settings_dialog.py`) - Application preferences
   - Tabbed interface: General, Appearance, Behavior, Advanced
   - Theme selection (Light/Dark/System)
   - Backup settings and auto-save configuration
   - Validation and logging preferences

4. **BackupRestoreDialog** (`backup_restore_dialog.py`) - Backup operations
   - Table view with timestamp, mode, size information
   - Create, restore, delete individual backups
   - Bulk delete old backups functionality
   - Automatic refresh and status updates

5. **ErrorDialog** (`error_dialog.py`) - Error display
   - Icon-based severity indicators (error/warning/info)
   - Detailed error information with stack traces
   - Copy to clipboard functionality
   - Issue reporting integration

##### ✅ Controllers Complete (T045-T048)
Successfully implemented all controller components in `src/gui/controllers/`:

1. **ConfigController** (`config_controller.py`) - Configuration management
   - Load/save operations with backup creation
   - Mode switching (Claude/Gemini/Both)
   - Configuration validation
   - Path management for all config files

2. **ServerController** (`server_controller.py`) - Server operations
   - Toggle, add, remove server functionality
   - Bulk operations (enable all/disable all)
   - Server validation with error reporting
   - Mode-aware server management

3. **PresetController** (`preset_controller.py`) - Preset management
   - Load, save, delete preset operations
   - Favorite toggle functionality
   - Built-in preset protection
   - Detailed preset information retrieval

4. **BackupController** (`backup_controller.py`) - Backup operations
   - Create, restore, delete backups
   - Cleanup old backups by age or count
   - Backup information and metadata
   - Server count tracking in backups

##### ✅ Event System & Handlers Complete (T049-T052)
Successfully implemented the complete event system and UI-controller integration:

1. **EventDispatcher** (`events/dispatcher.py`) - Central event management
   - Support for both synchronous and asynchronous event handlers
   - Comprehensive event types covering all application operations
   - Event history tracking with configurable limits
   - Pause/resume functionality for batch operations
   - Global dispatcher instance for application-wide communication

2. **StateManager** (`events/state_manager.py`) - Centralized state management
   - Automatic change detection and notification
   - Full undo/redo support with stack management
   - Batch mode for grouped state changes
   - Property suspension for preventing circular updates
   - State history tracking for debugging

3. **UI-Controller Integration** (`main_window.py`) - Complete event wiring
   - All controllers connected to UI components
   - Widget callbacks properly routed to controllers
   - Event handlers registered for all dispatcher events
   - Proper event emission for all user actions
   - Consistent error handling and user feedback

4. **Keyboard Shortcuts** (`main_window.py`) - Professional keyboard navigation
   - Comprehensive shortcut system for both PyQt6 and tkinter
   - File operations, server management, mode switching
   - Tool access, edit operations, help system
   - Mode-specific shortcuts (Ctrl+1/2/3)
   - Undo/redo support (Ctrl+Z/Y)

#### ✅ Phase 3.4 Complete: Integration (T053-T066)

##### ✅ Library Integration Complete (T053-T056)
- **T053-T055**: Controllers properly connected to ConfigManager, ServerManager, and PresetManager
- **T056**: Implemented `file_watcher.py` with FileWatcher and ConfigFileWatcher classes
  - Monitors config files for external changes
  - Thread-safe file monitoring with configurable check intervals
  - Automatic reload on file changes

##### ✅ UI Features Complete (T057-T060)
- **T057**: Implemented `search_bar.py` with real-time search and filtering
  - Dual framework support (PyQt6/tkinter)
  - Debounced search input (300ms delay)
  - Filter types: All, Enabled, Disabled, Error, Modified
- **T058**: Enhanced `server_list.py` with multi-selection support
  - Extended selection mode for Qt
  - Methods for batch operations on selected servers
- **T059**: Added drag-drop support for server reordering
  - QTreeWidget.DragDropMode.InternalMove for Qt implementation
- **T060**: Context menus already implemented in server list
  - Right-click operations: Enable/Disable, Remove

##### ✅ Threading & Performance Complete (T061-T063)
- **T061**: Implemented `worker_thread.py` for background operations
  - BackgroundTask class with status tracking and cancellation
  - WorkerThread with task queue and completion callbacks
  - FileOperationWorker for async config operations
- **T062**: Created `progress_widget.py` for operation feedback
  - ProgressWidget and ProgressDialog for both frameworks
  - Indeterminate mode for unknown duration operations
  - Cancel button support with event callbacks
- **T063**: Enhanced `state_manager.py` with thread safety
  - Added threading.RLock for all state operations
  - Thread-safe batch operations
  - Protected undo/redo stacks

##### ✅ tkinter Fallback Complete (T064-T066)
- **T064**: Full tkinter MainWindow implementation
  - Complete menu system with keyboard shortcuts
  - Toolbar for quick access operations
  - Status bar with save indicators
- **T065**: tkinter-specific server list enhancements
  - TkinterServerList with search and filter
  - TkinterServerListAdvanced with import/export functionality
- **T066**: tkinter dialog adapters for consistency
  - TkinterDialogAdapter base class
  - AddServerDialogTk with JSON validation
  - PresetManagerDialogTk with full preset management

### 🚀 Next Phase: Polish (Phase 3.5)
- Platform-specific testing (Windows, macOS, Linux)
- Performance optimization for large server lists
- Packaging with PyInstaller
- Documentation updates

## Development Commands

```bash
# Install for development
pip install -e .

# Run tests
pytest tests/ -v
pytest tests/test_config_manager.py::TestConfigManager::test_specific_method

# Run GUI contract tests (should fail before implementation)
pytest tests/test_gui/contract/ -v
pytest tests/test_gui/events/ -v
pytest tests/test_gui/integration/ -v

# Run specific contract test suite
pytest tests/test_gui/contract/test_config_load.py -v
pytest tests/test_gui/events/test_server_events.py -v

# Code quality
black src/ tests/           # Format code
flake8 src/ tests/          # Lint code
isort src/ tests/           # Sort imports
mypy src/                   # Type checking

# Main commands
mcp-config-manager interactive               # Launch interactive mode (primary interface)
mcp-config-manager gui                       # Launch GUI application (new in Phase 2)
mcp-config-manager status                    # Show current server status
mcp-config-manager enable <server>           # Enable specific server
mcp-config-manager disable <server>          # Disable specific server
mcp-config-manager preset minimal            # Apply minimal preset
mcp-config-manager validate ~/.claude.json   # Validate config file

# GUI-specific commands
mcp-config-manager gui --framework=tkinter   # Force tkinter backend
mcp-config-manager gui --theme=dark          # Launch with dark theme
mcp-config-manager gui --mode=claude         # Start in Claude-only mode
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **ConfigManager** (`core/config_manager.py`): Central orchestrator handling loading, saving, and syncing between Claude and Gemini configs. Primary API for both CLI and GUI.
- **ServerManager** (`core/server_manager.py`): Manages server enable/disable operations with separate storage for disabled servers.
- **PresetManager** (`core/presets.py`): Handles preset configurations in `~/.mcp_presets.json`.
- **Parsers** (`parsers/`): Claude and Gemini specific config file handling with validation.
- **GUI** (`gui/`): PyQt6/tkinter GUI components including main window, dialogs, and widgets.
- **Controllers** (`gui/controllers/`): GUI-library integration layer handling events and state.

### File Locations
- Claude config: `~/.claude.json`
- Gemini config: `~/.gemini/settings.json`
- Presets: `~/.mcp_presets.json`
- Disabled servers: `./disabled_servers.json` (in project directory)
- Backups: `~/.claude.json.backup.YYYYMMDD_HHMMSS`

## Critical Implementation Notes

1. **Interactive Mode is the Gold Standard** - Test all changes against `mcp-config-manager interactive` as it contains the complete original functionality users rely on.

2. **Mode Support** - All operations must support mode parameter: 'claude', 'gemini', or 'both' (synced).

3. **Error Handling** - Always create backups before changes, handle JSON parsing gracefully, never lose user configurations.

4. **Backwards Compatibility** - Original `mcp_toggle.py` users must be able to migrate seamlessly.

## Current Implementation Details

### Interactive Mode Commands
- `[1-N]` - Disable active server by number
- `[d1-N]` - Enable disabled server by number
- `[a]` - Enable all servers
- `[n]` - Disable all servers
- `[m]` - Minimal preset (context7 + browsermcp)
- `[w]` - Web dev preset (+ playwright)
- `[+]` - Add new server (paste JSON)
- `[p]` - Preset management
- `[c]` - Change CLI mode
- `[s]` - Save and exit
- `[q]` - Quit without saving

### CLI Commands
- `interactive` - Launch full interactive mode
- `status` - Show current server status
- `enable/disable <server>` - Toggle specific servers
- `enable-all/disable-all` - Bulk operations
- `preset <mode>` - Apply preset modes
- `validate <file>` - Validate config files

## GUI Development (Phase 2)

### Framework Architecture Decisions
- **Primary**: PyQt6 for professional native appearance
- **Fallback**: tkinter for environments without Qt
- **Pattern**: Controller-based architecture with event system
- **Testing**: Contract-first TDD approach

### Contract Test Structure
The GUI implementation follows a strict contract-based architecture:

```
tests/test_gui/
├── contract/           # API contracts between GUI and library
│   ├── test_config_*.py    # Configuration operations
│   ├── test_servers_*.py   # Server management
│   ├── test_presets_*.py   # Preset operations
│   └── test_backups_*.py   # Backup/restore operations
├── events/            # Event system contracts
│   ├── test_config_events.py   # Configuration events
│   ├── test_server_events.py   # Server state events
│   ├── test_preset_events.py   # Preset events
│   ├── test_app_events.py      # Application lifecycle
│   └── test_ui_events.py       # UI interactions
└── integration/       # End-to-end workflows
    ├── test_toggle_workflow.py     # Server enable/disable operations
    ├── test_preset_workflow.py     # Preset management workflows
    ├── test_add_server_workflow.py # Adding servers via JSON
    ├── test_mode_switch_workflow.py # Mode switching and sync
    └── test_backup_workflow.py     # Backup and restore operations
```

### Key Implementation Decisions

1. **Contract-First Development**: All tests written before implementation, defining exact API
2. **Event-Driven Architecture**: Loosely coupled components communicate via events
3. **Mode Abstraction**: GUI unaware of Claude/Gemini specifics, uses unified interface
4. **Request/Response Pattern**: All operations follow consistent request validation → execution → response format
5. **Error Handling**: Every operation returns `{success: bool, data/error: {...}}` structure
6. **Async Support**: Event system supports both sync and async handlers
7. **Rich Data Models**: Models include validation, filtering, state management, and serialization
8. **Type Safety**: Extensive use of Enums and type hints for reliability
9. **Separation of Concerns**: Each model handles its own validation and business logic
10. **Human-Readable Formatting**: Models provide user-friendly string representations (age, size, etc.)

### GUI Component Requirements
- Server list with enable/disable toggles
- Mode selection (Claude/Gemini/Both)
- Preset management interface
- JSON paste dialog for adding servers
- Backup/restore functionality
- Real-time validation feedback

### Integration Test Coverage
Each integration test file validates complete user workflows:

1. **test_toggle_workflow.py**: Server management operations
   - Enable/disable individual servers
   - Bulk operations (enable all/disable all)
   - State persistence and UI updates

2. **test_preset_workflow.py**: Preset management
   - List available presets
   - Apply presets to configuration
   - Save custom presets
   - Delete custom presets
   - Mode synchronization

3. **test_add_server_workflow.py**: Server addition
   - JSON validation
   - Duplicate detection
   - Environment variable handling
   - Multi-mode support

4. **test_mode_switch_workflow.py**: Mode management
   - Switch between Claude/Gemini/Both
   - Configuration synchronization
   - Unsaved changes warnings
   - Mode-specific operations

5. **test_backup_workflow.py**: Backup operations
   - Create and restore backups
   - Automatic backup on save
   - Retention limits
   - Selective restoration
   - Metadata preservation

## Recent Implementation Progress (2025-01-09)

### Latest Session: Phase 3.4 Integration Complete (T053-T066)
Successfully implemented all integration tasks, completing the core GUI functionality:

#### Key Accomplishments:
1. **Library Integration** - Controllers properly connected to core managers (already in place)
2. **Advanced UI Features** - Search, filtering, multi-selection, drag-drop all functional
3. **Background Operations** - Thread-safe file operations with progress tracking
4. **Complete tkinter Support** - Full fallback implementation ensuring universal compatibility

#### Architecture Decisions from This Session:

1. **File Watching Strategy**
   - Separate FileWatcher base class for reusability
   - ConfigFileWatcher specialization for MCP configs
   - Thread-based monitoring with configurable intervals
   - Callback-based change notifications

2. **Search/Filter Implementation**
   - Debounced search to reduce UI updates (300ms delay)
   - Consistent filtering logic across frameworks
   - ServerFilter helper for centralized filter logic
   - Real-time updates without full list rebuilds

3. **Threading Architecture**
   - Task-based approach with BackgroundTask objects
   - Cancellation tokens for graceful shutdown
   - Progress tracking built into task system
   - Separate FileOperationWorker for config operations

4. **tkinter Parity Strategy**
   - Wrapper approach maintaining compatibility
   - Feature parity where possible
   - Graceful degradation for unsupported features
   - Consistent API across both frameworks

#### Key Insights:

1. **Controller Connection Efficiency**
   - Controllers were already properly connected to managers
   - Good separation of concerns maintained throughout
   - Event system provides clean integration points

2. **Thread Safety Importance**
   - RLock usage prevents deadlocks in reentrant scenarios
   - Batch operations benefit from lock optimization
   - State consistency maintained across threads

3. **Framework Abstraction Success**
   - Dual framework support working seamlessly
   - Conditional imports with USING_QT flag effective
   - Users get native experience regardless of framework

4. **Progress Feedback Value**
   - Progress indicators crucial for user confidence
   - Indeterminate mode useful for unknown durations
   - Cancel support prevents user frustration

#### Next Steps:
- **Phase 3.5**: Polish phase focusing on platform testing and optimization
- **Performance**: Virtual scrolling for 100+ servers
- **Packaging**: PyInstaller configuration for distribution
- **Documentation**: Update user guides with GUI instructions

#### No Current Blockers
- All core functionality implemented
- Both frameworks fully functional
- Ready for platform testing and optimization

### Previous Session: Event System & Handlers (T049-T052)
Successfully implemented the complete event system, establishing robust communication between all GUI components:

#### Key Accomplishments:
1. **Event Dispatcher System** - Central hub for all application events with sync/async support
2. **State Management** - Centralized state with automatic change detection and undo/redo
3. **UI-Controller Integration** - All controllers properly wired to UI components
4. **Keyboard Shortcuts** - Professional keyboard navigation throughout the application

#### Architecture Decisions from This Session:

1. **Event-Driven Communication**
   - Loose coupling between components via dispatcher
   - Support for both synchronous and asynchronous handlers
   - Event history for debugging and monitoring
   - Batch mode for grouped operations

2. **State Management Pattern**
   - Single source of truth with ApplicationState
   - Automatic change detection and notification
   - Full undo/redo support with stack management
   - Property suspension to prevent circular updates

3. **Keyboard Navigation Strategy**
   - Comprehensive shortcuts matching professional applications
   - Consistent between PyQt6 and tkinter implementations
   - Mode switching via Ctrl+1/2/3 for quick access
   - Standard edit operations (Ctrl+Z/Y) for familiarity

4. **Error Handling Consistency**
   - All controller operations return {success, data/error} structure
   - Events emitted for both success and error cases
   - User feedback via status messages and dialogs
   - Proper logging at all levels

#### Key Insights:

1. **Event System Benefits**
   - Components remain decoupled and testable
   - Easy to add new features without modifying existing code
   - Clear flow of information through the application
   - Debugging simplified with event history

2. **State Management Importance**
   - Undo/redo greatly improves user experience
   - Centralized state prevents inconsistencies
   - Batch operations reduce event noise
   - Change tracking enables smart saving

3. **Keyboard Shortcut Value**
   - Power users expect keyboard navigation
   - Consistency with standard shortcuts reduces learning curve
   - Mode switching shortcuts (Ctrl+1/2/3) unique and memorable
   - Framework parity ensures consistent experience

#### Next Steps:
- **Immediate**: Library integration (T053-T056) to connect controllers with ConfigManager
- **Then**: Search and filtering implementation (T057-T058)
- **Finally**: Threading and performance optimization (T059-T063)

#### Potential Blockers:
- None identified - architecture is solid and extensible
- Event system provides clean integration points
- Controllers ready for ConfigManager connection
- All major architectural decisions validated

### Previous Session: Dialog and Controller Implementation (T040-T048)
Successfully completed all dialog and controller components, establishing the complete GUI-Library bridge:

#### Key Accomplishments:
1. **All 5 Dialogs Implemented** - Complete user interaction layer with dual framework support
2. **All 4 Controllers Implemented** - Full business logic bridge between GUI and core library
3. **Consistent Architecture** - Request/response pattern across all controllers
4. **Event System Ready** - Callback registration in place for all major operations

#### Architecture Decisions from This Session:

1. **Dual Framework Consistency**
   - Every dialog works identically in PyQt6 and tkinter
   - Conditional imports with USING_QT flag maintained throughout
   - Visual parity achieved despite framework limitations

2. **Controller Pattern Success**
   - Clean separation between UI (dialogs) and logic (controllers)
   - Controllers directly integrate with existing ConfigManager
   - No GUI framework dependencies in controllers

3. **Event-Driven Design Validated**
   - Callback registration pattern works well for loose coupling
   - Multiple callbacks per event supported
   - Easy to extend without modifying existing code

4. **Error Handling Strategy**
   - Consistent `{success: bool, data/error: {...}}` pattern
   - Comprehensive try-catch blocks with logging
   - User-friendly error messages with technical details

#### Key Insights:

1. **tkinter Limitations Addressed**
   - Tree view checkboxes simulated with text symbols (✓/✗)
   - Tab interfaces work well as notebook widgets
   - Color theming more limited but acceptable

2. **Validation Importance**
   - JSON validation in AddServerDialog prevents invalid configs
   - Built-in preset protection in PresetController
   - Configuration validation before save operations

3. **User Experience Considerations**
   - Live validation provides immediate feedback
   - Confirmation dialogs for destructive operations
   - Status messages and progress indicators planned

#### Next Steps:
- **Immediate**: Implement event dispatcher system (T049)
- **Integration**: Connect controllers to main window (T050)
- **Polish**: Add keyboard shortcuts and state management (T051-T052)
- **Testing**: Update contract tests to validate controller implementations

#### Potential Blockers:
- None identified - architecture is solid and extensible
- Controllers ready for integration with existing ConfigManager
- Event system design clear from callback patterns

### Previous Session Accomplishments (T035-T039)
Successfully completed tasks T035-T039, implementing the main window and core UI widgets:

#### Key Components Delivered:
1. **MainWindow** - Full-featured application window with menus, toolbar, and status bar
2. **ServerListWidget** - Interactive server list with toggle functionality
3. **ModeSelectorWidget** - Client mode selection with visual feedback

#### Implementation Decisions & Insights:

1. **Dual Framework Strategy Working Well**
   - PyQt6 as primary for professional appearance
   - tkinter fallback ensures universal compatibility
   - Conditional imports with USING_QT flag pattern proved effective

2. **Status Management Architecture**
   - Status bar with save indicator provides clear feedback
   - Window title updates with asterisk for unsaved changes
   - Temporary status messages with timeout support

3. **Widget Communication Pattern**
   - Qt signals for PyQt6 (pyqtSignal)
   - Callback lists for tkinter compatibility
   - Both patterns coexist cleanly without interference

4. **UI State Persistence**
   - Window geometry saved/restored via UIConfiguration model
   - Maximized state tracked for Qt
   - Settings preserved between sessions

5. **Server List Design**
   - Tree view provides clear information hierarchy
   - Checkboxes for immediate toggle action
   - Context menus for additional operations
   - Visual status indicators with color coding

### Next Steps & Considerations:

1. **Immediate Next Tasks (T040-T044)**:
   - Dialog implementations will need consistent styling
   - Modal vs non-modal dialog decisions pending
   - JSON validation for Add Server dialog critical

2. **Controller Integration (T045-T048)**:
   - Bridge between GUI and existing ConfigManager
   - Event handling will connect UI to business logic
   - Need to maintain separation of concerns

3. **Potential Challenges Identified**:
   - tkinter tree view doesn't support native checkboxes (using text symbols as workaround)
   - Color styling more limited in tkinter than Qt
   - Need to ensure consistent behavior across frameworks

4. **Performance Considerations**:
   - Server list may need virtual scrolling for 100+ servers (T070)
   - Search/filter implementation will need debouncing (T071)
   - Consider lazy loading for large configurations

### Code Quality Notes:
- Maintained consistent pattern across all widgets
- Proper separation between Qt and tkinter code paths
- Extensive use of type hints for clarity
- Docstrings on all public methods

### Testing Implications:
- Contract tests (T006-T029) will need updating once controllers implemented
- GUI components ready for unit testing
- Integration points clearly defined for future testing

## Testing Checklist

When making changes, verify:
1. Interactive mode (`mcp-config-manager interactive`) still works exactly as before
2. Backups are created before any config changes
3. Both Claude-only and Gemini-only modes function correctly
4. Sync between Claude and Gemini works when in 'both' mode
5. Error messages are clear when configs are missing or corrupted
6. Original `mcp_toggle.py` workflows remain supported
