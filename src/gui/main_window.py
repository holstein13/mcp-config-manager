"""Main window for MCP Config Manager GUI."""

import sys
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QToolBar, QStatusBar, QAction, QMessageBox,
        QApplication, QSplitter, QListWidget
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QIcon, QKeySequence
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    USING_QT = False

from .models.app_state import ApplicationState
from .models.ui_config import UIConfiguration


class MainWindow(QMainWindow if USING_QT else object):
    """Main application window for MCP Config Manager."""
    
    # Qt signals
    if USING_QT:
        config_loaded = pyqtSignal(dict)
        config_saved = pyqtSignal()
        mode_changed = pyqtSignal(str)
        server_toggled = pyqtSignal(str, bool)
        preset_applied = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the main window."""
        if USING_QT:
            super().__init__(parent)
            self._setup_qt_window()
        else:
            self._setup_tk_window()
        
        self.app_state = ApplicationState()
        self.ui_config = UIConfiguration()
        self._unsaved_changes = False
        self._status_bar = None
        self._status_label = None
        self._save_indicator = None
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._load_window_state()
    
    def _setup_qt_window(self):
        """Set up Qt window properties."""
        self.setWindowTitle("MCP Config Manager")
        self.setGeometry(100, 100, 1000, 700)
        
    def _setup_tk_window(self):
        """Set up tkinter window properties."""
        self.root = tk.Tk()
        self.root.title("MCP Config Manager")
        self.root.geometry("1000x700+100+100")
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        if USING_QT:
            self._setup_qt_ui()
        else:
            self._setup_tk_ui()
    
    def _setup_qt_ui(self):
        """Set up Qt UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content splitter (for future server list and details)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Placeholder for server list (will be replaced in T036)
        self.server_list_placeholder = QListWidget()
        self.server_list_placeholder.addItem("Server list will be implemented in T036")
        self.splitter.addWidget(self.server_list_placeholder)
        
        # Placeholder for details panel
        self.details_placeholder = QWidget()
        self.splitter.addWidget(self.details_placeholder)
        
        # Set splitter sizes (70% for list, 30% for details)
        self.splitter.setSizes([700, 300])
    
    def _setup_tk_ui(self):
        """Set up tkinter UI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Paned window (splitter)
        self.paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for server list
        list_frame = ttk.Frame(self.paned)
        self.paned.add(list_frame, weight=7)
        
        label = ttk.Label(list_frame, text="Server list will be implemented in T036")
        label.pack(padx=10, pady=10)
        
        # Placeholder for details
        details_frame = ttk.Frame(self.paned)
        self.paned.add(details_frame, weight=3)
    
    def _setup_menus(self):
        """Set up the menu bar."""
        if USING_QT:
            self._setup_qt_menus()
        else:
            self._setup_tk_menus()
    
    def _setup_qt_menus(self):
        """Set up Qt menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        self.load_action = QAction("&Load Configuration", self)
        self.load_action.setShortcut(QKeySequence.StandardKey.Open)
        self.load_action.triggered.connect(self.load_configuration)
        file_menu.addAction(self.load_action)
        
        self.save_action = QAction("&Save Configuration", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(self.save_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        self.add_server_action = QAction("&Add Server...", self)
        self.add_server_action.setShortcut(QKeySequence("Ctrl+N"))
        self.add_server_action.triggered.connect(self.add_server)
        edit_menu.addAction(self.add_server_action)
        
        edit_menu.addSeparator()
        
        self.enable_all_action = QAction("&Enable All", self)
        self.enable_all_action.triggered.connect(self.enable_all_servers)
        edit_menu.addAction(self.enable_all_action)
        
        self.disable_all_action = QAction("&Disable All", self)
        self.disable_all_action.triggered.connect(self.disable_all_servers)
        edit_menu.addAction(self.disable_all_action)
        
        edit_menu.addSeparator()
        
        self.settings_action = QAction("&Settings...", self)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(self.settings_action)
        
        # Presets menu
        presets_menu = menubar.addMenu("&Presets")
        
        self.manage_presets_action = QAction("&Manage Presets...", self)
        self.manage_presets_action.triggered.connect(self.manage_presets)
        presets_menu.addAction(self.manage_presets_action)
        
        presets_menu.addSeparator()
        
        # Preset actions will be dynamically added
        self.preset_actions = []
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        self.backup_action = QAction("&Backup Configuration", self)
        self.backup_action.triggered.connect(self.backup_configuration)
        tools_menu.addAction(self.backup_action)
        
        self.restore_action = QAction("&Restore Configuration...", self)
        self.restore_action.triggered.connect(self.restore_configuration)
        tools_menu.addAction(self.restore_action)
        
        tools_menu.addSeparator()
        
        self.validate_action = QAction("&Validate Configuration", self)
        self.validate_action.triggered.connect(self.validate_configuration)
        tools_menu.addAction(self.validate_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)
    
    def _setup_tk_menus(self):
        """Set up tkinter menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Configuration", command=self.load_configuration)
        file_menu.add_command(label="Save Configuration", command=self.save_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Server...", command=self.add_server)
        edit_menu.add_separator()
        edit_menu.add_command(label="Enable All", command=self.enable_all_servers)
        edit_menu.add_command(label="Disable All", command=self.disable_all_servers)
        edit_menu.add_separator()
        edit_menu.add_command(label="Settings...", command=self.show_settings)
        
        # Presets menu
        presets_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Presets", menu=presets_menu)
        presets_menu.add_command(label="Manage Presets...", command=self.manage_presets)
        presets_menu.add_separator()
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Backup Configuration", command=self.backup_configuration)
        tools_menu.add_command(label="Restore Configuration...", command=self.restore_configuration)
        tools_menu.add_separator()
        tools_menu.add_command(label="Validate Configuration", command=self.validate_configuration)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        if USING_QT:
            self._setup_qt_toolbar()
        else:
            self._setup_tk_toolbar()
    
    def _setup_qt_toolbar(self):
        """Set up Qt toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Add toolbar actions
        toolbar.addAction(self.load_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.add_server_action)
        toolbar.addSeparator()
        toolbar.addAction(self.enable_all_action)
        toolbar.addAction(self.disable_all_action)
        toolbar.addSeparator()
        toolbar.addAction(self.validate_action)
    
    def _setup_tk_toolbar(self):
        """Set up tkinter toolbar."""
        # Insert toolbar after menu but before main content
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, before=self.root.winfo_children()[-1])
        
        ttk.Button(toolbar, text="Load", command=self.load_configuration).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_configuration).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Add Server", command=self.add_server).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Enable All", command=self.enable_all_servers).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Disable All", command=self.disable_all_servers).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Validate", command=self.validate_configuration).pack(side=tk.LEFT, padx=2)
    
    def _setup_status_bar(self):
        """Set up the status bar with save indicator."""
        if USING_QT:
            self._setup_qt_status_bar()
        else:
            self._setup_tk_status_bar()
    
    def _setup_qt_status_bar(self):
        """Set up Qt status bar."""
        self._status_bar = self.statusBar()
        self._status_bar.setSizeGripEnabled(True)
        
        # Status message label
        from PyQt6.QtWidgets import QLabel
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)
        
        # Save indicator (permanent widget on the right)
        self._save_indicator = QLabel("")
        self._status_bar.addPermanentWidget(self._save_indicator)
        
        self._update_save_indicator()
    
    def _setup_tk_status_bar(self):
        """Set up tkinter status bar."""
        self._status_bar = ttk.Frame(self.root)
        self._status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message label
        self._status_label = ttk.Label(self._status_bar, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self._status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Save indicator
        self._save_indicator = ttk.Label(self._status_bar, text="", relief=tk.SUNKEN, anchor=tk.E)
        self._save_indicator.pack(side=tk.RIGHT, padx=5)
        
        self._update_save_indicator()
    
    def _update_save_indicator(self):
        """Update the save indicator based on unsaved changes."""
        if self._unsaved_changes:
            text = "● Modified"
            if USING_QT:
                self._save_indicator.setText(text)
                self._save_indicator.setStyleSheet("color: orange;")
            else:
                self._save_indicator.config(text=text, foreground="orange")
        else:
            text = "✓ Saved"
            if USING_QT:
                self._save_indicator.setText(text)
                self._save_indicator.setStyleSheet("color: green;")
            else:
                self._save_indicator.config(text=text, foreground="green")
    
    def set_unsaved_changes(self, unsaved: bool):
        """Set unsaved changes state and update UI."""
        self._unsaved_changes = unsaved
        self._update_save_indicator()
        
        # Update window title
        title = "MCP Config Manager"
        if unsaved:
            title += " *"
        
        if USING_QT:
            self.setWindowTitle(title)
        else:
            self.root.title(title)
    
    def set_status_message(self, message: str, timeout: int = 0):
        """Set status bar message."""
        if USING_QT:
            if timeout > 0:
                self._status_bar.showMessage(message, timeout * 1000)
            else:
                self._status_label.setText(message)
        else:
            self._status_label.config(text=message)
            if timeout > 0:
                self.root.after(timeout * 1000, lambda: self._status_label.config(text="Ready"))
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Shortcuts are set up in menu actions for Qt
        # For tkinter, we bind them here
        if not USING_QT:
            self.root.bind("<Control-o>", lambda e: self.load_configuration())
            self.root.bind("<Control-s>", lambda e: self.save_configuration())
            self.root.bind("<Control-n>", lambda e: self.add_server())
            self.root.bind("<Control-comma>", lambda e: self.show_settings())
            self.root.bind("<Control-q>", lambda e: self.root.quit())
    
    def _load_window_state(self):
        """Load window state from UI configuration."""
        if self.ui_config.window_geometry:
            geom = self.ui_config.window_geometry
            if USING_QT:
                self.setGeometry(geom['x'], geom['y'], geom['width'], geom['height'])
                if geom.get('maximized'):
                    self.showMaximized()
            else:
                self.root.geometry(f"{geom['width']}x{geom['height']}+{geom['x']}+{geom['y']}")
    
    def _save_window_state(self):
        """Save window state to UI configuration."""
        if USING_QT:
            self.ui_config.window_geometry = {
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height(),
                'maximized': self.isMaximized()
            }
        else:
            geom = self.root.geometry()
            # Parse tkinter geometry string
            parts = geom.split('+')
            size = parts[0].split('x')
            self.ui_config.window_geometry = {
                'x': int(parts[1]),
                'y': int(parts[2]),
                'width': int(size[0]),
                'height': int(size[1]),
                'maximized': False
            }
    
    # Action handlers (placeholders for now)
    def load_configuration(self):
        """Load configuration from file."""
        self.set_status_message("Loading configuration...")
        # Will be implemented with controllers
        self.set_status_message("Configuration loaded", 3)
    
    def save_configuration(self):
        """Save configuration to file."""
        self.set_status_message("Saving configuration...")
        # Will be implemented with controllers
        self.set_unsaved_changes(False)
        self.set_status_message("Configuration saved", 3)
    
    def add_server(self):
        """Show add server dialog."""
        print("Add server - will be implemented in T040")
    
    def enable_all_servers(self):
        """Enable all servers."""
        self.set_unsaved_changes(True)
        self.set_status_message("All servers enabled", 3)
    
    def disable_all_servers(self):
        """Disable all servers."""
        self.set_unsaved_changes(True)
        self.set_status_message("All servers disabled", 3)
    
    def show_settings(self):
        """Show settings dialog."""
        print("Settings - will be implemented in T042")
    
    def manage_presets(self):
        """Show preset manager dialog."""
        print("Manage presets - will be implemented in T041")
    
    def backup_configuration(self):
        """Create configuration backup."""
        self.set_status_message("Creating backup...")
        # Will be implemented with controllers
        self.set_status_message("Backup created", 3)
    
    def restore_configuration(self):
        """Show restore dialog."""
        print("Restore - will be implemented in T043")
    
    def validate_configuration(self):
        """Validate current configuration."""
        self.set_status_message("Validating configuration...")
        # Will be implemented with controllers
        self.set_status_message("Configuration is valid", 3)
    
    def show_about(self):
        """Show about dialog."""
        if USING_QT:
            QMessageBox.about(self, "About MCP Config Manager",
                            "MCP Config Manager\n\n"
                            "A cross-platform utility for managing Model Context Protocol servers.\n\n"
                            "Version 1.0.0")
        else:
            messagebox.showinfo("About MCP Config Manager",
                              "MCP Config Manager\n\n"
                              "A cross-platform utility for managing Model Context Protocol servers.\n\n"
                              "Version 1.0.0")
    
    def closeEvent(self, event):
        """Handle window close event (Qt)."""
        if self._unsaved_changes:
            if USING_QT:
                reply = QMessageBox.question(self, "Unsaved Changes",
                                           "You have unsaved changes. Do you want to save them?",
                                           QMessageBox.StandardButton.Save |
                                           QMessageBox.StandardButton.Discard |
                                           QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    self.save_configuration()
                    event.accept()
                elif reply == QMessageBox.StandardButton.Discard:
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        else:
            event.accept()
        
        if event.isAccepted():
            self._save_window_state()
    
    def run(self):
        """Run the application (tkinter only)."""
        if not USING_QT:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.root.mainloop()
    
    def _on_closing(self):
        """Handle window close event (tkinter)."""
        if self._unsaved_changes:
            result = messagebox.askyesnocancel("Unsaved Changes",
                                              "You have unsaved changes. Do you want to save them?")
            if result is True:
                self.save_configuration()
                self._save_window_state()
                self.root.destroy()
            elif result is False:
                self._save_window_state()
                self.root.destroy()
        else:
            self._save_window_state()
            self.root.destroy()


def main():
    """Main entry point for GUI application."""
    if USING_QT:
        app = QApplication(sys.argv)
        app.setApplicationName("MCP Config Manager")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        window = MainWindow()
        window.run()


if __name__ == "__main__":
    main()