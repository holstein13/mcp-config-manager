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

**Phase 5 Complete**: All tasks (5.1, 5.2, 5.3) are complete. The mode selector has been removed and the main window now uses per-client operations.

**Ready for Phase 6 (Dialogs and Detail Panels)**: With the main window updated, the next critical steps are:
1. ✅ ~~Update GUI controllers to use the new per-client model (Phase 3)~~ **COMPLETE**
2. ✅ ~~Implement the dual checkbox UI in server list (Tasks 4.1, 4.2)~~ **COMPLETE**
3. ✅ ~~Update main window to remove mode selector and integrate new server list behavior (Phase 5)~~ **COMPLETE**
4. Update dialogs and detail panels to support per-client enablement (Phase 6) - **NEXT**

The critical path continues: Phase 6 (Dialogs and Detail Panels) → Phase 7 (Testing) → Phase 8 (Cleanup)

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

### Phase 6: Dialogs and Detail Panels
**Goal**: Ensure all editing interfaces support per-client enablement

#### Task 6.1: Update ServerDetailsPanel ⬜
**File**: `src/mcp_config_manager/gui/widgets/server_details_panel.py`
- [ ] Add checkboxes showing "Enabled for: ☑ Claude ☑ Gemini"
- [ ] Allow toggling per-client enablement from details
- [ ] Show which clients use the current config
- [ ] Update save to preserve per-client states

#### Task 6.2: Update Add Server Dialog ⬜
**File**: `src/mcp_config_manager/gui/dialogs/add_server_dialog.py`
- [ ] Add checkboxes for "Enable for: ☑ Claude ☑ Gemini"
- [ ] Default both to checked for new servers
- [ ] Pass client states to controller when adding

#### Task 6.3: Update Delete Dialog ⬜
**File**: `src/mcp_config_manager/gui/dialogs/delete_servers_dialog.py`
- [ ] Show which clients each server is enabled for
- [ ] Allow selective deletion per client
- [ ] Update confirmation messages

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

## Notes
- Each task is designed to be < 100k tokens of work
- Tasks within a phase can often be parallelized
- Migration logic ensures no user data is lost
- UI changes are the most visible but depend on foundation work