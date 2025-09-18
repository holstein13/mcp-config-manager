#!/usr/bin/env python3
"""
Launcher script for MCP Config Manager GUI
This script properly initializes and launches the GUI application.
"""

import sys
import os

# Add the src directory to path so imports work
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def main():
    """Main entry point for the GUI application."""
    from mcp_config_manager.gui.main_window import run_gui_in_main_thread
    run_gui_in_main_thread()

if __name__ == "__main__":
    main()