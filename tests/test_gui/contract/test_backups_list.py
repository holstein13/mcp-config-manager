"""Contract test for GET /backups/list endpoint.

This test defines the contract between GUI and library for listing backups.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@pytest.mark.unimplemented
class TestBackupsListContract:
    """Contract tests for backup listing."""
    
    def test_list_backups_request_format(self):
        """Test that list request has expected format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "limit": 10,  # optional, defaults to all
            "sort": "desc"  # optional, "asc" or "desc", defaults to "desc"
        }
        
        # This should not raise
        controller.validate_list_request(request)
    
    def test_list_backups_response_format(self):
        """Test that list response has expected format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock the response
        mock_config_manager.get_backups.return_value = [
            {
                "path": "/home/user/.claude.json.backup.20240101_120000",
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "size": 2048
            },
            {
                "path": "/home/user/.claude.json.backup.20240102_120000",
                "timestamp": datetime(2024, 1, 2, 12, 0, 0),
                "size": 2560
            }
        ]
        
        response = controller.list_backups({"mode": "claude"})
        
        # Response must have this structure
        assert "success" in response
        assert "data" in response
        assert "backups" in response["data"]
        assert "total_count" in response["data"]
        assert "total_size" in response["data"]
        
        # Each backup must have expected fields
        for backup in response["data"]["backups"]:
            assert "path" in backup
            assert "timestamp" in backup
            assert "size" in backup
            assert "size_readable" in backup  # e.g., "2.0 KB"
            assert "age" in backup  # e.g., "2 days ago"
            assert "mode" in backup  # claude or gemini
    
    def test_list_backups_sorting(self):
        """Test backup sorting."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Setup mock data
        backups = [
            {"timestamp": datetime(2024, 1, 1), "path": "backup1"},
            {"timestamp": datetime(2024, 1, 3), "path": "backup3"},
            {"timestamp": datetime(2024, 1, 2), "path": "backup2"}
        ]
        mock_config_manager.get_backups.return_value = backups
        
        # Test descending sort (newest first)
        response = controller.list_backups({
            "mode": "claude",
            "sort": "desc"
        })
        
        timestamps = [b["timestamp"] for b in response["data"]["backups"]]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Test ascending sort (oldest first)
        response = controller.list_backups({
            "mode": "claude",
            "sort": "asc"
        })
        
        timestamps = [b["timestamp"] for b in response["data"]["backups"]]
        assert timestamps == sorted(timestamps)
    
    def test_list_backups_limit(self):
        """Test backup limit."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Setup many backups
        backups = [
            {"timestamp": datetime(2024, 1, i), "path": f"backup{i}"}
            for i in range(1, 21)
        ]
        mock_config_manager.get_backups.return_value = backups
        
        # Test with limit
        response = controller.list_backups({
            "mode": "claude",
            "limit": 5
        })
        
        assert len(response["data"]["backups"]) == 5
        assert response["data"]["total_count"] == 20  # Still shows total
    
    def test_list_backups_both_mode(self):
        """Test listing backups in 'both' mode."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Mock both Claude and Gemini backups
        mock_config_manager.get_backups.side_effect = [
            [{"timestamp": datetime.now(), "path": "claude_backup"}],
            [{"timestamp": datetime.now(), "path": "gemini_backup"}]
        ]
        
        response = controller.list_backups({"mode": "both"})
        
        # Should return merged list
        backups = response["data"]["backups"]
        assert len(backups) == 2
        
        # Each should have mode indicator
        modes = {b["mode"] for b in backups}
        assert "claude" in modes
        assert "gemini" in modes
    
    def test_list_backups_empty(self):
        """Test empty backup list."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # No backups
        mock_config_manager.get_backups.return_value = []
        
        response = controller.list_backups({"mode": "claude"})
        
        assert response["success"] is True
        assert response["data"]["backups"] == []
        assert response["data"]["total_count"] == 0
        assert response["data"]["total_size"] == 0
    
    def test_list_backups_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.backup_controller import BackupController
        
        controller = BackupController()
        mock_config_manager = Mock()
        controller.config_manager = mock_config_manager
        
        # Simulate error
        mock_config_manager.get_backups.side_effect = OSError("Cannot read directory")
        
        response = controller.list_backups({"mode": "claude"})
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]