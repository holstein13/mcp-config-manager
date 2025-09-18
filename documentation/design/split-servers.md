# Split Servers Implementation Plan

## Current Progress
**Phase 1 (Data Models):** ✅ Complete - All tasks (1.1, 1.2, 1.3) done
- Foundation laid for per-LLM server tracking
- Models now support independent Claude/Gemini enablement
- Disabled servers storage evolved to track per-LLM state
- Automatic migration from old format to new format
- Backward compatibility maintained throughout

**Phase 2 (Core Server Management):** ✅ Complete - All tasks (2.1, 2.2) done
- `get_enabled_servers()` now returns per-client states with `claude_enabled` and `gemini_enabled` flags
- `list_all_servers()` updated to return dict format with per-client information
- Added `bulk_enable_for_client()` and `bulk_disable_for_client()` for efficient bulk operations
- Added `sync_server_states()` to synchronize server states between Claude and Gemini
- All methods maintain backward compatibility with existing 'mode' parameter
- Comprehensive testing confirms all functionality works correctly

## Overview
Replace the current single checkbox + radio button mode selection system with dual checkbox columns (Claude and Gemini) in the server list. This will make the UI more intuitive, eliminate mode confusion, and allow users to directly control server enablement per LLM.

## Goals
1. **Simplify UX**: Remove mode selector, add two checkbox columns
2. **Independent Control**: Allow servers to be enabled/disabled per LLM independently
3. **Maintain Compatibility**: Ensure backward compatibility with existing configs
4. **Clean Architecture**: Remove mode-related complexity throughout codebase

## Migration Strategy for Remaining Tasks

### Key Patterns to Follow
1. **Client Parameter Pattern**: Replace `mode: Mode` with `client: str` ("claude"/"gemini"/None)
2. **Dual State Pattern**: Always update both `claude_servers` and `gemini_servers` dicts
3. **Backward Compatibility**: Keep updating legacy lists until Phase 8 cleanup
4. **UI Signal Pattern**: Emit signals with `(server_name, client, enabled)` tuple

### Backward Compatibility Approach
During the migration (Phases 1-7), backward compatibility is maintained to allow incremental updates:
- Event handlers accept both old (2-arg) and new (3-arg) signatures
- Controllers still accept 'mode' parameters alongside new 'client' parameters
- Legacy data structures (`active_servers`, `disabled_servers` lists) updated alongside new per-client dicts
- When no client specified, operations default to 'both' clients
- **All backward compatibility code will be removed in Phase 8 Task 8.2**

### Common Code Transformations
```python
# OLD: Mode-based
if self.app_state.mode == Mode.CLAUDE:
    # do something for Claude

# NEW: Client-based
if client == "claude":
    # do something for Claude
```

```python
# OLD: Single toggle
self.server_manager.toggle_server(name, mode=self.app_state.mode)

# NEW: Per-client toggle
self.server_manager.toggle_server(name, client="claude")  # or "gemini"
```

### Testing Considerations
- Test enabling server for Claude only, Gemini only, and both
- Verify backward compatibility with existing disabled_servers.json
- Ensure CLI interactive mode still works
- Check that save/load preserves per-client states

## Next Steps

**Phase 6 Complete**: All tasks (6.1, 6.2, 6.3) are complete. The dialogs and detail panels now support per-client enablement.

**Ready for Phase 7 (Testing and Validation)**: With all UI components updated, the next critical steps are:
1. ✅ ~~Update GUI controllers to use the new per-client model (Phase 3)~~ **COMPLETE**
2. ✅ ~~Implement the dual checkbox UI in server list (Tasks 4.1, 4.2)~~ **COMPLETE**
3. ✅ ~~Update main window to remove mode selector and integrate new server list behavior (Phase 5)~~ **COMPLETE**
4. ✅ ~~Update dialogs and detail panels to support per-client enablement (Phase 6)~~ **COMPLETE**
5. Comprehensive testing of all functionality (Phase 7) - **NEXT**

The critical path continues: Phase 7 (Testing) → Phase 8 (Cleanup)

**Current Session Accomplishments (Session 15):**
- ServerDetailsPanel now includes Claude/Gemini enablement checkboxes in header
- Add Server Dialog defaults both clients to enabled with option to change
- Delete Dialog shows per-client states and allows selective deletion
- Fixed ServerController bug with missing 'mode' key
- GUI launches successfully without errors
- All Phase 6 tasks complete and tested

**Key Accomplishments So Far:**
- Data models support per-client enablement (Phase 1 ✅)
- Server management handles per-client operations (Phase 2 ✅)
- ALL Controllers bridge between old and new paradigms (Phase 3 ✅ COMPLETE)
  - ServerController: per-client toggle and bulk operations
  - ConfigController: removed mode tracking, always loads both configs
  - PresetController: supports per-client preset data
  - BackupController: detects and handles new format
- Server list UI now has dual checkbox columns (Phase 4, Tasks 4.1-4.2 ✅)
  - Separate Claude and Gemini checkboxes per server
  - Per-column master checkboxes for bulk operations
  - Context menu supports per-client operations
  - Signals include client parameter for proper event handling
- All changes maintain backward compatibility
- Migration from old to new format happens automatically

**What's Ready for UI Implementation:**
- `ServerController.set_server_enabled(name, client, enabled)` - Set state for specific client
- `ServerController.get_servers()` returns items with `claude_enabled` and `gemini_enabled`
- `ServerController.get_server_states()` - Get all server states in one call
- `ConfigController.load_config()` - Always loads both configs
- `ConfigController.save_config(client)` - Can save for specific client or both

## Implementation Phases

### Phase 1: Data Model Updates (Foundation)
**Goal**: Establish per-LLM state tracking at the model level

#### Task 1.1: Update ServerListItem Model ✅
**File**: `src/mcp_config_manager/gui/models/server_list_item.py`
- [x] Add `claude_enabled: bool = False` property
- [x] Add `gemini_enabled: bool = False` property
- [x] Update `enable()` method to accept optional `client: str` parameter
- [x] Update `disable()` method to accept optional `client: str` parameter
- [x] Update `toggle()` method to work per-LLM
- [x] Add `get_enabled_state(client: str) -> bool` method
- [x] Update `to_dict()` and `from_dict()` to include both states
- [x] Remove or deprecate single `status` property usage for enablement

**Implementation Notes:**
- Added `claude_enabled` and `gemini_enabled` boolean fields at lines 75-76
- Methods now accept optional `client` parameter ("claude", "gemini", or None for both)
- When client is None, operations affect both LLMs (backward compatibility)
- Overall `status` field still exists but is derived from per-LLM states
- The `copy()` method was updated to include new fields (lines 339-340)

**Key Methods:**
- `enable(client: Optional[str])` - Enable for specific client or both
- `disable(client: Optional[str])` - Disable for specific client or both
- `toggle(client: Optional[str])` - Toggle state for client or both
- `get_enabled_state(client: str) -> bool` - Query specific client state

#### Task 1.2: Update Application State ✅
**File**: `src/mcp_config_manager/gui/models/app_state.py`
- [x] Remove `mode` property and `Mode` enum usage
- [x] Add `claude_servers: Dict[str, bool]` for tracking Claude states
- [x] Add `gemini_servers: Dict[str, bool]` for tracking Gemini states
- [x] Add methods for per-LLM state queries
- [x] Update any mode-dependent logic

**Implementation Notes:**
- Mode enum deprecated (kept as comment for reference during migration)
- Replaced single mode with two dictionaries: `claude_servers` and `gemini_servers`
- Each dict maps server_name -> enabled boolean
- Legacy `active_servers` and `disabled_servers` lists kept for backward compatibility
- All server methods updated to accept optional `client` parameter

**Phase 5 Implementation Notes (Session 14):**
- Removed ModeSelectorWidget completely from main_window.py and tkinter/main_window.py
- Updated all event handlers to use per-client operations instead of mode
- Modified _on_server_toggled() to handle both old (2-arg) and new (3-arg) signatures for backward compatibility
- Changed all controller calls to use 'both' as default instead of app_state.mode
- Removed mode switching keyboard shortcuts (Ctrl+1/2/3)
- Deleted mode_selector.py widget file entirely
- ConfigController.load_config() now always loads both configs
- Save/backup/validate operations now work on both configs by default

**New Helper Methods Added:**
- `get_server_enabled(server_name, client)` - Check if server enabled for client
- `set_server_enabled(server_name, client, enabled)` - Set per-client state
- `get_all_server_states()` - Returns dict of all servers with both client states
- `get_servers_for_client(client, enabled_only)` - Get client-specific server list
- `sync_from_legacy_lists()` - Migration helper to populate from old format

**Important for Next Tasks:**
- Controllers should use `client` string parameters, not Mode enum
- When no client specified, assume operation on both LLMs
- UI components need to track which client checkbox was clicked
- Server operations should update both the new dicts and legacy lists for compatibility

#### Task 1.3: Evolve Disabled Servers Storage ✅
**File**: `disabled_servers.json` structure
- [x] Design new format: `{"server_name": {"config": {...}, "disabled_for": ["claude"|"gemini"]}}`
- [x] Create migration function for existing format
- [x] Document the new structure

**Implementation Notes:**
- New format supports per-LLM tracking via `disabled_for` array
- Each server entry now has `config` (the server configuration) and `disabled_for` (list of clients)
- Automatic migration from old format happens on first load
- `_migrate_disabled_format()` converts old entries to new format (lines 305-328)
- `_normalize_to_new_format()` ensures consistency before saving (lines 330-349)
- All disable/enable operations updated to track per-client state

**New Format Example:**
```json
{
  "server_name": {
    "config": {
      "command": "npx",
      "args": [...],
      "env": {...}
    },
    "disabled_for": ["claude"]  // Only disabled for Claude, enabled for Gemini
  }
}
```

**Key Methods Updated:**
- `disable_server()` - Now tracks which client(s) the server is disabled for
- `enable_server()` - Can re-enable for specific clients while keeping disabled for others
- `list_all_servers()` - Returns disabled servers relevant to the requested mode
- `delete_server()` - Handles per-client deletion from disabled storage
- `update_server_config()` - Preserves per-client state when updating configs

**Backward Compatibility:**
- Old format automatically migrated on load: `{"server": {...config}}` → `{"server": {"config": {...}, "disabled_for": ["claude", "gemini"]}}`
- Migration assumes servers were disabled for both clients (preserves existing behavior)
- No manual intervention required - existing disabled_servers.json files will be migrated transparently

### Phase 2: Core Server Management Logic
**Goal**: Update backend to handle per-LLM server states

#### Task 2.1: Refactor ServerManager Core Methods ✅
**File**: `src/mcp_config_manager/core/server_manager.py`
- [x] Update `disable_server()` to handle per-client disabling
- [x] Update `enable_server()` to handle per-client enabling
- [x] Implement new storage format in `save_disabled_servers()`
- [x] Add migration logic in `load_disabled_servers()` for backward compatibility
- [x] Update `list_all_servers()` to be aware of per-client states
- [x] Update `delete_server()` for per-client deletion
- [x] Update `update_server_config()` to preserve per-client states
- [x] Update `get_enabled_servers()` to return per-client states
- [x] Keep 'mode' parameter for backward compatibility (not renamed to 'client')

**Implementation Notes:**
- `get_enabled_servers()` now returns servers with `claude_enabled` and `gemini_enabled` boolean flags
- `list_all_servers()` returns lists of dicts (not strings) with per-client state info
- Methods continue to use 'mode' parameter for backward compatibility
- All changes tested and working correctly

#### Task 2.2: Update Bulk Operations ✅
**File**: `src/mcp_config_manager/core/server_manager.py`
- [x] Add `bulk_enable_for_client(client: str, server_names: List[str])`
- [x] Add `bulk_disable_for_client(client: str, server_names: List[str])`
- [x] Update `list_all_servers()` to return per-client states
- [x] Add `sync_server_states()` for synchronizing between Claude/Gemini

**New Methods Added:**
- `bulk_enable_for_client()` - Enable multiple servers for a specific client
- `bulk_disable_for_client()` - Disable multiple servers for a specific client
- `sync_server_states()` - Copy server states from one client to another
- All methods handle missing configs gracefully and maintain data integrity

### Phase 3: GUI Controller Updates
**Goal**: Bridge the new data model with UI components

#### Task 3.1: Refactor ServerController ✅
**File**: `src/mcp_config_manager/gui/controllers/server_controller.py`
- [x] Added `set_server_enabled(server_name: str, client: str, enabled: bool)` for per-client control
- [x] Updated `get_servers()` to return unified rows with `claude_enabled` and `gemini_enabled` flags
- [x] Updated `bulk_operation()` to accept optional `client` parameter (backward compatible with `mode`)
- [x] Modified bulk operations to use new `bulk_enable_for_client()` and `bulk_disable_for_client()` methods
- [x] Added `get_server_states()` returning dict with per-client states
- [x] Kept `toggle_server()` for backward compatibility but internally uses per-client logic
- [x] Updated callbacks to include both `mode` (legacy) and `client` (new) fields

**Implementation Notes:**
- `set_server_enabled()` is the new primary method for toggling server state per client
- `get_servers()` now properly handles the new disabled server format with `disabled_for` array
- Bulk operations intelligently use per-client methods when targeting specific clients
- All methods maintain backward compatibility while supporting per-client operations

#### Task 3.2: Simplify ConfigController ✅
**File**: `src/mcp_config_manager/gui/controllers/config_controller.py`
- [x] Removed `current_mode` property and all mode state tracking
- [x] Updated `load_config()` to always load both Claude and Gemini configs
- [x] Modified `save_config()` to accept optional `client` parameter for targeted saves
- [x] Updated `validate_configuration()` to always validate both configs and return per-client results
- [x] Removed `change_mode()` method entirely - no longer needed
- [x] Updated `_get_server_list()` to return servers with `claude_enabled` and `gemini_enabled` flags
- [x] Replaced debug print statements with proper logger.debug() calls

**Implementation Notes:**
- ConfigController now treats both configs equally and always loads both
- The returned server list includes per-client enablement states
- Validation returns structured results for each client separately
- All mode-dependent logic has been removed

#### Task 3.3: Update Other Controllers ✅
**Files**: `preset_controller.py`, `backup_controller.py`
- [x] Remove mode parameters from preset operations
- [x] Update backup/restore to handle new state format
- [x] Ensure presets can specify per-client enablement

**Implementation Notes:**
- `PresetController` now accepts `client` parameter instead of `mode` for backward compatibility
- `load_preset()` can return per-client data when available in preset
- `save_preset()` supports new `save_per_client` flag to save per-client states
- Preset list now includes `claude_servers` and `gemini_servers` fields
- `BackupController` enhanced to detect and handle new disabled_servers format
- Backup info now includes per-client server counts (`claude_count`, `gemini_count`)
- `restore_backup()` properly handles per-client states in new format
- Both controllers maintain backward compatibility with existing code

### Phase 4: UI Components - Server List
**Goal**: Implement the dual checkbox column interface

#### Task 4.1: Redesign ServerListWidget (Qt) ✅
**File**: `src/mcp_config_manager/gui/widgets/server_list.py`
- [x] Change columns from `["☐ All", "Server", "Status", "Mode"]` to `["Claude", "Gemini", "Server", "Status"]`
- [x] Add checkbox in column 0 for Claude
- [x] Add checkbox in column 1 for Gemini
- [x] Update `_on_item_changed()` to detect which column changed
- [x] Emit `server_toggled` with client parameter: `server_toggled.emit(name, 'claude', enabled)`
- [x] Remove single master checkbox logic, add per-column master checkboxes
- [x] Add per-column header checkboxes for bulk operations
- [x] Update context menu for per-client operations

**Implementation Details:**
- Signals now include client parameter: `server_toggled.emit(server_name, client, enabled)`
- Separate master checkbox states for Claude (`claude_master_state`) and Gemini (`gemini_master_state`)
- Column 0 = Claude checkbox, Column 1 = Gemini checkbox
- Header clicks on Claude/Gemini columns toggle all checkboxes for that client
- Context menu includes per-client and "both" options
- `_toggle_server()` method now accepts optional `client` parameter
- Backward compatibility maintained for callbacks without client parameter

#### Task 4.2: Update ServerListWidget (Tkinter) ✅
**File**: `src/mcp_config_manager/gui/widgets/server_list.py` (Tkinter section)
- [x] Mirror Qt changes for Tkinter implementation
- [x] Update treeview columns to `("claude", "gemini", "server", "status")`
- [x] Handle checkbox rendering in Tkinter using ✓ marks
- [x] Update event bindings for dual checkboxes

**Implementation Details:**
- Column structure: Claude (✓/empty), Gemini (✓/empty), Server name, Status
- Context menu supports per-client enable/disable and "both" operations
- Double-click toggles both clients simultaneously
- Server name column index updated from 1 to 2 to account for dual checkboxes
- All tkinter event handlers updated to work with new column structure

### Phase 5: Main Window Integration
**Goal**: Remove mode selector and integrate new server list behavior

#### Task 5.1: Remove Mode Selector ✅
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Remove ModeSelectorWidget initialization (lines 183-188)
- [x] Remove mode selector from layout
- [x] Delete mode switching keyboard shortcuts (Ctrl+1/2/3)
- [x] Remove mode_changed event handlers
- [x] Clean up mode-related imports

#### Task 5.2: Update Event Handlers ✅
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Update `_on_server_toggled()` to accept client parameter
- [x] Remove all `app_state.mode` references
- [x] Update `refresh_server_list()` to work without mode
- [x] Modify status messages to reflect per-client operations
- [x] Update save/load to handle dual states

#### Task 5.3: Clean Up Mode Dependencies ✅
- [x] Remove mode selector widget file entirely
- [x] Update toolbar to remove mode-related elements
- [x] Simplify menu items that referenced modes
- [x] Update keyboard shortcuts documentation

### Phase 6: Dialogs and Detail Panels ✅ COMPLETE
**Goal**: Ensure all editing interfaces support per-client enablement

#### Task 6.1: Update ServerDetailsPanel ✅
**File**: `src/mcp_config_manager/gui/widgets/server_details_panel.py`
- [x] Add checkboxes showing "Enabled for: ☑ Claude ☑ Gemini"
- [x] Allow toggling per-client enablement from details
- [x] Show which clients use the current config
- [x] Update save to preserve per-client states

**Implementation Notes:**
- Added Claude and Gemini checkboxes in header section for both Qt and Tkinter
- Checkboxes trigger `_on_client_enablement_changed()` handler
- `load_server()` method now accepts `claude_enabled` and `gemini_enabled` parameters
- Client enablement changes marked as unsaved changes with orange indicators
- Added `client_enablement_changed_callbacks` for external components to track state

#### Task 6.2: Update Add Server Dialog ✅
**File**: `src/mcp_config_manager/gui/dialogs/add_server_dialog.py`
- [x] Add checkboxes for "Enable for: ☑ Claude ☑ Gemini"
- [x] Default both to checked for new servers
- [x] Pass client states to controller when adding

**Implementation Notes:**
- Added client enablement checkboxes (default to enabled for both)
- Result dictionary includes `_client_enablement` key with claude/gemini flags
- Both Qt and Tkinter implementations updated
- Checkboxes placed between JSON input and validation status

#### Task 6.3: Update Delete Dialog ✅
**File**: `src/mcp_config_manager/gui/dialogs/delete_servers_dialog.py`
- [x] Show which clients each server is enabled for
- [x] Allow selective deletion per client
- [x] Update confirmation messages

**Implementation Notes:**
- Server list now displays "(Enabled for: Claude, Gemini)" or "(Disabled)" status
- Added "Delete from:" checkboxes to select which clients to delete from
- Confirmation dialog shows which clients will be affected
- `get_client_selections()` method returns per-server client deletion flags
- Both Qt and Tkinter implementations updated

### Phase 7: Testing and Validation
**Goal**: Ensure all functionality works correctly

#### Task 7.1: Update Existing Tests ⬜
**Directory**: `tests/`
- [ ] Remove/update mode switching tests
- [ ] Update toggle workflow tests
- [ ] Fix any tests that assume single enabled state
- [ ] Update integration tests

#### Task 7.2: Add New Test Coverage ⬜
- [ ] Test enabling server for Claude only
- [ ] Test enabling server for Gemini only
- [ ] Test enabling for both simultaneously
- [ ] Test disabling for one while enabled for other
- [ ] Test migration from old format
- [ ] Test bulk operations per client
- [ ] Test save/load persistence

### Phase 8: Documentation and Cleanup
**Goal**: Update all documentation and clean up deprecated code

#### Task 8.1: Update Documentation ⬜
- [ ] Update README.md with new UI description
- [ ] Update CLAUDE.md with architectural changes
- [ ] Add migration guide for users
- [ ] Update screenshots if needed

#### Task 8.2: Code Cleanup ⬜
- [ ] Remove all deprecated mode-related code
- [ ] Remove backward compatibility code from _on_server_toggled() (accept only 3-arg signature)
- [ ] Remove 'mode' parameter support from all controllers (use only 'client')
- [ ] Remove legacy `active_servers` and `disabled_servers` lists from ApplicationState
- [ ] Remove Mode enum completely from app_state.py
- [ ] Remove all mode-to-client conversion code in controllers
- [ ] Clean up unused imports
- [ ] Run linters and formatters
- [ ] Verify no mode references remain

## Implementation Order
1. **Foundation First**: Complete Phase 1 (Data Models) entirely
2. **Backend Logic**: Complete Phase 2 (Server Management)
3. **Controllers**: Complete Phase 3 (Bridge Layer)
4. **UI Updates**: Phases 4-6 can be done in parallel
5. **Testing**: Phase 7 after UI is complete
6. **Polish**: Phase 8 cleanup and documentation

## Success Criteria
- [ ] Users can enable/disable servers independently for Claude and Gemini
- [ ] No mode selector visible in UI
- [ ] Two checkbox columns clearly show server states
- [ ] All existing functionality preserved
- [ ] Backward compatible with existing configs
- [ ] Tests pass
- [ ] Documentation updated

## Rollback Plan
If issues arise:
1. Git revert to master branch
2. Configs are backward compatible, no data loss
3. Can be deployed incrementally if needed

### Phase 9: Add Refresh Functionality for Live Configuration Reloading
**Goal**: Enable users to refresh the server list from JSON files without restarting the application

**Current Progress (Session 19):**
- ✅ Tasks 9.1-9.8 completed (80% of Phase 9)
- Core reload functionality fully implemented with comprehensive edge case handling
- Server Controller now supports force_reload parameter and cache clearing
- Enhanced conflict detection and resolution for external changes
- Detailed notifications for added/removed/modified servers
- JSON error handling with user-friendly messages
- ServerDetailsPanel now handles refresh with conflict resolution
- Visual feedback implemented with color-coded highlights for changes
- Remaining: Testing (9.9) and Performance optimization (9.10)

#### Task 9.1: Create Core Reload Method in MainWindow ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Create `reload_servers_from_disk()` method (line 926) that:
  - Checks for unsaved changes and prompts user to confirm if present
  - Sets status message "Refreshing servers from disk..."
  - Calls `config_controller.reload_config()` to force fresh read
  - Preserves current server selection if it still exists
  - Updates server list widget with new data
  - Shows success message with server count
  - Handles errors gracefully with status messages
- [x] Add state preservation during reload:
  - Save current selected server(s)
  - Restore selection after reload if server still exists
  - Clear details panel if selected server was removed
  - Show warning message if selected server no longer exists

**Implementation Notes:**
- Method added at line 926-1017
- Uses QMessageBox for Qt and tkinter messagebox for confirmations
- Emits CONFIG_LOADED event to update all components
- Clears unsaved changes flag after successful reload
- Shows server count in success message with checkmark emoji

#### Task 9.2: Add Refresh Button to Toolbar ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Qt Toolbar (line 404-409):
  - Added `QPushButton("🔄 Refresh")` after Save button
  - Applied consistent `button_style` styling
  - Set tooltip: "Reload server configurations from disk (F5)"
  - Connected clicked signal to `reload_servers_from_disk()`
- [x] Tkinter Toolbar (line 467-469):
  - Added `ttk.Button(text="Refresh")` after Save button
  - Bound command to `reload_servers_from_disk()`
  - Positioned between Save and separator

**Implementation Notes:**
- Qt button uses 🔄 emoji icon for visual consistency
- Tooltip mentions F5 keyboard shortcut
- Tkinter version uses plain text due to limited styling options

#### Task 9.3: Update Menu and Keyboard Shortcuts ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Add to File menu (Qt: line 235-238, Tk: line 317):
  - Created "Refresh Servers" QAction with F5 shortcut
  - Added to File menu after Save, before separator
  - Tkinter version shows "F5" as accelerator text
- [x] Update keyboard shortcuts (line 604 & 611 for Qt, 622 & 629 for Tk):
  - Redirected F5 to call `reload_servers_from_disk()` instead of `refresh_server_list()`
  - Updated Ctrl+R shortcut binding to use `reload_servers_from_disk()`
  - Both Qt and Tkinter key bindings now properly trigger full reload from disk

**Implementation Notes (Session 17):**
- Changed Qt shortcuts at lines 604 and 611 from `self.refresh_server_list` to `self.reload_servers_from_disk`
- Changed Tkinter bindings at lines 622 and 629 from `self.refresh_server_list()` to `self.reload_servers_from_disk()`
- These shortcuts now trigger a complete refresh from disk files rather than just updating the UI

#### Task 9.4: Enhance Config Controller for Force Reload ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/controllers/config_controller.py`
- [x] Add `reload_config()` method that:
  - Clears any cached configuration data
  - Forces ConfigManager to re-read from disk
  - Reloads both Claude and Gemini JSON files
  - Reloads disabled_servers.json
  - Returns fresh server list with per-client states
  - Emits appropriate events for UI updates
- [x] Add `force_reload` parameter to existing `load_config()` method
- [x] Ensure no stale data remains after reload

**Implementation Notes (Session 17):**
- Added `force_reload` parameter to `load_config()` method at line 24
- When `force_reload=True`, clears cached configs (`_claude_config`, `_gemini_config`) at lines 40-44
- Also clears disabled_servers cache in server_manager
- Added new `reload_config()` method at line 82 that calls `load_config(force_reload=True)`
- Debug logging indicates when a forced reload occurs
- All callbacks are properly triggered after reload for UI updates

#### Task 9.5: Update Server Controller for Fresh Data ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/controllers/server_controller.py`
- [x] Add `force_reload` parameter to `get_servers()` method
- [x] When force_reload=True:
  - Bypass any cached server data
  - Force fresh read of disabled_servers.json
  - Ensure all server states are current
- [x] Add method to clear internal caches if any exist

**Implementation Notes (Session 18):**
- Added `force_reload` parameter to `get_servers()` method at line 28
- When `force_reload=True`, clears all caches in server_manager and config_manager
- Added new `clear_caches()` method at line 877 for explicit cache clearing
- Updated `refresh_server_list()` in main_window.py to accept and pass force_reload parameter
- All cache clearing properly handles both server_manager and config_manager internal caches

#### Task 9.6: Handle Edge Cases and Conflicts ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Handle server deletion scenarios:
  - If selected server was deleted externally, clear details panel
  - Show notification about deleted servers
- [x] Handle server addition scenarios:
  - Add new servers to list with appropriate states
  - Optionally auto-select newly added servers
- [x] Handle configuration changes:
  - If server config changed externally while being edited, show conflict dialog
  - Offer options: Keep GUI changes, Accept file changes, Merge
- [x] Handle JSON errors:
  - If JSON becomes invalid, show error dialog
  - Keep current state and offer to fix or ignore

**Implementation Notes (Session 18):**
- Enhanced `reload_servers_from_disk()` method at line 947 with comprehensive edge case handling
- Added detection for added, removed, and modified servers during refresh
- Shows specific notifications for deleted servers (line 1064) and modified servers (line 1073)
- Handles unsaved changes in both general state and details panel separately
- Saves server state before reload for comparison and conflict detection
- Provides detailed status messages showing count of added/removed/modified servers
- Special handling for JSON parse errors with helpful error messages (line 1100)
- Automatically clears details panel when selected server is deleted
- Restores server selection after reload if server still exists
- Notifies about newly added servers if only a few were added (line 1091)

#### Task 9.7: Update Server Details Panel ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/widgets/server_details_panel.py`
- [x] Add `refresh_current_server()` method to reload from disk (line 748)
- [x] Handle case where current server no longer exists
- [x] Preserve or warn about unsaved field changes with conflict resolution dialog
- [x] Clear cache if server configuration cached locally (clear_cache method added)

**Implementation Notes (Session 19):**
- Added `refresh_current_server()` method at line 748 that handles:
  - Server deletion detection (shows warning if unsaved changes will be lost)
  - Configuration change detection with JSON comparison
  - Client enablement state change detection
  - Conflict resolution dialog when external changes conflict with unsaved changes
  - Options to keep local changes or accept external changes
- Added `clear_cache()` method for future caching implementations
- Integrated with main window's reload_servers_from_disk method

#### Task 9.8: Add Visual Feedback ✅ COMPLETE
**Files**: `src/mcp_config_manager/gui/widgets/server_list.py`, `src/mcp_config_manager/gui/main_window.py`
- [x] Show loading indicator during refresh (status bar shows "🔄 Refreshing...")
- [x] Highlight newly added servers temporarily (green background for 3 seconds)
- [x] Mark modified servers if their config changed (orange background for 3 seconds)
- [x] Show removed servers briefly before removing (red flash with strikethrough for 1 second)
- [x] Display refresh timestamp in status bar (shows "Refreshed at HH:MM:SS")

**Implementation Notes (Session 19):**
- Added to ServerListWidget (line 766):
  - `highlight_new_servers()` - Green background (#C8FFC8) for 3 seconds
  - `mark_modified_servers()` - Orange background (#FFEBC8) for 3 seconds
  - `flash_removed_servers()` - Red background (#FFC8C8) with strikethrough for 1 second
  - Auto-clearing of highlights with QTimer/after() scheduling
- Updated main_window.py (line 949, 1056-1071):
  - Added loading indicator at start of refresh
  - Added timestamp to completion message
  - Integrated visual feedback methods after successful refresh
- Both Qt and Tkinter versions implemented

#### Task 9.9: Testing and Documentation ⬜
- [ ] Create unit tests for reload functionality
- [ ] Test scenarios:
  - Add server to JSON while GUI running
  - Remove server from JSON while GUI running
  - Modify server config in JSON while GUI running
  - Corrupt JSON and verify error handling
  - Rapid refresh button clicks (no race conditions)
  - Refresh with unsaved changes in GUI
- [ ] Update README with refresh feature description
- [ ] Add tooltip help for refresh button
- [ ] Document in help dialog (F1)

#### Task 9.10: Optimize Performance ⬜
- [ ] Implement differential updates (only update changed servers)
- [ ] Add debouncing for rapid refresh clicks
- [ ] Consider file watching for auto-refresh option (future enhancement)
- [ ] Cache file modification times to detect actual changes
- [ ] Show "No changes detected" if files haven't changed

## Phase 10: Project-Specific MCP Server Discovery and Management
**Goal**: Enable discovery of MCP servers defined in project-specific Claude configurations and offer to promote them to the global configuration

**Current Progress (split-servers branch - Session Current):**
- ✅ Task 10.1: Extended Claude Parser with project discovery methods
- ✅ Task 10.2: Created ProjectDiscoveryService for scanning and caching
- ✅ Task 10.3: Updated Server Manager for Project Awareness
- ✅ Task 10.4: Created Project Server Discovery Dialog
- ✅ Task 10.5: Updated Server List Widget for Project Attribution
- ✅ Task 10.6: Added Discovery Menu Items and Toolbar
- ⬜ Tasks 10.7-10.10: Remaining consolidation wizard, CLI commands, testing, and advanced features

**Key Accomplishments This Session:**
- **Backend Support (Tasks 10.1-10.4):**
  - ServerManager now has full project server awareness with methods for:
    - Discovering project servers via `get_project_servers()`
    - Promoting individual servers with `promote_project_server()`
    - Handling duplicates with `merge_duplicate_servers()` using multiple strategies
    - Bulk consolidation with `consolidate_servers()`
    - Extended `list_all_servers()` to optionally include project servers with location attribution
  - Created comprehensive Project Server Discovery Dialog with:
    - Tree view showing projects and their servers
    - Visual duplicate detection and indication
    - Configuration preview panel
    - Conflict resolution strategies (skip/replace/rename)
    - Background discovery with progress reporting (Qt version)
    - Full promotion workflow implementation

- **UI Integration (Tasks 10.5-10.6):**
  - Server List Widget enhancements:
    - Added "Location" column displaying "Global" or project folder name
    - Project servers shown with 📁 icon and light blue background
    - Tooltips show full project paths on hover
    - "Promote to Global" context menu option for project servers
    - server_promoted signal for handling promotion requests
  - Main Window integration:
    - Added "Discover Project Servers..." to Tools menu (Ctrl+D)
    - Added 🔍 Discover toolbar button for quick access
    - Status bar shows project server counts when present
    - Integrated promotion handler to call ServerManager
    - Graceful fallback if discovery dialog not available

### Background
Claude Desktop supports project-specific `.claude.json` files that can define MCP servers under project paths (e.g., `/Users/username/Projects/my-project`). These servers are only available when Claude is opened within that project directory. This phase adds functionality to:
1. Discover all project-specific MCP servers across the file system
2. Display them in the GUI with clear project attribution
3. Offer to "promote" project servers to the global configuration
4. Handle conflicts when server names exist in multiple locations

### Task 10.1: Extend Claude Parser for Project Discovery ✅ COMPLETE
**File**: `src/mcp_config_manager/parsers/claude_parser.py`
- [x] Add `discover_project_servers()` method to scan for project-specific servers
- [x] Add `get_server_location(server_name)` to identify if server is global or project-specific
- [x] Add `promote_to_global(server_name, project_path)` to move server to global config
- [x] Add `get_all_server_locations()` returning map of server -> [global, project1, project2, ...]
- [x] Handle server name conflicts (same name in multiple projects)
- [x] Add `scan_for_project_configs()` to find .claude.json files in filesystem

**Implementation Notes (Session - pull-projects-json branch):**
- Added comprehensive project discovery methods to ClaudeConfigParser (lines 159-353)
- `discover_project_servers()` returns dict mapping project paths to server configs
- `get_server_location()` returns None for global, project path for project-specific
- `promote_to_global()` moves server from project to global with cleanup
- `get_all_server_locations()` maps server names to all their locations
- `scan_for_project_configs()` recursively finds .claude.json files with max depth control
- All methods include proper error handling and logging

### Task 10.2: Create Project Server Discovery Service ✅ COMPLETE
**File**: `src/mcp_config_manager/core/project_discovery.py` (new)
- [x] Create `ProjectDiscoveryService` class
- [x] Add `scan_projects()` method to find all project paths with MCP servers
- [x] Add caching mechanism to avoid repeated scans
- [x] Add background scanning capability with progress reporting
- [x] Create `ProjectServer` dataclass with fields:
  - `name: str`
  - `project_path: Path`
  - `config: Dict[str, Any]`
  - `is_duplicate: bool` (if name exists elsewhere)
  - `discovered_at: datetime` (timestamp of discovery)

**Implementation Notes (Session - pull-projects-json branch):**
- Created comprehensive ProjectDiscoveryService class (381 lines)
- `ProjectServer` dataclass includes all required fields plus discovery timestamp
- `scan_projects()` supports:
  - Multiple base paths with sensible defaults (Projects, Documents/Projects, Code, etc.)
  - Configurable max depth for directory traversal
  - 5-minute cache duration to avoid repeated filesystem scans
  - Progress callback for UI updates during scanning
  - Automatic duplicate detection across projects
- `scan_projects_async()` enables background scanning with callback
- Additional utility methods:
  - `get_project_servers_by_name()` - Find all instances of a server
  - `get_duplicate_servers()` - Get servers appearing in multiple projects
  - `export_discovery_report()` - Generate JSON report of discoveries
- Thread-safe implementation with scan lock
- Comprehensive error handling and logging throughout

### Task 10.3: Update Server Manager for Project Awareness ✅ COMPLETE
**File**: `src/mcp_config_manager/core/server_manager.py`
- [x] Add `get_project_servers()` method
- [x] Add `promote_project_server(server_name, from_project, to_global=True)`
- [x] Add `merge_duplicate_servers(server_name, strategy='keep_global'|'keep_project'|'merge')`
- [x] Update `list_all_servers()` to include project attribution
- [x] Add `consolidate_servers()` to move all project servers to global

**Implementation Notes (Session - Current):**
- Added comprehensive project awareness methods to ServerManager class
- `get_project_servers()` creates and uses ProjectDiscoveryService for scanning
- `promote_project_server()` moves servers from project to global with optional removal from project
- `merge_duplicate_servers()` handles three strategies: keep_global, keep_project, or merge
- `list_all_servers()` now accepts `include_project_servers` parameter and adds location field
- `consolidate_servers()` bulk promotes all project servers with conflict resolution
- All methods include proper error handling and logging

### Task 10.4: Create Project Server Discovery Dialog ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/dialogs/discover_servers_dialog.py` (new)
- [x] Create dialog showing discovered project servers
- [x] Display as tree: Project Path -> Server Name -> Config Preview
- [x] Add checkboxes to select servers for promotion
- [x] Show conflicts/duplicates with visual indicators
- [x] Add "Promote Selected" and "Promote All" buttons
- [x] Include conflict resolution options (replace, skip, rename)

**Implementation Notes (Session - Current):**
- Created comprehensive discovery dialog for both Qt and Tkinter
- Qt version uses QThread for background discovery with progress reporting
- Tree view shows projects as parent nodes with servers as children
- Visual indicators: ✅ for unique servers, ⚠️ for duplicates
- Configuration preview panel shows JSON config when server selected
- Three conflict resolution strategies: skip, replace, or rename with project suffix
- Promote operations integrate with ServerController when available
- Both "Promote Selected" and "Promote All" buttons implemented
- Refresh capability to re-scan projects

### Task 10.5: Update Server List Widget for Project Attribution ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/widgets/server_list.py`
- [x] Add "Location" column showing "Global" or project path
- [x] Add icon or color coding for project servers (📁 icon, light blue background)
- [x] Add tooltip showing full project path for project servers
- [x] Add context menu option "Promote to Global" for project servers
- [x] Added server_promoted signal for handling promotions
- [x] Add filter/group by location functionality ✅ COMPLETE

**Implementation Notes (Session - Current):**
- Added Location column to both Qt and Tkinter versions
- Project servers show with 📁 icon and shortened path (just project folder name)
- Light blue background (#E6F0FF) for project servers
- Full project path shown in tooltip on hover
- "Promote to Global" context menu option appears only for project servers
- server_promoted signal emitted when promotion requested
- **Filter/Group functionality added:**
  - Search box for filtering servers by name
  - Location dropdown to filter by Global/Project/All
  - "Group by Location" checkbox to organize servers hierarchically
  - Groups show as collapsible sections with bold headers
  - Clear filters button to reset all filters
  - get_location_stats() method returns server counts by location

### Task 10.6: Add Discovery Menu Items and Toolbar ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/main_window.py`
- [x] Add "Tools" menu with "Discover Project Servers..." item
- [x] Add toolbar button for server discovery (🔍 Discover)
- [x] Add status bar indicator showing project server count in refresh
- [x] Added discover_project_servers() method to handle discovery dialog
- [x] Added _on_server_promoted() handler for promotion requests
- [ ] Add automatic discovery on startup (future enhancement)
- [ ] Add progress dialog for discovery process (handled in dialog itself)

**Implementation Notes (Session - Current):**
- Added "Discover Project Servers..." to Tools menu with Ctrl+D shortcut
- Added 🔍 Discover button to toolbar (Qt) and plain "Discover" button (Tkinter)
- Status bar shows server counts: "X servers loaded (Y global, Z project)"
- discover_project_servers() method opens DiscoverServersDialog
- _on_server_promoted() handler calls ServerManager.promote_project_server()
- Graceful fallback if dialog not available yet

### Task 10.7: Create Project Server Consolidation Wizard ✅ COMPLETE
**File**: `src/mcp_config_manager/gui/wizards/consolidation_wizard.py` (new)
- [x] Multi-step wizard for consolidating project servers:
  - Step 1: Scan and discover all project servers
  - Step 2: Review and resolve conflicts
  - Step 3: Select servers to promote
  - Step 4: Preview changes
  - Step 5: Apply changes with backup
- [x] Add undo capability after consolidation (via backups)
- [x] Generate consolidation report

**Implementation Notes (Session Current):**
- Created comprehensive ConsolidationWizard class for both Qt and Tkinter
- 5-step wizard flow with progress tracking and visual feedback
- Background scanning with QThread for Qt version
- Conflict resolution strategies: skip, replace, or rename with project suffix
- Automatic backup creation before applying changes
- Detailed logging and report generation
- ConsolidationPlan dataclass for managing consolidation actions
- Full error handling and user feedback throughout

### Task 10.8: Add CLI Commands for Project Discovery ✅ COMPLETE
**File**: `src/mcp_config_manager/cli.py`
- [x] Add `[discover]` command to scan for project servers
- [x] Add `[promote <server>]` to promote specific server
- [x] Add `[consolidate]` to move all project servers to global
- [x] Add `[list-projects]` to show all projects with MCP servers
- [x] Update help text with new commands

**Implementation Notes (Session Current):**
- Added comprehensive CLI commands in both interactive and click command modes
- Interactive mode commands:
  - `discover`: Scans and displays all project servers with promotion options
  - `promote <server>`: Finds and promotes specific server from projects
  - `consolidate`: Bulk promotion with conflict resolution strategies
  - `list-projects`: Shows all projects with MCP servers and export option
- Click CLI commands:
  - `mcp-config-manager discover`: Launch discovery interface
  - `mcp-config-manager promote <server> [--project PATH]`: Promote server
  - `mcp-config-manager consolidate [--strategy skip|replace|rename] [-y]`: Bulk consolidation
  - `mcp-config-manager list-projects [--export FILE]`: List and optionally export
- Full conflict handling with skip/replace/rename strategies
- Export capabilities for project discovery reports
- Integrated with ProjectDiscoveryService and ServerManager

### Task 10.9: Testing and Documentation ⬜
- [ ] Unit tests for project discovery service
- [ ] Integration tests for promotion workflow
- [ ] Test conflict resolution strategies
- [ ] Test performance with many projects
- [ ] Update README with project discovery feature
- [ ] Add user guide for consolidation workflow

### Task 10.10: Advanced Features (Future) ⬜
- [ ] Add project templates (copy project servers to new projects)
- [ ] Add project server inheritance (base + override configs)
- [ ] Add sync between projects (keep servers in sync)
- [ ] Add project profiles (different server sets per project type)
- [ ] Add export/import for project server configurations

## Success Criteria for Phase 10
- [ ] Can discover all MCP servers across all project directories
- [ ] Clear visual distinction between global and project servers
- [ ] Easy one-click promotion from project to global
- [ ] Intelligent conflict resolution for duplicate names
- [ ] No data loss during consolidation
- [ ] Performance acceptable even with many projects
- [ ] Full CLI support for headless operation

## Technical Considerations
1. **Performance**: Scanning many projects could be slow
   - Implement caching and incremental scanning
   - Use threading for background discovery
   - Add option to limit scan depth

2. **Conflicts**: Same server name in multiple locations
   - Clear UI to show conflicts
   - Multiple resolution strategies
   - Preview changes before applying

3. **Safety**: Don't lose project-specific configurations
   - Always backup before changes
   - Offer undo/rollback
   - Clear confirmation dialogs

4. **Usability**: Make discovery intuitive
   - Auto-discover on first launch
   - Visual indicators for project servers
   - Bulk operations for efficiency

## Notes
- Each task is designed to be < 100k tokens of work
- Tasks within a phase can often be parallelized
- Migration logic ensures no user data is lost
- UI changes are the most visible but depend on foundation work