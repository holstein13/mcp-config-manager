#!/usr/bin/env python3
"""
Launcher script for MCP Config Manager macOS app
This script is the entry point for the py2app bundle.
"""

import sys
import os

# Add src directory to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    """Launch the GUI application."""
    from mcp_config_manager.gui.main_window import run_gui_in_main_thread
    run_gui_in_main_thread()

if __name__ == '__main__':
    main()
