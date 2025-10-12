"""Contract test for GET /servers/list endpoint.

This test defines the contract between GUI and library for listing servers.
Tests MUST fail initially and pass only after implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unimplemented
class TestServersListContract:
    """Contract tests for server listing."""
    
    def test_list_servers_request_format(self):
        """Test that list request has expected format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        
        # Request should accept these parameters
        request = {
            "mode": "claude",  # or "gemini" or "both"
            "include_disabled": True,  # optional, defaults to True
            "filter": "context"  # optional filter string
        }
        
        # This should not raise
        controller.validate_list_request(request)
    
    def test_list_servers_response_format(self):
        """Test that list response has expected format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock the response
        mock_server_manager.get_servers.return_value = {
            "active": ["server1", "server2"],
            "disabled": ["server3"]
        }
        
        response = controller.list_servers({"mode": "claude"})
        
        # Response must have this structure
        assert "success" in response
        assert "data" in response
        assert "servers" in response["data"]
        assert "total_count" in response["data"]
        assert "active_count" in response["data"]
        assert "disabled_count" in response["data"]
        
        # Each server must have expected fields
        for server in response["data"]["servers"]:
            assert "name" in server
            assert "enabled" in server
            assert "config" in server
            assert "source" in server  # claude or gemini
            assert "index" in server  # position in list
    
    def test_list_servers_filtering(self):
        """Test server filtering."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Setup mock data
        mock_server_manager.get_servers.return_value = {
            "active": ["context7", "browser-mcp", "filesystem"],
            "disabled": ["git-server"]
        }
        
        # Test with filter
        response = controller.list_servers({
            "mode": "claude",
            "filter": "context"
        })
        
        # Should only return matching servers
        servers = response["data"]["servers"]
        assert len(servers) == 1
        assert servers[0]["name"] == "context7"
    
    def test_list_servers_include_disabled(self):
        """Test include_disabled parameter."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Setup mock data
        mock_server_manager.get_servers.return_value = {
            "active": ["server1"],
            "disabled": ["server2"]
        }
        
        # Test with disabled included
        response = controller.list_servers({
            "mode": "claude",
            "include_disabled": True
        })
        
        assert len(response["data"]["servers"]) == 2
        
        # Test without disabled
        response = controller.list_servers({
            "mode": "claude",
            "include_disabled": False
        })
        
        assert len(response["data"]["servers"]) == 1
        assert response["data"]["servers"][0]["enabled"] is True
    
    def test_list_servers_error_handling(self):
        """Test error response format."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Simulate error
        mock_server_manager.get_servers.side_effect = FileNotFoundError("Config not found")
        
        response = controller.list_servers({"mode": "claude"})
        
        # Error response structure
        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]
    
    def test_list_servers_both_mode(self):
        """Test listing servers in 'both' mode."""
        from src.mcp_config_manager.gui.controllers.server_controller import ServerController
        
        controller = ServerController()
        mock_server_manager = Mock()
        controller.server_manager = mock_server_manager
        
        # Mock both Claude and Gemini servers
        mock_server_manager.get_servers.return_value = {
            "claude": {
                "active": ["server1"],
                "disabled": ["server2"]
            },
            "gemini": {
                "active": ["server3"],
                "disabled": []
            }
        }
        
        response = controller.list_servers({"mode": "both"})
        
        # Should return merged list with source info
        servers = response["data"]["servers"]
        assert len(servers) >= 3
        
        # Each server should have source
        sources = {s["source"] for s in servers}
        assert "claude" in sources
        assert "gemini" in sources