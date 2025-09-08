# Integration Plan for mcp_toggle.py

## Core Components to Extract:
1. Configuration loading/saving (config_manager.py)
2. Claude/Gemini specific parsing (parsers/)
3. Backup functionality (utils/backup.py)
4. Preset management (core/presets.py)
5. Server management (core/server_manager.py)
6. CLI interface (cli.py)
7. Sync functionality (utils/sync.py)

## File Mapping:
- backup_configs() → utils/backup.py
- load_config()/save_config() → parsers/
- preset functions → core/presets.py
- server enable/disable → core/server_manager.py
- main CLI loop → cli.py
- sync_configs() → utils/sync.py
