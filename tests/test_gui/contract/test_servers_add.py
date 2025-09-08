"""Contract test for POST /servers/add endpoint.

This test defines the contract between GUI and library for adding servers.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestServersAddContract:
    """Contract tests for server addition."""
    
    def test_add_server_request_format(self):
        """Test that add request has expected format."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "server_json": '{"command": "node", "args": ["server.js"]}',
            "server_name": "my-server",  # optional, extracted from JSON if not provided
            "enabled": True,  # optional, defaults to True
            "validate": True  # optional, defaults to True
        }
        
        # This should not raise
        controller.validate_add_request(request)
    
    def test_add_server_response_format(self):
        """Test that add response has expected format."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock the response
        mock_server_manager.add_server.return_value = True
        
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "node"}',
            "server_name": "my-server"
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "server_name" in response["data"]
        assert "config" in response["data"]
        assert "enabled" in response["data"]
        assert "validation_passed" in response["data"]
    
    def test_add_server_json_validation(self):
        """Test JSON validation."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Invalid JSON should fail
        with pytest.raises(ValueError, match="Invalid JSON"):
            controller.validate_add_request({
                "mode": "claude",
                "server_json": "not valid json"
            })
        
        # Empty JSON should fail
        with pytest.raises(ValueError, match="Server configuration cannot be empty"):
            controller.validate_add_request({
                "mode": "claude",
                "server_json": "{}"
            })
        
        # Missing required fields should fail when validate=True
        with pytest.raises(ValueError, match="Missing required field"):
            controller.validate_add_request({
                "mode": "claude",
                "server_json": '{"invalid": "config"}',
                "validate": True
            })
    
    def test_add_server_name_extraction(self):
        """Test automatic server name extraction."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Test with explicit name
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "node"}',
            "server_name": "explicit-name"
        })
        
        assert response["data"]["server_name"] == "explicit-name"
        
        # Test with name in JSON
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"name": "json-name", "command": "node"}'
        })
        
        assert response["data"]["server_name"] == "json-name"
        
        # Test with command-based name
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "my-server"}'
        })
        
        assert response["data"]["server_name"] == "my-server"
    
    def test_add_server_events(self):
        """Test that add emits expected events."""
        from src.gui.controllers.server_controller import ServerController
        from src.gui.events.dispatcher import EventDispatcher
        
        controller = ServerController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        
        # Track events
        events_received = []
        dispatcher.subscribe("server.adding", lambda e: events_received.append(e))
        dispatcher.subscribe("server.added", lambda e: events_received.append(e))
        dispatcher.subscribe("server.validated", lambda e: events_received.append(e))
        
        controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "node"}',
            "server_name": "test-server",
            "validate": True
        })
        
        event_types = [e["type"] for e in events_received]
        assert "server.adding" in event_types
        assert "server.added" in event_types
        assert "server.validated" in event_types
    
    def test_add_server_duplicate_handling(self):
        """Test duplicate server handling."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Simulate duplicate error
        mock_server_manager.add_server.side_effect = ValueError("Server already exists")
        
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "node"}',
            "server_name": "existing-server"
        })
        
        assert response["success"] is False
        assert "error" in response
        assert "already exists" in response["error"]["message"].lower()
    
    def test_add_server_both_mode(self):
        """Test adding server in 'both' mode."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        controller.add_server({
            "mode": "both",
            "server_json": '{"command": "node"}',
            "server_name": "test-server"
        })
        
        # Should add to both configs
        calls = mock_server_manager.add_server.call_args_list
        assert len(calls) >= 2
    
    def test_add_server_error_handling(self):
        """Test error response format."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Simulate error
        mock_server_manager.add_server.side_effect = Exception("Unexpected error")
        
        response = controller.add_server({
            "mode": "claude",
            "server_json": '{"command": "node"}',
            "server_name": "test-server"
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]