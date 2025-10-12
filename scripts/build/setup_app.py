"""
py2app setup script for MCP Config Manager
Creates a standalone macOS application bundle.
"""

from setuptools import setup
import os
import sys

# Ensure we're building from the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

APP = ['scripts/build/app_launcher.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,  # Don't emulate argv for drag-and-drop
    'packages': [
        'mcp_config_manager',
        'PyQt6',
        'click',
        'requests',
        'toml',
        'tomli',
    ],
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    'excludes': [
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
    ],
    'plist': {
        'CFBundleName': 'MCP Config Manager',
        'CFBundleDisplayName': 'MCP Config Manager',
        'CFBundleGetInfoString': 'Manage MCP server configurations',
        'CFBundleIdentifier': 'com.holstein13.mcp-config-manager',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 MCP Config Manager Contributors',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14',  # macOS Mojave or later
    },
    'iconfile': 'resources/icon.icns',
}

setup(
    name='MCP Config Manager',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
