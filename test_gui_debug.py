#!/usr/bin/env python3
"""Debug script to test GUI loading issue."""

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

# Test basic imports
print("Testing imports...")
try:
    from mcp_config_manager.core.config_manager import ConfigManager
    print("✓ ConfigManager imported")
except Exception as e:
    print(f"✗ ConfigManager import failed: {e}")
    sys.exit(1)

# Test ConfigManager initialization
print("\nTesting ConfigManager...")
try:
    config_manager = ConfigManager()
    print("✓ ConfigManager initialized")
except Exception as e:
    print(f"✗ ConfigManager init failed: {e}")
    sys.exit(1)

# Test loading configs
print("\nTesting config loading...")
try:
    claude_data, gemini_data = config_manager.load_configs()
    print(f"✓ Configs loaded - Claude servers: {len(claude_data.get('mcpServers', {}))}, Gemini servers: {len(gemini_data.get('mcpServers', {}))}")
except Exception as e:
    print(f"✗ Config loading failed: {e}")
    sys.exit(1)

# Test ServerManager
print("\nTesting ServerManager...")
try:
    enabled_servers = config_manager.server_manager.get_enabled_servers(claude_data, gemini_data, 'both')
    print(f"✓ Got {len(enabled_servers)} enabled servers")
    for server in enabled_servers[:3]:  # Show first 3
        print(f"  - {server['name']}: {server.get('config', {}).get('command', 'N/A')}")
except Exception as e:
    print(f"✗ ServerManager failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test GUI controllers
print("\nTesting GUI controllers...")
try:
    from mcp_config_manager.gui.controllers.config_controller import ConfigController
    print("✓ ConfigController imported")
    
    controller = ConfigController()  # It creates its own ConfigManager
    print("✓ ConfigController initialized")
    
    result = controller.load_config('both')
    if result['success']:
        print(f"✓ Config loaded via controller - {len(result['data']['servers'])} servers")
    else:
        print(f"✗ Config load failed: {result['error']}")
except Exception as e:
    print(f"✗ Controller test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed! Core functionality is working.")
print("\nNow testing GUI initialization...")

# Test GUI
try:
    from mcp_config_manager.gui.main_window import MainWindow, USING_QT
    print(f"✓ MainWindow imported (Using Qt: {USING_QT})")
    
    if USING_QT:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 available")
        
        # Create app but don't show window
        app = QApplication(sys.argv)
        print("✓ QApplication created")
        
        # Try creating window
        window = MainWindow()
        print("✓ MainWindow created successfully!")
        print("\nThe GUI framework is working. The issue may be in the event loop or display.")
    else:
        print("! Using tkinter fallback")
        
except Exception as e:
    print(f"✗ GUI test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Debug test complete. All components working.")