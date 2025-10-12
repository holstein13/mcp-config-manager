"""Contract test for POST /backups/create endpoint.

This test defines the contract between GUI and library for creating backups.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path


@pytest.mark.unimplemented
class TestBackupsCreateContract:
    """Contract tests for backup creation."""
    
    def test_create_backup_request_format(self):
        """Test that create request has expected format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "description": "Manual backup before major changes",  # optional
            "compress": False  # optional, defaults to False
        }
        
        # This should not raise
        controller.validate_create_request(request)
    
    def test_create_backup_response_format(self):
        """Test that create response has expected format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock the response
        backup_path = "/home/user/.claude.json.backup.20240101_120000"
        mock_config_manager.create_backup.return_value = backup_path
        
        response = controller.create_backup({"mode": "claude"})
        
        # Response must have this structure
        assert "success" in response
        assert response["success"] is True
        assert "data" in response
        assert "backup_path" in response["data"]
        assert "timestamp" in response["data"]
        assert "size" in response["data"]
        assert "mode" in response["data"]
        assert "description" in response["data"]
        assert "compressed" in response["data"]
    
    def test_create_backup_with_description(self):
        """Test backup with description."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        description = "Before upgrading to v2.0"
        response = controller.create_backup({
            "mode": "claude",
            "description": description
        })
        
        # Description should be stored
        assert response["data"]["description"] == description
        
        # Should be passed to manager
        mock_config_manager.create_backup.assert_called_with(
            mode="claude",
            description=description,
            compress=False
        )
    
    def test_create_backup_compression(self):
        """Test backup compression option."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Test with compression
        backup_path = "/home/user/.claude.json.backup.20240101_120000.gz"
        mock_config_manager.create_backup.return_value = backup_path
        
        response = controller.create_backup({
            "mode": "claude",
            "compress": True
        })
        
        assert response["data"]["compressed"] is True
        assert response["data"]["backup_path"].endswith(".gz")
        
        # Should pass compress flag
        mock_config_manager.create_backup.assert_called_with(
            mode="claude",
            description=None,
            compress=True
        )
    
    def test_create_backup_both_mode(self):
        """Test creating backups in 'both' mode."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock creating both backups
        mock_config_manager.create_backup.side_effect = [
            "/home/user/.claude.json.backup.20240101_120000",
            "/home/user/.gemini.json.backup.20240101_120000"
        ]
        
        response = controller.create_backup({"mode": "both"})
        
        # Should create both backups
        assert mock_config_manager.create_backup.call_count == 2
        
        # Response should include both
        assert response["success"] is True
        assert "backups" in response["data"]
        assert len(response["data"]["backups"]) == 2
        
        # Each should have mode
        modes = {b["mode"] for b in response["data"]["backups"]}
        assert "claude" in modes
        assert "gemini" in modes
    
    def test_create_backup_events(self):
        """Test that create emits expected events."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        from src.mcp_config_manager.gui.events.dispatcher import EventDispatcher
        
        controller = BackupController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Track events
        events_received = []
        dispatcher.subscribe("backup.creating", lambda e: events_received.append(e))
        dispatcher.subscribe("backup.created", lambda e: events_received.append(e))
        
        controller.create_backup({"mode": "claude"})
        
        event_types = [e["type"] for e in events_received]
        assert "backup.creating" in event_types
        assert "backup.created" in event_types
    
    def test_create_backup_validation(self):
        """Test request validation."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        
        # Missing mode should fail
        with pytest.raises(ValueError, match="Mode is required"):
            controller.validate_create_request({})
        
        # Invalid mode should fail
        with pytest.raises(ValueError, match="Invalid mode"):
            controller.validate_create_request({"mode": "invalid"})
    
    def test_create_backup_disk_space_check(self):
        """Test disk space checking."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Simulate low disk space
        mock_config_manager.check_disk_space.return_value = False
        
        response = controller.create_backup({"mode": "claude"})
        
        # Should warn about disk space
        assert response["success"] is False
        assert "disk space" in response["error"]["message"].lower()
    
    def test_create_backup_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Simulate error
        mock_config_manager.create_backup.side_effect = PermissionError("Cannot write backup")
        
        response = controller.create_backup({"mode": "claude"})
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]