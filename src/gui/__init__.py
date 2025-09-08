"""
GUI module for MCP Config Manager.

Provides cross-platform GUI interface using PyQt6 (primary) or tkinter (fallback).
"""

from typing import Optional, Type

# GUI framework detection and import
GUI_FRAMEWORK: Optional[str] = None
MainWindow: Optional[Type] = None

try:
    # Try PyQt6 first (preferred)
    from PyQt6 import QtCore, QtWidgets
    GUI_FRAMEWORK = "pyqt6"
    print("GUI Framework: PyQt6")
except ImportError:
    try:
        # Fallback to tkinter
        import tkinter as tk
        GUI_FRAMEWORK = "tkinter"
        print("GUI Framework: tkinter (fallback)")
    except ImportError:
        GUI_FRAMEWORK = None
        print("Warning: No GUI framework available")


def is_gui_available() -> bool:
    """Check if any GUI framework is available."""
    return GUI_FRAMEWORK is not None


def get_framework() -> Optional[str]:
    """Get the name of the available GUI framework."""
    return GUI_FRAMEWORK


__all__ = [
    'is_gui_available',
    'get_framework',
    'GUI_FRAMEWORK',
]