#!/usr/bin/env python3
"""
MCP Server Toggle for Claude and Gemini CLI
Manages MCP servers for both Claude Code CLI and Gemini CLI
Stores disabled servers in ~/claude_manager/disabled_servers.json
"""

import json
from pathlib import Path
import shutil
from datetime import datetime
import os
import sys

# Configuration paths
CLAUDE_CONFIG_PATH = Path.home() / '.claude.json'
GEMINI_CONFIG_PATH = Path.home() / '.gemini' / 'settings.json'
PRESETS_PATH = Path.home() / '.mcp_presets.json'

# Disabled servers storage - in the same directory as this script
SCRIPT_DIR = Path(__file__).parent.resolve() if '__file__' in globals() else Path.cwd()
DISABLED_PATH = SCRIPT_DIR / 'disabled_servers.json'

# CLI mode selection
CLI_MODE = 'both'  # 'claude', 'gemini', or 'both'

def ensure_gemini_config():
    """Ensure Gemini config directory and file exist."""
    gemini_dir = GEMINI_CONFIG_PATH.parent
    if not gemini_dir.exists():
        gemini_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created Gemini config directory: {gemini_dir}")
    
    if not GEMINI_CONFIG_PATH.exists():
        default_config = {"mcpServers": {}}
        with open(GEMINI_CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📝 Created Gemini config file: {GEMINI_CONFIG_PATH}")

def backup_configs():
    """Create timestamped backups of all config files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = []
    
    # Backup Claude config
    if CLAUDE_CONFIG_PATH.exists():
        claude_backup = CLAUDE_CONFIG_PATH.parent / f'.claude.json.backup.{timestamp}'
        shutil.copy2(CLAUDE_CONFIG_PATH, claude_backup)
        backups.append(('Claude', claude_backup))
    
    # Backup Gemini config
    if GEMINI_CONFIG_PATH.exists():
        gemini_backup = GEMINI_CONFIG_PATH.parent / f'settings.json.backup.{timestamp}'
        shutil.copy2(GEMINI_CONFIG_PATH, gemini_backup)
        backups.append(('Gemini', gemini_backup))
    
    for name, path in backups:
        print(f"✅ {name} backup: {path}")
    
    return backups

def load_config(config_path):
    """Load a config file."""
    if not config_path.exists():
        return {"mcpServers": {}}
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(data, config_path):
    """Save a config file."""
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_disabled_servers():
    """Load disabled servers from separate file."""
    if not DISABLED_PATH.exists():
        return {}
    with open(DISABLED_PATH, 'r') as f:
        return json.load(f)

def save_disabled_servers(disabled):
    """Save disabled servers to separate file."""
    DISABLED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DISABLED_PATH, 'w') as f:
        json.dump(disabled, f, indent=2)
    print(f"💾 Disabled servers saved to {DISABLED_PATH}")

def sync_configs(claude_data, gemini_data, mode='both'):
    """Synchronize servers between Claude and Gemini configs."""
    if mode == 'both':
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

def list_all_servers(claude_data, gemini_data, mode='both'):
    """List all servers (active and disabled) based on mode."""
    active = set()
    
    if mode in ['claude', 'both']:
        active.update(claude_data.get('mcpServers', {}).keys())
    
    if mode in ['gemini', 'both']:
        active.update(gemini_data.get('mcpServers', {}).keys())
    
    disabled_servers = load_disabled_servers()
    disabled = list(disabled_servers.keys())
    
    return sorted(list(active)), disabled

def disable_server(claude_data, gemini_data, server_name, mode='both'):
    """Move a server from active to disabled file."""
    disabled = load_disabled_servers()
    server_config = None
    
    # Get server config from either source
    if mode in ['claude', 'both'] and 'mcpServers' in claude_data and server_name in claude_data['mcpServers']:
        server_config = claude_data['mcpServers'][server_name]
        del claude_data['mcpServers'][server_name]
    
    if mode in ['gemini', 'both'] and 'mcpServers' in gemini_data and server_name in gemini_data['mcpServers']:
        if not server_config:
            server_config = gemini_data['mcpServers'][server_name]
        del gemini_data['mcpServers'][server_name]
    
    if server_config:
        disabled[server_name] = server_config
        save_disabled_servers(disabled)
        print(f"❌ Disabled: {server_name}")
        return True
    
    return False

def enable_server(claude_data, gemini_data, server_name, mode='both'):
    """Move a server from disabled file to active."""
    disabled = load_disabled_servers()
    
    if server_name in disabled:
        server_config = disabled[server_name]
        
        # Add to appropriate configs based on mode
        if mode in ['claude', 'both']:
            if 'mcpServers' not in claude_data:
                claude_data['mcpServers'] = {}
            claude_data['mcpServers'][server_name] = server_config.copy()
        
        if mode in ['gemini', 'both']:
            if 'mcpServers' not in gemini_data:
                gemini_data['mcpServers'] = {}
            gemini_data['mcpServers'][server_name] = server_config.copy()
        
        del disabled[server_name]
        save_disabled_servers(disabled)
        print(f"✅ Enabled: {server_name}")
        return True
    
    return False

def add_new_server(claude_data, gemini_data, mode='both'):
    """Add a new MCP server by pasting JSON configuration."""
    print("\n" + "="*60)
    print("➕ ADD NEW MCP SERVER")
    print("="*60)
    print("\nPaste the JSON configuration for your new MCP server.")
    print("Example:")
    print('''
"servername": {
  "command": "npx",
  "args": ["-y", "@package/name@latest"]
}
''')
    print("Paste your JSON below (press Enter twice when done):")
    print("-"*40)
    
    json_lines = []
    while True:
        line = input()
        if line == "" and json_lines and json_lines[-1] == "":
            break
        json_lines.append(line)
    
    if json_lines and json_lines[-1] == "":
        json_lines.pop()
    
    json_text = "\n".join(json_lines).strip()
    
    if not json_text:
        print("❌ No JSON provided")
        return claude_data, gemini_data
    
    try:
        parsed = json.loads(json_text)
        
        if isinstance(parsed, dict):
            if 'command' in parsed or 'args' in parsed or 'type' in parsed:
                server_name = input("\nServer name: ").strip()
                if not server_name:
                    print("❌ Server name required")
                    return claude_data, gemini_data
                
                # Add to appropriate configs
                if mode in ['claude', 'both']:
                    if 'mcpServers' not in claude_data:
                        claude_data['mcpServers'] = {}
                    claude_data['mcpServers'][server_name] = parsed
                    print(f"✅ Added {server_name} to Claude")
                
                if mode in ['gemini', 'both']:
                    if 'mcpServers' not in gemini_data:
                        gemini_data['mcpServers'] = {}
                    gemini_data['mcpServers'][server_name] = parsed
                    print(f"✅ Added {server_name} to Gemini")
            else:
                # Multiple servers
                for server_name, server_config in parsed.items():
                    if isinstance(server_config, dict):
                        if mode in ['claude', 'both']:
                            if 'mcpServers' not in claude_data:
                                claude_data['mcpServers'] = {}
                            claude_data['mcpServers'][server_name] = server_config
                        
                        if mode in ['gemini', 'both']:
                            if 'mcpServers' not in gemini_data:
                                gemini_data['mcpServers'] = {}
                            gemini_data['mcpServers'][server_name] = server_config
                        
                        print(f"✅ Added {server_name}")
        else:
            print("❌ Invalid JSON structure")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
    
    print("\n✨ Server(s) added successfully!")
    return claude_data, gemini_data

def load_presets():
    """Load presets from external file."""
    if not PRESETS_PATH.exists():
        default_presets = {
            "presets": {},
            "defaults": {
                "minimal": ["context7", "browsermcp"],
                "webdev": ["context7", "browsermcp", "playwright"],
                "fullstack": ["context7", "browsermcp", "playwright", "supabase", "clerk", "railway"],
                "testing": ["context7", "playwright", "memory"]
            }
        }
        save_presets(default_presets)
        return default_presets
    
    with open(PRESETS_PATH, 'r') as f:
        return json.load(f)

def save_presets(presets_data):
    """Save presets to external file."""
    with open(PRESETS_PATH, 'w') as f:
        json.dump(presets_data, f, indent=2)

def main():
    """Main interactive loop."""
    print("\n🔧 MCP Server Toggle for Claude & Gemini")
    print("="*50)
    
    # Ensure Gemini config exists
    ensure_gemini_config()
    
    # Select CLI mode
    print("\n🎯 Select CLI mode:")
    print("  [1] Claude only")
    print("  [2] Gemini only")
    print("  [3] Both (sync servers)")
    
    mode_choice = input("Mode (default=3): ").strip() or '3'
    
    if mode_choice == '1':
        CLI_MODE = 'claude'
        print("📘 Managing Claude CLI only")
    elif mode_choice == '2':
        CLI_MODE = 'gemini'
        print("💎 Managing Gemini CLI only")
    else:
        CLI_MODE = 'both'
        print("🔄 Managing both Claude & Gemini (synced)")
    
    print(f"\n📁 Disabled servers: {DISABLED_PATH}")
    
    # Create backups
    backup_configs()
    
    # Load configurations
    claude_data = load_config(CLAUDE_CONFIG_PATH) if CLI_MODE in ['claude', 'both'] else {"mcpServers": {}}
    gemini_data = load_config(GEMINI_CONFIG_PATH) if CLI_MODE in ['gemini', 'both'] else {"mcpServers": {}}
    
    # Sync if in both mode
    if CLI_MODE == 'both':
        claude_data, gemini_data = sync_configs(claude_data, gemini_data, CLI_MODE)
    
    presets_data = load_presets()
    
    while True:
        active, disabled = list_all_servers(claude_data, gemini_data, CLI_MODE)
        
        print("\n📊 Current Status:")
        print("-"*30)
        
        if CLI_MODE == 'both':
            print(f"Mode: 🔄 Both CLIs (synced)")
        elif CLI_MODE == 'claude':
            print(f"Mode: 📘 Claude only")
        else:
            print(f"Mode: 💎 Gemini only")
        
        if active:
            print("\n✅ ACTIVE servers (will run):")
            for i, server in enumerate(active, 1):
                print(f"  [{i}] {server}")
        else:
            print("\n✅ ACTIVE servers: None")
        
        if disabled:
            print("\n❌ DISABLED servers (won't run):")
            for i, server in enumerate(disabled, 1):
                print(f"  [d{i}] {server}")
        else:
            print("\n❌ DISABLED servers: None")
        
        print("\n📋 Actions:")
        print("  [1-N]  Disable active server")
        print("  [d1-N] Enable disabled server")
        print("  [a]    Enable ALL")
        print("  [n]    Disable ALL")
        print("  [m]    Minimal (context7 + browsermcp)")
        print("  [w]    Web dev (+ playwright)")
        print("  [+]    ➕ Add new MCP server")
        print("  [c]    🔄 Change CLI mode")
        print("  [s]    Save and exit")
        print("  [q]    Quit without saving")
        
        choice = input("\nAction: ").lower().strip()
        
        if choice == 'q':
            print("❌ Exiting without saving")
            break
            
        elif choice == 's':
            if CLI_MODE in ['claude', 'both']:
                save_config(claude_data, CLAUDE_CONFIG_PATH)
                print(f"✅ Claude config saved: {CLAUDE_CONFIG_PATH}")
            
            if CLI_MODE in ['gemini', 'both']:
                save_config(gemini_data, GEMINI_CONFIG_PATH)
                print(f"✅ Gemini config saved: {GEMINI_CONFIG_PATH}")
            
            print("\n⚠️  Restart Claude/Gemini CLI for changes to take effect")
            break
            
        elif choice == 'c':
            # Change CLI mode
            print("\n🎯 Select new CLI mode:")
            print("  [1] Claude only")
            print("  [2] Gemini only")
            print("  [3] Both (sync servers)")
            
            new_mode = input("Mode: ").strip()
            if new_mode == '1':
                CLI_MODE = 'claude'
                print("📘 Switched to Claude only")
            elif new_mode == '2':
                CLI_MODE = 'gemini'
                print("💎 Switched to Gemini only")
            else:
                CLI_MODE = 'both'
                claude_data, gemini_data = sync_configs(claude_data, gemini_data, 'both')
                print("🔄 Switched to both (synced)")
            
        elif choice == 'a':
            # Enable all
            disabled_list = list(disabled)
            for server in disabled_list:
                enable_server(claude_data, gemini_data, server, CLI_MODE)
                
        elif choice == 'n':
            # Disable all
            active_list = list(active)
            for server in active_list:
                disable_server(claude_data, gemini_data, server, CLI_MODE)
                
        elif choice == 'm':
            # Minimal mode
            defaults = presets_data.get('defaults', {})
            keep_active = defaults.get('minimal', ['context7', 'browsermcp'])
            
            for server in active:
                if server not in keep_active:
                    disable_server(claude_data, gemini_data, server, CLI_MODE)
            
            for server in keep_active:
                if server in disabled:
                    enable_server(claude_data, gemini_data, server, CLI_MODE)
            
            print(f"✅ Minimal mode: {', '.join(keep_active)}")
            
        elif choice == 'w':
            # Web dev mode
            defaults = presets_data.get('defaults', {})
            keep_active = defaults.get('webdev', ['context7', 'browsermcp', 'playwright'])
            
            for server in active:
                if server not in keep_active:
                    disable_server(claude_data, gemini_data, server, CLI_MODE)
            
            for server in keep_active:
                if server in disabled:
                    enable_server(claude_data, gemini_data, server, CLI_MODE)
            
            print(f"✅ Web dev mode: {', '.join(keep_active)}")
            
        elif choice == '+':
            claude_data, gemini_data = add_new_server(claude_data, gemini_data, CLI_MODE)
            
        elif choice.startswith('d'):
            # Enable disabled server
            try:
                idx = int(choice[1:]) - 1
                if 0 <= idx < len(disabled):
                    enable_server(claude_data, gemini_data, disabled[idx], CLI_MODE)
            except ValueError:
                print("❌ Invalid input")
                
        else:
            # Disable active server
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(active):
                    disable_server(claude_data, gemini_data, active[idx], CLI_MODE)
            except ValueError:
                print("❌ Invalid input")

if __name__ == "__main__":
    main()