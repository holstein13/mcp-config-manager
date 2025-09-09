"""GUI module for MCP Config Manager."""

# Framework detection and availability
USING_QT = False
HAS_TKINTER = False

try:
    from PyQt6.QtWidgets import QApplication
    USING_QT = True
except ImportError:
    try:
        import tkinter
        HAS_TKINTER = True
    except ImportError:
        pass


def is_gui_available() -> bool:
    """Check if any GUI framework is available."""
    return USING_QT or HAS_TKINTER


def get_framework() -> str:
    """Get the name of the available GUI framework."""
    if USING_QT:
        return "pyqt6"
    elif HAS_TKINTER:
        return "tkinter"
    else:
        return "none"


__all__ = [
    'is_gui_available',
    'get_framework',
    'USING_QT',
    'HAS_TKINTER',
]