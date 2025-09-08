# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Config Manager is a cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems. Built from the battle-tested `mcp_toggle.py` script, now with modular architecture.

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
- Framework selection and setup needed
- Main server management window design
- Preset management interface
- Settings and configuration dialogs

## Development Commands

```bash
# Install for development
pip install -e .

# Run tests
pytest tests/ -v
pytest tests/test_config_manager.py::TestConfigManager::test_specific_method

# Code quality
black src/ tests/           # Format code
flake8 src/ tests/          # Lint code
isort src/ tests/           # Sort imports
mypy src/                   # Type checking

# Main commands
mcp-config-manager interactive               # Launch interactive mode (primary interface)
mcp-config-manager status                    # Show current server status
mcp-config-manager enable <server>           # Enable specific server
mcp-config-manager disable <server>          # Disable specific server
mcp-config-manager preset minimal            # Apply minimal preset
mcp-config-manager validate ~/.claude.json   # Validate config file
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **ConfigManager** (`core/config_manager.py`): Central orchestrator handling loading, saving, and syncing between Claude and Gemini configs. Primary API for both CLI and GUI.
- **ServerManager** (`core/server_manager.py`): Manages server enable/disable operations with separate storage for disabled servers.
- **PresetManager** (`core/presets.py`): Handles preset configurations in `~/.mcp_presets.json`.
- **Parsers** (`parsers/`): Claude and Gemini specific config file handling with validation.

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

Currently exploring GUI framework options:
- PyQt6 for professional appearance
- tkinter for simpler deployment
- Focus on cross-platform packaging

GUI must include:
- Server list with enable/disable toggles
- Mode selection (Claude/Gemini/Both)
- Preset management interface
- JSON paste dialog for adding servers

## Testing Checklist

When making changes, verify:
1. Interactive mode (`mcp-config-manager interactive`) still works exactly as before
2. Backups are created before any config changes
3. Both Claude-only and Gemini-only modes function correctly
4. Sync between Claude and Gemini works when in 'both' mode
5. Error messages are clear when configs are missing or corrupted
6. Original `mcp_toggle.py` workflows remain supported
