cat > README.md << 'EOF'
# MCP Config Manager

A cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems.

**Based on the battle-tested `mcp_toggle.py` script with enhanced architecture and GUI interface.**

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![GUI](https://img.shields.io/badge/GUI-PyQt6%20%7C%20Tkinter-green.svg)

## 🎉 Project Status

### ✅ GUI is FULLY FUNCTIONAL!
The graphical interface is complete and working with all major features operational. The application provides a modern, user-friendly way to manage MCP servers without touching JSON files.

## 🚀 Current Features

### ✅ Fully Implemented
- **🖥️ Graphical User Interface** - Modern cross-platform GUI with PyQt6/tkinter
- **Interactive CLI Management** - Full-featured interactive mode for server management
- **Multi-Client Support** - Manages both `.claude.json` and `.gemini/settings.json` files
- **Server Enable/Disable** - Toggle servers on/off without losing configurations
- **Master Checkbox** - Bulk select/deselect all servers at once
- **Configuration Syncing** - Synchronize servers between Claude and Gemini
- **Automatic Backups** - Timestamped backups before any changes
- **Preset Management** - Save and load project-specific configurations
- **Quick Preset Modes** - Minimal, web dev, fullstack, and testing presets
- **JSON Server Addition** - Add new servers by pasting JSON configurations
- **Cross-Platform Support** - Works on Windows, macOS, and Linux
- **Command Line Interface** - Full CLI with individual commands
- **Configuration Validation** - Validate config file structure
- **Visual Status Indicators** - Clear enabled/disabled status with colors
- **Keyboard Shortcuts** - Professional keyboard navigation (Cmd+S to save, etc.)

### 🚧 Next Features (Planning Phase)
- **Server Detail View** - Edit server configurations directly in the GUI (in planning)
- **Health Monitoring** - Real-time server connection status
- **Import/Export** - Backup and restore entire configurations
- **Auto-Discovery** - Automatically find and suggest MCP servers

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Claude Code CLI and/or Gemini CLI installed
- PyQt6 (optional, for better GUI experience): `pip install PyQt6`

### Quick Install
```bash
git clone https://github.com/yourusername/mcp-config-manager.git
cd mcp-config-manager
pip install -e .

# Optional: Install PyQt6 for better GUI experience
pip install PyQt6
```

## 🚀 Usage

### GUI Mode (NEW! - Recommended)
Launch the graphical interface:

```bash
mcp-config-manager gui
```

The GUI provides:
- 🖥️ Visual server list with checkboxes
- ☑ Master checkbox for bulk operations
- 🔄 Mode switching between Claude/Gemini/Both
- 💾 Save button with visual feedback
- ➕ Add new servers via JSON
- 📁 Preset management dialog
- ⌨️ Full keyboard shortcuts (Cmd+S to save, etc.)

### Interactive CLI Mode
Launch the command-line interactive interface:

```bash
mcp-config-manager interactive
```
This gives you the complete interface from the original mcp_toggle.py script with:

- ✅/❌ Visual server status
- 🔄 Real-time mode switching (Claude/Gemini/Both)
- 📁 Preset management
- ➕ Add servers by pasting JSON
- 🎯 Quick preset modes (minimal, web dev, etc.)

### Command Line Usage

```bash
# Show current status
mcp-config-manager status

# Enable/disable specific servers
mcp-config-manager enable server-name
mcp-config-manager disable server-name

# Bulk operations
mcp-config-manager enable-all
mcp-config-manager disable-all

# Apply preset modes
mcp-config-manager preset minimal    # Only context7 + browsermcp
mcp-config-manager preset webdev     # + playwright
mcp-config-manager preset fullstack  # + supabase, clerk, railway

# Validate configurations
mcp-config-manager validate ~/.claude.json
```

### Working with Modes

The tool supports three modes:

- **Claude only** (`--mode claude`) - Only manages `.claude.json`
- **Gemini only** (`--mode gemini`) - Only manages `.gemini/settings.json`
- **Both (synced)** (`--mode both`) - Keeps both configs synchronized

## 🖼️ Screenshots

### Interactive Mode

```
🔧 MCP Config Manager - Interactive Mode
==================================================

📊 Current Status:
------------------------------
Mode: 🔄 Both CLIs (synced)

✅ ACTIVE servers (will run):
  [1] context7
  [2] browsermcp
  [3] playwright

❌ DISABLED servers (won't run):
  [d1] supabase
  [d2] clerk

📋 Actions:
  [1-N]  Disable active server
  [d1-N] Enable disabled server
  [a]    Enable ALL
  [n]    Disable ALL
  [m]    Minimal (context7 + browsermcp)
  [w]    Web dev (+ playwright)
  [+]    ➕ Add new MCP server
  [p]    📁 Preset management
  [c]    🔄 Change CLI mode
  [s]    Save and exit
  [q]    Quit without saving

Action: 
```

## 🛠️ Development

### Project Structure

```
src/mcp_config_manager/
├── core/
│   ├── config_manager.py    # Main configuration management
│   ├── server_manager.py    # Server enable/disable logic
│   └── presets.py          # Preset management
├── parsers/
│   ├── claude_parser.py    # Claude config parsing
│   ├── gemini_parser.py    # Gemini config parsing
│   └── base_parser.py      # Parser interface
├── utils/
│   ├── backup.py           # Backup functionality
│   ├── sync.py             # Config synchronization
│   └── file_utils.py       # File path utilities
├── gui/                    # Future GUI components
└── cli.py                  # Command line interface
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-config-manager.git
cd mcp-config-manager

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest

# Run the application
mcp-config-manager interactive
```

## 📁 File Locations

- **Claude config:** `~/.claude.json`
- **Gemini config:** `~/.gemini/settings.json`
- **Presets:** `~/.mcp_presets.json`
- **Disabled servers:** `./disabled_servers.json` (in project directory)
- **Backups:** `~/.claude.json.backup.YYYYMMDD_HHMMSS`

## 🗺️ Roadmap

### ✅ Phase 1: Core Functionality - COMPLETE

- Interactive CLI interface
- Multi-client support (Claude + Gemini)
- Server enable/disable with storage
- Configuration synchronization
- Automatic backups
- Preset management
- JSON server addition
- Command line interface

### ✅ Phase 2: GUI Development - COMPLETE

- Cross-platform GUI framework (PyQt6/tkinter)
- Main server management window with checkboxes
- Master checkbox for bulk operations
- Preset management dialog
- Settings and configuration dialogs
- Add server via JSON paste
- Keyboard shortcuts and professional UX
- Visual status indicators and feedback

### 🚧 Phase 3: Polish & Platform Testing - IN PROGRESS

Current focus:
- ✅ macOS platform testing and optimization
- ⏳ Windows platform testing
- ⏳ Linux platform testing
- ⏳ Performance optimization for large server lists
- ⏳ PyInstaller packaging

### 📋 Phase 4: Advanced Features - PLANNED

Next major features:
- **Server Detail View** - Click server name to edit configuration in side panel
- **Field Editors** - Visual editors for each configuration field type
- **Real-time Validation** - Immediate feedback on configuration changes
- **Health Monitoring** - Real-time server connection status
- **Import/Export** - Backup and restore configurations
- **Server Discovery** - Auto-detect available MCP servers

### 🚀 Phase 5: Distribution

- Packaged installers (Windows MSI, macOS DMG, Linux AppImage)
- Auto-updater mechanism
- Plugin architecture for extensions
- IDE integrations (VS Code, IntelliJ, etc.)

## 🎯 Migration from Original Script

If you're using the original `mcp_toggle.py` script:

- **Your configs are preserved** - The tool uses the same file locations
- **Your presets carry over** - `~/.mcp_presets.json` is used directly
- **Same functionality** - All original features are available in interactive mode
- **Enhanced capabilities** - Plus new CLI commands and better error handling

## 🤝 Contributing

We welcome contributions! The original `mcp_toggle.py` script was a fantastic foundation, and we're building on that success.

### Areas for Contribution

- 🎨 **GUI Development** - Help build the cross-platform interface
- 🔍 **Server Discovery** - Auto-detect available MCP servers
- 🧪 **Testing** - Add test coverage for all components
- 📚 **Documentation** - Improve guides and examples
- 🐛 **Bug Reports** - Found an issue? Let us know!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original `mcp_toggle.py` script that inspired this project
- The Anthropic team for developing the Model Context Protocol
- The open source community for feedback and contributions

---

**Ready to get started?** Run `mcp-config-manager interactive` and experience the full power of MCP server management!