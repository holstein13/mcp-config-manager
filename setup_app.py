"""
py2app setup script for MCP Config Manager

Usage:
    python3 setup_app.py py2app
"""

from setuptools import setup
import sys
import os

# Ensure we're using the right Python
if sys.version_info < (3, 8):
    print("Python 3.8+ is required")
    sys.exit(1)

# Application metadata
APP_NAME = "MCP Config Manager"
APP_VERSION = "1.0.0"
APP_IDENTIFIER = "com.mcpconfig.manager"

# Main script that launches the GUI
APP = ['launch_gui.py']

# Additional data files (if any)
DATA_FILES = []

# py2app options
OPTIONS = {
    'py2app': {
        'argv_emulation': False,  # Don't use argv emulation
        'iconfile': 'icon.icns' if os.path.exists('icon.icns') else None,  # Uses icon.icns if it exists
        'plist': {
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleIdentifier': APP_IDENTIFIER,
            'CFBundleVersion': APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSBackgroundOnly': False,
            'LSUIElement': False,
        },
        'packages': [
            'mcp_config_manager',
            'PyQt6',
            'click',
        ],
        'includes': [
            'mcp_config_manager.gui',
            'mcp_config_manager.core',
            'mcp_config_manager.parsers',
            'mcp_config_manager.utils',
            'mcp_config_manager.cli',
        ],
        'excludes': [
            'tkinter',  # Exclude tkinter since we're using PyQt6
            'test',
            'unittest',
        ],
        'resources': [],
        'frameworks': [],
    }
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=['py2app'],
    install_requires=[
        'click>=8.0.0',
        'PyQt6',
    ],
)