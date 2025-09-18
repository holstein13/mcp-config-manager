"""
Project Server Discovery Service for finding and managing project-specific MCP servers.
"""

from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
import json
import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ProjectServer:
    """Represents an MCP server found in a project configuration."""
    name: str
    project_path: Path
    config: Dict[str, Any]
    is_duplicate: bool = False
    discovered_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'project_path': str(self.project_path),
            'config': self.config,
            'is_duplicate': self.is_duplicate,
            'discovered_at': self.discovered_at.isoformat()
        }


class ProjectDiscoveryService:
    """Service for discovering and managing project-specific MCP servers."""

    def __init__(self, claude_parser=None):
        """
        Initialize the discovery service.

        Args:
            claude_parser: Optional ClaudeConfigParser instance
        """
        self._cache: Dict[str, List[ProjectServer]] = {}
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
        self._scan_lock = threading.Lock()
        self._progress_callback = None
        self.claude_parser = claude_parser

    def set_progress_callback(self, callback):
        """
        Set a callback for progress reporting during scans.

        Args:
            callback: Function(current: int, total: int, message: str)
        """
        self._progress_callback = callback

    def scan_projects(self, base_paths: List[Path] = None, max_depth: int = 3,
                      use_cache: bool = True) -> Dict[str, List[ProjectServer]]:
        """
        Scan for all project paths with MCP servers.

        Args:
            base_paths: List of paths to scan. Defaults to user home and common project dirs
            max_depth: Maximum directory depth to scan
            use_cache: Whether to use cached results if available

        Returns:
            Dict mapping project path to list of ProjectServer objects
        """
        # Check cache first
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached project server data")
            return self._cache

        with self._scan_lock:
            # Double-check cache after acquiring lock
            if use_cache and self._is_cache_valid():
                return self._cache

            # Default scan paths if none provided
            if base_paths is None:
                home = Path.home()
                base_paths = [
                    home / "Projects",
                    home / "Documents" / "Projects",
                    home / "Code",
                    home / "Development",
                    home / "repos",
                    home / "workspace"
                ]
                # Filter to existing directories
                base_paths = [p for p in base_paths if p.exists()]

            project_servers = {}
            all_server_names = set()

            # First pass: collect all servers
            total_paths = len(base_paths)
            for idx, base_path in enumerate(base_paths):
                if self._progress_callback:
                    self._progress_callback(
                        idx, total_paths,
                        f"Scanning {base_path.name}..."
                    )

                servers = self._scan_single_path(base_path, max_depth)
                for project_path, server_list in servers.items():
                    if project_path not in project_servers:
                        project_servers[project_path] = []
                    project_servers[project_path].extend(server_list)

                    # Track all server names for duplicate detection
                    for server in server_list:
                        all_server_names.add(server.name)

            # Second pass: mark duplicates
            server_name_counts = {}
            for project_path, servers in project_servers.items():
                for server in servers:
                    if server.name not in server_name_counts:
                        server_name_counts[server.name] = 0
                    server_name_counts[server.name] += 1

            for project_path, servers in project_servers.items():
                for server in servers:
                    if server_name_counts[server.name] > 1:
                        server.is_duplicate = True

            # Update cache
            self._cache = project_servers
            self._cache_expiry = datetime.now() + self._cache_duration

            if self._progress_callback:
                total_servers = sum(len(servers) for servers in project_servers.values())
                self._progress_callback(
                    total_paths, total_paths,
                    f"Found {total_servers} servers in {len(project_servers)} projects"
                )

            logger.info(f"Discovered {len(project_servers)} projects with MCP servers")
            return project_servers

    def _scan_single_path(self, base_path: Path, max_depth: int) -> Dict[str, List[ProjectServer]]:
        """
        Scan a single path for project configurations.

        Args:
            base_path: Path to scan
            max_depth: Maximum directory depth

        Returns:
            Dict mapping project path to list of ProjectServer objects
        """
        project_servers = {}

        if not self.claude_parser:
            logger.warning("No Claude parser available for scanning")
            return project_servers

        try:
            # Find all .claude.json files
            claude_configs = self.claude_parser.scan_for_project_configs(base_path, max_depth)

            for config_path in claude_configs:
                try:
                    # Parse the configuration
                    config = self.claude_parser.parse(config_path)

                    # Look for project-specific servers
                    for key, value in config.items():
                        # Skip global mcpServers
                        if key == 'mcpServers':
                            continue

                        # Check if this is a project path with servers
                        if isinstance(key, str) and key.startswith('/'):
                            if isinstance(value, dict) and 'mcpServers' in value:
                                project_path = Path(key)
                                servers = []

                                for server_name, server_config in value['mcpServers'].items():
                                    servers.append(ProjectServer(
                                        name=server_name,
                                        project_path=project_path,
                                        config=server_config,
                                        is_duplicate=False
                                    ))

                                if servers:
                                    project_servers[str(project_path)] = servers

                except Exception as e:
                    logger.error(f"Error parsing config at {config_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning path {base_path}: {e}")

        return project_servers

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if not self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry

    def clear_cache(self):
        """Clear the cached discovery data."""
        self._cache.clear()
        self._cache_expiry = None
        logger.debug("Cleared project discovery cache")

    def get_project_servers_by_name(self, server_name: str) -> List[ProjectServer]:
        """
        Get all instances of a server across different projects.

        Args:
            server_name: Name of the server to find

        Returns:
            List of ProjectServer objects with matching name
        """
        matching_servers = []

        for project_path, servers in self._cache.items():
            for server in servers:
                if server.name == server_name:
                    matching_servers.append(server)

        return matching_servers

    def get_duplicate_servers(self) -> Dict[str, List[ProjectServer]]:
        """
        Get all servers that appear in multiple projects.

        Returns:
            Dict mapping server name to list of ProjectServer objects
        """
        duplicates = {}

        # Group servers by name
        servers_by_name: Dict[str, List[ProjectServer]] = {}
        for project_path, servers in self._cache.items():
            for server in servers:
                if server.name not in servers_by_name:
                    servers_by_name[server.name] = []
                servers_by_name[server.name].append(server)

        # Filter to only duplicates
        for name, servers in servers_by_name.items():
            if len(servers) > 1:
                duplicates[name] = servers

        return duplicates

    def scan_projects_async(self, base_paths: List[Path] = None,
                            max_depth: int = 3,
                            callback=None):
        """
        Scan for projects asynchronously in a background thread.

        Args:
            base_paths: List of paths to scan
            max_depth: Maximum directory depth
            callback: Function to call when scan completes with results
        """
        def _scan_thread():
            try:
                results = self.scan_projects(base_paths, max_depth, use_cache=False)
                if callback:
                    callback(results, None)
            except Exception as e:
                logger.error(f"Error in async scan: {e}")
                if callback:
                    callback(None, e)

        thread = threading.Thread(target=_scan_thread, daemon=True)
        thread.start()
        return thread

    def export_discovery_report(self, output_path: Path) -> bool:
        """
        Export a discovery report to JSON.

        Args:
            output_path: Path to write the report

        Returns:
            True if successful, False otherwise
        """
        try:
            report = {
                'scan_timestamp': datetime.now().isoformat(),
                'total_projects': len(self._cache),
                'total_servers': sum(len(servers) for servers in self._cache.values()),
                'projects': {}
            }

            for project_path, servers in self._cache.items():
                report['projects'][project_path] = [
                    server.to_dict() for server in servers
                ]

            # Find duplicates
            duplicates = self.get_duplicate_servers()
            report['duplicates'] = {
                name: [server.to_dict() for server in servers]
                for name, servers in duplicates.items()
            }

            # Write report
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Exported discovery report to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting discovery report: {e}")
            return False