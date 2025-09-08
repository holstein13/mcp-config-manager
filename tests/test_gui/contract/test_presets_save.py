"""Contract test for POST /presets/save endpoint.

This test defines the contract between GUI and library for saving presets.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPresetsSaveContract:
    """Contract tests for preset saving."""
    
    def test_save_preset_request_format(self):
        """Test that save request has expected format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Request should accept these parameters
        request = {
            "preset_name": "my-custom-preset",
            "servers": ["server1", "server2", "server3"],
            "description": "My custom preset for development",  # optional
            "overwrite": False  # optional, defaults to False
        }
        
        # This should not raise
        controller.validate_save_request(request)
    
    def test_save_preset_response_format(self):
        """Test that save response has expected format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Mock the response
        mock_preset_manager.save_preset.return_value = True
        
        response = controller.save_preset({
            "preset_name": "my-preset",
            "servers": ["server1", "server2"]
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "preset_name" in response["data"]
        assert "servers" in response["data"]
        assert "server_count" in response["data"]
        assert "created_at" in response["data"]
        assert "overwritten" in response["data"]
    
    def test_save_preset_overwrite_behavior(self):
        """Test overwrite behavior."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Setup existing preset
        mock_preset_manager.get_presets.return_value = {
            "existing-preset": ["server1"]
        }
        
        # Test without overwrite (should fail)
        with pytest.raises(ValueError, match="Preset already exists"):
            controller.validate_save_request({
                "preset_name": "existing-preset",
                "servers": ["server2"],
                "overwrite": False
            })
        
        # Test with overwrite (should succeed)
        response = controller.save_preset({
            "preset_name": "existing-preset",
            "servers": ["server2"],
            "overwrite": True
        })
        
        assert response["success"] is True
        assert response["data"]["overwritten"] is True
    
    def test_save_preset_validation(self):
        """Test request validation."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Missing preset_name should fail
        with pytest.raises(ValueError, match="Preset name is required"):
            controller.validate_save_request({
                "servers": ["server1"]
            })
        
        # Missing servers should fail
        with pytest.raises(ValueError, match="Servers list is required"):
            controller.validate_save_request({
                "preset_name": "my-preset"
            })
        
        # Empty servers list should fail
        with pytest.raises(ValueError, match="Servers list cannot be empty"):
            controller.validate_save_request({
                "preset_name": "my-preset",
                "servers": []
            })
        
        # Invalid preset name should fail
        with pytest.raises(ValueError, match="Invalid preset name"):
            controller.validate_save_request({
                "preset_name": "minimal",  # Reserved builtin name
                "servers": ["server1"]
            })
        
        # Invalid characters in name should fail
        with pytest.raises(ValueError, match="Invalid characters"):
            controller.validate_save_request({
                "preset_name": "my/preset",
                "servers": ["server1"]
            })
    
    def test_save_preset_events(self):
        """Test that save emits expected events."""
        from src.gui.controllers.preset_controller import PresetController
        from src.gui.events.dispatcher import EventDispatcher
        
        controller = PresetController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Track events
        events_received = []
        dispatcher.subscribe("preset.saving", lambda e: events_received.append(e))
        dispatcher.subscribe("preset.saved", lambda e: events_received.append(e))
        
        controller.save_preset({
            "preset_name": "my-preset",
            "servers": ["server1"]
        })
        
        event_types = [e["type"] for e in events_received]
        assert "preset.saving" in event_types
        assert "preset.saved" in event_types
    
    def test_save_preset_error_handling(self):
        """Test error response format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Simulate error
        mock_preset_manager.save_preset.side_effect = IOError("Cannot write file")
        
        response = controller.save_preset({
            "preset_name": "my-preset",
            "servers": ["server1"]
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]