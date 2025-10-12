"""Integration test for mode switching workflow.

This test verifies the complete mode switching workflow:
1. User switches between Claude/Gemini/Both modes
2. Configuration is loaded for selected mode
3. Server lists update appropriately
4. Sync operations work in 'both' mode
5. Save operations respect mode boundaries

This test should FAIL until GUI is implemented.
"""

import pytest
from unittest.mock import Mock, patch
import json
from pathlib import Path


@pytest.mark.unimplemented
class TestModeSwitchWorkflow:
    """Test complete mode switching workflow and synchronization."""
    
    def test_switch_from_claude_to_gemini_workflow(self):
        """Test switching from Claude to Gemini mode."""
        # This will fail with ModuleNotFoundError until GUI is implemented
        from src.mcp_config_manager.gui.controllers import ConfigController, ServerController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        from src.mcp_config_manager.gui.widgets import ModeSelector
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        config_controller = ConfigController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('mode.changed', lambda e: events_received.append(e))
        dispatcher.subscribe('config.loaded', lambda e: events_received.append(e))
        dispatcher.subscribe('ui.refresh', lambda e: events_received.append(e))
        
        # Step 1: Load initial Claude configuration
        claude_response = config_controller.handle_request({
            'action': 'load_config',
            'mode': 'claude'
        })
        
        assert claude_response['success'] is True
        assert app_state.mode == 'claude'
        
        # Get Claude servers
        claude_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        claude_server_names = [s['name'] for s in claude_servers['data']['servers']]
        
        # Step 2: Switch to Gemini mode
        switch_request = {
            'action': 'switch_mode',
            'from_mode': 'claude',
            'to_mode': 'gemini'
        }
        
        switch_response = config_controller.handle_request(switch_request)
        
        # Verify mode switch
        assert switch_response['success'] is True
        assert switch_response['data']['mode'] == 'gemini'
        assert app_state.mode == 'gemini'
        
        # Verify events
        assert any(e.type == 'mode.changed' for e in events_received)
        assert any(e.type == 'config.loaded' for e in events_received)
        assert any(e.type == 'ui.refresh' for e in events_received)
        
        # Step 3: Verify Gemini configuration loaded
        gemini_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'gemini'
        })
        gemini_server_names = [s['name'] for s in gemini_servers['data']['servers']]
        
        # Servers might be different between modes
        # (unless in sync mode, which we're not)
        assert gemini_servers['data']['mode'] == 'gemini'
        
        # Step 4: Verify unsaved changes warning if needed
        if app_state.has_unsaved_changes:
            mode_change_event = next(
                e for e in events_received 
                if e.type == 'mode.changed'
            )
            assert 'unsaved_changes_warning' in mode_change_event.data
            
    def test_switch_to_both_mode_sync_workflow(self):
        """Test switching to 'both' mode and syncing configurations."""
        from src.mcp_config_manager.gui.controllers import ConfigController, ServerController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        config_controller = ConfigController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track sync events
        sync_events = []
        dispatcher.subscribe('mode.synced', lambda e: sync_events.append(e))
        dispatcher.subscribe('config.merged', lambda e: sync_events.append(e))
        
        # Step 1: Set up different configs in Claude and Gemini
        # Claude: enable context7
        app_state.mode = 'claude'
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'context7'
        })
        
        # Gemini: enable playwright
        app_state.mode = 'gemini'
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'playwright'
        })
        
        # Step 2: Switch to 'both' mode
        switch_response = config_controller.handle_request({
            'action': 'switch_mode',
            'from_mode': 'gemini',
            'to_mode': 'both'
        })
        
        assert switch_response['success'] is True
        assert switch_response['data']['mode'] == 'both'
        
        # Step 3: Verify sync prompt/action
        assert 'sync_required' in switch_response['data']
        assert switch_response['data']['sync_required'] is True
        
        # Step 4: Execute sync
        sync_response = config_controller.handle_request({
            'action': 'sync_configurations',
            'sync_direction': 'merge'  # Merge both configs
        })
        
        assert sync_response['success'] is True
        
        # Verify sync events
        assert len(sync_events) > 0
        assert any(e.type == 'mode.synced' for e in sync_events)
        assert any(e.type == 'config.merged' for e in sync_events)
        
        # Step 5: Verify both configs now have same servers
        servers_response = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'both'
        })
        
        # In sync mode, both configs should have union of servers
        enabled_servers = [
            s['name'] for s in servers_response['data']['servers']
            if s['enabled']
        ]
        assert 'context7' in enabled_servers
        assert 'playwright' in enabled_servers
        
    def test_unsaved_changes_warning_on_mode_switch(self):
        """Test warning when switching modes with unsaved changes."""
        from src.mcp_config_manager.gui.controllers import ConfigController, ServerController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        from src.mcp_config_manager.gui.dialogs import ConfirmationDialog
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        config_controller = ConfigController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track warning events
        warnings = []
        dispatcher.subscribe('warning.shown', lambda e: warnings.append(e))
        
        # Make changes in Claude mode
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'new-server'
        })
        
        assert app_state.has_unsaved_changes is True
        
        # Try to switch mode
        switch_response = config_controller.handle_request({
            'action': 'switch_mode',
            'from_mode': 'claude',
            'to_mode': 'gemini',
            'force': False  # Don't force, should show warning
        })
        
        # Should require confirmation
        assert switch_response['success'] is False
        assert 'requires_confirmation' in switch_response['data']
        assert switch_response['data']['requires_confirmation'] is True
        assert 'unsaved_changes' in switch_response['data']['warning']
        
        # Verify warning event
        assert len(warnings) > 0
        
        # Force switch (user confirmed)
        force_response = config_controller.handle_request({
            'action': 'switch_mode',
            'from_mode': 'claude',
            'to_mode': 'gemini',
            'force': True  # User confirmed
        })
        
        assert force_response['success'] is True
        assert app_state.mode == 'gemini'
        assert app_state.has_unsaved_changes is False  # Reset after switch
        
    def test_mode_specific_operations_workflow(self):
        """Test that operations respect current mode."""
        from src.mcp_config_manager.gui.controllers import ServerController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Enable server in Claude mode
        claude_response = controller.handle_request({
            'action': 'enable_server',
            'server_name': 'claude-only-server',
            'mode': 'claude'
        })
        
        assert claude_response['success'] is True
        
        # Switch to Gemini mode
        app_state.mode = 'gemini'
        
        # Enable different server in Gemini mode
        gemini_response = controller.handle_request({
            'action': 'enable_server',
            'server_name': 'gemini-only-server',
            'mode': 'gemini'
        })
        
        assert gemini_response['success'] is True
        
        # Switch back to Claude and verify servers
        app_state.mode = 'claude'
        claude_servers = controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        
        claude_enabled = [
            s['name'] for s in claude_servers['data']['servers']
            if s['enabled']
        ]
        assert 'claude-only-server' in claude_enabled
        assert 'gemini-only-server' not in claude_enabled
        
        # Switch to Gemini and verify
        app_state.mode = 'gemini'
        gemini_servers = controller.handle_request({
            'action': 'list_servers',
            'mode': 'gemini'
        })
        
        gemini_enabled = [
            s['name'] for s in gemini_servers['data']['servers']
            if s['enabled']
        ]
        assert 'gemini-only-server' in gemini_enabled
        assert 'claude-only-server' not in gemini_enabled
        
    def test_both_mode_synchronized_changes_workflow(self):
        """Test that changes in 'both' mode affect both configs."""
        from src.mcp_config_manager.gui.controllers import ConfigController, ServerController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        
        # Setup in 'both' mode
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='both')
        config_controller = ConfigController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track sync events
        sync_events = []
        dispatcher.subscribe('config.synchronized', lambda e: sync_events.append(e))
        
        # Enable server in 'both' mode
        response = server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'synced-server',
            'mode': 'both'
        })
        
        assert response['success'] is True
        assert 'claude_updated' in response['data']
        assert 'gemini_updated' in response['data']
        assert response['data']['claude_updated'] is True
        assert response['data']['gemini_updated'] is True
        
        # Verify sync event
        assert len(sync_events) > 0
        
        # Switch to Claude mode and verify
        app_state.mode = 'claude'
        claude_check = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        
        claude_servers = [s['name'] for s in claude_check['data']['servers'] if s['enabled']]
        assert 'synced-server' in claude_servers
        
        # Switch to Gemini mode and verify
        app_state.mode = 'gemini'
        gemini_check = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'gemini'
        })
        
        gemini_servers = [s['name'] for s in gemini_check['data']['servers'] if s['enabled']]
        assert 'synced-server' in gemini_servers
        
    def test_mode_indicator_ui_update_workflow(self):
        """Test that UI mode indicator updates correctly."""
        from src.mcp_config_manager.gui.controllers import ConfigController
        from src.mcp_config_manager.gui.events import EventDispatcher
        from src.mcp_config_manager.gui.models import ApplicationState
        from src.mcp_config_manager.gui.widgets import ModeSelector
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ConfigController(dispatcher, app_state)
        
        # Track UI update events
        ui_updates = []
        dispatcher.subscribe('ui.mode_indicator.update', lambda e: ui_updates.append(e))
        
        # Test all mode transitions
        modes = ['claude', 'gemini', 'both']
        
        for i, target_mode in enumerate(modes):
            response = controller.handle_request({
                'action': 'switch_mode',
                'to_mode': target_mode
            })
            
            assert response['success'] is True
            
            # Verify UI update event
            assert len(ui_updates) == i + 1
            latest_update = ui_updates[-1]
            assert latest_update.data['mode'] == target_mode
            assert 'display_text' in latest_update.data
            assert 'icon' in latest_update.data
            
        # Verify display text for each mode
        mode_displays = {
            'claude': 'Claude',
            'gemini': 'Gemini',
            'both': 'Both (Synced)'
        }
        
        for update in ui_updates:
            mode = update.data['mode']
            expected_text = mode_displays[mode]
            assert expected_text in update.data['display_text']