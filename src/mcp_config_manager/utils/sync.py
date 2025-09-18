"""
Synchronization utilities for MCP configurations
"""

from typing import Dict, Any, Set


def sync_server_configs(claude_data: Dict[str, Any], gemini_data: Dict[str, Any], codex_data: Dict[str, Any] = None) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Synchronize servers between Claude, Gemini, and optionally Codex configs.

    This maintains backward compatibility - if codex_data is None, it performs
    the original two-way sync and returns None as the third element.
    """
    # Check if we're doing three-way sync
    if codex_data is not None:
        return sync_three_way(claude_data, gemini_data, codex_data)

    # Original two-way sync logic
    all_servers = set()
    all_servers.update(claude_data.get('mcpServers', {}).keys())
    all_servers.update(gemini_data.get('mcpServers', {}).keys())

    # Sync servers to both configs
    for server in all_servers:
        if server in claude_data.get('mcpServers', {}):
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            if server not in gemini_data['mcpServers']:
                gemini_data['mcpServers'][server] = claude_data['mcpServers'][server].copy()
        elif server in gemini_data.get('mcpServers', {}):
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            if server not in claude_data['mcpServers']:
                claude_data['mcpServers'][server] = gemini_data['mcpServers'][server].copy()

    return claude_data, gemini_data, None


def sync_three_way(claude_data: Dict[str, Any], gemini_data: Dict[str, Any], codex_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Perform three-way synchronization between Claude, Gemini, and Codex configs.

    This function ensures all three configurations have the same set of servers,
    while preserving client-specific settings.
    """
    # Get all unique servers from all three configs
    all_servers = set()
    all_servers.update(claude_data.get('mcpServers', {}).keys())
    all_servers.update(gemini_data.get('mcpServers', {}).keys())
    all_servers.update(codex_data.get('mcp_servers', {}).keys())  # Note: Codex uses underscore

    # Sync servers to all configs
    for server in all_servers:
        # Find the source of truth (first config that has this server)
        source_config = None
        source_data = None

        if server in claude_data.get('mcpServers', {}):
            source_config = 'claude'
            source_data = claude_data['mcpServers'][server]
        elif server in gemini_data.get('mcpServers', {}):
            source_config = 'gemini'
            source_data = gemini_data['mcpServers'][server]
        elif server in codex_data.get('mcp_servers', {}):
            source_config = 'codex'
            source_data = codex_data['mcp_servers'][server]

        if source_data:
            # Copy to Claude if missing
            if server not in claude_data.get('mcpServers', {}):
                if 'mcpServers' not in claude_data:
                    claude_data['mcpServers'] = {}
                claude_data['mcpServers'][server] = _convert_for_claude(source_data, source_config)

            # Copy to Gemini if missing
            if server not in gemini_data.get('mcpServers', {}):
                if 'mcpServers' not in gemini_data:
                    gemini_data['mcpServers'] = {}
                gemini_data['mcpServers'][server] = _convert_for_gemini(source_data, source_config)

            # Copy to Codex if missing (note the underscore in mcp_servers)
            if server not in codex_data.get('mcp_servers', {}):
                if 'mcp_servers' not in codex_data:
                    codex_data['mcp_servers'] = {}
                codex_data['mcp_servers'][server] = _convert_for_codex(source_data, source_config)

    return claude_data, gemini_data, codex_data


def _convert_for_claude(server_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Convert server data to Claude format."""
    if source == 'claude':
        return server_data.copy()

    result = {}

    # Common fields
    if 'command' in server_data:
        result['command'] = server_data['command']
    if 'args' in server_data:
        result['args'] = server_data['args']
    if 'env' in server_data:
        result['env'] = server_data['env']

    # Handle Codex-specific fields
    if source == 'codex':
        # Codex might have 'headers' for HTTP servers
        if 'headers' in server_data:
            # Claude doesn't directly support headers, add as comment or env
            if 'env' not in result:
                result['env'] = {}
            result['env']['_HEADERS'] = str(server_data['headers'])

    return result


def _convert_for_gemini(server_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Convert server data to Gemini format."""
    if source == 'gemini':
        return server_data.copy()

    # Gemini uses same format as Claude
    return _convert_for_claude(server_data, source)


def _convert_for_codex(server_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Convert server data to Codex format.

    Codex has some specific requirements:
    - Uses 'command' and 'args' for stdio servers
    - Can have 'headers' for HTTP servers
    - Environment variables in 'env' table
    """
    if source == 'codex':
        return server_data.copy()

    result = {}

    # Common fields
    if 'command' in server_data:
        result['command'] = server_data['command']
    if 'args' in server_data:
        result['args'] = server_data['args']
    if 'env' in server_data:
        result['env'] = server_data['env']
        # Remove any special markers we might have added
        if '_HEADERS' in result['env']:
            del result['env']['_HEADERS']

    return result


def resolve_sync_conflicts(claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                          codex_data: Dict[str, Any], strategy: str = 'merge') -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Resolve conflicts when syncing configurations.

    Strategies:
    - 'merge': Keep all servers from all configs (default)
    - 'claude': Claude config takes precedence
    - 'gemini': Gemini config takes precedence
    - 'codex': Codex config takes precedence
    """
    if strategy == 'merge':
        # Default behavior - merge all servers
        return sync_three_way(claude_data, gemini_data, codex_data)
    elif strategy == 'claude':
        # Claude takes precedence - copy Claude servers to others
        for server, config in claude_data.get('mcpServers', {}).items():
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            gemini_data['mcpServers'][server] = config.copy()

            if 'mcp_servers' not in codex_data:
                codex_data['mcp_servers'] = {}
            codex_data['mcp_servers'][server] = _convert_for_codex(config, 'claude')
        return claude_data, gemini_data, codex_data
    elif strategy == 'gemini':
        # Gemini takes precedence
        for server, config in gemini_data.get('mcpServers', {}).items():
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            claude_data['mcpServers'][server] = config.copy()

            if 'mcp_servers' not in codex_data:
                codex_data['mcp_servers'] = {}
            codex_data['mcp_servers'][server] = _convert_for_codex(config, 'gemini')
        return claude_data, gemini_data, codex_data
    elif strategy == 'codex':
        # Codex takes precedence
        for server, config in codex_data.get('mcp_servers', {}).items():
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            claude_data['mcpServers'][server] = _convert_for_claude(config, 'codex')

            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            gemini_data['mcpServers'][server] = _convert_for_gemini(config, 'codex')
        return claude_data, gemini_data, codex_data
    else:
        # Unknown strategy, fall back to merge
        return sync_three_way(claude_data, gemini_data, codex_data)


def get_all_servers(claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                   codex_data: Dict[str, Any] = None, mode: str = 'all') -> Set[str]:
    """Get all server names from configs based on mode.

    Modes:
    - 'claude': Only Claude servers
    - 'gemini': Only Gemini servers
    - 'codex': Only Codex servers
    - 'both': Claude and Gemini (backward compatibility)
    - 'all': All three configs
    """
    servers = set()

    if mode in ['claude', 'both', 'all']:
        servers.update(claude_data.get('mcpServers', {}).keys())

    if mode in ['gemini', 'both', 'all']:
        servers.update(gemini_data.get('mcpServers', {}).keys())

    if mode in ['codex', 'all'] and codex_data is not None:
        servers.update(codex_data.get('mcp_servers', {}).keys())

    return servers


def validate_synced_configs(claude_data: Dict[str, Any], gemini_data: Dict[str, Any],
                          codex_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate that configs are properly synced.

    Returns:
        tuple: (is_valid, list of validation errors)
    """
    errors = []

    # Get server sets
    claude_servers = set(claude_data.get('mcpServers', {}).keys())
    gemini_servers = set(gemini_data.get('mcpServers', {}).keys())
    codex_servers = set(codex_data.get('mcp_servers', {}).keys())

    # Check if all configs have same servers
    if not (claude_servers == gemini_servers == codex_servers):
        # Find differences
        only_claude = claude_servers - gemini_servers - codex_servers
        only_gemini = gemini_servers - claude_servers - codex_servers
        only_codex = codex_servers - claude_servers - gemini_servers

        if only_claude:
            errors.append(f"Servers only in Claude: {', '.join(only_claude)}")
        if only_gemini:
            errors.append(f"Servers only in Gemini: {', '.join(only_gemini)}")
        if only_codex:
            errors.append(f"Servers only in Codex: {', '.join(only_codex)}")

    # Validate each server config has required fields
    for server in claude_servers:
        claude_config = claude_data['mcpServers'].get(server, {})
        if not claude_config.get('command') and not claude_config.get('url'):
            errors.append(f"Claude server '{server}' missing command or url")

    for server in gemini_servers:
        gemini_config = gemini_data['mcpServers'].get(server, {})
        if not gemini_config.get('command') and not gemini_config.get('url'):
            errors.append(f"Gemini server '{server}' missing command or url")

    for server in codex_servers:
        codex_config = codex_data['mcp_servers'].get(server, {})
        if not codex_config.get('command') and not codex_config.get('url'):
            errors.append(f"Codex server '{server}' missing command or url")

    return len(errors) == 0, errors
