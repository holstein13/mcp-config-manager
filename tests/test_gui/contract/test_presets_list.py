"""Contract test for GET /presets/list endpoint.

This test defines the contract between GUI and library for listing presets.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPresetsListContract:
    """Contract tests for preset listing."""
    
    def test_list_presets_request_format(self):
        """Test that list request has expected format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        
        # Request should accept these parameters
        request = {
            "include_builtin": True,  # optional, defaults to True
            "include_custom": True,  # optional, defaults to True
        }
        
        # This should not raise
        controller.validate_list_request(request)
    
    def test_list_presets_response_format(self):
        """Test that list response has expected format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Mock the response
        mock_preset_manager.get_presets.return_value = {
            "minimal": ["context7", "browsermcp"],
            "web-dev": ["context7", "browsermcp", "playwright"],
            "custom-preset": ["server1", "server2"]
        }
        
        response = controller.list_presets(request={})
        
        # Response must have this structure
        assert "success" in response
        assert "data" in response
        assert "presets" in response["data"]
        assert "total_count" in response["data"]
        assert "builtin_count" in response["data"]
        assert "custom_count" in response["data"]
        
        # Each preset must have expected fields
        for preset in response["data"]["presets"]:
            assert "name" in preset
            assert "servers" in preset
            assert "is_builtin" in preset
            assert "description" in preset
            assert "server_count" in preset
    
    def test_list_presets_builtin_filtering(self):
        """Test filtering builtin presets."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Setup mock data
        mock_preset_manager.get_presets.return_value = {
            "minimal": ["context7"],  # builtin
            "web-dev": ["playwright"],  # builtin
            "custom": ["server1"]  # custom
        }
        
        # Test with only builtin
        response = controller.list_presets({
            "include_builtin": True,
            "include_custom": False
        })
        
        presets = response["data"]["presets"]
        assert all(p["is_builtin"] for p in presets)
        assert len(presets) == 2
        
        # Test with only custom
        response = controller.list_presets({
            "include_builtin": False,
            "include_custom": True
        })
        
        presets = response["data"]["presets"]
        assert all(not p["is_builtin"] for p in presets)
        assert len(presets) == 1
    
    def test_list_presets_descriptions(self):
        """Test preset descriptions."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        mock_preset_manager.get_presets.return_value = {
            "minimal": ["context7", "browsermcp"],
            "web-dev": ["context7", "browsermcp", "playwright"]
        }
        
        response = controller.list_presets({})
        
        # Builtin presets should have descriptions
        presets = response["data"]["presets"]
        minimal = next(p for p in presets if p["name"] == "minimal")
        assert "Minimal" in minimal["description"] or "Basic" in minimal["description"]
        
        web_dev = next(p for p in presets if p["name"] == "web-dev")
        assert "Web" in web_dev["description"] or "Development" in web_dev["description"]
    
    def test_list_presets_error_handling(self):
        """Test error response format."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # Simulate error
        mock_preset_manager.get_presets.side_effect = FileNotFoundError("Presets file not found")
        
        response = controller.list_presets({})
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]
    
    def test_list_presets_empty(self):
        """Test empty preset list."""
        from src.gui.controllers.preset_controller import PresetController
        
        controller = PresetController()
        mock_preset_manager = Mock()
        controller.preset_manager = mock_preset_manager
        
        # No presets
        mock_preset_manager.get_presets.return_value = {}
        
        response = controller.list_presets({})
        
        assert response["success"] is True
        assert response["data"]["presets"] == []
        assert response["data"]["total_count"] == 0