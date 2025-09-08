"""
Server management functionality
Extracted from mcp_toggle.py
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from ..utils.file_utils import get_disabled_servers_path


class ServerManager:
    """Manages MCP server enabling/disabling and storage"""
    
    def __init__(self, disabled_path: Path = None):
        self.disabled_path = disabled_path or get_disabled_servers_path()
    
    def load_disabled_servers(self) -> Dict[str, Any]:
        """Load disabled servers from storage file"""
        if not self.disabled_path.exists():
            return {}
        
        try:
            with open(self.disabled_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_disabled_servers(self, disabled: Dict[str, Any]) -> None:
        """Save disabled servers to storage file"""
        self.disabled_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.disabled_path, 'w') as f:
            json.dump(disabled, f, indent=2)
    
    def disable_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                      server_name: str, mode: str = 'both') -> bool:
        """Move a server from active to disabled storage"""
        disabled = self.load_disabled_servers()
        server_config = None
        
        # Get server config from appropriate source
        if mode in ['claude', 'both'] and 'mcpServers' in claude_data:
            if server_name in claude_data['mcpServers']:
                server_config = claude_data['mcpServers'][server_name]
                del claude_data['mcpServers'][server_name]
        
        if mode in ['gemini', 'both'] and 'mcpServers' in gemini_data:
            if server_name in gemini_data['mcpServers']:
                if not server_config:
                    server_config = gemini_data['mcpServers'][server_name]
                del gemini_data['mcpServers'][server_name]
        
        if server_config:
            disabled[server_name] = server_config
            self.save_disabled_servers(disabled)
            return True
        
        return False
    
    def enable_server(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                     server_name: str, mode: str = 'both') -> bool:
        """Move a server from disabled storage to active"""
        disabled = self.load_disabled_servers()
        
        if server_name in disabled:
            server_config = disabled[server_name]
            
            # Add to appropriate configs based on mode
            if mode in ['claude', 'both']:
                if 'mcpServers' not in claude_data:
                    claude_data['mcpServers'] = {}
                claude_data['mcpServers'][server_name] = server_config.copy()
            
            if mode in ['gemini', 'both']:
                if 'mcpServers' not in gemini_data:
                    gemini_data['mcpServers'] = {}
                gemini_data['mcpServers'][server_name] = server_config.copy()
            
            del disabled[server_name]
            self.save_disabled_servers(disabled)
            return True
        
        return False
    
    def list_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                        mode: str = 'both') -> Tuple[List[str], List[str]]:
        """List all servers (active and disabled) based on mode"""
        active = set()
        
        if mode in ['claude', 'both']:
            active.update(claude_data.get('mcpServers', {}).keys())
        
        if mode in ['gemini', 'both']:
            active.update(gemini_data.get('mcpServers', {}).keys())
        
        disabled_servers = self.load_disabled_servers()
        disabled = list(disabled_servers.keys())
        
        return sorted(list(active)), disabled
    
    def disable_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                           mode: str = 'both') -> int:
        """Disable all active servers"""
        active, _ = self.list_all_servers(claude_data, gemini_data, mode)
        count = 0
        
        for server in active:
            if self.disable_server(claude_data, gemini_data, server, mode):
                count += 1
        
        return count
    
    def enable_all_servers(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                          mode: str = 'both') -> int:
        """Enable all disabled servers"""
        _, disabled = self.list_all_servers(claude_data, gemini_data, mode)
        count = 0
        
        for server in disabled:
            if self.enable_server(claude_data, gemini_data, server, mode):
                count += 1
        
        return count
    
    def add_new_server_from_json(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                                json_text: str, mode: str = 'both') -> Tuple[bool, str]:
        """Add a new server from JSON configuration"""
        try:
            parsed = json.loads(json_text.strip())
            
            if isinstance(parsed, dict):
                if 'command' in parsed or 'args' in parsed or 'type' in parsed:
                    # Single server config, need server name
                    return False, "Server name required for single server config"
                else:
                    # Multiple servers
                    for server_name, server_config in parsed.items():
                        if isinstance(server_config, dict):
                            self._add_server_to_configs(claude_data, gemini_data, 
                                                       server_name, server_config, mode)
                    return True, f"Added {len(parsed)} servers"
            else:
                return False, "Invalid JSON structure"
                
        except json.JSONDecodeError as e:
            return False, f"JSON parsing failed: {e}"
    
    def add_server_with_name(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                            server_name: str, server_config: Dict[str, Any], 
                            mode: str = 'both') -> bool:
        """Add a server with a specific name"""
        return self._add_server_to_configs(claude_data, gemini_data, server_name, server_config, mode)
    
    def _add_server_to_configs(self, claude_data: Dict[str, Any], gemini_data: Dict[str, Any], 
                              server_name: str, server_config: Dict[str, Any], 
                              mode: str = 'both') -> bool:
        """Internal method to add server to appropriate configs"""
        if mode in ['claude', 'both']:
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            claude_data['mcpServers'][server_name] = server_config
        
        if mode in ['gemini', 'both']:
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            gemini_data['mcpServers'][server_name] = server_config
        
        return True
