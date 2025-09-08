"""
Resources module for MCP Config Manager GUI.

Contains icons, styles, and other static resources.
"""

from pathlib import Path

RESOURCES_DIR = Path(__file__).parent
ICONS_DIR = RESOURCES_DIR / "icons"
STYLES_DIR = RESOURCES_DIR / "styles"

__all__ = ['RESOURCES_DIR', 'ICONS_DIR', 'STYLES_DIR']