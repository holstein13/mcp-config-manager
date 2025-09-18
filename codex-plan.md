# Codex Integration Implementation Plan

## Overview
Add support for ChatGPT's Codex CLI as a third configuration target alongside Claude and Gemini in the MCP Config Manager application. Codex uses TOML format (`~/.codex/config.toml`) instead of JSON.

## Architecture Principles
- **Encapsulation**: Keep TOML/JSON conversion logic isolated in the parser layer
- **Backward Compatibility**: Ensure existing Claude/Gemini functionality remains unchanged
- **Progressive Enhancement**: Add Codex support without breaking existing features
- **Migration Safety**: Backup existing configurations before any destructive operations
- **Dynamic Client Support**: Refactor to support N clients rather than hardcoding 3

## Task Breakdown

### Phase 1: Core Infrastructure (Est: 30,000 tokens)

#### Task 1.1: Add TOML Dependencies
- [x] Add `toml>=0.10.2` to requirements.txt
- [x] Install dependency: `pip install toml`
- [x] Verify import works in Python environment

#### Task 1.2: Create CodexConfigParser
**File**: `src/mcp_config_manager/parsers/codex_parser.py`
- [x] Create parser class inheriting from BaseConfigParser
- [x] Implement `parse()` method for reading TOML
- [x] Implement `write()` method with TOML table structure
- [x] Implement `validate()` method for Codex-specific validation
- [x] Add TOML↔JSON conversion helpers:
  - [x] `_toml_to_internal()`: Convert TOML tables to internal dict format
  - [x] `_internal_to_toml()`: Convert internal dict to TOML tables
- [x] Handle special cases:
  - [x] Environment variables (`[mcp_servers.name.env]`)
  - [x] Headers for HTTP servers (`[mcp_servers.name.headers]`)
  - [x] Array arguments (`args = ["npx", "-y", "package"]`)

#### Task 1.3: Update File Utilities
**File**: `src/mcp_config_manager/utils/file_utils.py`
- [x] Add `get_codex_config_path()` → `~/.codex/config.toml`
- [x] Add `ensure_codex_config_exists()` function
- [x] Update `ensure_config_directories()` to include Codex
- [x] Add Codex path validation helpers

> **Phase 1 completion notes (2025-09-18)**
> - Implemented a dedicated `CodexConfigParser` with round-trip TOML support, project-table handling, and validation tuned for Codex's stdio/http semantics.
> - Verified the `toml` dependency is available at runtime and wired writer logic to use it for serialization.
> - Extended file utilities with Codex-aware helpers, ensuring default `config.toml` scaffolding plus a reusable validator for downstream callers.
> - Ready to proceed to Phase 2 now that core infrastructure for Codex configs aligns with Claude/Gemini parity.

> **Phase 2 completion notes (2025-09-18)**
> - Added a reusable `CLIDetector` with TTL caching so the app can surface Codex availability alongside Claude/Gemini without hammering the filesystem.
> - Expanded `ConfigManager` to juggle three configs in tandem, introducing Codex parsing/saving, dynamic mode resolution, and an availability API for the GUI.
> - Refactored `ServerManager` around a client map, updated enable/disable/list flows, and migrated disabled-server storage to track per-client state (including Codex) while leaving merge tooling for a later phase.
> - Threaded Codex-aware load/save calls through CLI and GUI controllers to keep interactions in sync with the new triple-return contract.

### Phase 2: Data Model Updates (Est: 30,000 tokens)

#### Task 2.1: Create CLI Detection System
**File**: `src/mcp_config_manager/core/cli_detector.py` (new)
- [x] Create `CLIDetector` class with detection methods
- [x] Implement `detect_claude()` - check for Claude Desktop app/config
- [x] Implement `detect_gemini()` - check for Gemini CLI installation
- [x] Implement `detect_codex()` - check for Codex CLI installation
- [x] Add `detect_all()` method returning availability dict
- [x] Cache detection results with TTL (time-to-live)
- [x] Add `refresh_detection()` method to force re-check
- [ ] Handle platform-specific detection (Windows/Mac/Linux)

#### Task 2.2: Extend ConfigManager
**File**: `src/mcp_config_manager/core/config_manager.py`
- [x] Add `codex_path` attribute and `codex_parser` instance
- [x] Add `cli_detector` instance for CLI availability
- [x] Update `ConfigMode` enum to include `CODEX` and `ALL`
- [x] Modify `load_configs()` to return triple: `(claude_data, gemini_data, codex_data)`
- [x] Update `save_configs()` to handle `codex_data` parameter
- [x] Add mode checking for 'codex' and 'all' in all methods
- [x] Update constructor to accept optional `codex_path` parameter
- [x] Add `get_cli_availability()` method returning status dict

#### Task 2.3: Update Server Manager
**File**: `src/mcp_config_manager/core/server_manager.py`
- [x] Refactor to use configurable client list instead of hardcoded names
- [x] Add `SUPPORTED_CLIENTS = ['claude', 'gemini', 'codex']`
- [x] Update `list_all_servers()` to handle three configurations
- [x] Modify `enable_server()` and `disable_server()` for Codex
- [ ] Update server merging logic to handle triple configs

#### Task 2.4: Update Disabled Servers Storage
**File**: `src/mcp_config_manager/core/server_manager.py`
- [x] Migrate storage format to support dynamic clients
- [x] Add migration function for existing disabled_servers.json
- [x] Update `_load_disabled_servers()` with migration logic
- [ ] Test backward compatibility with existing files

### Phase 3: Synchronization & Backup (Est: 20,000 tokens)

#### Task 3.1: Three-Way Sync Logic
**File**: `src/mcp_config_manager/utils/sync.py`
- [x] Update `sync_server_configs()` to accept three configs
- [x] Add `sync_three_way()` helper function
- [x] Implement conflict resolution for three-way sync
- [x] Handle TOML-specific fields during sync
- [x] Add validation for synced configurations

#### Task 3.2: Backup System Updates
**File**: `src/mcp_config_manager/utils/backup.py`
- [x] Update `backup_all_configs()` to include Codex
- [x] Add Codex backup file naming convention
- [x] Update `restore_from_backup()` to handle TOML files
- [x] Add backup validation for TOML format
- [x] Test backup/restore roundtrip for all three formats

> **Phase 3 completion notes (2025-09-18)**
> - Extended `sync_server_configs()` with backward-compatible three-way sync support, maintaining the original two-way sync when codex_data is None.
> - Implemented comprehensive `sync_three_way()` function that merges servers across all three configurations while preserving client-specific settings.
> - Added conversion helpers (`_convert_for_claude`, `_convert_for_gemini`, `_convert_for_codex`) to handle format differences between clients, particularly for TOML-specific fields like headers.
> - Implemented `resolve_sync_conflicts()` with multiple strategies (merge, claude, gemini, codex) for handling synchronization conflicts.
> - Added `validate_synced_configs()` to verify all three configs have matching server sets and required fields.
> - Enhanced backup system to handle TOML files for Codex, with proper file naming conventions (codex-backup-*.toml).
> - Implemented `restore_from_backup()` with automatic backup type detection and format validation.
> - Added `validate_backup()` function that checks both file naming conventions and content validity (including TOML parsing for Codex backups).
> - Tested backup/restore roundtrip successfully - all three config formats (Claude JSON, Gemini JSON, Codex TOML) backup and restore correctly.
> - Ready to proceed to Phase 4 for GUI data layer updates.

### Phase 4: GUI Updates - Data Layer (Est: 30,000 tokens)

#### Task 4.1: Update Server Models
**File**: `src/mcp_config_manager/gui/models/server_list_item.py`
- [ ] Add `codex_enabled` property to ServerListItem
- [ ] Update initialization to accept Codex state
- [ ] Add Codex to toggle methods
- [ ] Update state comparison methods

#### Task 4.2: Update Application State
**File**: `src/mcp_config_manager/gui/models/app_state.py`
- [ ] Add `codex_config` to ApplicationState
- [ ] Update state management for three configs
- [ ] Add Codex mode to current_mode tracking
- [ ] Update state validation methods

#### Task 4.3: Update Controllers
**Files to update**:
- `src/mcp_config_manager/gui/controllers/config_controller.py`
  - [ ] Add Codex support to load/save operations
  - [ ] Update validation for TOML format
  - [ ] Add Codex-specific error handling

- `src/mcp_config_manager/gui/controllers/server_controller.py`
  - [ ] Add Codex column to server list data
  - [ ] Update `toggle_server()` for Codex
  - [ ] Add bulk toggle support for Codex

- `src/mcp_config_manager/gui/controllers/preset_controller.py`
  - [ ] Include Codex state in preset save/load
  - [ ] Update preset validation for three clients

### Phase 5: GUI Updates - Presentation Layer (Est: 40,000 tokens)

#### Task 5.1: Update Server List Widget
**File**: `src/mcp_config_manager/gui/widgets/server_list.py`
- [ ] Add "Codex" column (index 2) to tree widget
- [ ] Update header to show 6 columns total
- [ ] Add `codex_master_state` tracking
- [ ] Implement Codex master checkbox logic
- [ ] Update `_on_header_clicked()` for column 2
- [ ] Adjust column widths:
  - Claude: 70px
  - Gemini: 70px
  - Codex: 70px
  - Server: Stretch
  - Status: 100px
  - Location: 120px
- [ ] Update checkbox state management for three columns
- [ ] Add Codex to bulk toggle methods
- [ ] **Add CLI availability checking**:
  - [ ] Store `cli_availability` dict from config manager
  - [ ] Disable checkboxes for unavailable CLIs
  - [ ] Show grayed-out appearance for disabled columns
  - [ ] Update tooltips to indicate "Claude/Gemini/Codex not installed"

#### Task 5.2: Update Server Details Panel
**File**: `src/mcp_config_manager/gui/widgets/server_details_panel.py`
- [ ] Add Codex checkbox to details view
- [ ] Update layout to accommodate third checkbox
- [ ] Add Codex-specific tooltips mentioning TOML format
- [ ] Update state synchronization logic
- [ ] Add visual indicators for Codex state
- [ ] **Disable checkbox if Codex not installed**
- [ ] Show installation hint in tooltip when disabled

#### Task 5.3: Update Main Window
**File**: `src/mcp_config_manager/gui/main_window.py`
- [ ] Add Codex to mode selection menu
- [ ] Update status bar to show Codex server count
- [ ] Add Codex file path to configuration display
- [ ] Update window title for Codex mode
- [ ] Add keyboard shortcuts for Codex operations
- [ ] **Add refresh button for CLI detection**:
  - [ ] Add "Refresh CLIs" button/menu item
  - [ ] Connect to cli_detector.refresh_detection()
  - [ ] Update UI state after refresh
  - [ ] Show notification of detected changes
  - [ ] Auto-detect on app startup

### Phase 6: CLI Updates (Est: 15,000 tokens)

#### Task 6.1: Extend CLI Commands
**File**: `src/mcp_config_manager/cli.py`
- [ ] Add 'codex' and 'all' to `--mode` choices
- [ ] Update help text for all commands
- [ ] Add Codex column to `list` command output
- [ ] Update `toggle` command for Codex
- [ ] Add Codex support to `sync` command
- [ ] Update interactive mode menu:
  - Add "3. Codex only"
  - Add "5. All three (Claude + Gemini + Codex)"
  - Renumber subsequent options

#### Task 6.2: Update CLI Display
- [ ] Add Codex status to server listing
- [ ] Update summary statistics
- [ ] Add Codex path to config info display
- [ ] Update validation messages

### Phase 7: Presets & Import/Export (Est: 20,000 tokens)

#### Task 7.1: Update Preset System
**File**: `src/mcp_config_manager/core/presets.py`
- [ ] Add Codex server states to preset format
- [ ] Update preset loading to set Codex states
- [ ] Add migration for old presets without Codex
- [ ] Update built-in presets with Codex defaults
- [ ] Test preset compatibility across versions

#### Task 7.2: Import/Export Enhancement
- [ ] Add TOML import capability
- [ ] Add export to TOML format option
- [ ] Create conversion utilities TOML↔JSON
- [ ] Add format detection for imports
- [ ] Update validation for imported configs

### Phase 8: Testing (Est: 25,000 tokens)

#### Task 8.1: Unit Tests for CodexConfigParser
**File**: `tests/test_codex_parser.py` (new)
- [ ] Test TOML reading with various structures
- [ ] Test TOML writing and format preservation
- [ ] Test TOML↔JSON conversion accuracy
- [ ] Test validation edge cases
- [ ] Test error handling for malformed TOML

#### Task 8.2: Integration Tests
**Files to update**:
- `tests/test_config_manager.py`
  - [ ] Add Codex mode tests
  - [ ] Test three-way operations
  - [ ] Test migration scenarios

- `tests/test_gui/` (various)
  - [ ] Update GUI contract tests for Codex
  - [ ] Test three-column display
  - [ ] Test Codex toggle operations

#### Task 8.3: End-to-End Tests
- [ ] Test full workflow with actual Codex CLI
- [ ] Verify TOML output works with Codex
- [ ] Test backup/restore with all three configs
- [ ] Test preset apply across all clients
- [ ] Verify no regression in Claude/Gemini

### Phase 9: Documentation (Est: 10,000 tokens)

#### Task 9.1: Update User Documentation
**Files to update**:
- `README.md`
  - [ ] Add Codex to feature list
  - [ ] Update installation instructions
  - [ ] Add Codex-specific usage examples

- `documentation/design/codex-mcp.md`
  - [ ] Integrate with main documentation
  - [ ] Add troubleshooting section
  - [ ] Document HTTP bug workarounds

#### Task 9.2: Add Migration Guide
**File**: `MIGRATION.md` (new)
- [ ] Document upgrade process
- [ ] Explain storage format changes
- [ ] Provide rollback instructions
- [ ] Include FAQ section

### Phase 10: Polish & Optimization (Est: 15,000 tokens)

#### Task 10.1: Performance Optimization
- [ ] Optimize three-way sync algorithm
- [ ] Add caching for TOML parsing
- [ ] Minimize GUI redraws for triple updates
- [ ] Profile and optimize hot paths

#### Task 10.2: Error Handling & Recovery
- [ ] Add graceful TOML parse error recovery
- [ ] Implement config corruption detection
- [ ] Add automatic backup before risky operations
- [ ] Improve error messages for Codex issues

#### Task 10.3: Final Polish
- [ ] Add loading indicators for triple operations
- [ ] Ensure consistent UI state during updates
- [ ] Add success notifications for Codex operations
- [ ] Verify all tooltips and help text
- [ ] Final testing pass

## Success Criteria
1. ✅ Codex column appears and functions in GUI
2. ✅ TOML files are correctly read and written
3. ✅ Three-way sync works without data loss
4. ✅ Existing Claude/Gemini functionality unchanged
5. ✅ CLI supports all three modes
6. ✅ Presets work across all clients
7. ✅ Backups include Codex configuration
8. ✅ Tests pass for all new functionality
9. ✅ Documentation is complete and accurate
10. ✅ No performance regression
11. ✅ **CLI detection works - unavailable CLIs show grayed out**
12. ✅ **Refresh button updates CLI availability dynamically**

## Risk Mitigation
- **TOML Library Issues**: Have fallback to tomli/tomli_w if toml has issues
- **Migration Failures**: Always backup before migration, provide rollback
- **GUI Layout Issues**: Test on all platforms (Windows/Mac/Linux)
- **Codex CLI Changes**: Document tested Codex version, monitor for updates
- **Performance Impact**: Profile before/after, optimize if >10% slower

## Rollout Strategy
1. **Phase 1-3**: Core functionality (backend)
2. **Phase 4-5**: GUI integration
3. **Phase 6-7**: CLI and presets
4. **Phase 8**: Testing
5. **Phase 9-10**: Documentation and polish

Each phase can be a separate PR to keep changes manageable and reviewable.

## CLI Detection Details

### Detection Methods by Platform

#### Claude Desktop
- **macOS**: Check for `/Applications/Claude.app` or `~/Applications/Claude.app`
- **Windows**: Check registry or `%APPDATA%/Claude`
- **Linux**: Check for Snap/Flatpak installation or config file presence
- **Fallback**: Check if `~/.claude.json` exists

#### Gemini CLI
- **All platforms**: Check if `gemini` command is in PATH
- **Config check**: Verify `~/.gemini/settings.json` exists
- **Version check**: Run `gemini --version` to validate installation

#### Codex CLI
- **All platforms**: Check if `codex` command is in PATH
- **Config check**: Verify `~/.codex/` directory exists
- **Version check**: Run `codex --version` to validate installation

### UI Behavior for Unavailable CLIs

1. **Visual States**:
   - Available: Normal checkbox, fully interactive
   - Unavailable: Grayed out checkbox, disabled interaction
   - Checking: Loading spinner during detection

2. **Tooltips**:
   - Available: "Toggle Claude/Gemini/Codex for [server name]"
   - Unavailable: "Claude/Gemini/Codex not installed. Click Refresh to check again."

3. **Master Checkbox**:
   - Disabled if CLI unavailable
   - Shows count only for available CLIs

4. **Refresh Behavior**:
   - Manual refresh via button/menu
   - Auto-refresh on app startup
   - Notification when CLI availability changes

## Estimated Total Tokens: ~235,000
Split across 10 phases, each under 40,000 tokens, making implementation manageable.
