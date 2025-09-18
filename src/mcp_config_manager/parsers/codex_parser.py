"""Parser for Codex configuration files (config.toml)."""

from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from .base_parser import BaseConfigParser

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    import tomli as tomllib  # type: ignore

import toml

logger = logging.getLogger(__name__)

_ServerConfig = Dict[str, Any]


class CodexConfigParser(BaseConfigParser):
    """Parser for Codex `config.toml` configuration files."""

    TOP_LEVEL_SERVER_KEY = "mcpServers"
    TOML_SERVER_KEY = "mcp_servers"
    PROJECTS_KEY = "projects"

    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse Codex TOML configuration file into the internal dict format."""
        if not config_path.exists():
            return {self.TOP_LEVEL_SERVER_KEY: {}}

        try:
            with config_path.open("rb") as handle:
                toml_data = tomllib.load(handle)
        except (tomllib.TOMLDecodeError, ValueError) as exc:  # type: ignore[attr-defined]
            raise ValueError(f"Invalid TOML in Codex config: {exc}") from exc
        except Exception as exc:  # pragma: no cover - unlikely
            raise IOError(f"Error reading Codex config: {exc}") from exc

        internal = self._toml_to_internal(toml_data)
        logger.debug("Parsed Codex config %s -> %d servers", config_path, len(internal.get(self.TOP_LEVEL_SERVER_KEY, {})))
        return internal

    def write(self, config: Dict[str, Any], output_path: Path) -> None:
        """Write the internal configuration dict back to Codex TOML format."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            toml_payload = self._internal_to_toml(config)
            with output_path.open("w", encoding="utf-8") as handle:
                toml.dump(toml_payload, handle)
        except Exception as exc:  # pragma: no cover - file system failure
            raise IOError(f"Error writing Codex config: {exc}") from exc

    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate that the provided configuration matches expected structure."""
        if not isinstance(config, dict):
            return False

        servers = config.get(self.TOP_LEVEL_SERVER_KEY) or config.get(self.TOML_SERVER_KEY)
        if servers is not None and not isinstance(servers, dict):
            return False

        if isinstance(servers, dict):
            for name, server_config in servers.items():
                if not isinstance(server_config, dict):
                    logger.debug("Codex server %s has invalid config type %s", name, type(server_config))
                    return False
                if not self._is_valid_server_config(server_config):
                    logger.debug("Codex server %s failed structural validation", name)
                    return False

        projects = config.get(self.PROJECTS_KEY)
        if projects is not None:
            if not isinstance(projects, dict):
                return False
            for project_path, project_config in projects.items():
                if not isinstance(project_config, dict):
                    logger.debug("Project %s has invalid config type %s", project_path, type(project_config))
                    return False
                servers_block = project_config.get(self.TOP_LEVEL_SERVER_KEY) or project_config.get(self.TOML_SERVER_KEY)
                if servers_block is not None and not isinstance(servers_block, dict):
                    return False
                if isinstance(servers_block, dict):
                    for name, server_config in servers_block.items():
                        if not isinstance(server_config, dict) or not self._is_valid_server_config(server_config):
                            return False
        return True

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def _toml_to_internal(self, toml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TOML payload into Claude/Gemini-style internal structure."""
        internal: Dict[str, Any] = {}

        internal[self.TOP_LEVEL_SERVER_KEY] = self._convert_server_table(
            toml_data.get(self.TOML_SERVER_KEY, {})
        )

        # Translate project-specific sections
        projects = toml_data.get(self.PROJECTS_KEY)
        if isinstance(projects, dict):
            converted_projects: Dict[str, Any] = {}
            for project_path, project_config in projects.items():
                if not isinstance(project_config, dict):
                    continue
                converted_entry: Dict[str, Any] = {}
                converted_entry[self.TOP_LEVEL_SERVER_KEY] = self._convert_server_table(
                    project_config.get(self.TOML_SERVER_KEY, {})
                )
                for key, value in project_config.items():
                    if key != self.TOML_SERVER_KEY:
                        converted_entry[key] = deepcopy(value)
                converted_projects[project_path] = converted_entry
            if converted_projects:
                internal[self.PROJECTS_KEY] = converted_projects

        # Copy any remaining root-level keys that Codex might use (e.g. model, profile)
        for key, value in toml_data.items():
            if key in (self.TOML_SERVER_KEY, self.PROJECTS_KEY):
                continue
            internal[key] = deepcopy(value)

        return internal

    def _internal_to_toml(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal representation back into Codex TOML layout."""
        toml_payload: Dict[str, Any] = {}

        servers = config.get(self.TOP_LEVEL_SERVER_KEY) or config.get(self.TOML_SERVER_KEY)
        toml_payload[self.TOML_SERVER_KEY] = self._convert_server_table_for_toml(servers or {})

        projects = config.get(self.PROJECTS_KEY, {})
        if isinstance(projects, dict) and projects:
            toml_projects: Dict[str, Any] = {}
            for project_path, project_config in projects.items():
                if not isinstance(project_config, dict):
                    continue
                toml_entry: Dict[str, Any] = {}
                servers_block = project_config.get(self.TOP_LEVEL_SERVER_KEY) or project_config.get(self.TOML_SERVER_KEY)
                toml_entry[self.TOML_SERVER_KEY] = self._convert_server_table_for_toml(servers_block or {})
                for key, value in project_config.items():
                    if key in (self.TOP_LEVEL_SERVER_KEY, self.TOML_SERVER_KEY):
                        continue
                    toml_entry[key] = deepcopy(value)
                toml_projects[project_path] = toml_entry
            if toml_projects:
                toml_payload[self.PROJECTS_KEY] = toml_projects

        for key, value in config.items():
            if key in (self.TOP_LEVEL_SERVER_KEY, self.TOML_SERVER_KEY, self.PROJECTS_KEY):
                continue
            toml_payload[key] = deepcopy(value)

        return toml_payload

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _convert_server_table(self, servers: Any) -> Dict[str, _ServerConfig]:
        """Normalize server table from TOML into internal dict."""
        result: Dict[str, _ServerConfig] = {}
        if not isinstance(servers, dict):
            return result

        for name, server_config in servers.items():
            if not isinstance(server_config, dict):
                continue
            normalized: _ServerConfig = {}
            for key, value in server_config.items():
                if key in ("env", "headers"):
                    normalized[key] = dict(value) if isinstance(value, dict) else {}
                elif key == "args":
                    normalized[key] = list(value) if isinstance(value, (list, tuple)) else []
                else:
                    normalized[key] = deepcopy(value)
            result[name] = normalized
        return result

    def _convert_server_table_for_toml(self, servers: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare server table for TOML serialization."""
        result: Dict[str, Any] = {}
        if not isinstance(servers, dict):
            return result

        for name, server_config in servers.items():
            if not isinstance(server_config, dict):
                continue
            toml_entry: Dict[str, Any] = {}

            # Ensure type field is present (default to stdio)
            server_type = server_config.get("type", "stdio")
            toml_entry["type"] = server_type

            # Ensure required fields based on type
            if server_type == "stdio":
                # stdio requires command
                if "command" in server_config:
                    toml_entry["command"] = server_config["command"]
                elif not server_config.get("command"):
                    # Provide a default or skip this server
                    logger.warning(f"Server '{name}' of type stdio missing command field, skipping")
                    continue
            elif server_type == "http":
                # http requires url, but Codex also seems to require command
                if "url" in server_config:
                    toml_entry["url"] = server_config["url"]
                else:
                    logger.warning(f"Server '{name}' of type http missing url field, skipping")
                    continue
                # Add command for http servers (Codex requirement)
                if "command" not in server_config:
                    toml_entry["command"] = "curl"  # Default command for HTTP servers
                    toml_entry["args"] = []

            # Copy other fields
            for key, value in server_config.items():
                if key in ("type", "command", "url"):  # Already handled above
                    if key not in toml_entry:  # Only add if not already set
                        toml_entry[key] = value
                elif key == "args":
                    toml_entry[key] = list(value) if isinstance(value, (list, tuple)) else []
                elif key in ("env", "headers"):
                    toml_entry[key] = dict(value) if isinstance(value, dict) else {}
                else:
                    toml_entry[key] = deepcopy(value)

            result[name] = toml_entry
        return result

    def _is_valid_server_config(self, server_config: Dict[str, Any]) -> bool:
        """Lightweight validation for a single server configuration."""
        server_type = server_config.get("type", "stdio")  # Default to stdio if not specified

        # Check required fields based on type
        if server_type == "stdio":
            if not server_config.get("command"):
                logger.debug(f"Server config missing required 'command' field for stdio type")
                return False
        elif server_type == "http":
            if not server_config.get("url"):
                logger.debug(f"Server config missing required 'url' field for http type")
                return False
            # Note: Codex also requires 'command' for http servers, but we'll add a default in conversion

        # Validate field types
        if "args" in server_config and not isinstance(server_config["args"], (list, tuple)):
            logger.debug(f"Server config 'args' field is not a list: {type(server_config['args'])}")
            return False
        if "env" in server_config and not isinstance(server_config["env"], dict):
            logger.debug(f"Server config 'env' field is not a dict: {type(server_config['env'])}")
            return False
        if "headers" in server_config and not isinstance(server_config["headers"], dict):
            logger.debug(f"Server config 'headers' field is not a dict: {type(server_config['headers'])}")
            return False
        if "enabled" in server_config and not isinstance(server_config["enabled"], bool):
            logger.debug(f"Server config 'enabled' field is not a bool: {type(server_config['enabled'])}")
            return False

        return True

    # Public convenience helpers ------------------------------------------------

    def get_servers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Return the global server table from the configuration."""
        return config.get(self.TOP_LEVEL_SERVER_KEY, {})

    def set_servers(self, config: Dict[str, Any], servers: Dict[str, Any]) -> Dict[str, Any]:
        """Replace the global server table in the configuration."""
        config[self.TOP_LEVEL_SERVER_KEY] = servers
        return config

    def add_server(self, config: Dict[str, Any], name: str, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add or replace a server definition."""
        servers = config.setdefault(self.TOP_LEVEL_SERVER_KEY, {})
        servers[name] = server_config
        return config

    def remove_server(self, config: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Remove a server definition if it exists."""
        servers = config.get(self.TOP_LEVEL_SERVER_KEY)
        if isinstance(servers, dict) and name in servers:
            del servers[name]
        return config
