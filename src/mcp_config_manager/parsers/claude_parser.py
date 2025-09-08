"""
Parser for Claude configuration files (.claude.json)
Enhanced with functionality from mcp_toggle.py
"""

from typing import Dict, Any
from pathlib import Path
import json
from .base_parser import BaseConfigParser


class ClaudeConfigParser(BaseConfigParser):
    """Parser for Claude .claude.json configuration files"""
    
    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse Claude configuration file"""
        if not config_path.exists():
            return {"mcpServers": {}}
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Claude config: {e}")
        except Exception as e:
            raise IOError(f"Error reading Claude config: {e}")
    
    def write(self, config: Dict[str, Any], output_path: Path) -> None:
        """Write Claude configuration file"""
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise IOError(f"Error writing Claude config: {e}")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate Claude configuration structure"""
        if not isinstance(config, dict):
            return False
        
        # Check for mcpServers section
        if 'mcpServers' in config:
            if not isinstance(config['mcpServers'], dict):
                return False
            
            # Validate each server configuration
            for server_name, server_config in config['mcpServers'].items():
                if not isinstance(server_config, dict):
                    return False
                
                # Check for required fields
                if 'command' not in server_config:
                    return False
                
                # Validate args if present
                if 'args' in server_config and not isinstance(server_config['args'], list):
                    return False
                
                # Validate env if present
                if 'env' in server_config and not isinstance(server_config['env'], dict):
                    return False
        
        return True
    
    def get_servers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get active servers from config"""
        return config.get('mcpServers', {})
    
    def set_servers(self, config: Dict[str, Any], servers: Dict[str, Any]) -> Dict[str, Any]:
        """Set active servers in config"""
        config['mcpServers'] = servers
        return config
    
    def add_server(self, config: Dict[str, Any], name: str, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a server to the configuration"""
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        config['mcpServers'][name] = server_config
        return config
    
    def remove_server(self, config: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Remove a server from the configuration"""
        if 'mcpServers' in config and name in config['mcpServers']:
            del config['mcpServers'][name]
        return config
