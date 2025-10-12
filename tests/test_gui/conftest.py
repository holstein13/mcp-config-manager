"""
pytest configuration for GUI tests.

Provides fixtures and configuration for testing GUI components with both
PyQt6 and tkinter frameworks.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# Try to import GUI framework
GUI_FRAMEWORK = None
try:
    from PyQt6 import QtWidgets
    GUI_FRAMEWORK = "pyqt6"
except ImportError:
    try:
        import tkinter as tk
        GUI_FRAMEWORK = "tkinter"
    except ImportError:
        pass


@pytest.fixture
def gui_framework():
    """Return the available GUI framework name."""
    return GUI_FRAMEWORK


@pytest.fixture
def qt_app():
    """Provide a Qt application for testing (if PyQt6 available)."""
    if GUI_FRAMEWORK == "pyqt6":
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
        # Don't quit the app here as pytest-qt handles it
    else:
        pytest.skip("PyQt6 not available")


@pytest.fixture
def tk_root():
    """Provide a tkinter root window for testing (if tkinter available)."""
    if GUI_FRAMEWORK == "tkinter":
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide during tests
        yield root
        root.destroy()
    else:
        pytest.skip("tkinter not available")


@pytest.fixture
def main_window(qt_app, tk_root):
    """Create a main window for testing."""
    from gui.main_window import MainWindow
    
    window = MainWindow()
    window.setup()
    
    if GUI_FRAMEWORK == "pyqt6":
        yield window.window
        window.window.close()
    elif GUI_FRAMEWORK == "tkinter":
        yield window.window
        # Window already destroyed by tk_root fixture
    else:
        pytest.skip("No GUI framework available")


@pytest.fixture
def mock_config_manager(mocker):
    """Mock ConfigManager for testing."""
    from mcp_config_manager.core.config_manager import ConfigManager
    
    mock = mocker.Mock(spec=ConfigManager)
    mock.mode = "both"
    mock.get_all_servers.return_value = {
        "active": ["server1", "server2"],
        "disabled": ["server3"]
    }
    return mock


@pytest.fixture
def mock_server_manager(mocker):
    """Mock ServerManager for testing."""
    from mcp_config_manager.core.server_manager import ServerManager
    
    mock = mocker.Mock(spec=ServerManager)
    mock.list_servers.return_value = {
        "active": {"server1": {}, "server2": {}},
        "disabled": {"server3": {}}
    }
    return mock


@pytest.fixture
def mock_preset_manager(mocker):
    """Mock PresetManager for testing."""
    from mcp_config_manager.core.presets import PresetManager
    
    mock = mocker.Mock(spec=PresetManager)
    mock.list_presets.return_value = {
        "minimal": {"servers": ["context7", "browsermcp"]},
        "webdev": {"servers": ["context7", "browsermcp", "playwright"]}
    }
    return mock


# pytest-qt specific configuration if available
if GUI_FRAMEWORK == "pyqt6":
    try:
        import pytest_qt
        # pytest-qt will automatically add its fixtures
    except ImportError:
        pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "gui: mark test as requiring GUI framework"
    )
    config.addinivalue_line(
        "markers",
        "pyqt6: mark test as requiring PyQt6"
    )
    config.addinivalue_line(
        "markers",
        "tkinter: mark test as requiring tkinter"
    )
    config.addinivalue_line(
        "markers",
        "unimplemented: mark test as testing features not yet implemented (will be skipped)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on available GUI framework."""
    for item in items:
        # Skip tests marked as testing unimplemented features
        if "unimplemented" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Feature not yet implemented - TODO"))

        # Skip GUI tests if no framework available
        if "gui" in item.keywords and GUI_FRAMEWORK is None:
            item.add_marker(pytest.mark.skip(reason="No GUI framework available"))

        # Skip PyQt6-specific tests if not available
        if "pyqt6" in item.keywords and GUI_FRAMEWORK != "pyqt6":
            item.add_marker(pytest.mark.skip(reason="PyQt6 not available"))

        # Skip tkinter-specific tests if not available
        if "tkinter" in item.keywords and GUI_FRAMEWORK != "tkinter":
            item.add_marker(pytest.mark.skip(reason="tkinter not available"))