"""Contract test for POST /servers/bulk endpoint.

This test defines the contract between GUI and library for bulk server operations.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestServersBulkContract:
    """Contract tests for bulk server operations."""
    
    def test_bulk_operation_request_format(self):
        """Test that bulk request has expected format."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "operation": "enable",  # or "disable", "remove", "toggle"
            "servers": ["server1", "server2", "server3"],  # list of server names
            "save_immediately": False  # optional, defaults to False
        }
        
        # This should not raise
        controller.validate_bulk_request(request)
    
    def test_bulk_enable_response_format(self):
        """Test that bulk enable response has expected format."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock the response
        mock_server_manager.bulk_enable.return_value = {
            "succeeded": ["server1", "server2"],
            "failed": []
        }
        
        response = controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": ["server1", "server2"]
        })
        
        # Response must have this structure
        assert "success" in response
        assert "data" in response
        assert "operation" in response["data"]
        assert "succeeded" in response["data"]
        assert "failed" in response["data"]
        assert "total" in response["data"]
        assert "saved" in response["data"]
    
    def test_bulk_disable_all(self):
        """Test disable all servers operation."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock getting all servers
        mock_server_manager.get_servers.return_value = {
            "active": ["server1", "server2", "server3"],
            "disabled": []
        }
        
        response = controller.bulk_operation({
            "mode": "claude",
            "operation": "disable",
            "servers": "*"  # Special value for all servers
        })
        
        # Should disable all active servers
        mock_server_manager.bulk_disable.assert_called_once()
        call_args = mock_server_manager.bulk_disable.call_args
        assert len(call_args[0][0]) == 3  # All 3 servers
    
    def test_bulk_enable_all(self):
        """Test enable all servers operation."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock getting all servers
        mock_server_manager.get_servers.return_value = {
            "active": [],
            "disabled": ["server1", "server2", "server3"]
        }
        
        response = controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": "*"  # Special value for all servers
        })
        
        # Should enable all disabled servers
        mock_server_manager.bulk_enable.assert_called_once()
        call_args = mock_server_manager.bulk_enable.call_args
        assert len(call_args[0][0]) == 3  # All 3 servers
    
    def test_bulk_operation_events(self):
        """Test that bulk operations emit expected events."""
        from src.gui.controllers.server_controller import ServerController
        from src.gui.events.dispatcher import EventDispatcher
        
        controller = ServerController()
        dispatcher = EventDispatcher()
        controller.dispatcher = dispatcher
        
        # Track events
        events_received = []
        dispatcher.subscribe("bulk.starting", lambda e: events_received.append(e))
        dispatcher.subscribe("bulk.progress", lambda e: events_received.append(e))
        dispatcher.subscribe("bulk.completed", lambda e: events_received.append(e))
        
        controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": ["server1", "server2"]
        })
        
        event_types = [e["type"] for e in events_received]
        assert "bulk.starting" in event_types
        assert "bulk.completed" in event_types
    
    def test_bulk_operation_validation(self):
        """Test request validation."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Invalid operation should fail
        with pytest.raises(ValueError, match="Invalid operation"):
            controller.validate_bulk_request({
                "mode": "claude",
                "operation": "invalid",
                "servers": []
            })
        
        # Missing servers should fail
        with pytest.raises(ValueError, match="Servers list is required"):
            controller.validate_bulk_request({
                "mode": "claude",
                "operation": "enable"
            })
        
        # Empty servers list should fail (unless "*")
        with pytest.raises(ValueError, match="Servers list cannot be empty"):
            controller.validate_bulk_request({
                "mode": "claude",
                "operation": "enable",
                "servers": []
            })
    
    def test_bulk_operation_partial_failure(self):
        """Test handling of partial failures."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock partial failure
        mock_server_manager.bulk_enable.return_value = {
            "succeeded": ["server1"],
            "failed": [("server2", "Not found"), ("server3", "Permission denied")]
        }
        
        response = controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": ["server1", "server2", "server3"]
        })
        
        # Response should indicate partial success
        assert response["success"] is True  # Overall operation succeeded
        assert len(response["data"]["succeeded"]) == 1
        assert len(response["data"]["failed"]) == 2
        
        # Failed items should have error details
        for failure in response["data"]["failed"]:
            assert "server" in failure
            assert "reason" in failure
    
    def test_bulk_operation_save_immediately(self):
        """Test save_immediately parameter."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        mock_config_manager = Mock()
        controller.server_manager = mock_server_manager
        controller.config_manager = mock_config_manager
        
        # Test without immediate save
        controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": ["server1"],
            "save_immediately": False
        })
        
        mock_config_manager.save_config.assert_not_called()
        
        # Test with immediate save
        controller.bulk_operation({
            "mode": "claude",
            "operation": "enable",
            "servers": ["server1"],
            "save_immediately": True
        })
        
        mock_config_manager.save_config.assert_called_once()
    
    def test_bulk_remove_operation(self):
        """Test bulk remove operation."""
        from src.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        response = controller.bulk_operation({
            "mode": "claude",
            "operation": "remove",
            "servers": ["server1", "server2"]
        })
        
        # Should call remove for each server
        mock_server_manager.remove_server.assert_called()
        assert mock_server_manager.remove_server.call_count == 2