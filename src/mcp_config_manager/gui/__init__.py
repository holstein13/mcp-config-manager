"""GUI module for MCP Config Manager."""

# Framework detection and availability
_using_qt = None
_has_tkinter = None

def is_gui_available() -> bool:
    """Check if any GUI framework is available."""
    return get_framework() != "none"

def get_framework() -> str:
    """Get the name of the available GUI framework."""
    global _using_qt, _has_tkinter
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Getting framework")

    if _using_qt is None:
        logging.debug("Checking for PyQt6")
        try:
            from PyQt6.QtWidgets import QApplication
            _using_qt = True
            logging.debug("PyQt6 found")
        except ImportError:
            _using_qt = False
            logging.debug("PyQt6 not found")

    if _using_qt:
        logging.debug("Using PyQt6")
        return "pyqt6"

    if _has_tkinter is None:
        logging.debug("Checking for tkinter")
        try:
            import tkinter
            _has_tkinter = True
            logging.debug("tkinter found")
        except ImportError:
            _has_tkinter = False
            logging.debug("tkinter not found")
    
    if _has_tkinter:
        logging.debug("Using tkinter")
        return "tkinter"

    logging.debug("No GUI framework found")
    return "none"

# Properties to lazily access the framework info
@property
def USING_QT() -> bool:
    return get_framework() == "pyqt6"

@property
def HAS_TKINTER() -> bool:
    return get_framework() == "tkinter"


__all__ = [
    'is_gui_available',
    'get_framework',
    'USING_QT',
    'HAS_TKINTER',
]