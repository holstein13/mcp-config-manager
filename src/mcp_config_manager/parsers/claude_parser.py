"""
Parser for Claude configuration files (.claude.json)
Enhanced with functionality from mcp_toggle.py
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
import logging
from .base_parser import BaseConfigParser

logger = logging.getLogger(__name__)


class ClaudeConfigParser(BaseConfigParser):
    """Parser for Claude .claude.json configuration files"""
    
    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse Claude configuration file"""
        if not config_path.exists():
            return {"mcpServers": {}}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
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

            with open(output_path, 'w', encoding='utf-8') as f:
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

                # Validate args if present
                if 'args' in server_config and not isinstance(server_config['args'], list):
                    return False

                # Validate env if present
                if 'env' in server_config and not isinstance(server_config['env'], dict):
                    return False

                # Validate headers if present (for http/sse)
                if 'headers' in server_config and not isinstance(server_config['headers'], dict):
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

    def discover_project_servers(self, config_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all project-specific MCP servers in the Claude configuration.

        Returns:
            Dict mapping project paths to list of server configurations.
            Each server config includes 'name' and 'config' keys.
        """
        project_servers = {}

        try:
            config = self.parse(config_path)

            # Iterate through all top-level keys looking for project paths
            for key, value in config.items():
                # Skip the global mcpServers key
                if key == 'mcpServers':
                    continue

                # Check if this looks like a project path (starts with /)
                if isinstance(key, str) and key.startswith('/'):
                    if isinstance(value, dict) and 'mcpServers' in value:
                        servers = []
                        for server_name, server_config in value['mcpServers'].items():
                            servers.append({
                                'name': server_name,
                                'config': server_config
                            })
                        if servers:
                            project_servers[key] = servers
                            logger.debug(f"Found {len(servers)} servers in project: {key}")

        except Exception as e:
            logger.error(f"Error discovering project servers: {e}")

        return project_servers

    def get_server_location(self, config_path: Path, server_name: str) -> Optional[str]:
        """
        Identify if a server is global or project-specific.

        Returns:
            None for global servers, project path string for project-specific servers,
            or None if server not found.
        """
        try:
            config = self.parse(config_path)

            # Check global servers first
            if 'mcpServers' in config and server_name in config['mcpServers']:
                return None  # Global server

            # Check project-specific servers
            for key, value in config.items():
                if key != 'mcpServers' and isinstance(value, dict):
                    if 'mcpServers' in value and server_name in value['mcpServers']:
                        return key  # Return the project path

        except Exception as e:
            logger.error(f"Error getting server location: {e}")

        return None  # Server not found

    def promote_to_global(self, config_path: Path, server_name: str, project_path: str) -> bool:
        """
        Move a project-specific server to the global configuration.

        Args:
            config_path: Path to the Claude configuration file
            server_name: Name of the server to promote
            project_path: Project path where the server is currently located

        Returns:
            True if successful, False otherwise
        """
        try:
            config = self.parse(config_path)

            # Find the server in the project configuration
            if project_path not in config:
                logger.warning(f"Project path {project_path} not found in config")
                return False

            project_config = config[project_path]
            if not isinstance(project_config, dict) or 'mcpServers' not in project_config:
                logger.warning(f"No mcpServers found in project {project_path}")
                return False

            if server_name not in project_config['mcpServers']:
                logger.warning(f"Server {server_name} not found in project {project_path}")
                return False

            # Get the server configuration
            server_config = project_config['mcpServers'][server_name]

            # Check if server already exists in global
            if 'mcpServers' not in config:
                config['mcpServers'] = {}

            if server_name in config['mcpServers']:
                logger.warning(f"Server {server_name} already exists in global config")
                return False

            # Move server to global
            config['mcpServers'][server_name] = server_config
            del project_config['mcpServers'][server_name]

            # Clean up empty project config if needed
            if not project_config['mcpServers']:
                del project_config['mcpServers']
            if not project_config:
                del config[project_path]

            # Write updated config
            self.write(config, config_path)
            logger.info(f"Promoted server {server_name} from {project_path} to global")
            return True

        except Exception as e:
            logger.error(f"Error promoting server to global: {e}")
            return False

    def get_all_server_locations(self, config_path: Path) -> Dict[str, List[str]]:
        """
        Get a mapping of server names to their locations (global and/or project paths).

        Returns:
            Dict mapping server name to list of locations.
            'global' represents global configuration, otherwise project paths.
        """
        server_locations = {}

        try:
            config = self.parse(config_path)

            # Check global servers
            if 'mcpServers' in config:
                for server_name in config['mcpServers']:
                    if server_name not in server_locations:
                        server_locations[server_name] = []
                    server_locations[server_name].append('global')

            # Check project-specific servers
            for key, value in config.items():
                if key != 'mcpServers' and isinstance(value, dict):
                    if 'mcpServers' in value:
                        for server_name in value['mcpServers']:
                            if server_name not in server_locations:
                                server_locations[server_name] = []
                            server_locations[server_name].append(key)

        except Exception as e:
            logger.error(f"Error getting all server locations: {e}")

        return server_locations

    def scan_for_project_configs(self, base_path: Path, max_depth: int = 3) -> List[Path]:
        """
        Scan filesystem for .claude.json files that might contain project configs.

        Args:
            base_path: Starting path for the scan
            max_depth: Maximum directory depth to scan

        Returns:
            List of paths to .claude.json files found
        """
        project_configs = []

        try:
            # Use rglob with max depth control
            pattern = '.claude.json'

            def scan_dir(path: Path, current_depth: int = 0):
                if current_depth > max_depth:
                    return

                try:
                    for item in path.iterdir():
                        if item.is_file() and item.name == pattern:
                            project_configs.append(item)
                        elif item.is_dir() and not item.name.startswith('.'):
                            # Skip hidden directories
                            scan_dir(item, current_depth + 1)
                except PermissionError:
                    # Skip directories we can't access
                    pass

            scan_dir(base_path)
            logger.info(f"Found {len(project_configs)} .claude.json files in {base_path}")

        except Exception as e:
            logger.error(f"Error scanning for project configs: {e}")

        return project_configs
