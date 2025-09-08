"""Contract test for POST /validate endpoint.

This test defines the contract between GUI and library for configuration validation.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestValidateContract:
    """Contract tests for configuration validation."""
    
    def test_validate_request_format(self):
        """Test that validate request has expected format."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "config_path": "/home/user/.claude.json",  # optional, uses default if not provided
            "config_content": None,  # optional, JSON string to validate without file
            "strict": True  # optional, defaults to True
        }
        
        # This should not raise
        controller.validate_config_request(request)
    
    def test_validate_response_format(self):
        """Test that validate response has expected format."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock the response
        mock_config_manager.validate_config.return_value = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        response = controller.validate_config({"mode": "claude"})
        
        # Response must have this structure
        assert "success" in response
        assert "data" in response
        assert "valid" in response["data"]
        assert "errors" in response["data"]
        assert "warnings" in response["data"]
        assert "checked_path" in response["data"]
        assert "mode" in response["data"]
    
    def test_validate_with_errors(self):
        """Test validation with errors."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock validation errors
        mock_config_manager.validate_config.return_value = {
            "valid": False,
            "errors": [
                {
                    "field": "mcpServers.server1.command",
                    "message": "Command field is required",
                    "severity": "error"
                },
                {
                    "field": "mcpServers.server2.args",
                    "message": "Args must be an array",
                    "severity": "error"
                }
            ],
            "warnings": [
                {
                    "field": "mcpServers.server3.env",
                    "message": "Environment variable API_KEY is not set",
                    "severity": "warning"
                }
            ]
        }
        
        response = controller.validate_config({"mode": "claude"})
        
        assert response["success"] is True  # Request succeeded
        assert response["data"]["valid"] is False  # But config is invalid
        assert len(response["data"]["errors"]) == 2
        assert len(response["data"]["warnings"]) == 1
        
        # Each error/warning has expected structure
        for error in response["data"]["errors"]:
            assert "field" in error
            assert "message" in error
            assert "severity" in error
    
    def test_validate_content_without_file(self):
        """Test validating JSON content directly."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        config_content = json.dumps({
            "mcpServers": {
                "test-server": {
                    "command": "node",
                    "args": ["server.js"]
                }
            }
        })
        
        response = controller.validate_config({
            "mode": "claude",
            "config_content": config_content
        })
        
        # Should validate the content
        mock_config_manager.validate_config.assert_called_once()
        call_args = mock_config_manager.validate_config.call_args
        assert "content" in call_args[1] or config_content in str(call_args)
    
    def test_validate_strict_mode(self):
        """Test strict vs non-strict validation."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Strict mode - warnings are errors
        mock_config_manager.validate_config.return_value = {
            "valid": False,
            "errors": [],
            "warnings": [{"message": "Deprecated field used"}]
        }
        
        response = controller.validate_config({
            "mode": "claude",
            "strict": True
        })
        
        assert response["data"]["valid"] is False
        
        # Non-strict mode - warnings don't fail validation
        mock_config_manager.validate_config.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [{"message": "Deprecated field used"}]
        }
        
        response = controller.validate_config({
            "mode": "claude",
            "strict": False
        })
        
        assert response["data"]["valid"] is True
        assert len(response["data"]["warnings"]) > 0
    
    def test_validate_both_mode(self):
        """Test validating both configurations."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock different results for each
        mock_config_manager.validate_config.side_effect = [
            {"valid": True, "errors": [], "warnings": []},  # Claude valid
            {"valid": False, "errors": [{"message": "Invalid"}], "warnings": []}  # Gemini invalid
        ]
        
        response = controller.validate_config({"mode": "both"})
        
        # Should validate both
        assert mock_config_manager.validate_config.call_count == 2
        
        # Response should include both results
        assert "claude" in response["data"]
        assert "gemini" in response["data"]
        assert response["data"]["claude"]["valid"] is True
        assert response["data"]["gemini"]["valid"] is False
        assert response["data"]["valid"] is False  # Overall false if any invalid
    
    def test_validate_schema_checking(self):
        """Test schema validation."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock schema errors
        mock_config_manager.validate_config.return_value = {
            "valid": False,
            "errors": [
                {
                    "field": "mcpServers",
                    "message": "Must be an object",
                    "severity": "error",
                    "schema_violation": True
                }
            ],
            "warnings": []
        }
        
        response = controller.validate_config({"mode": "claude"})
        
        # Should indicate schema violations
        errors = response["data"]["errors"]
        assert any(e.get("schema_violation") for e in errors)
    
    def test_validate_error_handling(self):
        """Test error response format."""
        from src.gui.controllers.config_controller import ConfigController
        
        controller = ConfigController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Simulate error
        mock_config_manager.validate_config.side_effect = FileNotFoundError("Config not found")
        
        response = controller.validate_config({
            "mode": "claude",
            "config_path": "/nonexistent/config.json"
        })
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]
    
    def test_validate_events(self):
        """Test that validate emits expected events."""
        from src.gui.controllers.config_controller import ConfigController
        from src.gui.events.dispatcher import EventDispatcher
        
        controller = ConfigController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Track events
        events_received = []
        dispatcher.subscribe("validation.starting", lambda e: events_received.append(e))
        dispatcher.subscribe("validation.completed", lambda e: events_received.append(e))
        
        controller.validate_config({"mode": "claude"})
        
        event_types = [e["type"] for e in events_received]
        assert "validation.starting" in event_types
        assert "validation.completed" in event_types