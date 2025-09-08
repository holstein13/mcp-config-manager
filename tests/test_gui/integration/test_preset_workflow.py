"""Integration test for preset workflow.

This test verifies the complete preset management workflow:
1. User lists available presets
2. User applies a preset
3. Configuration is updated
4. State reflects preset application
5. User can save custom preset
6. User can delete custom preset

This test should FAIL until GUI is implemented.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import json


class TestPresetWorkflow:
    """Test complete preset workflow from user action to state update."""
    
    def test_list_and_apply_preset_workflow(self):
        """Test listing presets and applying one."""
        # This will fail with ModuleNotFoundError until GUI is implemented
        from src.gui.controllers import PresetController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState, PresetListItem
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = PresetController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('preset.listed', lambda e: events_received.append(e))
        dispatcher.subscribe('preset.applied', lambda e: events_received.append(e))
        dispatcher.subscribe('state.changed', lambda e: events_received.append(e))
        
        # Step 1: User requests preset list
        request = {
            'action': 'list_presets',
            'mode': 'claude'
        }
        
        response = controller.handle_request(request)
        
        # Verify preset list returned
        assert response['success'] is True
        assert 'presets' in response['data']
        assert len(response['data']['presets']) > 0
        
        # Should have minimal and web_dev presets
        preset_names = [p['name'] for p in response['data']['presets']]
        assert 'minimal' in preset_names
        assert 'web_dev' in preset_names
        
        # Verify event fired
        assert any(e.type == 'preset.listed' for e in events_received)
        
        # Step 2: User applies minimal preset
        apply_request = {
            'action': 'apply_preset',
            'preset_name': 'minimal',
            'mode': 'claude'
        }
        
        apply_response = controller.handle_request(apply_request)
        
        # Verify preset applied
        assert apply_response['success'] is True
        assert 'servers_enabled' in apply_response['data']
        assert 'servers_disabled' in apply_response['data']
        
        # Verify events
        assert any(e.type == 'preset.applied' for e in events_received)
        assert any(e.type == 'state.changed' for e in events_received)
        
        # Step 3: Verify state updated
        assert app_state.active_preset == 'minimal'
        assert app_state.has_unsaved_changes is True
        
        # Minimal preset should enable only context7 and browsermcp
        enabled_servers = app_state.get_enabled_servers()
        assert 'context7' in enabled_servers
        assert 'browsermcp' in enabled_servers
        
    def test_save_custom_preset_workflow(self):
        """Test saving current configuration as custom preset."""
        from src.gui.controllers import PresetController, ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        preset_controller = PresetController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('preset.saved', lambda e: events_received.append(e))
        dispatcher.subscribe('preset.listed', lambda e: events_received.append(e))
        
        # Step 1: Configure some servers
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'context7'
        })
        server_controller.handle_request({
            'action': 'enable_server', 
            'server_name': 'playwright'
        })
        
        # Step 2: Save as custom preset
        save_request = {
            'action': 'save_preset',
            'preset_name': 'my_custom',
            'description': 'My custom development setup',
            'mode': 'claude'
        }
        
        save_response = preset_controller.handle_request(save_request)
        
        # Verify preset saved
        assert save_response['success'] is True
        assert save_response['data']['preset_name'] == 'my_custom'
        
        # Verify event fired
        assert any(e.type == 'preset.saved' for e in events_received)
        
        # Step 3: Verify preset appears in list
        list_response = preset_controller.handle_request({
            'action': 'list_presets',
            'mode': 'claude'
        })
        
        preset_names = [p['name'] for p in list_response['data']['presets']]
        assert 'my_custom' in preset_names
        
        # Find the custom preset
        custom_preset = next(
            p for p in list_response['data']['presets'] 
            if p['name'] == 'my_custom'
        )
        assert custom_preset['description'] == 'My custom development setup'
        assert custom_preset['is_custom'] is True
        
    def test_delete_custom_preset_workflow(self):
        """Test deleting a custom preset."""
        from src.gui.controllers import PresetController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = PresetController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('preset.deleted', lambda e: events_received.append(e))
        
        # Step 1: Create a custom preset
        controller.handle_request({
            'action': 'save_preset',
            'preset_name': 'to_delete',
            'description': 'Will be deleted',
            'mode': 'claude'
        })
        
        # Step 2: Delete the preset
        delete_request = {
            'action': 'delete_preset',
            'preset_name': 'to_delete'
        }
        
        delete_response = controller.handle_request(delete_request)
        
        # Verify deletion
        assert delete_response['success'] is True
        assert delete_response['data']['preset_name'] == 'to_delete'
        
        # Verify event
        assert any(e.type == 'preset.deleted' for e in events_received)
        
        # Step 3: Verify preset no longer in list
        list_response = controller.handle_request({
            'action': 'list_presets',
            'mode': 'claude'
        })
        
        preset_names = [p['name'] for p in list_response['data']['presets']]
        assert 'to_delete' not in preset_names
        
    def test_preset_validation_workflow(self):
        """Test preset validation and error handling."""
        from src.gui.controllers import PresetController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = PresetController(dispatcher, app_state)
        
        # Track error events
        errors_received = []
        dispatcher.subscribe('error.occurred', lambda e: errors_received.append(e))
        
        # Test 1: Apply non-existent preset
        response = controller.handle_request({
            'action': 'apply_preset',
            'preset_name': 'non_existent',
            'mode': 'claude'
        })
        
        assert response['success'] is False
        assert 'not found' in response['error'].lower()
        assert len(errors_received) > 0
        
        # Test 2: Save preset with invalid name
        response = controller.handle_request({
            'action': 'save_preset',
            'preset_name': '',  # Empty name
            'description': 'Invalid preset',
            'mode': 'claude'
        })
        
        assert response['success'] is False
        assert 'name' in response['error'].lower()
        
        # Test 3: Delete built-in preset (should fail)
        response = controller.handle_request({
            'action': 'delete_preset',
            'preset_name': 'minimal'  # Built-in preset
        })
        
        assert response['success'] is False
        assert 'cannot delete' in response['error'].lower()
        
    def test_preset_mode_sync_workflow(self):
        """Test preset application across different modes."""
        from src.gui.controllers import PresetController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='both')  # Synced mode
        controller = PresetController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('preset.applied', lambda e: events_received.append(e))
        dispatcher.subscribe('mode.synced', lambda e: events_received.append(e))
        
        # Apply preset in synced mode
        response = controller.handle_request({
            'action': 'apply_preset',
            'preset_name': 'minimal',
            'mode': 'both'
        })
        
        assert response['success'] is True
        
        # Should update both Claude and Gemini configs
        assert 'claude_servers' in response['data']
        assert 'gemini_servers' in response['data']
        
        # Verify sync event
        assert any(e.type == 'mode.synced' for e in events_received)
        
        # Both configs should have same servers enabled
        claude_enabled = response['data']['claude_servers']['enabled']
        gemini_enabled = response['data']['gemini_servers']['enabled']
        assert set(claude_enabled) == set(gemini_enabled)