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
- Current phase: GUI Development (Phase 2)
- Active branch: master

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

### 🔄 Phase 2 In Progress: GUI Development

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

#### 🚀 Phase 3.3 Ready: Core Implementation
- Can now proceed with implementation to satisfy all test contracts
- Will implement controllers, models, and event system
- Target: Make all 25 test files pass

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

## Testing Checklist

When making changes, verify:
1. Interactive mode (`mcp-config-manager interactive`) still works exactly as before
2. Backups are created before any config changes
3. Both Claude-only and Gemini-only modes function correctly
4. Sync between Claude and Gemini works when in 'both' mode
5. Error messages are clear when configs are missing or corrupted
6. Original `mcp_toggle.py` workflows remain supported
