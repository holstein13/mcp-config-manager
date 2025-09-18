#!/usr/bin/env python3
"""
App launcher for py2app bundle
"""

import sys
from mcp_config_manager.cli import main

if __name__ == '__main__':
    # Launch the GUI directly when running as app bundle
    sys.argv = ['mcp-config-manager', 'gui']
    main()