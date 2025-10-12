"""Contract test for POST /servers/toggle endpoint.

This test defines the contract between GUI and library for toggling servers.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unimplemented
class TestServersToggleContract:
    """Contract tests for server toggling."""
    
    def test_toggle_server_request_format(self):
        """Test that toggle request has expected format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "server_name": "context7",
            "enabled": False,  # new state
            "save_immediately": False  # optional, defaults to False
        }
        
        # This should not raise
        controller.validate_toggle_request(request)
    
    def test_toggle_server_response_format(self):
        """Test that toggle response has expected format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock the response
        mock_server_manager.toggle_server.return_value = True
        
        response = controller.toggle_server({
            "mode": "claude",
            "server_name": "context7",
            "enabled": False
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "server_name" in response["data"]
        assert "new_state" in response["data"]
        assert "previous_state" in response["data"]
        assert "saved" in response["data"]
    
    def test_toggle_server_events(self):
        """Test that toggle emits expected events."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        from src.mcp_config_manager.gui.events.dispatcher import EventDispatcher
        
        controller = ServerController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        
        # Track events
        events_received = []
        dispatcher.subscribe("server.toggling", lambda e: events_received.append(e))
        dispatcher.subscribe("server.toggled", lambda e: events_received.append(e))
        dispatcher.subscribe("server.enabled", lambda e: events_received.append(e))
        dispatcher.subscribe("server.disabled", lambda e: events_received.append(e))
        
        # Test enabling
        controller.toggle_server({
            "mode": "claude",
            "server_name": "context7",
            "enabled": True
        })
        
        event_types = [e["type"] for e in events_received]
        assert "server.toggling" in event_types
        assert "server.toggled" in event_types
        assert "server.enabled" in event_types
        
        # Test disabling
        events_received.clear()
        controller.toggle_server({
            "mode": "claude",
            "server_name": "context7",
            "enabled": False
        })
        
        event_types = [e["type"] for e in events_received]
        assert "server.disabled" in event_types
    
    def test_toggle_server_validation(self):
        """Test request validation."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Missing mode should fail
        with pytest.raises(ValueError, match="Mode is required"):
            controller.validate_toggle_request({
                "server_name": "context7",
                "enabled": False
            })
        
        # Missing server_name should fail
        with pytest.raises(ValueError, match="Server name is required"):
            controller.validate_toggle_request({
                "mode": "claude",
                "enabled": False
            })
        
        # Missing enabled state should fail
        with pytest.raises(ValueError, match="Enabled state is required"):
            controller.validate_toggle_request({
                "mode": "claude",
                "server_name": "context7"
            })
        
        # Invalid mode should fail
        with pytest.raises(ValueError, match="Invalid mode"):
            controller.validate_toggle_request({
                "mode": "invalid",
                "server_name": "context7",
                "enabled": False
            })
    
    def test_toggle_server_both_mode(self):
        """Test toggling in 'both' mode affects both configs."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Toggle in both mode
        controller.toggle_server({
            "mode": "both",
            "server_name": "context7",
            "enabled": False
        })
        
        # Should call toggle for both claude and gemini
        calls = mock_server_manager.toggle_server.call_args_list
        assert len(calls) >= 2
        
        # Verify both modes were updated
        modes_updated = [call[1].get("mode") or call[0][0] for call in calls]
        assert "claude" in modes_updated or any("claude" in str(c) for c in calls)
        assert "gemini" in modes_updated or any("gemini" in str(c) for c in calls)
    
    def test_toggle_server_save_immediately(self):
        """Test save_immediately parameter."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        mock_config_manager = Mock()
        controller.server_manager = mock_server_manager
        controller.config_manager = mock_config_manager
        
        # Test without immediate save
        controller.toggle_server({
            "mode": "claude",
            "server_name": "context7",
            "enabled": False,
            "save_immediately": False
        })
        
        mock_config_manager.save_config.assert_not_called()
        
        # Test with immediate save
        controller.toggle_server({
            "mode": "claude",
            "server_name": "context7",
            "enabled": False,
            "save_immediately": True
        })
        
        mock_config_manager.save_config.assert_called_once()
    
    def test_toggle_server_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Simulate error
        mock_server_manager.toggle_server.side_effect = KeyError("Server not found")
        
        response = controller.toggle_server({
            "mode": "claude",
            "server_name": "nonexistent",
            "enabled": False
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]