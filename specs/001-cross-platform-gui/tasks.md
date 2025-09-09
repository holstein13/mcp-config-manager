# Tasks: Cross-Platform GUI for MCP Configuration Management

**Input**: Design documents from `/specs/001-cross-platform-gui/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, PyQt6 (primary), tkinter (fallback)
   → Libraries: ConfigManager, ServerManager, PresetManager
   → Structure: Single project with GUI module
2. Load optional design documents:
   → data-model.md: ApplicationState, UIConfiguration, ServerListItem, etc.
   → contracts/: gui-library-contract.yaml, event-contract.yaml
   → research.md: PyQt6 selected, PyInstaller packaging, pytest-qt testing
3. Generate tasks by category:
   → Setup: PyQt6 setup, project structure, testing framework
   → Tests: Contract tests for all endpoints, event tests
   → Core: GUI models, main window, dialogs, controllers
   → Integration: Library integration, event handling
   → Polish: Platform testing, packaging, performance
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests? ✓
   → All entities have models? ✓
   → All endpoints implemented? ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **GUI Module**: `src/gui/`, `tests/test_gui/`
- **Resources**: `src/resources/`
- **Existing Core**: `src/mcp_config_manager/`

## Phase 3.1: Setup
- [x] T001 Create GUI module structure at src/gui/ with __init__.py, main_window.py, controllers/, dialogs/, widgets/
- [x] T002 Install PyQt6 dependencies and configure fallback to tkinter in src/gui/__init__.py
- [x] T003 [P] Set up pytest-qt testing framework in tests/test_gui/conftest.py
- [x] T004 [P] Create resource directories at src/resources/icons/ and src/resources/styles/
- [x] T005 [P] Configure GUI entry point in src/mcp_config_manager/__main__.py for 'gui' command

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests - GUI-Library Integration
- [x] T006 [P] Contract test POST /config/load in tests/test_gui/contract/test_config_load.py
- [x] T007 [P] Contract test POST /config/save in tests/test_gui/contract/test_config_save.py
- [x] T008 [P] Contract test GET /servers/list in tests/test_gui/contract/test_servers_list.py
- [x] T009 [P] Contract test POST /servers/toggle in tests/test_gui/contract/test_servers_toggle.py
- [x] T010 [P] Contract test POST /servers/add in tests/test_gui/contract/test_servers_add.py
- [x] T011 [P] Contract test POST /servers/bulk in tests/test_gui/contract/test_servers_bulk.py
- [x] T012 [P] Contract test GET /presets/list in tests/test_gui/contract/test_presets_list.py
- [x] T013 [P] Contract test POST /presets/load in tests/test_gui/contract/test_presets_load.py
- [x] T014 [P] Contract test POST /presets/save in tests/test_gui/contract/test_presets_save.py
- [x] T015 [P] Contract test DELETE /presets/delete in tests/test_gui/contract/test_presets_delete.py
- [x] T016 [P] Contract test GET /backups/list in tests/test_gui/contract/test_backups_list.py
- [x] T017 [P] Contract test POST /backups/create in tests/test_gui/contract/test_backups_create.py
- [x] T018 [P] Contract test POST /backups/restore in tests/test_gui/contract/test_backups_restore.py
- [x] T019 [P] Contract test POST /validate in tests/test_gui/contract/test_validate.py

### Event Contract Tests
- [x] T020 [P] Event test ConfigurationLoaded/Saved events in tests/test_gui/events/test_config_events.py
- [x] T021 [P] Event test ServerToggled/Added/Removed events in tests/test_gui/events/test_server_events.py
- [x] T022 [P] Event test PresetLoaded/Saved/Deleted events in tests/test_gui/events/test_preset_events.py
- [x] T023 [P] Event test ModeChanged/StateChanged events in tests/test_gui/events/test_app_events.py
- [x] T024 [P] Event test ViewChanged/SelectionChanged events in tests/test_gui/events/test_ui_events.py

### Integration Tests from User Stories
- [x] T025 [P] Integration test server toggle workflow in tests/test_gui/integration/test_toggle_workflow.py
- [x] T026 [P] Integration test preset apply workflow in tests/test_gui/integration/test_preset_workflow.py
- [x] T027 [P] Integration test add server workflow in tests/test_gui/integration/test_add_server_workflow.py
- [x] T028 [P] Integration test mode switching workflow in tests/test_gui/integration/test_mode_switch_workflow.py
- [x] T029 [P] Integration test backup/restore workflow in tests/test_gui/integration/test_backup_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models
- [x] T030 [P] ApplicationState model in src/gui/models/app_state.py
- [x] T031 [P] UIConfiguration model in src/gui/models/ui_config.py
- [x] T032 [P] ServerListItem model in src/gui/models/server_list_item.py
- [x] T033 [P] PresetListItem model in src/gui/models/preset_list_item.py
- [x] T034 [P] BackupInfo model in src/gui/models/backup_info.py

### Main Window
- [x] T035 Create MainWindow class with menu bar and toolbar in src/gui/main_window.py
- [x] T036 Implement server list widget in src/gui/widgets/server_list.py
- [x] T037 Implement server toggle functionality in src/gui/widgets/server_list.py
- [x] T038 Add status bar with save indicator in src/gui/main_window.py
- [x] T039 Implement mode selector widget in src/gui/widgets/mode_selector.py

### Dialogs
- [x] T040 [P] Add Server dialog in src/gui/dialogs/add_server_dialog.py
- [x] T041 [P] Preset Manager dialog in src/gui/dialogs/preset_manager_dialog.py
- [x] T042 [P] Settings dialog in src/gui/dialogs/settings_dialog.py
- [x] T043 [P] Backup/Restore dialog in src/gui/dialogs/backup_restore_dialog.py
- [x] T044 [P] Error dialog with details in src/gui/dialogs/error_dialog.py

### Controllers (GUI-Library Bridge)
- [x] T045 [P] ConfigController for load/save operations in src/gui/controllers/config_controller.py
- [x] T046 [P] ServerController for server management in src/gui/controllers/server_controller.py
- [x] T047 [P] PresetController for preset operations in src/gui/controllers/preset_controller.py
- [x] T048 [P] BackupController for backup/restore in src/gui/controllers/backup_controller.py

### Event Handling
- [ ] T049 Event dispatcher system in src/gui/events/dispatcher.py
- [ ] T050 Connect UI events to controllers in src/gui/main_window.py
- [ ] T051 Implement state change notifications in src/gui/events/state_manager.py
- [ ] T052 Add keyboard shortcuts in src/gui/main_window.py

## Phase 3.4: Integration

### Library Integration
- [ ] T053 Connect ConfigController to ConfigManager in src/gui/controllers/config_controller.py
- [ ] T054 Connect ServerController to ServerManager in src/gui/controllers/server_controller.py
- [ ] T055 Connect PresetController to PresetManager in src/gui/controllers/preset_controller.py
- [ ] T056 Implement config file watching in src/gui/utils/file_watcher.py

### UI Features
- [ ] T057 [P] Implement search/filter in src/gui/widgets/search_bar.py
- [ ] T058 [P] Add multi-selection support in src/gui/widgets/server_list.py
- [ ] T059 [P] Implement drag-drop for server reordering in src/gui/widgets/server_list.py
- [ ] T060 [P] Add right-click context menus in src/gui/widgets/server_list.py

### Threading
- [ ] T061 Background file operations in src/gui/utils/worker_thread.py
- [ ] T062 Progress indicators for long operations in src/gui/widgets/progress_widget.py
- [ ] T063 Thread-safe state updates in src/gui/events/state_manager.py

### tkinter Fallback
- [ ] T064 [P] tkinter MainWindow implementation in src/gui/tkinter/main_window.py
- [ ] T065 [P] tkinter server list in src/gui/tkinter/server_list.py
- [ ] T066 [P] tkinter dialogs adapter in src/gui/tkinter/dialogs.py

## Phase 3.5: Polish

### Platform Testing
- [ ] T067 [P] Windows-specific testing in tests/test_gui/platform/test_windows.py
- [ ] T068 [P] macOS-specific testing in tests/test_gui/platform/test_macos.py
- [ ] T069 [P] Linux-specific testing in tests/test_gui/platform/test_linux.py

### Performance
- [ ] T070 Virtual scrolling for 100+ servers in src/gui/widgets/server_list.py
- [ ] T071 Debounce search input in src/gui/widgets/search_bar.py
- [ ] T072 Lazy load preset contents in src/gui/controllers/preset_controller.py
- [ ] T073 Performance tests (<100ms response) in tests/test_gui/performance/test_response_time.py

### Packaging
- [ ] T074 [P] PyInstaller spec file in build/mcp-config-manager.spec
- [ ] T075 [P] Windows installer configuration in build/windows/installer.iss
- [ ] T076 [P] macOS DMG configuration in build/macos/dmg_config.json
- [ ] T077 [P] Linux AppImage configuration in build/linux/appimage.yml

### Documentation
- [ ] T078 [P] Update CLAUDE.md with GUI commands and architecture
- [ ] T079 [P] Create GUI user guide in docs/gui_guide.md
- [ ] T080 [P] Add screenshots to quickstart.md

### Final Validation
- [ ] T081 Run all quickstart.md workflows end-to-end
- [ ] T082 Verify all keyboard shortcuts work
- [ ] T083 Test with 200+ servers for performance
- [ ] T084 Validate cross-platform appearance

## Dependencies
- Setup (T001-T005) blocks everything
- All tests (T006-T029) must complete before implementation (T030-T066)
- Data models (T030-T034) before UI components
- Main window (T035-T039) before dialogs
- Controllers (T045-T048) before library integration (T053-T056)
- Core implementation before platform testing
- Everything before final validation (T081-T084)

## Parallel Execution Examples

### Test Phase Parallel Batch
```bash
# Launch all contract tests together (T006-T019):
Task: "Contract test POST /config/load in tests/test_gui/contract/test_config_load.py"
Task: "Contract test POST /config/save in tests/test_gui/contract/test_config_save.py"
Task: "Contract test GET /servers/list in tests/test_gui/contract/test_servers_list.py"
# ... continue for all contract tests
```

### Model Creation Parallel Batch
```bash
# Launch all model tasks together (T030-T034):
Task: "ApplicationState model in src/gui/models/app_state.py"
Task: "UIConfiguration model in src/gui/models/ui_config.py"
Task: "ServerListItem model in src/gui/models/server_list_item.py"
Task: "PresetListItem model in src/gui/models/preset_list_item.py"
Task: "BackupInfo model in src/gui/models/backup_info.py"
```

### Dialog Implementation Parallel Batch
```bash
# Launch all dialog tasks together (T040-T044):
Task: "Add Server dialog in src/gui/dialogs/add_server_dialog.py"
Task: "Preset Manager dialog in src/gui/dialogs/preset_manager_dialog.py"
Task: "Settings dialog in src/gui/dialogs/settings_dialog.py"
Task: "Backup/Restore dialog in src/gui/dialogs/backup_restore_dialog.py"
Task: "Error dialog with details in src/gui/dialogs/error_dialog.py"
```

## Notes
- [P] tasks = different files, no shared state
- Verify all tests fail before implementing
- Commit after each task with descriptive message
- Run tests continuously during implementation
- Use constitution principles throughout

## Validation Checklist
*GATE: All must pass before execution*

- [x] All contracts have corresponding tests (T006-T019 cover gui-library-contract, T020-T024 cover event-contract)
- [x] All entities have model tasks (T030-T034 cover all data model entities)
- [x] All tests come before implementation (Phase 3.2 before Phase 3.3)
- [x] Parallel tasks truly independent (verified - different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task in same phase

## Estimated Effort
- **Total Tasks**: 84
- **Parallel Groups**: 12 (significant time savings)
- **Critical Path**: Setup → Tests → Main Window → Integration → Validation
- **Estimated Duration**: 2-3 weeks with focused execution