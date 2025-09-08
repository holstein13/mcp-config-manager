"""
Synchronization utilities for MCP configurations
"""

from typing import Dict, Any, Set


def sync_server_configs(claude_data: Dict[str, Any], gemini_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Synchronize servers between Claude and Gemini configs."""
    # Get all unique servers from both configs
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
    
    return claude_data, gemini_data


def get_all_servers(claude_data: Dict[str, Any], gemini_data: Dict[str, Any], mode: str = 'both') -> Set[str]:
    """Get all server names from configs based on mode."""
    servers = set()
    
    if mode in ['claude', 'both']:
        servers.update(claude_data.get('mcpServers', {}).keys())
    
    if mode in ['gemini', 'both']:
        servers.update(gemini_data.get('mcpServers', {}).keys())
    
    return servers
