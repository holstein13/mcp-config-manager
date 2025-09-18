"""
py2app setup script for MCP Config Manager
Build macOS app bundle with: python setup_py2app.py py2app
"""

from setuptools import setup
import sys

# Ensure we're on macOS
if sys.platform != 'darwin':
    print("This setup script is for macOS only. Use setup.py for other platforms.")
    sys.exit(1)

APP = ['src/mcp_config_manager/app_launcher.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': False,  # Don't use argv emulation (causes issues with some Qt apps)
    'plist': {
        'CFBundleName': 'MCP Config Manager',
        'CFBundleDisplayName': 'MCP Config Manager',
        'CFBundleIdentifier': 'com.mcpconfig.manager',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '10.14.0',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2024 MCP Config Manager Contributors',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': [
        'PyQt6',
        'click',
    ],
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'mcp_config_manager',
        'mcp_config_manager.core',
        'mcp_config_manager.core.config_manager',
        'mcp_config_manager.core.server_manager',
        'mcp_config_manager.core.presets',
        'mcp_config_manager.gui',
        'mcp_config_manager.gui.main_window',
        'mcp_config_manager.parsers',
        'mcp_config_manager.utils',
        'mcp_config_manager.utils.file_utils',
        'mcp_config_manager.utils.backup',
    ],
    'excludes': [
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        'test',
        'tests',
        'unittest',
    ],
    'iconfile': 'icon.icns',  # Use the project icon
    'dist_dir': 'py2app_dist',
    'bdist_base': 'build/py2app',
}

setup(
    name='MCP Config Manager',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    packages=[
        'mcp_config_manager',
        'mcp_config_manager.core',
        'mcp_config_manager.gui',
        'mcp_config_manager.gui.controllers',
        'mcp_config_manager.gui.dialogs',
        'mcp_config_manager.gui.events',
        'mcp_config_manager.gui.models',
        'mcp_config_manager.gui.widgets',
        'mcp_config_manager.parsers',
        'mcp_config_manager.utils',
    ],
    package_dir={'': 'src'},
)