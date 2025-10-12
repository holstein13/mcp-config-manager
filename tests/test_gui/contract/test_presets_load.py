"""Contract test for POST /presets/load endpoint.

This test defines the contract between GUI and library for loading presets.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unimplemented
class TestPresetsLoadContract:
    """Contract tests for preset loading."""
    
    def test_load_preset_request_format(self):
        """Test that load request has expected format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "preset_name": "minimal",
            "merge": False,  # optional, defaults to False (replace mode)
            "save_immediately": False  # optional, defaults to False
        }
        
        # This should not raise
        controller.validate_load_request(request)
    
    def test_load_preset_response_format(self):
        """Test that load response has expected format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Mock the response
        mock_preset_manager.load_preset.return_value = ["context7", "browsermcp"]
        
        response = controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal"
        })
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "preset_name" in response["data"]
        assert "servers_loaded" in response["data"]
        assert "servers_count" in response["data"]
        assert "mode" in response["data"]
        assert "merged" in response["data"]
        assert "saved" in response["data"]
    
    def test_load_preset_merge_mode(self):
        """Test merge vs replace mode."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        mock_server_manager = Mock()
        controller.preset_manager = mock_preset_manager
        controller.server_manager = mock_server_manager
        
        # Setup existing servers
        mock_server_manager.get_servers.return_value = {
            "active": ["existing-server"],
            "disabled": []
        }
        
        # Preset servers
        mock_preset_manager.load_preset.return_value = ["context7", "browsermcp"]
        
        # Test replace mode (default)
        response = controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal",
            "merge": False
        })
        
        # Should disable existing and enable preset servers
        assert response["data"]["merged"] is False
        mock_server_manager.bulk_disable.assert_called_once()
        mock_server_manager.bulk_enable.assert_called_once()
        
        # Reset mocks
        mock_server_manager.reset_mock()
        
        # Test merge mode
        response = controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal",
            "merge": True
        })
        
        # Should only enable preset servers, not disable existing
        assert response["data"]["merged"] is True
        mock_server_manager.bulk_disable.assert_not_called()
        mock_server_manager.bulk_enable.assert_called_once()
    
    def test_load_preset_events(self):
        """Test that load emits expected events."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        from src.mcp_config_manager.gui.events.dispatcher import EventDispatcher
        
        controller = PresetController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Track events
        events_received = []
        dispatcher.subscribe("preset.loading", lambda e: events_received.append(e))
        dispatcher.subscribe("preset.loaded", lambda e: events_received.append(e))
        dispatcher.subscribe("servers.changed", lambda e: events_received.append(e))
        
        controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal"
        })
        
        event_types = [e["type"] for e in events_received]
        assert "preset.loading" in event_types
        assert "preset.loaded" in event_types
        assert "servers.changed" in event_types
    
    def test_load_preset_validation(self):
        """Test request validation."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Missing mode should fail
        with pytest.raises(ValueError, match="Mode is required"):
            controller.validate_load_request({
                "preset_name": "minimal"
            })
        
        # Missing preset_name should fail
        with pytest.raises(ValueError, match="Preset name is required"):
            controller.validate_load_request({
                "mode": "claude"
            })
        
        # Invalid mode should fail
        with pytest.raises(ValueError, match="Invalid mode"):
            controller.validate_load_request({
                "mode": "invalid",
                "preset_name": "minimal"
            })
        
        # Nonexistent preset should fail
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        mock_preset_manager.get_presets.return_value = {"minimal": []}
        
        with pytest.raises(ValueError, match="Preset not found"):
            controller.validate_load_request({
                "mode": "claude",
                "preset_name": "nonexistent"
            })
    
    def test_load_preset_save_immediately(self):
        """Test save_immediately parameter."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        mock_config_manager = Mock()
        controller.preset_manager = mock_preset_manager
        controller.config_manager = mock_config_manager
        
        # Test without immediate save
        controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal",
            "save_immediately": False
        })
        
        mock_config_manager.save_config.assert_not_called()
        
        # Test with immediate save
        controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal",
            "save_immediately": True
        })
        
        mock_config_manager.save_config.assert_called_once()
    
    def test_load_preset_both_mode(self):
        """Test loading preset in 'both' mode."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        mock_server_manager = Mock()
        controller.preset_manager = mock_preset_manager
        controller.server_manager = mock_server_manager
        
        controller.load_preset({
            "mode": "both",
            "preset_name": "minimal"
        })
        
        # Should apply to both configs
        calls = mock_server_manager.bulk_enable.call_args_list
        # Verify both modes were updated
        assert any("claude" in str(c) for c in calls) or len(calls) >= 2
    
    def test_load_preset_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Simulate error
        mock_preset_manager.load_preset.side_effect = Exception("Failed to load preset")
        
        response = controller.load_preset({
            "mode": "claude",
            "preset_name": "minimal"
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]