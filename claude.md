# MCP Config Manager - Claude Code Instructions

## Project Overview

MCP Config Manager is a cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems. This project was built by integrating and enhancing the original `mcp_toggle.py` script into a professional, modular architecture.

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

## Architecture

### Project Structuresrc/mcp_config_manager/
├── core/
│   ├── config_manager.py    # Main configuration management (COMPLETE)
│   ├── server_manager.py    # Server enable/disable logic (COMPLETE)
│   └── presets.py          # Preset management (COMPLETE)
├── parsers/
│   ├── claude_parser.py    # Claude config parsing (COMPLETE)
│   ├── gemini_parser.py    # Gemini config parsing (COMPLETE)
│   └── base_parser.py      # Parser interface (COMPLETE)
├── utils/
│   ├── backup.py           # Backup functionality (COMPLETE)
│   ├── sync.py             # Config synchronization (COMPLETE)
│   └── file_utils.py       # File path utilities (COMPLETE)
├── gui/                    # GUI components (TODO)
└── cli.py                  # Command line interface (COMPLETE)

### Key Components

1. **ConfigManager** (`core/config_manager.py`)
   - Central orchestrator for all configuration operations
   - Handles loading, saving, syncing between Claude and Gemini
   - Manages backups and validation
   - Primary API for both CLI and future GUI

2. **ServerManager** (`core/server_manager.py`)
   - Manages server enable/disable operations
   - Handles disabled server storage in separate JSON file
   - Supports bulk operations (enable all, disable all)
   - Handles server addition from JSON configurations

3. **PresetManager** (`core/presets.py`)
   - Manages preset configurations in `~/.mcp_presets.json`
   - Supports saving/loading project-specific server sets
   - Provides default preset modes (minimal, webdev, fullstack)

4. **Parsers** (`parsers/`)
   - Claude and Gemini specific configuration file handling
   - Validation and error handling
   - Abstracted through base parser interface

## Development Guidelines

### When Working on This Project

1. **Interactive Mode is the Gold Standard**
   - The interactive CLI (`mcp-config-manager interactive`) contains all the original script functionality
   - Test any changes against this mode to ensure compatibility
   - This is what users currently rely on

2. **Maintain Backwards Compatibility**
   - Original `mcp_toggle.py` users should be able to migrate seamlessly
   - Preserve existing file locations (`~/.claude.json`, `~/.mcp_presets.json`, etc.)
   - Don't break existing workflows

3. **File Locations (Important)**
   - Claude config: `~/.claude.json`
   - Gemini config: `~/.gemini/settings.json`
   - Presets: `~/.mcp_presets.json`
   - Disabled servers: `./disabled_servers.json` (in project directory)
   - Backups: `~/.claude.json.backup.YYYYMMDD_HHMMSS`

4. **Testing Strategy**
   - Always test with real config files (make backups first!)
   - Test both Claude-only and Gemini-only modes
   - Test sync functionality between both systems
   - Verify backup creation and restoration

### Code Patterns

1. **Error Handling**
   - Always handle JSON parsing errors gracefully
   - Create backups before making changes
   - Provide clear error messages to users
   - Never lose user configurations

2. **Mode Support**
   - All operations should support `mode` parameter: 'claude', 'gemini', or 'both'
   - 'both' mode should sync configurations between systems
   - Respect user's choice of which system(s) to manage

3. **Configuration Management**
   - Use the ConfigManager as the primary API
   - Don't directly manipulate config files from other components
   - Always validate configurations after changes

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

## Next Development Priorities

1. **GUI Framework Selection**
   - Recommend PyQt6 for professional appearance
   - Alternative: tkinter for simpler deployment
   - Consider cross-platform packaging requirements

2. **GUI Core Features**
   - Server list with enable/disable toggles
   - Mode selection (Claude/Gemini/Both)
   - Preset management interface
   - Add server dialog with JSON paste

3. **Advanced Features**
   - Health monitoring (ping MCP servers)
   - Auto-discovery of available MCP servers
   - Drag-and-drop server organization
   - Import/export configurations

## Working with Original Script Logic

The original `mcp_toggle.py` functionality is preserved in:
- `examples/original_mcp_toggle.py` - Original script for reference
- Interactive mode - Full original functionality
- Core modules - Logic extracted and enhanced

When making changes, refer to the original script to understand user expectations and workflows.

## Testing the Project

```bashInstall in development mode
pip install -e .Test interactive mode (primary interface)
mcp-config-manager interactiveTest CLI commands
mcp-config-manager status
mcp-config-manager preset minimal
mcp-config-manager enable context7Run test suite
pytest tests/ -vTest with real configs (backup first!)
cp ~/.claude.json ~/.claude.json.manual-backup
mcp-config-manager validate ~/.claude.json

## Important Notes for Claude Code

1. **This is a working, production-ready tool** - The interactive mode is already being used by users
2. **Preserve existing functionality** - Don't break what's working
3. **Build incrementally** - Add GUI as enhancement, not replacement
4. **Test thoroughly** - Configuration management is critical, errors lose user data
5. **Follow the established patterns** - The architecture is designed for extensibility

## File Modification Guidelines

- **Never directly edit**: User config files without backups
- **Always validate**: JSON before writing to config files
- **Preserve structure**: Maintain existing config file formats
- **Handle errors gracefully**: Network issues, permission problems, etc.
- **Create examples**: For any new server types or configurations

## Questions to Ask When Developing

1. Does this work in all three modes (claude/gemini/both)?
2. Are backups created before making changes?
3. Is the interactive mode still fully functional?
4. Can users migrate from the original script seamlessly?
5. Are error messages clear and actionable?
6. Does this handle edge cases (missing files, corrupted JSON, etc.)?
