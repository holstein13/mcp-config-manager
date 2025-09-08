"""Integration test for add server workflow.

This test verifies the complete server addition workflow:
1. User opens add server dialog
2. User pastes JSON configuration
3. Configuration is validated
4. Server is added to configuration
5. State reflects new server
6. Server appears in UI list

This test should FAIL until GUI is implemented.
"""

import pytest
from unittest.mock import Mock, patch
import json


class TestAddServerWorkflow:
    """Test complete add server workflow from paste to state update."""
    
    def test_add_server_via_json_paste_workflow(self):
        """Test adding a server by pasting JSON configuration."""
        # This will fail with ModuleNotFoundError until GUI is implemented
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState, ServerListItem
        from src.gui.dialogs import AddServerDialog
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('server.added', lambda e: events_received.append(e))
        dispatcher.subscribe('server.validated', lambda e: events_received.append(e))
        dispatcher.subscribe('state.changed', lambda e: events_received.append(e))
        dispatcher.subscribe('ui.refresh', lambda e: events_received.append(e))
        
        # Step 1: User initiates add server
        dialog_request = {
            'action': 'open_add_dialog',
            'mode': 'claude'
        }
        
        # Simulate dialog interaction
        dialog = AddServerDialog()
        
        # Step 2: User pastes JSON
        json_input = json.dumps({
            "command": "uvx",
            "args": ["--from", "git+https://github.com/test/server.git", "server"],
            "env": {
                "SERVER_CONFIG": "/path/to/config"
            }
        })
        
        # Step 3: Validate JSON
        validation_request = {
            'action': 'validate_server_json',
            'json_string': json_input,
            'server_name': 'test-server'
        }
        
        validation_response = controller.handle_request(validation_request)
        
        # Verify validation
        assert validation_response['success'] is True
        assert validation_response['data']['is_valid'] is True
        assert 'parsed_config' in validation_response['data']
        
        # Verify validation event
        assert any(e.type == 'server.validated' for e in events_received)
        
        # Step 4: Add server to configuration
        add_request = {
            'action': 'add_server',
            'server_name': 'test-server',
            'config': validation_response['data']['parsed_config'],
            'mode': 'claude'
        }
        
        add_response = controller.handle_request(add_request)
        
        # Verify server added
        assert add_response['success'] is True
        assert add_response['data']['server_name'] == 'test-server'
        assert add_response['data']['enabled'] is True  # New servers default to enabled
        
        # Verify events
        assert any(e.type == 'server.added' for e in events_received)
        assert any(e.type == 'state.changed' for e in events_received)
        assert any(e.type == 'ui.refresh' for e in events_received)
        
        # Step 5: Verify state updated
        assert 'test-server' in app_state.get_enabled_servers()
        assert app_state.has_unsaved_changes is True
        
        # Step 6: Verify server appears in list
        list_request = {
            'action': 'list_servers',
            'mode': 'claude'
        }
        
        list_response = controller.handle_request(list_request)
        
        server_names = [s['name'] for s in list_response['data']['servers']]
        assert 'test-server' in server_names
        
        # Find the new server
        new_server = next(
            s for s in list_response['data']['servers']
            if s['name'] == 'test-server'
        )
        assert new_server['enabled'] is True
        assert new_server['command'] == 'uvx'
        
    def test_add_duplicate_server_workflow(self):
        """Test handling duplicate server names."""
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Track error events
        errors_received = []
        dispatcher.subscribe('error.occurred', lambda e: errors_received.append(e))
        dispatcher.subscribe('validation.failed', lambda e: errors_received.append(e))
        
        # Add initial server
        server_config = {
            "command": "node",
            "args": ["server.js"]
        }
        
        controller.handle_request({
            'action': 'add_server',
            'server_name': 'existing-server',
            'config': server_config,
            'mode': 'claude'
        })
        
        # Try to add duplicate
        duplicate_response = controller.handle_request({
            'action': 'add_server',
            'server_name': 'existing-server',  # Same name
            'config': server_config,
            'mode': 'claude'
        })
        
        # Should fail with appropriate error
        assert duplicate_response['success'] is False
        assert 'already exists' in duplicate_response['error'].lower()
        
        # Verify error event
        assert any(e.type == 'error.occurred' for e in errors_received)
        
        # Original server should remain unchanged
        list_response = controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        
        existing_servers = [
            s for s in list_response['data']['servers']
            if s['name'] == 'existing-server'
        ]
        assert len(existing_servers) == 1  # Only one instance
        
    def test_add_server_with_invalid_json_workflow(self):
        """Test handling invalid JSON input."""
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Track validation events
        events_received = []
        dispatcher.subscribe('validation.failed', lambda e: events_received.append(e))
        
        # Test various invalid inputs
        invalid_inputs = [
            "not json at all",
            '{"command": }',  # Invalid JSON syntax
            '{}',  # Missing required fields
            '{"command": ""}',  # Empty command
            '{"command": "test", "args": "not-array"}',  # Wrong type for args
        ]
        
        for invalid_json in invalid_inputs:
            response = controller.handle_request({
                'action': 'validate_server_json',
                'json_string': invalid_json,
                'server_name': 'test'
            })
            
            assert response['success'] is False
            assert 'is_valid' in response['data']
            assert response['data']['is_valid'] is False
            assert 'error' in response['data']
        
        # Verify validation failed events
        assert len(events_received) == len(invalid_inputs)
        
    def test_add_server_to_multiple_modes_workflow(self):
        """Test adding server to both Claude and Gemini."""
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup in synced mode
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='both')
        controller = ServerController(dispatcher, app_state)
        
        # Track sync events
        sync_events = []
        dispatcher.subscribe('mode.synced', lambda e: sync_events.append(e))
        
        # Add server in synced mode
        server_config = {
            "command": "python",
            "args": ["-m", "server"],
            "env": {"PORT": "8080"}
        }
        
        response = controller.handle_request({
            'action': 'add_server',
            'server_name': 'synced-server',
            'config': server_config,
            'mode': 'both'
        })
        
        assert response['success'] is True
        
        # Should be added to both configs
        assert 'claude_config' in response['data']
        assert 'gemini_config' in response['data']
        
        # Verify sync event fired
        assert len(sync_events) > 0
        
        # Verify server in both modes
        for mode in ['claude', 'gemini']:
            list_response = controller.handle_request({
                'action': 'list_servers',
                'mode': mode
            })
            
            server_names = [s['name'] for s in list_response['data']['servers']]
            assert 'synced-server' in server_names
            
    def test_add_server_with_environment_variables_workflow(self):
        """Test adding server with environment variables."""
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Server with complex environment
        server_config = {
            "command": "docker",
            "args": ["run", "my-server"],
            "env": {
                "API_KEY": "secret-key",
                "DATABASE_URL": "postgres://localhost:5432/db",
                "DEBUG": "true",
                "PORT": "3000"
            }
        }
        
        # Add server
        response = controller.handle_request({
            'action': 'add_server',
            'server_name': 'env-server',
            'config': server_config,
            'mode': 'claude'
        })
        
        assert response['success'] is True
        
        # Verify environment variables preserved
        list_response = controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        
        env_server = next(
            s for s in list_response['data']['servers']
            if s['name'] == 'env-server'
        )
        
        assert 'env' in env_server
        assert env_server['env']['API_KEY'] == 'secret-key'
        assert env_server['env']['DATABASE_URL'] == 'postgres://localhost:5432/db'
        assert env_server['env']['DEBUG'] == 'true'
        assert env_server['env']['PORT'] == '3000'
        
    def test_add_server_cancel_workflow(self):
        """Test canceling add server dialog."""
        from src.gui.controllers import ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = ServerController(dispatcher, app_state)
        
        # Track cancel events
        cancel_events = []
        dispatcher.subscribe('dialog.cancelled', lambda e: cancel_events.append(e))
        
        # Initial server count
        initial_response = controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        initial_count = len(initial_response['data']['servers'])
        
        # Simulate dialog cancel
        cancel_response = controller.handle_request({
            'action': 'cancel_add_dialog'
        })
        
        assert cancel_response['success'] is True
        
        # Verify cancel event
        assert len(cancel_events) > 0
        
        # Server count should be unchanged
        final_response = controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        final_count = len(final_response['data']['servers'])
        
        assert final_count == initial_count
        assert app_state.has_unsaved_changes is False