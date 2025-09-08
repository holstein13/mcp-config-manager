"""
Preset management functionality
Extracted from mcp_toggle.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from ..utils.file_utils import get_presets_path


class PresetManager:
    """Manages MCP server presets and default configurations"""
    
    def __init__(self, presets_path: Path = None):
        self.presets_path = presets_path or get_presets_path()
        self._ensure_presets_file()
    
    def _ensure_presets_file(self):
        """Ensure presets file exists with default structure"""
        if not self.presets_path.exists():
            default_presets = {
                "presets": {},
                "defaults": {
                    "minimal": ["context7", "browsermcp"],
                    "webdev": ["context7", "browsermcp", "playwright"],
                    "fullstack": ["context7", "browsermcp", "playwright", "supabase", "clerk", "railway"],
                    "testing": ["context7", "playwright", "memory"]
                }
            }
            self.save_presets(default_presets)
    
    def load_presets(self) -> Dict[str, Any]:
        """Load presets from file"""
        try:
            with open(self.presets_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ensure_presets_file()
            return self.load_presets()
    
    def save_presets(self, presets_data: Dict[str, Any]) -> None:
        """Save presets to file"""
        self.presets_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.presets_path, 'w') as f:
            json.dump(presets_data, f, indent=2)
    
    def get_default_servers(self, mode: str) -> List[str]:
        """Get default server list for a mode"""
        presets = self.load_presets()
        defaults = presets.get('defaults', {})
        return defaults.get(mode, [])
    
    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get a specific preset by name"""
        presets = self.load_presets()
        return presets.get('presets', {}).get(preset_name, {})
    
    def save_preset(self, name: str, description: str, servers: Dict[str, Any]) -> None:
        """Save a new preset"""
        presets = self.load_presets()
        if 'presets' not in presets:
            presets['presets'] = {}
        
        presets['presets'][name] = {
            'description': description,
            'servers': servers
        }
        
        self.save_presets(presets)
    
    def list_presets(self) -> List[str]:
        """List all available preset names"""
        presets = self.load_presets()
        return list(presets.get('presets', {}).keys())
    
    def delete_preset(self, preset_name: str) -> bool:
        """Delete a preset"""
        presets = self.load_presets()
        if preset_name in presets.get('presets', {}):
            del presets['presets'][preset_name]
            self.save_presets(presets)
            return True
        return False
