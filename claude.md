# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Config Manager is a cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems. Built from the battle-tested `mcp_toggle.py` script, now with modular architecture.

## Current Status

- **Phase**: 3.6.4 Complete - Visual Polish implemented
- **Branch**: 001-cross-platform-gui  
- **Platform**: macOS (Darwin 24.6.0)
- **GUI**: Fully functional with PyQt6

### System State
- **Server Editing**: ✅ Select servers from list and edit configurations
- **Validation**: ✅ Real-time field validation with visual feedback
- **Keyboard Shortcuts**: ✅ Ctrl+S save, Esc cancel
- **Master Checkbox**: ✅ Text-based bulk operations (☐/☑/⊟)
- **Server Toggle**: ✅ Enable/disable servers via checkboxes
- **Save Function**: ✅ Persists changes correctly
- **Interactive Mode**: ✅ Remains primary interface
- **Visual Polish**: ✅ All visual enhancements complete

### Visual Enhancements (Session 13)
- ✅ **T104**: Blue highlight (#0078D4) for selected servers with hover effects
- ✅ **T105**: Orange indicators (#FF6B00) for unsaved changes in header
- ✅ **T106**: Red borders (2px) with light background for validation errors
- ✅ **T107**: Empty state message with helpful tips when no server selected

### Next Phase: Tkinter Support (T108-T112)
- Create tkinter field editor equivalents
- Create tkinter ServerDetailsPanel
- Create tkinter AddFieldDialog
- Ensure API consistency between Qt and tkinter
- Test tkinter visual parity

## Architecture

```
src/mcp_config_manager/
├── core/               # Business logic
│   ├── config_manager.py   # Central orchestrator
│   ├── server_manager.py   # Server operations
│   └── presets.py         # Preset management
├── gui/                # GUI components
│   ├── main_window.py     # Main application window
│   ├── controllers/       # GUI-library bridge
│   ├── widgets/          # UI components
│   └── dialogs/          # Modal dialogs
└── parsers/            # Config file handlers
```

### Key Files
- **Config**: `~/.claude.json`, `~/.gemini/settings.json`
- **Presets**: `~/.mcp_presets.json`
- **Disabled**: `./disabled_servers.json` (project root)
- **Backups**: `~/.claude.json.backup.YYYYMMDD_HHMMSS`

## Development Commands

```bash
# Install
pip install -e .

# Run
mcp-config-manager interactive    # Primary CLI interface
mcp-config-manager gui            # GUI application
mcp-config-manager status         # Show server status

# Testing
pytest tests/ -v
pytest tests/test_gui/ -v

# Code Quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

## Critical Implementation Notes

### Server Operations
- All operations support modes: 'claude', 'gemini', 'both'
- ServerManager methods require: `(claude_data, gemini_data, server_name, mode)`
- Controllers convert Mode enum to string with `.value`
- Always create backups before changes

### GUI Event Flow
1. User selects server → `server_selected` signal
2. ServerDetailsPanel loads configuration
3. User edits fields → validation runs
4. User saves → `server_updated` signal
5. Controller updates configuration
6. ConfigManager persists changes

### Known Issues
- **macOS Qt Bug**: Checkboxes render as blue squares (visual only, functionality works)
- **Multiple GUI Processes**: May accumulate from testing - use `pkill -f mcp_config_manager`

## Recent Work (Session 13)

### Completed (T104-T107) - Visual Polish
- ✅ **T104**: Blue highlight for selected servers
  - Added custom QStyleSheet with #0078D4 background
  - Included hover effects with light blue (#E3F2FD)
- ✅ **T105**: Orange indicators for unsaved changes
  - Header text turns orange (#FF6B00) when changes pending
  - Added "(unsaved)" suffix with orange bullet point
  - Resets to normal after save/cancel
- ✅ **T106**: Enhanced validation error styling  
  - Increased border width to 2px for visibility
  - Added light red background (#FFF5F5) for error fields
  - Orange borders/background for modified fields
- ✅ **T107**: Empty state message
  - QStackedWidget switches between empty state and form
  - Helpful message with emoji indicators
  - Includes keyboard shortcut tips

### Key Decisions (Session 13)
1. **Color Scheme**: Blue for selection, orange for changes, red for errors
2. **Empty State**: Used QStackedWidget for clean transitions
3. **Visual Feedback**: All state changes now have clear visual indicators
4. **Task Clarification**: T108-T112 are for Tkinter support, not additional UX features

## Previous Work (Session 12)

### Completed (T098-T103)
- ✅ Separated checkbox toggle from row selection events
- ✅ Integrated ServerDetailsPanel into main window
- ✅ Connected signals between list and detail panel
- ✅ Added `update_server()` to ServerController
- ✅ Added `update_server_config()` to ServerManager
- ✅ Implemented keyboard shortcuts in detail panel

## Interactive Mode Commands

Essential commands that must continue working:
- `[1-N]` - Disable server by number
- `[d1-N]` - Enable disabled server
- `[a]` - Enable all
- `[n]` - Disable all
- `[m]` - Minimal preset
- `[+]` - Add server (JSON)
- `[s]` - Save and exit
- `[q]` - Quit without saving

## Testing Checklist

Before any major change:
1. Interactive mode works exactly as before
2. Backups created before config changes
3. Claude/Gemini modes function correctly
4. Sync works in 'both' mode
5. Error handling preserves user data

## User Environment

- 9 active servers (context7, browsermcp, playwright, etc.)
- 2 disabled servers (XcodeBuildMCP, memory)
- Both Claude and Gemini configs present
- PyQt6 installed and working

# Important Guidelines

- Interactive mode is the gold standard - test all changes against it
- Never lose user configurations
- Maintain backwards compatibility with `mcp_toggle.py`
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary
- ALWAYS prefer editing existing files to creating new ones