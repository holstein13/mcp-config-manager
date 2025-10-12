"""
Parser for Claude CLI 'mcp add' commands.

Converts commands like:
  claude mcp add firecrawl -e KEY=value -- npx -y firecrawl-mcp

To JSON format:
  {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {"KEY": "value"}
    }
  }
"""

import re
from typing import Dict, Any, List, Tuple, Optional
import shlex


class ClaudeCliParser:
    """Parser for Claude MCP add CLI commands."""

    @staticmethod
    def is_cli_command(text: str) -> bool:
        """
        Check if the input text is a Claude MCP add command.

        Args:
            text: Input text to check

        Returns:
            True if text appears to be a Claude MCP add command
        """
        text = text.strip()
        # Avoid false positives: JSON objects/arrays starting with { or [
        # should not be mistaken for CLI commands even if they contain the prefix
        if text.startswith(('{', '[')):
            return False
        return text.startswith('claude mcp add')

    @staticmethod
    def parse_cli_command(command: str, convert_mcp_remote: bool = False) -> Dict[str, Any]:
        """
        Parse a Claude MCP add command into JSON configuration.

        Args:
            command: CLI command string (e.g., 'claude mcp add servername ...')
            convert_mcp_remote: If True, convert mcp-remote commands to native SSE format.
                               If False (default), keep as command/args.

        Returns:
            Dictionary with server configuration

        Raises:
            ValueError: If command format is invalid
        """
        command = command.strip()

        # Normalize whitespace for prefix check (collapse multiple spaces)
        normalized = ' '.join(command.split())

        # Verify it's a valid command
        if not normalized.startswith('claude mcp add'):
            raise ValueError("Command must start with 'claude mcp add'")

        # Remove 'claude mcp add' prefix (use normalized version)
        command = normalized[len('claude mcp add'):].strip()

        if not command:
            raise ValueError("No server configuration provided after 'claude mcp add'")

        # Parse the command using shlex to handle quoted strings properly
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Failed to parse command: {e}")

        if not tokens:
            raise ValueError("No tokens found after 'claude mcp add'")

        # Extract server name, flags, and command
        server_name, transport, env_vars, _, command_parts = ClaudeCliParser._parse_tokens(tokens)

        # Build the server configuration
        server_config = ClaudeCliParser._build_config(transport, env_vars, command_parts,
                                                      convert_mcp_remote=convert_mcp_remote)

        # Return in the format expected by the add server dialog
        return {
            server_name: server_config
        }

    @staticmethod
    def _parse_tokens(tokens: List[str]) -> Tuple[str, Optional[str], Dict[str, str], Optional[str], List[str]]:
        """
        Parse tokens into server name, flags, and command parts.

        Args:
            tokens: List of command tokens

        Returns:
            Tuple of (server_name, transport, env_vars, scope, command_parts)
        """
        server_name = None
        transport = None
        env_vars = {}
        scope = None
        command_parts = []

        i = 0
        separator_found = False

        while i < len(tokens):
            token = tokens[i]

            # Handle '--' separator
            if token == '--':
                separator_found = True
                i += 1
                # Everything after '--' is the command
                command_parts = tokens[i:]
                break

            # Handle --transport flag
            elif token == '--transport':
                if i + 1 >= len(tokens):
                    raise ValueError("--transport flag requires a value")
                transport = tokens[i + 1]
                i += 2
                continue

            # Handle -e or --env flag
            elif token in ['-e', '--env']:
                if i + 1 >= len(tokens):
                    raise ValueError(f"{token} flag requires a value")
                env_pair = tokens[i + 1]
                key, value = ClaudeCliParser._parse_env_var(env_pair)
                env_vars[key] = value
                i += 2
                continue

            # Handle --scope flag
            elif token == '--scope':
                if i + 1 >= len(tokens):
                    raise ValueError("--scope flag requires a value")
                scope = tokens[i + 1]
                i += 2
                continue

            # If we haven't found the server name yet, this is it
            elif server_name is None:
                server_name = token
                i += 1

            # If transport is 'sse' and we have a URL, it's part of the config
            elif transport == 'sse' and token.startswith('http'):
                # For SSE, the URL is the connection endpoint
                command_parts.append(token)
                i += 1

            else:
                # Unknown token, might be start of command without '--'
                # Treat rest as command
                command_parts = tokens[i:]
                break

        if not server_name:
            raise ValueError("No server name provided")

        return server_name, transport, env_vars, scope, command_parts

    @staticmethod
    def _parse_env_var(env_str: str) -> Tuple[str, str]:
        """
        Parse environment variable string like 'KEY=value'.

        Args:
            env_str: Environment variable string

        Returns:
            Tuple of (key, value)
        """
        if '=' not in env_str:
            raise ValueError(f"Invalid environment variable format: {env_str} (expected KEY=value)")

        key, value = env_str.split('=', 1)
        if not key:
            raise ValueError(f"Invalid environment variable format: {env_str} (key cannot be empty)")

        return key, value

    @staticmethod
    def _build_config(transport: Optional[str], env_vars: Dict[str, str],
                     command_parts: List[str], convert_mcp_remote: bool = False) -> Dict[str, Any]:
        """
        Build server configuration dictionary.

        Args:
            transport: Transport type (e.g., 'sse')
            env_vars: Environment variables dictionary
            command_parts: Command and arguments
            convert_mcp_remote: If True, convert mcp-remote commands to native SSE format

        Returns:
            Server configuration dictionary
        """
        config = {}

        # Handle SSE transport
        if transport == 'sse':
            config['type'] = 'sse'
            if command_parts and (command_parts[0].startswith('https://') or command_parts[0].startswith('http://')):
                config['url'] = command_parts[0]
            else:
                raise ValueError("SSE transport requires a valid URL (http:// or https://)")

        # Handle stdio transport (default)
        else:
            if not command_parts:
                raise ValueError("No command provided for stdio transport")

            # Optionally detect mcp-remote pattern and convert to native SSE format
            # Pattern: npx [-y] mcp-remote <url>
            if convert_mcp_remote and ClaudeCliParser._is_mcp_remote_command(command_parts):
                url = ClaudeCliParser._extract_mcp_remote_url(command_parts)
                config['type'] = 'sse'
                config['url'] = url
            else:
                # Standard stdio command with args
                # First part is the command, rest are args
                config['command'] = command_parts[0]

                if len(command_parts) > 1:
                    config['args'] = command_parts[1:]

        # Add environment variables if any
        if env_vars:
            config['env'] = env_vars

        return config

    @staticmethod
    def _is_mcp_remote_command(command_parts: List[str]) -> bool:
        """
        Check if command is using mcp-remote (indicating SSE server).

        Patterns detected:
        - npx mcp-remote <url>
        - npx -y mcp-remote <url>

        Args:
            command_parts: Command and arguments list

        Returns:
            True if this is an mcp-remote command
        """
        if not command_parts or command_parts[0] != 'npx':
            return False

        # Look for 'mcp-remote' in the args
        return 'mcp-remote' in command_parts

    @staticmethod
    def _extract_mcp_remote_url(command_parts: List[str]) -> str:
        """
        Extract URL from mcp-remote command.

        Args:
            command_parts: Command and arguments list (e.g., ['npx', '-y', 'mcp-remote', 'https://...'])

        Returns:
            The SSE URL

        Raises:
            ValueError: If URL cannot be found
        """
        # Find the index of 'mcp-remote'
        try:
            mcp_remote_index = command_parts.index('mcp-remote')
        except ValueError:
            raise ValueError("mcp-remote not found in command")

        # URL should be the next argument after mcp-remote
        url_index = mcp_remote_index + 1

        if url_index >= len(command_parts):
            raise ValueError("No URL provided after mcp-remote")

        url = command_parts[url_index]

        if not (url.startswith('https://') or url.startswith('http://')):
            raise ValueError(f"Invalid URL for mcp-remote: {url}")

        return url


def parse_cli_to_json(cli_command: str) -> Dict[str, Any]:
    """
    Convenience function to parse CLI command to JSON.

    Args:
        cli_command: Claude MCP add command string

    Returns:
        Dictionary with server configuration

    Raises:
        ValueError: If command format is invalid
    """
    parser = ClaudeCliParser()
    return parser.parse_cli_command(cli_command)
