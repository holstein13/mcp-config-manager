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
        """Get active servers from config, including project-specific servers"""
        servers = {}

        # Get global servers
        if 'mcpServers' in config:
            servers.update(config['mcpServers'])

        # Get project-specific servers (they are stored under project paths)
        for key, value in config.items():
            if isinstance(value, dict) and 'mcpServers' in value:
                # This is a project-specific configuration
                servers.update(value['mcpServers'])

        return servers
    
    def set_servers(self, config: Dict[str, Any], servers: Dict[str, Any]) -> Dict[str, Any]:
        """Set active servers in config, preserving project structure"""
        # Create a map to track which server belongs to which section
        server_locations = {}

        # First, identify where each existing server is located
        if 'mcpServers' in config:
            for server_name in config['mcpServers']:
                server_locations[server_name] = None  # Global server

        for key, value in config.items():
            if isinstance(value, dict) and 'mcpServers' in value:
                for server_name in value['mcpServers']:
                    server_locations[server_name] = key  # Project-specific server

        # Update servers in their original locations or add to global
        for server_name, server_config in servers.items():
            location = server_locations.get(server_name)
            if location is None:
                # Global server or new server - add to global
                if 'mcpServers' not in config:
                    config['mcpServers'] = {}
                config['mcpServers'][server_name] = server_config
            else:
                # Project-specific server - update in project section
                if location in config and isinstance(config[location], dict):
                    if 'mcpServers' not in config[location]:
                        config[location]['mcpServers'] = {}
                    config[location]['mcpServers'][server_name] = server_config

        # Remove servers that are not in the new set
        all_current_servers = set(self.get_servers(config).keys())
        servers_to_remove = all_current_servers - set(servers.keys())

        for server_name in servers_to_remove:
            location = server_locations.get(server_name)
            if location is None:
                # Global server
                if 'mcpServers' in config and server_name in config['mcpServers']:
                    del config['mcpServers'][server_name]
            else:
                # Project-specific server
                if location in config and isinstance(config[location], dict):
                    if 'mcpServers' in config[location] and server_name in config[location]['mcpServers']:
                        del config[location]['mcpServers'][server_name]

        return config
    
    def add_server(self, config: Dict[str, Any], name: str, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a server to the configuration"""
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        config['mcpServers'][name] = server_config
        return config
    
    def remove_server(self, config: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Remove a server from the configuration, checking all locations"""
        # Check global servers
        if 'mcpServers' in config and name in config['mcpServers']:
            del config['mcpServers'][name]
            return config

        # Check project-specific servers
        for key, value in config.items():
            if isinstance(value, dict) and 'mcpServers' in value:
                if name in value['mcpServers']:
                    del value['mcpServers'][name]
                    return config

        return config
