"""
GUI Launcher for MCP Config Manager macOS app
"""

import sys

if __name__ == "__main__":
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("PyQt6 not available, trying tkinter...")
        from mcp_config_manager.gui.tkinter.main_window import main as tk_main

        sys.exit(tk_main())

    from mcp_config_manager.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
