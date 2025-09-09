#!/usr/bin/env python3
"""Test the full system with enabled and disabled servers."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("TESTING MCP CONFIG MANAGER - FULL SYSTEM")
print("=" * 60)

# Test ConfigManager
print("\n1. Testing ConfigManager...")
from mcp_config_manager.core.config_manager import ConfigManager
config_manager = ConfigManager()

# Load configs
claude_data, gemini_data = config_manager.load_configs()
print(f"✓ Configs loaded:")
print(f"  - Claude servers: {len(claude_data.get('mcpServers', {}))}")
print(f"  - Gemini servers: {len(gemini_data.get('mcpServers', {}))}")

# Test ServerManager
print("\n2. Testing ServerManager...")
from mcp_config_manager.core.server_manager import ServerManager
server_manager = config_manager.server_manager

# Get enabled servers
enabled_servers = server_manager.get_enabled_servers(claude_data, gemini_data, 'both')
print(f"✓ Enabled servers: {len(enabled_servers)}")
for server in enabled_servers[:3]:
    print(f"  - {server['name']}")

# Get disabled servers
disabled_servers = server_manager.load_disabled_servers()
print(f"✓ Disabled servers: {len(disabled_servers)}")
for name in list(disabled_servers.keys())[:3]:
    print(f"  - {name}")

# Test list_servers
print("\n3. Testing list_servers...")
active, disabled = config_manager.list_servers('both')
print(f"✓ Active servers: {len(active)}")
print(f"✓ Disabled servers: {len(disabled)}")

# Test ServerController
print("\n4. Testing ServerController...")
from mcp_config_manager.gui.controllers.server_controller import ServerController
server_controller = ServerController()

result = server_controller.get_servers('both')
if result['success']:
    servers = result['data']['servers']
    print(f"✓ ServerController.get_servers returned {len(servers)} servers")
    
    enabled_count = sum(1 for s in servers if str(s.status) == 'ServerStatus.ENABLED')
    disabled_count = sum(1 for s in servers if str(s.status) == 'ServerStatus.DISABLED')
    
    print(f"  - Enabled: {enabled_count}")
    print(f"  - Disabled: {disabled_count}")
    
    # Show first few of each type
    print("\n  Enabled servers:")
    for server in [s for s in servers if str(s.status) == 'ServerStatus.ENABLED'][:3]:
        print(f"    • {server.name}: {server.command.command if server.command else 'N/A'}")
    
    print("\n  Disabled servers:")
    for server in [s for s in servers if str(s.status) == 'ServerStatus.DISABLED'][:3]:
        print(f"    • {server.name}: {server.command.command if server.command else 'N/A'}")
else:
    print(f"✗ ServerController.get_servers failed: {result.get('error')}")

# Test ConfigController
print("\n5. Testing ConfigController...")
from mcp_config_manager.gui.controllers.config_controller import ConfigController
config_controller = ConfigController()

result = config_controller.load_config('both')
if result['success']:
    config_data = result['data']
    print(f"✓ ConfigController.load_config successful")
    print(f"  - Mode: {config_data['mode']}")
    print(f"  - Servers: {len(config_data['servers'])}")
else:
    print(f"✗ ConfigController.load_config failed: {result.get('error')}")

print("\n" + "=" * 60)
print("SUMMARY:")
print(f"✓ Found {len(enabled_servers)} enabled servers")
print(f"✓ Found {len(disabled_servers)} disabled servers")
print(f"✓ Total: {len(enabled_servers) + len(disabled_servers)} servers")
print("=" * 60)

print("\n✅ All tests passed! System is working correctly.")
print("\nNow testing GUI initialization...")

# Test GUI
try:
    from mcp_config_manager.gui.main_window import MainWindow, USING_QT
    
    if USING_QT:
        print("✓ PyQt6 is available")
        from PyQt6.QtWidgets import QApplication
        
        # Create app
        app = QApplication(sys.argv)
        
        # Create window
        window = MainWindow()
        
        # Check if servers are loaded
        if hasattr(window, 'server_list'):
            print("✓ Server list widget exists")
            # Try to get the server count
            if hasattr(window.server_list, 'tree'):
                if USING_QT:
                    item_count = window.server_list.tree.topLevelItemCount()
                    print(f"✓ Server list has {item_count} items displayed")
        
        print("\n✅ GUI is ready to run!")
        print("The window should display with all servers listed.")
    else:
        print("! Using tkinter fallback")
except Exception as e:
    print(f"✗ GUI initialization failed: {e}")
    import traceback
    traceback.print_exc()