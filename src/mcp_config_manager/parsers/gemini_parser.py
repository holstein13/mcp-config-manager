"""
Parser for Gemini configuration files (.gemini/settings.json)
Enhanced with functionality from mcp_toggle.py
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
from .base_parser import BaseConfigParser


class GeminiConfigParser(BaseConfigParser):
    """Parser for Gemini settings.json configuration files"""
    
    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse Gemini configuration file"""
        if not config_path.exists():
            return {"mcpServers": {}, "googleCloudProject": None}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure googleCloudProject field exists
                if 'googleCloudProject' not in data:
                    data['googleCloudProject'] = None
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Gemini config: {e}")
        except Exception as e:
            raise IOError(f"Error reading Gemini config: {e}")
    
    def write(self, config: Dict[str, Any], output_path: Path) -> None:
        """Write Gemini configuration file"""
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise IOError(f"Error writing Gemini config: {e}")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate Gemini configuration structure"""
        if not isinstance(config, dict):
            return False
        
        # Gemini can have mcpServers at root level or nested
        if 'mcpServers' in config:
            return self._validate_servers(config['mcpServers'])
        
        return True
    
    def _validate_servers(self, servers: Dict[str, Any]) -> bool:
        """Validate server configurations"""
        if not isinstance(servers, dict):
            return False

        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                return False

            # Check for required fields based on server type
            server_type = server_config.get('type', 'stdio')

            if server_type == 'stdio':
                # stdio servers require command
                if 'command' not in server_config:
                    return False
            elif server_type in ('http', 'sse'):
                # http/sse servers require url, command is optional
                if 'url' not in server_config:
                    return False

            # Validate field types if present
            if 'args' in server_config and not isinstance(server_config['args'], list):
                return False
            if 'env' in server_config and not isinstance(server_config['env'], dict):
                return False
            if 'headers' in server_config and not isinstance(server_config['headers'], dict):
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

    def get_google_cloud_project(self, config: Dict[str, Any]) -> Optional[str]:
        """Get the Google Cloud Project ID from config"""
        return config.get('googleCloudProject')

    def set_google_cloud_project(self, config: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Set the Google Cloud Project ID in config"""
        config['googleCloudProject'] = project_id
        return config
