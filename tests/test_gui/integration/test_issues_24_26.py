"""Integration tests for Issues #24 and #26.

Issue #24: GUI adds _client_enablement server when adding via JSON
Issue #26: GUI cannot delete servers properly

These tests verify the fixes for:
- Extracting and removing _client_enablement metadata before adding servers
- Per-client deletion respecting user's checkbox selections
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
import logging
from pathlib import Path


class TestIssue24ClientEnablementMetadata:
    """Test that _client_enablement metadata is properly handled (Issue #24)."""

    @patch('mcp_config_manager.gui.main_window.USING_QT', False)
    @patch('mcp_config_manager.gui.main_window.AddServerDialog')
    def test_add_server_extracts_client_enablement_metadata(self, mock_dialog_class):
        """Test that _client_enablement is extracted and not added as a server."""
        from mcp_config_manager.gui.main_window import MainWindow

        # Mock the dialog to return JSON with _client_enablement
        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance

        server_json = {
            'test-server': {
                'command': 'npx',
                'args': ['-y', '@test/server']
            },
            '_client_enablement': {
                'claude': True,
                'gemini': False
            }
        }
        mock_dialog_instance.show.return_value = server_json.copy()

        # Mock server controller
        mock_controller = Mock()
        mock_controller.add_server.return_value = {
            'success': True,
            'server_names': ['test-server']
        }

        # Create window and inject mocked controller
        window = MainWindow()
        window.server_controller = mock_controller

        # Call add_server
        window.add_server()

        # Verify _client_enablement was extracted (not in the JSON passed to controller)
        mock_controller.add_server.assert_called_once()
        passed_json, mode = mock_controller.add_server.call_args[0]

        # _client_enablement should NOT be in the server JSON
        assert '_client_enablement' not in passed_json

        # Only the actual server should be present
        assert 'test-server' in passed_json
        assert passed_json['test-server']['command'] == 'npx'

        # Mode should be 'claude' (based on metadata: claude=True, gemini=False)
        assert mode == 'claude'

    @patch('mcp_config_manager.gui.main_window.USING_QT', False)
    @patch('mcp_config_manager.gui.main_window.AddServerDialog')
    def test_add_server_both_clients_enabled(self, mock_dialog_class):
        """Test mode='both' when both clients are enabled in metadata."""
        from mcp_config_manager.gui.main_window import MainWindow

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance

        server_json = {
            'test-server': {
                'command': 'npx',
                'args': ['-y', '@test/server']
            },
            '_client_enablement': {
                'claude': True,
                'gemini': True
            }
        }
        mock_dialog_instance.show.return_value = server_json.copy()

        mock_controller = Mock()
        mock_controller.add_server.return_value = {
            'success': True,
            'server_names': ['test-server']
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.add_server()

        # Mode should be 'both'
        _, mode = mock_controller.add_server.call_args[0]
        assert mode == 'both'

    @patch('mcp_config_manager.gui.main_window.USING_QT', False)
    @patch('mcp_config_manager.gui.main_window.AddServerDialog')
    def test_add_server_gemini_only(self, mock_dialog_class):
        """Test mode='gemini' when only Gemini is enabled."""
        from mcp_config_manager.gui.main_window import MainWindow

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance

        server_json = {
            'test-server': {
                'command': 'npx',
                'args': ['-y', '@test/server']
            },
            '_client_enablement': {
                'claude': False,
                'gemini': True
            }
        }
        mock_dialog_instance.show.return_value = server_json.copy()

        mock_controller = Mock()
        mock_controller.add_server.return_value = {
            'success': True,
            'server_names': ['test-server']
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.add_server()

        _, mode = mock_controller.add_server.call_args[0]
        assert mode == 'gemini'

    @patch('mcp_config_manager.gui.main_window.USING_QT', False)
    @patch('mcp_config_manager.gui.main_window.AddServerDialog')
    def test_add_server_no_metadata_defaults_to_both(self, mock_dialog_class):
        """Test that missing _client_enablement defaults to mode='both'."""
        from mcp_config_manager.gui.main_window import MainWindow

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance

        # No _client_enablement in the JSON
        server_json = {
            'test-server': {
                'command': 'npx',
                'args': ['-y', '@test/server']
            }
        }
        mock_dialog_instance.show.return_value = server_json.copy()

        mock_controller = Mock()
        mock_controller.add_server.return_value = {
            'success': True,
            'server_names': ['test-server']
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.add_server()

        _, mode = mock_controller.add_server.call_args[0]
        assert mode == 'both'

    @patch('mcp_config_manager.gui.main_window.USING_QT', False)
    @patch('mcp_config_manager.gui.main_window.AddServerDialog')
    def test_add_server_neither_client_defaults_to_both(self, mock_dialog_class):
        """Test that both=False in metadata still defaults to 'both' (defensive)."""
        from mcp_config_manager.gui.main_window import MainWindow

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance

        server_json = {
            'test-server': {
                'command': 'npx',
                'args': ['-y', '@test/server']
            },
            '_client_enablement': {
                'claude': False,
                'gemini': False
            }
        }
        mock_dialog_instance.show.return_value = server_json.copy()

        mock_controller = Mock()
        mock_controller.add_server.return_value = {
            'success': True,
            'server_names': ['test-server']
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.add_server()

        _, mode = mock_controller.add_server.call_args[0]
        assert mode == 'both'


class TestIssue26PerClientDeletion:
    """Test per-client deletion respects user selections (Issue #26)."""

    @patch('mcp_config_manager.gui.main_window.USING_QT', True)
    @patch('mcp_config_manager.gui.main_window.QMessageBox')
    @patch('mcp_config_manager.gui.main_window.DeleteServersDialog')
    def test_delete_servers_uses_client_selections(self, mock_dialog_class, mock_qmessagebox):
        """Test that deletion respects per-client checkbox selections."""
        from mcp_config_manager.gui.main_window import MainWindow
        from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus

        # Mock server list items with per-client enablement
        server_item = ServerListItem(
            name='test-server',
            status=ServerStatus.ENABLED,
            claude_enabled=True,
            gemini_enabled=True,
            config={'command': 'npx', 'args': ['-y', '@test/server']}
        )

        # Mock controller to return server list
        mock_controller = Mock()
        mock_controller.get_servers.return_value = {
            'success': True,
            'data': {'servers': [server_item]}
        }
        mock_controller.delete_server.return_value = {'success': True}

        # Mock delete dialog to simulate user selecting Claude only
        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_selected_servers.return_value = ['test-server']
        mock_dialog_instance.get_client_selections.return_value = {
            'test-server': {'claude': True, 'gemini': False}
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.refresh_server_list = Mock()
        window.set_unsaved_changes = Mock()
        window.set_status_message = Mock()

        # Call delete_servers
        window.delete_servers()

        # Verify delete was called with mode='claude' (not 'both')
        mock_controller.delete_server.assert_called_once_with('test-server', 'claude')

    @patch('mcp_config_manager.gui.main_window.USING_QT', True)
    @patch('mcp_config_manager.gui.main_window.QMessageBox')
    @patch('mcp_config_manager.gui.main_window.DeleteServersDialog')
    def test_delete_servers_both_clients(self, mock_dialog_class, mock_qmessagebox):
        """Test deletion from both clients when both checkboxes selected."""
        from mcp_config_manager.gui.main_window import MainWindow
        from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus

        server_item = ServerListItem(
            name='test-server',
            status=ServerStatus.ENABLED,
            claude_enabled=True,
            gemini_enabled=True,
            config={'command': 'npx', 'args': ['-y', '@test/server']}
        )

        mock_controller = Mock()
        mock_controller.get_servers.return_value = {
            'success': True,
            'data': {'servers': [server_item]}
        }
        mock_controller.delete_server.return_value = {'success': True}

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_selected_servers.return_value = ['test-server']
        # Both clients selected
        mock_dialog_instance.get_client_selections.return_value = {
            'test-server': {'claude': True, 'gemini': True}
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.refresh_server_list = Mock()
        window.set_unsaved_changes = Mock()
        window.set_status_message = Mock()

        window.delete_servers()

        mock_controller.delete_server.assert_called_once_with('test-server', 'both')

    @patch('mcp_config_manager.gui.main_window.USING_QT', True)
    @patch('mcp_config_manager.gui.main_window.QMessageBox')
    @patch('mcp_config_manager.gui.main_window.DeleteServersDialog')
    def test_delete_servers_gemini_only(self, mock_dialog_class, mock_qmessagebox):
        """Test deletion from Gemini only."""
        from mcp_config_manager.gui.main_window import MainWindow
        from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus

        server_item = ServerListItem(
            name='test-server',
            status=ServerStatus.ENABLED,
            claude_enabled=True,
            gemini_enabled=True,
            config={'command': 'npx', 'args': ['-y', '@test/server']}
        )

        mock_controller = Mock()
        mock_controller.get_servers.return_value = {
            'success': True,
            'data': {'servers': [server_item]}
        }
        mock_controller.delete_server.return_value = {'success': True}

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_selected_servers.return_value = ['test-server']
        mock_dialog_instance.get_client_selections.return_value = {
            'test-server': {'claude': False, 'gemini': True}
        }

        window = MainWindow()
        window.server_controller = mock_controller
        window.refresh_server_list = Mock()
        window.set_unsaved_changes = Mock()
        window.set_status_message = Mock()

        window.delete_servers()

        mock_controller.delete_server.assert_called_once_with('test-server', 'gemini')

    @patch('mcp_config_manager.gui.main_window.USING_QT', True)
    @patch('mcp_config_manager.gui.main_window.QMessageBox')
    @patch('mcp_config_manager.gui.main_window.DeleteServersDialog')
    def test_delete_servers_neither_client_skips_with_warning(self, mock_dialog_class, mock_qmessagebox, caplog):
        """Test that neither client selected skips deletion and logs warning."""
        from mcp_config_manager.gui.main_window import MainWindow
        from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus

        server_item = ServerListItem(
            name='test-server',
            status=ServerStatus.ENABLED,
            claude_enabled=True,
            gemini_enabled=True,
            config={'command': 'npx', 'args': ['-y', '@test/server']}
        )

        mock_controller = Mock()
        mock_controller.get_servers.return_value = {
            'success': True,
            'data': {'servers': [server_item]}
        }

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_dialog_instance.exec.return_value = True
        mock_dialog_instance.get_selected_servers.return_value = ['test-server']
        # Neither client selected (edge case)
        mock_dialog_instance.get_client_selections.return_value = {
            'test-server': {'claude': False, 'gemini': False}
        }

        with caplog.at_level(logging.WARNING):
            window = MainWindow()
            window.server_controller = mock_controller
            window.refresh_server_list = Mock()
            window.set_unsaved_changes = Mock()
            window.set_status_message = Mock()

            window.delete_servers()

        # Should NOT call delete_server
        mock_controller.delete_server.assert_not_called()

        # Should log a warning
        assert any("skipped" in record.message.lower() for record in caplog.records)

    @patch('mcp_config_manager.gui.main_window.USING_QT', True)
    @patch('mcp_config_manager.gui.main_window.DeleteServersDialog')
    def test_delete_servers_passes_client_flags_to_dialog(self, mock_dialog_class):
        """Test that claude_enabled and gemini_enabled are passed to DeleteServersDialog."""
        from mcp_config_manager.gui.main_window import MainWindow
        from mcp_config_manager.gui.models.server_list_item import ServerListItem, ServerStatus

        # Create server items with different client enablement
        server1 = ServerListItem(
            name='server1',
            status=ServerStatus.ENABLED,
            claude_enabled=True,
            gemini_enabled=False,
            config={'command': 'npx'}
        )
        server2 = ServerListItem(
            name='server2',
            status=ServerStatus.ENABLED,
            claude_enabled=False,
            gemini_enabled=True,
            config={'command': 'npx'}
        )

        mock_controller = Mock()
        mock_controller.get_servers.return_value = {
            'success': True,
            'data': {'servers': [server1, server2]}
        }

        mock_dialog_instance = Mock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_dialog_instance.exec.return_value = False  # User cancels

        window = MainWindow()
        window.server_controller = mock_controller

        window.delete_servers()

        # Verify dialog was created with correct server info including client flags
        call_args = mock_dialog_class.call_args
        servers_dict = call_args[0][1]  # Second positional arg

        assert 'server1' in servers_dict
        assert servers_dict['server1']['claude_enabled'] is True
        assert servers_dict['server1']['gemini_enabled'] is False

        assert 'server2' in servers_dict
        assert servers_dict['server2']['claude_enabled'] is False
        assert servers_dict['server2']['gemini_enabled'] is True
