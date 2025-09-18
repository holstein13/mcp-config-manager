# MCP Config Manager - Development Tasks

## Current Sprint: GUI Foundation

### High Priority Tasks

#### GUI-001: Framework Setup and Basic Window
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 4-6 hours
**Priority**: Critical

**Description**: Set up the GUI framework and create the basic application structure.

**Acceptance Criteria**:
- [ ] GUI framework selected and installed (PyQt6 recommended)
- [ ] Basic application window with proper title and icon
- [ ] Application can be launched from command line
- [ ] Window is properly sized and centered on screen
- [ ] Basic menu structure in place
- [ ] Integration with existing ConfigManager class

**Technical Details**:
- Create `src/mcp_config_manager/gui/main_window.py`
- Create `src/mcp_config_manager/gui/app.py` for application setup
- Update CLI to include `gui` command that actually works
- Ensure cross-platform compatibility (Windows, macOS, Linux)

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/main_window.py` (NEW)
- `src/mcp_config_manager/gui/app.py` (NEW)
- `src/mcp_config_manager/gui/__init__.py` (UPDATE)
- `src/mcp_config_manager/cli.py` (UPDATE gui command)
- `requirements.txt` (ADD GUI dependencies)

---

#### GUI-002: Server List Display
**Status**: 📋 Todo  
**Assignee**: TBD
**Estimate**: 6-8 hours
**Priority**: Critical
**Depends on**: GUI-001

**Description**: Create the main server list widget that displays active and disabled servers.

**Acceptance Criteria**:
- [ ] Server list widget displays all servers with status (✅/❌)
- [ ] Clear visual distinction between active and disabled servers
- [ ] List updates in real-time when servers are toggled
- [ ] Scrollable list for large numbers of servers
- [ ] Server names are clearly readable
- [ ] Status icons are intuitive and consistent

**Technical Details**:
- Use QListWidget or QTreeWidget for server display
- Implement custom item widgets for server display
- Integrate with ServerManager to get current status
- Add refresh functionality
- Handle empty server list gracefully

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/widgets/server_list.py` (NEW)
- `src/mcp_config_manager/gui/widgets/__init__.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

#### GUI-003: Enable/Disable Toggle Functionality
**Status**: 📋 Todo
**Assignee**: TBD  
**Estimate**: 4-6 hours
**Priority**: Critical
**Depends on**: GUI-002

**Description**: Implement server enable/disable functionality in the GUI.

**Acceptance Criteria**:
- [ ] Toggle switches or checkboxes for each server
- [ ] Clicking toggle immediately enables/disables server
- [ ] Visual feedback during toggle operation
- [ ] Error handling for failed toggle operations
- [ ] Confirmation for bulk operations
- [ ] Undo functionality for accidental toggles

**Technical Details**:
- Add toggle controls to server list items
- Connect toggle signals to ServerManager methods
- Implement progress indicators for operations
- Add error dialog for failed operations
- Consider batch operations for multiple selections

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/widgets/server_list.py` (UPDATE)
- `src/mcp_config_manager/gui/dialogs/error_dialog.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

#### GUI-004: Mode Selection Interface
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 3-4 hours  
**Priority**: High
**Depends on**: GUI-001

**Description**: Add interface for selecting CLI mode (Claude/Gemini/Both).

**Acceptance Criteria**:
- [ ] Radio buttons or dropdown for mode selection
- [ ] Current mode clearly displayed
- [ ] Mode change takes effect immediately
- [ ] Sync operation triggered when switching to "Both" mode
- [ ] Mode preference persisted between sessions
- [ ] Clear indication of what each mode does

**Technical Details**:
- Add mode selection widget to main window
- Integrate with ConfigManager mode handling
- Save mode preference to settings file
- Update server list when mode changes
- Show appropriate warnings for mode switches

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/widgets/mode_selector.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)
- `src/mcp_config_manager/utils/settings.py` (NEW)

---

### Medium Priority Tasks

#### GUI-005: Preset Management Interface
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 8-10 hours
**Priority**: Medium
**Depends on**: GUI-003

**Description**: Create interface for managing and applying presets.

**Acceptance Criteria**:
- [ ] Preset list with names and descriptions
- [ ] Apply preset button with confirmation
- [ ] Save current configuration as new preset
- [ ] Edit existing preset metadata
- [ ] Delete preset with confirmation
- [ ] Import/export preset functionality

**Technical Details**:
- Create preset management dialog
- Integrate with PresetManager class
- Add preset quick-access buttons (minimal, webdev, etc.)
- Implement preset validation
- Consider preset categories or tags

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/dialogs/preset_dialog.py` (NEW)
- `src/mcp_config_manager/gui/widgets/preset_toolbar.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

#### GUI-006: Add Server Dialog
**Status**: 📋 Todo  
**Assignee**: TBD
**Estimate**: 6-8 hours
**Priority**: Medium
**Depends on**: GUI-003

**Description**: Create dialog for adding new MCP servers via JSON paste.

**Acceptance Criteria**:
- [ ] Large text area for JSON pasting
- [ ] JSON syntax validation with error highlighting
- [ ] Server name input for single server configs
- [ ] Preview of parsed configuration
- [ ] Support for multiple JSON formats
- [ ] Clear error messages for invalid JSON

**Technical Details**:
- Create modal dialog with JSON text editor
- Implement JSON syntax highlighting if possible
- Add real-time validation feedback
- Integrate with ServerManager.add_server_from_json
- Consider JSON formatting/beautification

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/dialogs/add_server_dialog.py` (NEW)
- `src/mcp_config_manager/gui/widgets/json_editor.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

#### GUI-007: Settings and Preferences
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 4-6 hours
**Priority**: Medium
**Depends on**: GUI-004

**Description**: Create settings dialog for application preferences.

**Acceptance Criteria**:
- [ ] Settings dialog accessible from menu
- [ ] File path preferences (config locations)
- [ ] Backup preferences (retention, location)
- [ ] UI preferences (theme, size, etc.)
- [ ] Default mode selection
- [ ] Auto-backup frequency settings

**Technical Details**:
- Create settings dialog with tabbed interface
- Implement settings persistence
- Add file browser for path selection
- Validate setting values
- Apply settings without restart where possible

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/dialogs/settings_dialog.py` (NEW)
- `src/mcp_config_manager/utils/settings.py` (UPDATE)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

### Low Priority Tasks

#### GUI-008: Menu System and Shortcuts
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 3-4 hours
**Priority**: Low
**Depends on**: GUI-001

**Description**: Implement comprehensive menu system with keyboard shortcuts.

**Acceptance Criteria**:
- [ ] File menu (Open, Save, Exit, etc.)
- [ ] Edit menu (Undo, Redo, Select All, etc.)
- [ ] Tools menu (Validate, Backup, etc.)
- [ ] Help menu (About, Documentation, etc.)
- [ ] Keyboard shortcuts for common actions
- [ ] Context menus for server list items

**Technical Details**:
- Create menu bar with standard menus
- Add keyboard shortcuts (Ctrl+S, Ctrl+O, etc.)
- Implement context-sensitive menus
- Add status bar for feedback
- Ensure cross-platform menu behavior

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)
- `src/mcp_config_manager/gui/menus/main_menu.py` (NEW)

---

#### GUI-009: Help System and Tooltips
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 4-5 hours
**Priority**: Low
**Depends on**: GUI-008

**Description**: Add comprehensive help system and tooltips.

**Acceptance Criteria**:
- [ ] Tooltips for all UI elements
- [ ] Help dialog with usage instructions
- [ ] About dialog with version info
- [ ] Quick start guide accessible from UI
- [ ] Context-sensitive help
- [ ] Links to online documentation

**Technical Details**:
- Add tooltips to all interactive elements
- Create help dialog with searchable content
- Implement about dialog with system info
- Consider integrated help browser
- Add "What's This?" help mode

**Files to Create/Modify**:
- `src/mcp_config_manager/gui/dialogs/help_dialog.py` (NEW)
- `src/mcp_config_manager/gui/dialogs/about_dialog.py` (NEW)
- `src/mcp_config_manager/gui/main_window.py` (UPDATE)

---

## Future Phase Tasks

### Health Monitoring Tasks

#### HEALTH-001: Server Health Checking
**Status**: 📋 Backlog
**Estimate**: 12-15 hours
**Priority**: Medium

**Description**: Implement health checking for MCP servers.

**Acceptance Criteria**:
- [ ] Ping servers to check connectivity
- [ ] Display connection status in server list
- [ ] Health check scheduling and background operation
- [ ] Error reporting for failed connections
- [ ] Performance metrics collection

---

#### HEALTH-002: Health Dashboard
**Status**: 📋 Backlog  
**Estimate**: 8-10 hours
**Priority**: Medium
**Depends on**: HEALTH-001

**Description**: Create visual dashboard for server health.

**Acceptance Criteria**:
- [ ] Visual status indicators (green/yellow/red)
- [ ] Response time graphs
- [ ] Error logs and history
- [ ] Health trends over time
- [ ] Troubleshooting suggestions

---

### Server Discovery Tasks

#### DISCOVERY-001: NPM Package Discovery
**Status**: 📋 Backlog
**Estimate**: 10-12 hours  
**Priority**: Low

**Description**: Discover MCP servers from NPM registry.

**Acceptance Criteria**:
- [ ] Search npmjs.org for MCP packages
- [ ] Parse package metadata
- [ ] Suggest installation commands
- [ ] Filter by popularity and maintenance
- [ ] Cache discovery results

---

#### DISCOVERY-002: Local Installation Detection
**Status**: 📋 Backlog
**Estimate**: 8-10 hours
**Priority**: Low

**Description**: Detect locally installed MCP servers.

**Acceptance Criteria**:
- [ ] Scan for NPM packages with MCP capabilities
- [ ] Detect Python MCP servers
- [ ] Suggest configurations for detected servers
- [ ] Handle multiple installation locations
- [ ] Validate detected servers

---

## Testing Tasks

#### TEST-001: GUI Integration Tests
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 6-8 hours
**Priority**: High
**Depends on**: GUI-003

**Description**: Create integration tests for GUI functionality.

**Acceptance Criteria**:
- [ ] Test server list display and updates
- [ ] Test enable/disable operations
- [ ] Test mode switching
- [ ] Test error handling
- [ ] Cross-platform testing

**Technical Details**:
- Use pytest-qt for GUI testing
- Create test fixtures for sample configurations
- Mock file operations for safety
- Test error conditions and edge cases

**Files to Create/Modify**:
- `tests/test_gui_integration.py` (NEW)
- `tests/fixtures/gui_fixtures.py` (NEW)

---

#### TEST-002: End-to-End Testing
**Status**: 📋 Todo
**Assignee**: TBD  
**Estimate**: 4-6 hours
**Priority**: Medium
**Depends on**: TEST-001

**Description**: Create end-to-end tests for complete workflows.

**Acceptance Criteria**:
- [ ] Test complete server management workflows
- [ ] Test preset save/load workflows
- [ ] Test configuration sync workflows
- [ ] Test backup and restore workflows
- [ ] Performance testing with large configs

---

## Documentation Tasks

#### DOC-001: GUI User Guide
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 4-6 hours
**Priority**: Medium
**Depends on**: GUI-006

**Description**: Create comprehensive user guide for GUI.

**Acceptance Criteria**:
- [ ] Screenshot walkthrough of main features
- [ ] Step-by-step tutorials for common tasks
- [ ] Troubleshooting section
- [ ] Migration guide from CLI
- [ ] Video tutorials for complex features

---

#### DOC-002: Developer Documentation
**Status**: 📋 Todo
**Assignee**: TBD
**Estimate**: 3-4 hours
**Priority**: Low

**Description**: Document GUI architecture for contributors.

**Acceptance Criteria**:
- [ ] GUI architecture overview
- [ ] Widget documentation
- [ ] Styling and theming guide
- [ ] Testing guidelines for GUI
- [ ] Cross-platform considerations

---

## Task Management

### Status Legend
- 📋 Todo - Not started
- 🔄 In Progress - Currently being worked on
- ✅ Done - Completed and tested
- ❌ Blocked - Cannot proceed due to dependencies
- 🔍 Review - Completed, awaiting review

### Priority Levels
- **Critical**: Must be completed for basic functionality
- **High**: Important for user experience
- **Medium**: Nice to have, enhances functionality
- **Low**: Future enhancements, not essential

### Estimation Guidelines
- **1-2 hours**: Simple bug fixes, minor enhancements
- **3-4 hours**: Small features, simple dialogs
- **6-8 hours**: Medium features, complex widgets
- **10+ hours**: Major features, complex integrations

### Assignment Process
1. Review task dependencies
2. Ensure all prerequisites are met
3. Estimate time and complexity
4. Break down large tasks if needed
5. Assign based on skills and availability

### Definition of Done
For each task to be considered complete:
- [ ] Implementation meets all acceptance criteria
- [ ] Code is tested (unit tests where applicable)
- [ ] Code is documented (docstrings, comments)
- [ ] Cross-platform compatibility verified
- [ ] No regressions introduced
- [ ] Code review completed (if working in team)

## Notes for Claude Code

When working on these tasks, remember:

1. **Start with the critical path**: GUI-001 → GUI-002 → GUI-003 enables basic functionality
2. **Test frequently**: Each task should be tested independently
3. **Maintain backwards compatibility**: CLI functionality must remain intact
4. **Follow existing patterns**: Use the established architecture and coding style
5. **Document as you go**: Update docstrings and comments for new code

The interactive CLI mode is the current gold standard - any GUI feature should match or exceed its functionality.
