"""Contract test for DELETE /presets/delete endpoint.

This test defines the contract between GUI and library for deleting presets.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unimplemented
class TestPresetsDeleteContract:
    """Contract tests for preset deletion."""
    
    def test_delete_preset_request_format(self):
        """Test that delete request has expected format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Request should accept these parameters
        request = {
            "preset_name": "my-custom-preset",
            "confirm": True  # optional safety check, defaults to False
        }
        
        # This should not raise
        controller.validate_delete_request(request)
    
    def test_delete_preset_response_format(self):
        """Test that delete response has expected format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Mock the response
        mock_preset_manager.delete_preset.return_value = True
        
        response = controller.delete_preset({
            "preset_name": "my-preset",
            "confirm": True
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "preset_name" in response["data"]
        assert "deleted_at" in response["data"]
    
    def test_delete_preset_confirmation(self):
        """Test confirmation requirement."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Without confirmation should fail
        with pytest.raises(ValueError, match="Confirmation required"):
            controller.validate_delete_request({
                "preset_name": "my-preset",
                "confirm": False
            })
        
        # With confirmation should succeed
        response = controller.delete_preset({
            "preset_name": "my-preset",
            "confirm": True
        })
        
        mock_preset_manager.delete_preset.assert_called_once()
    
    def test_delete_preset_validation(self):
        """Test request validation."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Missing preset_name should fail
        with pytest.raises(ValueError, match="Preset name is required"):
            controller.validate_delete_request({
                "confirm": True
            })
        
        # Builtin preset should fail
        mock_preset_manager.is_builtin_preset.return_value = True
        
        with pytest.raises(ValueError, match="Cannot delete builtin preset"):
            controller.validate_delete_request({
                "preset_name": "minimal",
                "confirm": True
            })
        
        # Nonexistent preset should fail
        mock_preset_manager.is_builtin_preset.return_value = False
        mock_preset_manager.get_presets.return_value = {}
        
        with pytest.raises(ValueError, match="Preset not found"):
            controller.validate_delete_request({
                "preset_name": "nonexistent",
                "confirm": True
            })
    
    def test_delete_preset_events(self):
        """Test that delete emits expected events."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        from src.mcp_config_manager.gui.events.dispatcher import EventDispatcher
        
        controller = PresetController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Track events
        events_received = []
        dispatcher.subscribe("preset.deleting", lambda e: events_received.append(e))
        dispatcher.subscribe("preset.deleted", lambda e: events_received.append(e))
        
        controller.delete_preset({
            "preset_name": "my-preset",
            "confirm": True
        })
        
        event_types = [e["type"] for e in events_received]
        assert "preset.deleting" in event_types
        assert "preset.deleted" in event_types
    
    def test_delete_preset_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Simulate error
        mock_preset_manager.delete_preset.side_effect = PermissionError("Cannot delete file")
        
        response = controller.delete_preset({
            "preset_name": "my-preset",
            "confirm": True
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]