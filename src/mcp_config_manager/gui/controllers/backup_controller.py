"""Controller for backup and restore operations."""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime
import logging
import os
import json

from mcp_config_manager.core.config_manager import ConfigManager
from mcp_config_manager.core.config_manager import ConfigMode

logger = logging.getLogger(__name__)


class BackupController:
    """Controller for managing backup/restore operations between GUI and library."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the backup controller.
        
        Args:
            config_manager: Optional ConfigManager instance to use
        """
        self.config_manager = config_manager or ConfigManager()
        self.on_backup_created_callbacks: List[Callable] = []
        self.on_backup_restored_callbacks: List[Callable] = []
        self.on_backup_deleted_callbacks: List[Callable] = []
    
    def get_backup_list(self) -> Dict[str, Any]:
        """Get list of available backups.
        
        Returns:
            Dictionary with:
                - success: bool
                - backups: list of backup dictionaries
                - error: error message if failed
        """
        try:
            backups = []
            
            # Get backup directory
            config_path = self.config_manager.claude_parser.config_path if self.config_manager.claude_parser else Path.home() / '.claude.json'
            backup_dir = config_path.parent
            
            # Find all backup files
            backup_pattern = f"{config_path.name}.backup.*"
            for backup_file in backup_dir.glob(backup_pattern):
                try:
                    # Parse timestamp from filename
                    # Format: .claude.json.backup.YYYYMMDD_HHMMSS
                    timestamp_str = backup_file.name.split('.')[-1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Get file info
                    file_stat = backup_file.stat()
                    size_bytes = file_stat.st_size
                    
                    # Try to read server count from backup
                    server_count = 0
                    claude_count = 0
                    gemini_count = 0
                    mode = "Unknown"
                    try:
                        with open(backup_file, 'r') as f:
                            backup_data = json.load(f)
                            if 'mcpServers' in backup_data:
                                claude_count = len(backup_data.get('mcpServers', {}))
                                server_count = claude_count
                                mode = "Claude"
                            elif 'servers' in backup_data:
                                gemini_count = len(backup_data.get('servers', {}))
                                server_count = gemini_count
                                mode = "Gemini"
                            # Check for new format with per-client states
                            if 'disabled_servers' in backup_data:
                                disabled = backup_data['disabled_servers']
                                if isinstance(disabled, dict) and disabled:
                                    # Check if it's the new format with disabled_for
                                    first_value = next(iter(disabled.values()))
                                    if isinstance(first_value, dict) and 'disabled_for' in first_value:
                                        mode = "Both (per-client)"
                    except:
                        pass
                    
                    backups.append({
                        'filename': str(backup_file),
                        'timestamp': timestamp.isoformat(),
                        'size_bytes': size_bytes,
                        'server_count': server_count,
                        'claude_count': claude_count,
                        'gemini_count': gemini_count,
                        'mode': mode,
                        'is_auto': False  # Could be enhanced to detect auto backups
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse backup file {backup_file}: {str(e)}")
                    continue
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'backups': backups
            }
            
        except Exception as e:
            error_msg = f"Failed to get backup list: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'backups': [],
                'error': error_msg
            }
    
    def create_backup(self, description: str = "", client: Optional[str] = None) -> Dict[str, Any]:
        """Create a new backup of current configuration.

        Args:
            description: Optional description for the backup
            client: Optional client to backup ('claude', 'gemini', or None for both)

        Returns:
            Dictionary with:
                - success: bool
                - backup_file: path to created backup
                - error: error message if failed
        """
        try:
            # Create backup (config_manager handles per-client if needed)
            result = self.config_manager.create_backup()

            if result.get('success'):
                backup_file = result.get('backup_file')

                # Notify callbacks
                for callback in self.on_backup_created_callbacks:
                    callback({
                        'backup_file': backup_file,
                        'description': description,
                        'client': client
                    })

                return {
                    'success': True,
                    'backup_file': backup_file
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to create backup')
                }
            
        except Exception as e:
            error_msg = f"Failed to create backup: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def restore_backup(self, backup_file: str, client: Optional[str] = None) -> Dict[str, Any]:
        """Restore configuration from a backup file.

        Args:
            backup_file: Path to backup file to restore
            client: Optional client to restore for ('claude', 'gemini', or None for both)

        Returns:
            Dictionary with:
                - success: bool
                - servers_restored: number of servers restored
                - claude_restored: number of Claude servers restored
                - gemini_restored: number of Gemini servers restored
                - error: error message if failed
        """
        try:
            # Check if backup file exists
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f"Backup file not found: {backup_file}"
                }

            # Create a backup of current config before restoring
            self.config_manager.create_backup()

            # Restore from backup
            result = self.config_manager.restore_backup(backup_file)

            if result.get('success'):
                # Count servers in restored config
                servers_restored = 0
                claude_restored = 0
                gemini_restored = 0
                try:
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                        if 'mcpServers' in backup_data:
                            claude_restored = len(backup_data.get('mcpServers', {}))
                            servers_restored = claude_restored
                        elif 'servers' in backup_data:
                            gemini_restored = len(backup_data.get('servers', {}))
                            servers_restored = gemini_restored
                        # Check for new format with per-client states
                        if 'disabled_servers' in backup_data:
                            disabled = backup_data['disabled_servers']
                            if isinstance(disabled, dict) and disabled:
                                # Count based on disabled_for arrays
                                for server_name, server_data in disabled.items():
                                    if isinstance(server_data, dict) and 'disabled_for' in server_data:
                                        disabled_for = server_data['disabled_for']
                                        if 'claude' not in disabled_for:
                                            claude_restored += 1
                                        if 'gemini' not in disabled_for:
                                            gemini_restored += 1
                                servers_restored = max(claude_restored, gemini_restored)
                except:
                    pass

                # Notify callbacks
                for callback in self.on_backup_restored_callbacks:
                    callback({
                        'backup_file': backup_file,
                        'servers_restored': servers_restored,
                        'claude_restored': claude_restored,
                        'gemini_restored': gemini_restored,
                        'client': client
                    })

                return {
                    'success': True,
                    'servers_restored': servers_restored,
                    'claude_restored': claude_restored,
                    'gemini_restored': gemini_restored
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to restore backup')
                }
            
        except Exception as e:
            error_msg = f"Failed to restore backup: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_backup(self, backup_file: str) -> Dict[str, Any]:
        """Delete a backup file.
        
        Args:
            backup_file: Path to backup file to delete
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f"Backup file not found: {backup_file}"
                }
            
            # Delete the file
            backup_path.unlink()
            
            # Notify callbacks
            for callback in self.on_backup_deleted_callbacks:
                callback({'backup_file': backup_file})
            
            return {'success': True}
            
        except Exception as e:
            error_msg = f"Failed to delete backup: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_old_backups(self, days_old: int = 30) -> Dict[str, Any]:
        """Delete backups older than specified days.
        
        Args:
            days_old: Delete backups older than this many days
            
        Returns:
            Dictionary with:
                - success: bool
                - deleted_count: number of backups deleted
                - error: error message if failed
        """
        try:
            deleted_count = 0
            cutoff_timestamp = datetime.now().timestamp() - (days_old * 86400)
            
            # Get all backups
            backups_result = self.get_backup_list()
            if not backups_result['success']:
                return {
                    'success': False,
                    'error': backups_result.get('error', 'Failed to get backup list')
                }
            
            for backup in backups_result['backups']:
                try:
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(backup['timestamp'])
                    
                    # Check if older than cutoff
                    if timestamp.timestamp() < cutoff_timestamp:
                        # Delete this backup
                        result = self.delete_backup(backup['filename'])
                        if result['success']:
                            deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process backup {backup['filename']}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            error_msg = f"Failed to delete old backups: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def cleanup_backups(self, keep_count: int = 10) -> Dict[str, Any]:
        """Keep only the most recent N backups.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Dictionary with:
                - success: bool
                - deleted_count: number of backups deleted
                - error: error message if failed
        """
        try:
            deleted_count = 0
            
            # Get all backups
            backups_result = self.get_backup_list()
            if not backups_result['success']:
                return {
                    'success': False,
                    'error': backups_result.get('error', 'Failed to get backup list')
                }
            
            backups = backups_result['backups']
            
            # If we have more than keep_count, delete the oldest ones
            if len(backups) > keep_count:
                # Backups are already sorted newest first
                backups_to_delete = backups[keep_count:]
                
                for backup in backups_to_delete:
                    result = self.delete_backup(backup['filename'])
                    if result['success']:
                        deleted_count += 1
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            error_msg = f"Failed to cleanup backups: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_backup_info(self, backup_file: str) -> Dict[str, Any]:
        """Get detailed information about a backup file.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Dictionary with:
                - success: bool
                - info: backup information dictionary
                - error: error message if failed
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f"Backup file not found: {backup_file}"
                }
            
            # Get file info
            file_stat = backup_path.stat()
            
            # Parse timestamp from filename
            timestamp_str = backup_path.name.split('.')[-1]
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            # Read backup content
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Determine type and count servers
            claude_servers = {}
            gemini_servers = {}
            if 'mcpServers' in backup_data:
                mode = "Claude"
                claude_servers = backup_data.get('mcpServers', {})
                servers = claude_servers
            elif 'servers' in backup_data:
                mode = "Gemini"
                gemini_servers = backup_data.get('servers', {})
                servers = gemini_servers
            else:
                mode = "Unknown"
                servers = {}

            # Check for new format with per-client states
            if 'disabled_servers' in backup_data:
                disabled = backup_data['disabled_servers']
                if isinstance(disabled, dict) and disabled:
                    first_value = next(iter(disabled.values()), None)
                    if first_value and isinstance(first_value, dict) and 'disabled_for' in first_value:
                        mode = "Both (per-client)"
                        # Count enabled servers per client
                        for server_name, server_data in disabled.items():
                            if isinstance(server_data, dict) and 'disabled_for' in server_data:
                                disabled_for = server_data['disabled_for']
                                if 'claude' not in disabled_for:
                                    claude_servers[server_name] = server_data.get('config', {})
                                if 'gemini' not in disabled_for:
                                    gemini_servers[server_name] = server_data.get('config', {})
            
            info = {
                'filename': str(backup_path),
                'timestamp': timestamp.isoformat(),
                'size_bytes': file_stat.st_size,
                'mode': mode,
                'server_count': len(servers),
                'servers': list(servers.keys()),
                'claude_count': len(claude_servers),
                'gemini_count': len(gemini_servers),
                'claude_servers': list(claude_servers.keys()),
                'gemini_servers': list(gemini_servers.keys()),
                'has_env_vars': any('env' in s for s in servers.values() if isinstance(s, dict))
            }
            
            return {
                'success': True,
                'info': info
            }
            
        except Exception as e:
            error_msg = f"Failed to get backup info: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def on_backup_created(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for backup created event.
        
        Args:
            callback: Function to call when backup is created
        """
        self.on_backup_created_callbacks.append(callback)
    
    def on_backup_restored(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for backup restored event.
        
        Args:
            callback: Function to call when backup is restored
        """
        self.on_backup_restored_callbacks.append(callback)
    
    def on_backup_deleted(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for backup deleted event.
        
        Args:
            callback: Function to call when backup is deleted
        """
        self.on_backup_deleted_callbacks.append(callback)