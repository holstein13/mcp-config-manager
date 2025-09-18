# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

MCP Config Manager is a cross-platform utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems. It is an evolution of the `mcp_toggle.py` script, with a more robust and modular architecture.

The tool is written in Python and provides both an interactive CLI and a command-line interface for managing server configurations. It supports managing configurations for both Claude (`~/.claude.json`) and Gemini (`~/.gemini/settings.json`), including the ability to synchronize configurations between them.

## Building and Running

### Installation

To install the project for development, use the following command:

```bash
pip install -e .
```

### Running the application

The primary interface is the interactive mode:

```bash
mcp-config-manager interactive
```

Other commands are also available:

```bash
# Show current server status
mcp-config-manager status

# Enable or disable a specific server
mcp-config-manager enable <server>
mcp-config-manager disable <server>

# Apply a preset
mcp-config-manager preset minimal
```

### Testing

To run the test suite, use `pytest`:

```bash
pytest tests/ -v
```

You can also run specific tests:

```bash
pytest tests/test_config_manager.py::TestConfigManager::test_specific_method
```

## Development Conventions

### Code Style

The project uses the following tools to maintain code quality:

*   **`black`** for code formatting
*   **`flake8`** for linting
*   **`isort`** for sorting imports
*   **`mypy`** for type checking

You can run these tools using the following commands:

```bash
black src/ tests/
flake8 src/ tests/
isort src/ tests/
mypy src/
```

### Architecture

The project has a modular architecture, with a clear separation of concerns:

*   **`ConfigManager` (`core/config_manager.py`):** The central orchestrator that handles loading, saving, and syncing configurations.
*   **`ServerManager` (`core/server_manager.py`):** Manages enabling and disabling servers.
*   **`PresetManager` (`core/presets.py`):** Handles preset configurations.
*   **Parsers (`parsers/`):** Contains parsers for Claude and Gemini specific configuration files.

### Critical Implementation Notes

1.  **Interactive Mode is Key:** The interactive mode (`mcp-config-manager interactive`) is the most important feature. All changes should be tested against it to ensure full functionality.
2.  **Mode Support:** All operations must support the `mode` parameter, which can be 'claude', 'gemini', or 'both'.
3.  **Error Handling:** The tool should handle errors gracefully, especially when parsing JSON files. It should also create backups before making any changes to user configurations.
4.  **Backwards Compatibility:** The tool should be backward compatible with the original `mcp_toggle.py` script.
