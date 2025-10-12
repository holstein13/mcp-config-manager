"""Contract test for POST /config/save endpoint.

This test defines the contract between GUI and library for saving configuration.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json


@pytest.mark.unimplemented
class TestConfigSaveContract:
    """Contract tests for configuration saving."""
    
    def test_save_config_request_format(self):
        """Test that save request has expected format."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "servers": [
                {"name": "server1", "enabled": True, "config": {}},
                {"name": "server2", "enabled": False, "config": {}}
            ],
            "create_backup": True  # optional, defaults to True
        }
        
        # This should not raise
        controller.validate_save_request(request)
    
    def test_save_config_response_format(self):
        """Test that save response has expected format."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock the response
        mock_config_manager.save_config.return_value = True
        
        response = controller.save_config({
            "mode": "claude",
            "servers": []
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "saved_paths" in response["data"]
        assert "backup_path" in response["data"]
        assert "timestamp" in response["data"]
    
    def test_save_config_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Simulate error
        mock_config_manager.save_config.side_effect = PermissionError("Cannot write file")
        
        response = controller.save_config({
            "mode": "claude",
            "servers": []
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]
    
    def test_save_config_events(self):
        """Test that save emits expected events."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        from src.mcp_config_manager.gui.events.dispatcher import EventDispatcher
        
        controller = ConfigController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        
        # Track events
        events_received = []
        dispatcher.subscribe("config.saving", lambda e: events_received.append(e))
        dispatcher.subscribe("config.saved", lambda e: events_received.append(e))
        dispatcher.subscribe("backup.created", lambda e: events_received.append(e))
        
        controller.save_config({
            "mode": "claude",
            "servers": [],
            "create_backup": True
        })
        
        # Must emit saving and saved events
        event_types = [e["type"] for e in events_received]
        assert "config.saving" in event_types
        assert "config.saved" in event_types
        assert "backup.created" in event_types
    
    def test_save_config_validation(self):
        """Test request validation."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        
        # Invalid mode should fail
        with pytest.raises(ValueError, match="Invalid mode"):
            controller.validate_save_request({
                "mode": "invalid",
                "servers": []
            })
        
        # Missing mode should fail
        with pytest.raises(ValueError, match="Mode is required"):
            controller.validate_save_request({"servers": []})
        
        # Missing servers should fail
        with pytest.raises(ValueError, match="Servers list is required"):
            controller.validate_save_request({"mode": "claude"})
        
        # Invalid server structure should fail
        with pytest.raises(ValueError, match="Invalid server format"):
            controller.validate_save_request({
                "mode": "claude",
                "servers": [{"invalid": "structure"}]
            })
    
    def test_save_config_backup_behavior(self):
        """Test backup creation behavior."""
        from src.mcp_config_manager.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Test with backup enabled (default)
        controller.save_config({
            "mode": "claude",
            "servers": []
        })
        
        mock_config_manager.create_backup.assert_called_once()
        
        # Test with backup disabled
        mock_config_manager.reset_mock()
        controller.save_config({
            "mode": "claude",
            "servers": [],
            "create_backup": False
        })
        
        mock_config_manager.create_backup.assert_not_called()