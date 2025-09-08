"""Integration test for backup and restore workflow.

This test verifies the complete backup/restore workflow:
1. User creates a backup
2. Backup is saved with timestamp
3. User can list available backups
4. User can restore from backup
5. Configuration is restored correctly
6. Multiple backups are managed properly

This test should FAIL until GUI is implemented.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import json


class TestBackupWorkflow:
    """Test complete backup and restore workflow."""
    
    def test_create_and_restore_backup_workflow(self):
        """Test creating a backup and restoring from it."""
        # This will fail with ModuleNotFoundError until GUI is implemented
        from src.gui.controllers import BackupController, ConfigController, ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState, BackupInfo
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        backup_controller = BackupController(dispatcher, app_state)
        config_controller = ConfigController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track events
        events_received = []
        dispatcher.subscribe('backup.created', lambda e: events_received.append(e))
        dispatcher.subscribe('backup.restored', lambda e: events_received.append(e))
        dispatcher.subscribe('config.loaded', lambda e: events_received.append(e))
        
        # Step 1: Make some changes to config
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'test-server'
        })
        
        server_controller.handle_request({
            'action': 'disable_server',
            'server_name': 'context7'
        })
        
        # Get current state
        current_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        enabled_before = [
            s['name'] for s in current_servers['data']['servers']
            if s['enabled']
        ]
        
        # Step 2: Create backup
        backup_request = {
            'action': 'create_backup',
            'mode': 'claude',
            'description': 'Test backup before changes'
        }
        
        backup_response = backup_controller.handle_request(backup_request)
        
        # Verify backup created
        assert backup_response['success'] is True
        assert 'backup_id' in backup_response['data']
        assert 'timestamp' in backup_response['data']
        assert 'file_path' in backup_response['data']
        
        backup_id = backup_response['data']['backup_id']
        
        # Verify event
        assert any(e.type == 'backup.created' for e in events_received)
        
        # Step 3: Make more changes
        server_controller.handle_request({
            'action': 'disable_server',
            'server_name': 'test-server'
        })
        
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'playwright'
        })
        
        # Step 4: List backups
        list_request = {
            'action': 'list_backups',
            'mode': 'claude'
        }
        
        list_response = backup_controller.handle_request(list_request)
        
        assert list_response['success'] is True
        assert 'backups' in list_response['data']
        assert len(list_response['data']['backups']) > 0
        
        # Find our backup
        our_backup = next(
            b for b in list_response['data']['backups']
            if b['id'] == backup_id
        )
        assert our_backup['description'] == 'Test backup before changes'
        
        # Step 5: Restore from backup
        restore_request = {
            'action': 'restore_backup',
            'backup_id': backup_id,
            'mode': 'claude'
        }
        
        restore_response = backup_controller.handle_request(restore_request)
        
        # Verify restore successful
        assert restore_response['success'] is True
        assert restore_response['data']['backup_id'] == backup_id
        assert 'servers_restored' in restore_response['data']
        
        # Verify events
        assert any(e.type == 'backup.restored' for e in events_received)
        assert any(e.type == 'config.loaded' for e in events_received)
        
        # Step 6: Verify configuration restored
        restored_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        enabled_after = [
            s['name'] for s in restored_servers['data']['servers']
            if s['enabled']
        ]
        
        # Should match state when backup was created
        assert set(enabled_after) == set(enabled_before)
        assert 'test-server' in enabled_after
        assert 'context7' not in enabled_after  # Was disabled before backup
        
    def test_automatic_backup_on_save_workflow(self):
        """Test automatic backup creation when saving."""
        from src.gui.controllers import ConfigController, BackupController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        config_controller = ConfigController(dispatcher, app_state)
        backup_controller = BackupController(dispatcher, app_state)
        
        # Track backup events
        backup_events = []
        dispatcher.subscribe('backup.auto_created', lambda e: backup_events.append(e))
        
        # Make changes
        app_state.has_unsaved_changes = True
        
        # Save configuration (should trigger auto-backup)
        save_response = config_controller.handle_request({
            'action': 'save_config',
            'mode': 'claude',
            'auto_backup': True  # Enable auto-backup
        })
        
        assert save_response['success'] is True
        
        # Verify auto-backup created
        assert 'backup_created' in save_response['data']
        assert save_response['data']['backup_created'] is True
        assert 'backup_id' in save_response['data']
        
        # Verify event
        assert len(backup_events) > 0
        auto_backup_event = backup_events[0]
        assert auto_backup_event.data['automatic'] is True
        
    def test_backup_retention_limit_workflow(self):
        """Test backup retention and cleanup."""
        from src.gui.controllers import BackupController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = BackupController(dispatcher, app_state)
        
        # Track cleanup events
        cleanup_events = []
        dispatcher.subscribe('backup.cleaned_up', lambda e: cleanup_events.append(e))
        
        # Create multiple backups (exceed retention limit)
        backup_ids = []
        max_backups = 10  # Typical retention limit
        
        for i in range(max_backups + 5):
            response = controller.handle_request({
                'action': 'create_backup',
                'mode': 'claude',
                'description': f'Backup {i}'
            })
            backup_ids.append(response['data']['backup_id'])
        
        # List backups
        list_response = controller.handle_request({
            'action': 'list_backups',
            'mode': 'claude'
        })
        
        # Should only keep max_backups most recent
        assert len(list_response['data']['backups']) <= max_backups
        
        # Oldest backups should be removed
        remaining_ids = [b['id'] for b in list_response['data']['backups']]
        for old_id in backup_ids[:5]:  # First 5 should be removed
            assert old_id not in remaining_ids
        
        # Most recent should be kept
        for recent_id in backup_ids[-max_backups:]:
            assert recent_id in remaining_ids
            
        # Verify cleanup event
        assert len(cleanup_events) > 0
        
    def test_restore_with_confirmation_workflow(self):
        """Test restore requires confirmation when unsaved changes exist."""
        from src.gui.controllers import BackupController, ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        from src.gui.dialogs import ConfirmationDialog
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        backup_controller = BackupController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Track confirmation events
        confirmations = []
        dispatcher.subscribe('confirmation.required', lambda e: confirmations.append(e))
        
        # Create a backup
        backup_response = backup_controller.handle_request({
            'action': 'create_backup',
            'mode': 'claude'
        })
        backup_id = backup_response['data']['backup_id']
        
        # Make changes (create unsaved state)
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'new-server'
        })
        assert app_state.has_unsaved_changes is True
        
        # Try to restore (should require confirmation)
        restore_response = backup_controller.handle_request({
            'action': 'restore_backup',
            'backup_id': backup_id,
            'mode': 'claude',
            'force': False
        })
        
        # Should require confirmation
        assert restore_response['success'] is False
        assert 'requires_confirmation' in restore_response['data']
        assert restore_response['data']['requires_confirmation'] is True
        assert 'warning' in restore_response['data']
        
        # Verify confirmation event
        assert len(confirmations) > 0
        
        # Force restore (user confirmed)
        force_response = backup_controller.handle_request({
            'action': 'restore_backup',
            'backup_id': backup_id,
            'mode': 'claude',
            'force': True
        })
        
        assert force_response['success'] is True
        assert app_state.has_unsaved_changes is False  # Reset after restore
        
    def test_backup_file_corruption_handling_workflow(self):
        """Test handling of corrupted backup files."""
        from src.gui.controllers import BackupController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='claude')
        controller = BackupController(dispatcher, app_state)
        
        # Track error events
        errors = []
        dispatcher.subscribe('error.occurred', lambda e: errors.append(e))
        
        # Try to restore from non-existent backup
        restore_response = controller.handle_request({
            'action': 'restore_backup',
            'backup_id': 'non-existent-backup',
            'mode': 'claude'
        })
        
        assert restore_response['success'] is False
        assert 'not found' in restore_response['error'].lower()
        
        # Verify error event
        assert len(errors) > 0
        error_event = errors[0]
        assert error_event.data['type'] == 'backup_not_found'
        
    def test_backup_metadata_workflow(self):
        """Test backup metadata storage and retrieval."""
        from src.gui.controllers import BackupController, ConfigController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='both')  # Test with both mode
        backup_controller = BackupController(dispatcher, app_state)
        config_controller = ConfigController(dispatcher, app_state)
        
        # Create backup with metadata
        backup_response = backup_controller.handle_request({
            'action': 'create_backup',
            'mode': 'both',
            'description': 'Pre-deployment backup',
            'metadata': {
                'version': '1.0.0',
                'author': 'test_user',
                'reason': 'Before major update'
            }
        })
        
        assert backup_response['success'] is True
        backup_id = backup_response['data']['backup_id']
        
        # Get backup details
        details_response = backup_controller.handle_request({
            'action': 'get_backup_details',
            'backup_id': backup_id
        })
        
        assert details_response['success'] is True
        backup_info = details_response['data']['backup']
        
        # Verify metadata preserved
        assert backup_info['description'] == 'Pre-deployment backup'
        assert 'metadata' in backup_info
        assert backup_info['metadata']['version'] == '1.0.0'
        assert backup_info['metadata']['author'] == 'test_user'
        assert backup_info['metadata']['reason'] == 'Before major update'
        
        # Verify backup includes both configs
        assert 'claude_config' in backup_info
        assert 'gemini_config' in backup_info
        assert backup_info['mode'] == 'both'
        
    def test_selective_backup_restore_workflow(self):
        """Test selective restore of specific configurations."""
        from src.gui.controllers import BackupController, ServerController
        from src.gui.events import EventDispatcher
        from src.gui.models import ApplicationState
        
        # Setup in both mode
        dispatcher = EventDispatcher()
        app_state = ApplicationState(mode='both')
        backup_controller = BackupController(dispatcher, app_state)
        server_controller = ServerController(dispatcher, app_state)
        
        # Configure different states for Claude and Gemini
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'claude-server',
            'mode': 'claude'
        })
        
        server_controller.handle_request({
            'action': 'enable_server',
            'server_name': 'gemini-server',
            'mode': 'gemini'
        })
        
        # Create backup of both
        backup_response = backup_controller.handle_request({
            'action': 'create_backup',
            'mode': 'both',
            'description': 'Both configs backup'
        })
        backup_id = backup_response['data']['backup_id']
        
        # Change both configs
        server_controller.handle_request({
            'action': 'disable_all',
            'mode': 'both'
        })
        
        # Selectively restore only Claude config
        restore_response = backup_controller.handle_request({
            'action': 'restore_backup',
            'backup_id': backup_id,
            'mode': 'claude',  # Only restore Claude
            'selective': True
        })
        
        assert restore_response['success'] is True
        assert 'claude_restored' in restore_response['data']
        assert restore_response['data']['claude_restored'] is True
        assert 'gemini_restored' not in restore_response['data']
        
        # Verify Claude restored, Gemini unchanged
        claude_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'claude'
        })
        claude_enabled = [
            s['name'] for s in claude_servers['data']['servers']
            if s['enabled']
        ]
        assert 'claude-server' in claude_enabled
        
        gemini_servers = server_controller.handle_request({
            'action': 'list_servers',
            'mode': 'gemini'
        })
        gemini_enabled = [
            s['name'] for s in gemini_servers['data']['servers']
            if s['enabled']
        ]
        assert 'gemini-server' not in gemini_enabled  # Still disabled