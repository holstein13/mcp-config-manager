#!/usr/bin/env python3
"""
Fix Context7 MCP server configuration in Codex.

This script corrects the Context7 configuration from HTTP type to stdio type,
which resolves timeout issues.
"""

from pathlib import Path
from mcp_config_manager.core.config_manager import ConfigManager
from mcp_config_manager.core.server_manager import ServerManager

def main():
    print("🔧 Fixing Context7 configuration...")

    # Initialize managers
    config_manager = ConfigManager()
    server_manager = ServerManager()

    # Load current configurations
    claude_data, gemini_data, codex_data = config_manager.load_configs()

    print(f"📂 Loaded configurations from:")
    print(f"   Claude: {config_manager.claude_path}")
    print(f"   Gemini: {config_manager.gemini_path}")
    print(f"   Codex:  {config_manager.codex_path}")

    # Check current Context7 configuration
    codex_servers = codex_data.get("mcpServers", {})
    if "context7" in codex_servers:
        current_config = codex_servers["context7"]
        print(f"\n📋 Current Context7 config:")
        print(f"   Type: {current_config.get('type')}")
        print(f"   Command: {current_config.get('command')}")
        print(f"   URL: {current_config.get('url', 'N/A')}")
        print(f"   Args: {current_config.get('args', [])}")

        # Check for API key
        has_api_key = False
        if "headers" in current_config and "CONTEXT7_API_KEY" in current_config.get("headers", {}):
            has_api_key = True
            print(f"   API Key: Found in headers")
        elif "env" in current_config and "CONTEXT7_API_KEY" in current_config.get("env", {}):
            has_api_key = True
            print(f"   API Key: Found in env")
    else:
        print("\n❌ Context7 not found in configuration")
        current_config = None

    # Fix the configuration
    fixed = server_manager.fix_context7_config(claude_data, gemini_data, codex_data)

    if fixed:
        print("\n✅ Fixed Context7 configuration!")

        # Show new configuration
        updated_config = codex_data.get("mcpServers", {}).get("context7", {})
        print(f"\n📋 New Context7 config:")
        print(f"   Type: {updated_config.get('type')}")
        print(f"   Command: {updated_config.get('command')}")
        print(f"   Args: {updated_config.get('args', [])}")
        if "env" in updated_config:
            print(f"   API Key: Preserved in env")

        # Save the configurations
        config_manager.save_configs(claude_data, gemini_data, codex_data, mode="codex")
        print("\n💾 Configuration saved!")

        print("\n🚀 Context7 should now work correctly in Codex!")
        print("   Try restarting Codex to apply the changes.")
    else:
        if current_config and current_config.get("type") == "stdio":
            print("\n✅ Context7 configuration is already correct!")
        else:
            print("\n⚠️ No changes were needed.")

if __name__ == "__main__":
    main()