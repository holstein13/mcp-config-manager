"""Controller for preset management operations."""

from typing import Dict, Any, List, Optional, Callable
import logging

from mcp_config_manager.core.config_manager import ConfigManager
from mcp_config_manager.core.config_manager import ConfigMode

logger = logging.getLogger(__name__)


class PresetController:
    """Controller for managing preset operations between GUI and library."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the preset controller.
        
        Args:
            config_manager: Optional ConfigManager instance to use
        """
        self.config_manager = config_manager or ConfigManager()
        self.on_preset_loaded_callbacks: List[Callable] = []
        self.on_preset_saved_callbacks: List[Callable] = []
        self.on_preset_deleted_callbacks: List[Callable] = []
    
    def get_preset_list(self) -> Dict[str, Any]:
        """Get list of available presets.
        
        Returns:
            Dictionary with:
                - success: bool
                - presets: list of preset dictionaries
                - error: error message if failed
        """
        try:
            presets = []
            
            # Get all presets from preset manager
            all_presets = self.config_manager.preset_manager.list_presets()
            
            for preset_name, preset_data in all_presets.items():
                # Count servers
                enabled_count = len(preset_data.get('enabled_servers', {}))
                disabled_count = len(preset_data.get('disabled_servers', {}))
                total_count = enabled_count + disabled_count
                
                presets.append({
                    'name': preset_name,
                    'description': preset_data.get('description', ''),
                    'server_count': total_count,
                    'enabled_count': enabled_count,
                    'disabled_count': disabled_count,
                    'is_builtin': preset_name in ['minimal', 'web_dev', 'data_science', 'full'],
                    'is_favorite': preset_data.get('is_favorite', False),
                    'mode': preset_data.get('mode', 'both')
                })
            
            return {
                'success': True,
                'presets': presets
            }
            
        except Exception as e:
            error_msg = f"Failed to get preset list: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'presets': [],
                'error': error_msg
            }
    
    def load_preset(self, preset_name: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """Load and apply a preset configuration.
        
        Args:
            preset_name: Name of the preset to load
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - servers_enabled: list of enabled server names
                - servers_disabled: list of disabled server names
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            # Apply the preset
            result = self.config_manager.apply_preset(preset_name, config_mode)
            
            if result.get('success'):
                # Get the preset data to return details
                preset_data = self.config_manager.preset_manager.get_preset(preset_name)
                
                servers_enabled = list(preset_data.get('enabled_servers', {}).keys())
                servers_disabled = list(preset_data.get('disabled_servers', {}).keys())
                
                # Notify callbacks
                for callback in self.on_preset_loaded_callbacks:
                    callback({
                        'preset': preset_name,
                        'servers_enabled': servers_enabled,
                        'servers_disabled': servers_disabled,
                        'mode': mode
                    })
                
                return {
                    'success': True,
                    'servers_enabled': servers_enabled,
                    'servers_disabled': servers_disabled
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to load preset')
                }
            
        except Exception as e:
            error_msg = f"Failed to load preset: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def save_preset(self, preset_name: str, description: str = "",
                   mode: Optional[str] = None) -> Dict[str, Any]:
        """Save current configuration as a preset.
        
        Args:
            preset_name: Name for the preset
            description: Description of the preset
            mode: Configuration mode ('claude', 'gemini', 'both', or None for current)
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Determine mode
            if mode:
                mode_map = {
                    'claude': ConfigMode.CLAUDE,
                    'gemini': ConfigMode.GEMINI,
                    'both': ConfigMode.BOTH
                }
                config_mode = mode_map.get(mode.lower(), ConfigMode.BOTH)
            else:
                config_mode = ConfigMode.BOTH
            
            # Get current server configuration
            enabled_servers = self.config_manager.server_manager.get_enabled_servers(config_mode)
            disabled_servers = self.config_manager.server_manager.get_disabled_servers(config_mode)
            
            # Create preset data
            preset_data = {
                'description': description,
                'enabled_servers': enabled_servers,
                'disabled_servers': disabled_servers,
                'mode': config_mode.value
            }
            
            # Save the preset
            result = self.config_manager.preset_manager.save_preset(preset_name, preset_data)
            
            if result.get('success'):
                # Notify callbacks
                for callback in self.on_preset_saved_callbacks:
                    callback({
                        'preset': preset_name,
                        'description': description,
                        'mode': mode
                    })
                
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to save preset')
                }
            
        except Exception as e:
            error_msg = f"Failed to save preset: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_preset(self, preset_name: str) -> Dict[str, Any]:
        """Delete a custom preset.
        
        Args:
            preset_name: Name of the preset to delete
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Check if it's a built-in preset
            builtin_presets = ['minimal', 'web_dev', 'data_science', 'full']
            if preset_name in builtin_presets:
                return {
                    'success': False,
                    'error': f"Cannot delete built-in preset '{preset_name}'"
                }
            
            # Delete the preset
            result = self.config_manager.preset_manager.delete_preset(preset_name)
            
            if result.get('success'):
                # Notify callbacks
                for callback in self.on_preset_deleted_callbacks:
                    callback({'preset': preset_name})
                
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to delete preset')
                }
            
        except Exception as e:
            error_msg = f"Failed to delete preset: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_preset_details(self, preset_name: str) -> Dict[str, Any]:
        """Get detailed information about a preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Dictionary with:
                - success: bool
                - preset: preset data dictionary
                - error: error message if failed
        """
        try:
            preset_data = self.config_manager.preset_manager.get_preset(preset_name)
            
            if preset_data:
                # Format the preset data
                result = {
                    'name': preset_name,
                    'description': preset_data.get('description', ''),
                    'enabled_servers': preset_data.get('enabled_servers', {}),
                    'disabled_servers': preset_data.get('disabled_servers', {}),
                    'mode': preset_data.get('mode', 'both'),
                    'is_builtin': preset_name in ['minimal', 'web_dev', 'data_science', 'full'],
                    'is_favorite': preset_data.get('is_favorite', False)
                }
                
                return {
                    'success': True,
                    'preset': result
                }
            else:
                return {
                    'success': False,
                    'error': f"Preset '{preset_name}' not found"
                }
            
        except Exception as e:
            error_msg = f"Failed to get preset details: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def update_preset(self, preset_name: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing preset.
        
        Args:
            preset_name: Name of the preset to update
            preset_data: New preset data
            
        Returns:
            Dictionary with:
                - success: bool
                - error: error message if failed
        """
        try:
            # Check if it's a built-in preset
            builtin_presets = ['minimal', 'web_dev', 'data_science', 'full']
            if preset_name in builtin_presets:
                return {
                    'success': False,
                    'error': f"Cannot modify built-in preset '{preset_name}'"
                }
            
            # Get existing preset
            existing = self.config_manager.preset_manager.get_preset(preset_name)
            if not existing:
                return {
                    'success': False,
                    'error': f"Preset '{preset_name}' not found"
                }
            
            # Merge with new data
            existing.update(preset_data)
            
            # Save the updated preset
            result = self.config_manager.preset_manager.save_preset(preset_name, existing)
            
            if result.get('success'):
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to update preset')
                }
            
        except Exception as e:
            error_msg = f"Failed to update preset: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def toggle_favorite(self, preset_name: str) -> Dict[str, Any]:
        """Toggle favorite status of a preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Dictionary with:
                - success: bool
                - is_favorite: new favorite status
                - error: error message if failed
        """
        try:
            # Get existing preset
            preset_data = self.config_manager.preset_manager.get_preset(preset_name)
            if not preset_data:
                return {
                    'success': False,
                    'error': f"Preset '{preset_name}' not found"
                }
            
            # Toggle favorite
            current_favorite = preset_data.get('is_favorite', False)
            preset_data['is_favorite'] = not current_favorite
            
            # Save the updated preset
            result = self.config_manager.preset_manager.save_preset(preset_name, preset_data)
            
            if result.get('success'):
                return {
                    'success': True,
                    'is_favorite': preset_data['is_favorite']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to update favorite status')
                }
            
        except Exception as e:
            error_msg = f"Failed to toggle favorite: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def on_preset_loaded(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for preset loaded event.
        
        Args:
            callback: Function to call when preset is loaded
        """
        self.on_preset_loaded_callbacks.append(callback)
    
    def on_preset_saved(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for preset saved event.
        
        Args:
            callback: Function to call when preset is saved
        """
        self.on_preset_saved_callbacks.append(callback)
    
    def on_preset_deleted(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for preset deleted event.
        
        Args:
            callback: Function to call when preset is deleted
        """
        self.on_preset_deleted_callbacks.append(callback)