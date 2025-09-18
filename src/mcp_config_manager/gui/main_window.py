"""Main window for MCP Config Manager GUI."""

import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QToolBar, QStatusBar, QMessageBox,
        QApplication, QSplitter, QListWidget
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QIcon, QKeySequence, QAction
    USING_QT = True
    HAS_TKINTER = False
    tk = None
    ttk = None
    messagebox = None
except ImportError:
    USING_QT = False
    HAS_TKINTER = False
    QMainWindow = object
    QWidget = object
    QVBoxLayout = object
    QHBoxLayout = object
    QMenuBar = object
    QToolBar = object
    QStatusBar = object
    QAction = object
    QMessageBox = object
    QApplication = object
    QSplitter = object
    QListWidget = object
    Qt = None
    QTimer = None
    pyqtSignal = None
    QIcon = None
    QKeySequence = None
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        HAS_TKINTER = True
    except ImportError:
        tk = None
        ttk = None
        messagebox = None
        HAS_TKINTER = False

from .models.app_state import ApplicationState
from .models.ui_config import UIConfiguration, WindowGeometry
from .controllers.config_controller import ConfigController
from .controllers.server_controller import ServerController
from .controllers.preset_controller import PresetController
from .controllers.backup_controller import BackupController
from .events.dispatcher import dispatcher, EventType, Event
from .widgets.server_list import ServerListWidget
from .widgets.server_details_panel import ServerDetailsPanel
from .dialogs.add_server_dialog import AddServerDialog
from .dialogs.preset_manager_dialog import PresetManagerDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.backup_restore_dialog import BackupRestoreDialog
from .dialogs.delete_servers_dialog import DeleteServersDialog


class MainWindow(QMainWindow if USING_QT else object):
    """Main application window for MCP Config Manager."""
    
    # Qt signals
    if USING_QT:
        config_loaded = pyqtSignal(dict)
        config_saved = pyqtSignal()
        mode_changed = pyqtSignal(str)
        server_toggled = pyqtSignal(str, bool)
        preset_applied = pyqtSignal(str)
    
    def __init__(self, config_manager=None, parent=None):
        """Initialize the main window."""
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("MainWindow.__init__ started")

        if USING_QT:
            super().__init__(parent)
            self._setup_qt_window()
        elif HAS_TKINTER:
            self._setup_tk_window()
        else:
            raise RuntimeError("No GUI framework available")

        logging.debug("Framework setup complete")

        self.config_manager = config_manager
        self.app_state = ApplicationState()
        self.ui_config = UIConfiguration()
        self._unsaved_changes = False
        self._status_bar = None
        self._status_label = None
        self._save_indicator = None
        # Remove mode from app_state as we're using per-client states now
        # Mode is deprecated and will be removed completely in phase 8
        
        logging.debug("Initializing controllers")
        # Initialize controllers
        self.config_controller = ConfigController()
        self.server_controller = ServerController()
        self.preset_controller = PresetController()
        self.backup_controller = BackupController()
        
        logging.debug("Initializing widgets")
        # Initialize widgets
        self.server_list_widget = None
        
        logging.debug("Setting up UI")
        self._setup_ui()
        logging.debug("Setting up menus")
        self._setup_menus()
        logging.debug("Setting up toolbar")
        self._setup_toolbar()
        logging.debug("Setting up status bar")
        self._setup_status_bar()
        logging.debug("Setting up shortcuts")
        self._setup_shortcuts()
        logging.debug("Connecting events")
        self._connect_events()
        logging.debug("Registering event handlers")
        self._register_event_handlers()
        
        logging.debug("Scheduling configuration load")
        # Load initial configuration after all UI is ready
        # Set initial status
        self.set_status_message("Ready", timeout=0)
        
        # Use QTimer to delay loading to allow window to show first
        print("DEBUG: About to schedule/call configuration load")
        print(f"DEBUG: USING_QT = {USING_QT}")
        
        if USING_QT:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.load_configuration)
        else:
            # For tkinter, use after method
            self.root.after(100, self.load_configuration)
        
        logging.debug("Loading window state")
        self._load_window_state()
        logging.debug("MainWindow.__init__ finished")
    
    def _setup_qt_window(self):
        """Set up Qt window properties."""
        self.setWindowTitle("MCP Config Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        # Ensure window gets focus and comes to front
        self.raise_()
        self.activateWindow()
        
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
        main_layout.setSpacing(0)  # Remove spacing between widgets
        
        # Content splitter (for future server list and details)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Server list widget
        self.server_list = ServerListWidget()
        self.splitter.addWidget(self.server_list)
        
        # Server details panel
        self.server_details_panel = ServerDetailsPanel()
        self.splitter.addWidget(self.server_details_panel)
        
        # Set splitter sizes (60% for list, 40% for details)
        self.splitter.setSizes([600, 400])
    
    def _setup_tk_ui(self):
        """Set up tkinter UI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Paned window (splitter)
        self.paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Server list widget
        self.server_list = ServerListWidget(self.paned)
        self.paned.add(self.server_list.frame, weight=6)
        
        # Server details panel
        self.server_details_panel = ServerDetailsPanel(self.paned)
        self.paned.add(self.server_details_panel.get_widget(), weight=4)
    
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
        
        self.save_action = QAction("&Save Configuration", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(self.save_action)

        self.refresh_action = QAction("&Refresh Servers", self)
        self.refresh_action.setShortcut(QKeySequence("F5"))
        self.refresh_action.triggered.connect(self.reload_servers_from_disk)
        file_menu.addAction(self.refresh_action)

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

        self.discover_servers_action = QAction("&Discover Project Servers...", self)
        self.discover_servers_action.setShortcut(QKeySequence("Ctrl+D"))
        self.discover_servers_action.triggered.connect(self.discover_project_servers)
        tools_menu.addAction(self.discover_servers_action)

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
        file_menu.add_command(label="Save Configuration", command=self.save_configuration)
        file_menu.add_command(label="Refresh Servers", command=self.reload_servers_from_disk, accelerator="F5")
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
        tools_menu.add_command(label="Discover Project Servers...", command=self.discover_project_servers, accelerator="Ctrl+D")
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
        """Set up Qt toolbar with improved visual hierarchy."""
        from PyQt6.QtWidgets import QPushButton, QToolBar, QWidget
        from PyQt6.QtCore import QSize
        
        self.toolbar = QToolBar("Main")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Set toolbar style to show buttons with text
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Dynamic Revert button - only shown when there are unsaved changes
        # Create a QAction instead of a QPushButton for better toolbar integration
        self.revert_action = QAction("Revert", self)
        self.revert_action.triggered.connect(self.on_revert_changes)
        self.revert_action.setToolTip("Discard changes and reload from file")
        # Don't add it to toolbar yet - we'll add/remove it dynamically
        
        # Store reference to the action for later use
        self.revert_action_added = False
        
        # Consistent button style for all toolbar buttons
        button_style = """
            QPushButton {
                background-color: #F8F8F8;
                border: 1px solid #CCCCCC;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """
        
        # Add spacing at the start of the toolbar
        spacer = QWidget()
        spacer.setFixedWidth(8)
        self.toolbar.addWidget(spacer)
        
        # Primary action - Save Configuration
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setStyleSheet(button_style)
        save_btn.setToolTip("Save current configuration")
        self.toolbar.addWidget(save_btn)

        # Refresh button - reload from disk
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.reload_servers_from_disk)
        refresh_btn.setStyleSheet(button_style)
        refresh_btn.setToolTip("Reload server configurations from disk (F5)")
        self.toolbar.addWidget(refresh_btn)

        self.toolbar.addSeparator()
        
        # Secondary action - Add Server
        add_btn = QPushButton("➕ Add Server")
        add_btn.clicked.connect(self.add_server)
        add_btn.setStyleSheet(button_style)
        add_btn.setToolTip("Add a new server configuration")
        self.toolbar.addWidget(add_btn)
        
        # Delete Server button
        delete_btn = QPushButton("🗑️ Delete Server")
        delete_btn.clicked.connect(self.delete_servers)
        delete_btn.setStyleSheet(button_style)
        delete_btn.setToolTip("Delete multiple server configurations")
        self.toolbar.addWidget(delete_btn)
        
        self.toolbar.addSeparator()

        # Discover Project Servers button
        discover_btn = QPushButton("🔍 Discover")
        discover_btn.clicked.connect(self.discover_project_servers)
        discover_btn.setStyleSheet(button_style)
        discover_btn.setToolTip("Discover project-specific MCP servers (Ctrl+D)")
        self.toolbar.addWidget(discover_btn)

        self.toolbar.addSeparator()

        # Tertiary action - Validate
        validate_btn = QPushButton("✓ Validate")
        validate_btn.clicked.connect(self.validate_configuration)
        validate_btn.setStyleSheet(button_style)
        validate_btn.setToolTip("Validate current configuration")
        self.toolbar.addWidget(validate_btn)
        
        self.toolbar.addSeparator()
        
        # Backup button
        backup_btn = QPushButton("📦 Backup")
        backup_btn.setToolTip("Create backup of configuration files")
        backup_btn.clicked.connect(self.quick_backup)
        backup_btn.setStyleSheet(button_style)
        self.toolbar.addWidget(backup_btn)
        
        # Restore button
        restore_btn = QPushButton("📂 Restore")
        restore_btn.setToolTip("Restore configuration from backup files")
        restore_btn.clicked.connect(self.quick_restore)
        restore_btn.setStyleSheet(button_style)
        self.toolbar.addWidget(restore_btn)
    
    def _setup_tk_toolbar(self):
        """Set up tkinter toolbar with improved visual hierarchy."""
        # Insert toolbar after menu but before main content
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, before=self.root.winfo_children()[-1])
        
        # Dynamic Revert button - only shown when there are unsaved changes
        self.revert_btn = ttk.Button(toolbar, text="Revert", command=self.on_revert_changes)
        # Initially hidden by not packing
        
        # Primary action - Save
        save_btn = ttk.Button(toolbar, text="Save", command=self.save_configuration)
        save_btn.pack(side=tk.LEFT, padx=2)
        # Note: tkinter doesn't support button styling as richly as Qt

        # Refresh button
        refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.reload_servers_from_disk)
        refresh_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Secondary actions
        ttk.Button(toolbar, text="Add Server", command=self.add_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Server", command=self.delete_servers).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Discover servers button
        ttk.Button(toolbar, text="Discover", command=self.discover_project_servers).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Tertiary action
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
        logging.debug(f"set_unsaved_changes called with unsaved={unsaved}")
        self._unsaved_changes = unsaved
        self._update_save_indicator()
        
        # Add/remove Revert action from toolbar based on unsaved changes
        if hasattr(self, 'revert_action') and hasattr(self, 'toolbar'):
            logging.debug(f"revert_action exists, setting visibility to {unsaved}")
            if USING_QT:
                if unsaved and not self.revert_action_added:
                    # Get the Save button action to insert before it
                    actions = self.toolbar.actions()
                    if actions:
                        # Insert before the first action (Save button)
                        self.toolbar.insertAction(actions[0], self.revert_action)
                    else:
                        self.toolbar.addAction(self.revert_action)
                    self.revert_action_added = True
                    logging.debug("Added revert action to toolbar")
                elif not unsaved and self.revert_action_added:
                    self.toolbar.removeAction(self.revert_action)
                    self.revert_action_added = False
                    logging.debug("Removed revert action from toolbar")
            else:
                if unsaved and not self.revert_btn.winfo_ismapped():
                    self.revert_btn.pack(side=tk.LEFT, padx=2, before=self.root.winfo_children()[1].winfo_children()[0])
                elif not unsaved and self.revert_btn.winfo_ismapped():
                    self.revert_btn.pack_forget()
        else:
            logging.debug("revert_action or toolbar does not exist yet")
        
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
        if USING_QT:
            # Qt shortcuts are set up in menu actions, but we add additional ones here
            from PyQt6.QtGui import QShortcut
            
            # Additional shortcuts not in menus
            QShortcut(QKeySequence("Ctrl+R"), self, self.reload_servers_from_disk)
            QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
            QShortcut(QKeySequence("Ctrl+P"), self, self.manage_presets)
            QShortcut(QKeySequence("Ctrl+B"), self, self.backup_configuration)
            QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.restore_configuration)
            QShortcut(QKeySequence("Ctrl+Shift+V"), self, self.validate_configuration)
            QShortcut(QKeySequence("F1"), self, self.show_help)
            QShortcut(QKeySequence("F5"), self, self.reload_servers_from_disk)
            QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_action)
            QShortcut(QKeySequence("Ctrl+Y"), self, self._redo_action)
            QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo_action)
            QShortcut(QKeySequence("Escape"), self, self._clear_selection)
        else:
            # Tkinter key bindings
            self.root.bind("<Control-s>", lambda e: self.save_configuration())
            self.root.bind("<Control-n>", lambda e: self.add_server())
            self.root.bind("<Control-comma>", lambda e: self.show_settings())
            self.root.bind("<Control-q>", lambda e: self.quit_application())
            self.root.bind("<Control-r>", lambda e: self.reload_servers_from_disk())
            self.root.bind("<Control-f>", lambda e: self._focus_search())
            self.root.bind("<Control-p>", lambda e: self.manage_presets())
            self.root.bind("<Control-b>", lambda e: self.backup_configuration())
            self.root.bind("<Control-Shift-R>", lambda e: self.restore_configuration())
            self.root.bind("<Control-Shift-V>", lambda e: self.validate_configuration())
            self.root.bind("<F1>", lambda e: self.show_help())
            self.root.bind("<F5>", lambda e: self.reload_servers_from_disk())
            self.root.bind("<Control-z>", lambda e: self._undo_action())
            self.root.bind("<Control-y>", lambda e: self._redo_action())
            self.root.bind("<Control-Shift-Z>", lambda e: self._redo_action())
            self.root.bind("<Escape>", lambda e: self._clear_selection())
    
    def _load_window_state(self):
        """Load window state from UI configuration."""
        if self.ui_config.window_geometry:
            geom = self.ui_config.window_geometry
            if USING_QT:
                self.setGeometry(geom.x, geom.y, geom.width, geom.height)
                if geom.maximized:
                    self.showMaximized()
            else:
                self.root.geometry(f"{geom.width}x{geom.height}+{geom.x}+{geom.y}")
    
    def _save_window_state(self):
        """Save window state to UI configuration."""
        if USING_QT:
            self.ui_config.window_geometry = WindowGeometry(
                x=self.x(),
                y=self.y(),
                width=self.width(),
                height=self.height(),
                maximized=self.isMaximized()
            )
        else:
            geom = self.root.geometry()
            # Parse tkinter geometry string
            parts = geom.split('+')
            size = parts[0].split('x')
            self.ui_config.window_geometry = WindowGeometry(
                x=int(parts[1]),
                y=int(parts[2]),
                width=int(size[0]),
                height=int(size[1]),
                maximized=False
            )
    
    # Action handlers (placeholders for now)
    def _connect_events(self):
        """Connect UI events to controllers."""
        # Connect widget signals to controller methods
        if hasattr(self, 'server_list') and self.server_list:
            # For Qt signals
            if USING_QT:
                self.server_list.server_toggled.connect(self._on_server_toggled)
                self.server_list.server_selected.connect(self._on_server_selected)
                self.server_list.servers_bulk_toggled.connect(self._handle_servers_bulk_toggled)
                self.server_list.server_promoted.connect(self._on_server_promoted)
            else:
                # For tkinter callbacks
                self.server_list._toggle_callbacks.append(self._on_server_toggled)
                self.server_list._selection_callbacks.append(self._on_server_selected)
        
        # Connect server details panel signals
        if hasattr(self, 'server_details_panel'):
            if USING_QT:
                self.server_details_panel.server_updated.connect(self._on_server_updated)
                self.server_details_panel.server_deleted.connect(self._on_server_deleted)
            else:
                # For tkinter callbacks
                self.server_details_panel.update_callbacks.append(self._on_server_updated)
                self.server_details_panel.server_deleted_callbacks.append(self._on_server_deleted)
    
    def _register_event_handlers(self):
        """Register handlers for dispatcher events."""
        # Configuration events
        dispatcher.subscribe(EventType.CONFIG_LOADED, self._handle_config_loaded)
        dispatcher.subscribe(EventType.CONFIG_SAVED, self._handle_config_saved)
        dispatcher.subscribe(EventType.CONFIG_ERROR, self._handle_config_error)
        
        # Server events
        dispatcher.subscribe(EventType.SERVER_TOGGLED, self._handle_server_toggled)
        dispatcher.subscribe(EventType.SERVER_ADDED, self._handle_server_added)
        dispatcher.subscribe(EventType.SERVERS_BULK_TOGGLED, self._handle_servers_bulk_toggled)
        
        # Preset events
        dispatcher.subscribe(EventType.PRESET_APPLIED, self._handle_preset_applied)
        dispatcher.subscribe(EventType.PRESET_SAVED, self._handle_preset_saved)
        
        # Mode events removed - no longer needed with per-client operations
        
        # Backup events
        dispatcher.subscribe(EventType.BACKUP_CREATED, self._handle_backup_created)
        dispatcher.subscribe(EventType.BACKUP_RESTORED, self._handle_backup_restored)
        
        # Application events
        dispatcher.subscribe(EventType.APP_ERROR, self._handle_app_error)
    
    # Widget event callbacks
    def _on_server_toggled(self, *args):
        """Handle server toggle from widget.

        Can be called with either:
        - (server_name, enabled) - old style, toggles for both clients
        - (server_name, client, enabled) - new style, toggles for specific client

        Args:
            *args: Variable arguments depending on calling style
        """
        if len(args) == 2:
            # Old style: (server_name, enabled)
            server_name, enabled = args
            client = 'both'  # Default to both for backward compatibility
            logging.debug(f"_on_server_toggled called with old style: server={server_name}, enabled={enabled}")
        elif len(args) == 3:
            # New style: (server_name, client, enabled)
            server_name, client, enabled = args
            logging.debug(f"_on_server_toggled called with new style: server={server_name}, client={client}, enabled={enabled}")
        else:
            logging.error(f"_on_server_toggled called with unexpected args: {args}")
            return

        # Use the new per-client method
        result = self.server_controller.set_server_enabled(server_name, client, enabled)

        if result['success']:
            logging.debug(f"Server toggle successful, calling set_unsaved_changes(True)")
            self.set_unsaved_changes(True)
            dispatcher.emit_now(EventType.SERVER_TOGGLED,
                                {'server': server_name, 'client': client, 'enabled': enabled},
                                source='MainWindow')
        else:
            logging.error(f"Server toggle failed: {result.get('error')}")
            self.set_status_message(f"Error: {result['error']}", timeout=5)
    
    def _on_server_selected(self, server_name: str):
        """Handle server selection from widget."""
        self.app_state.selected_server = server_name
        dispatcher.emit_now(EventType.UI_SELECTION_CHANGED,
                           {'selection': server_name},
                           source='MainWindow')
        
        # Load the server configuration into the details panel
        if hasattr(self, 'server_details_panel'):
            # Get the server configuration from the servers list
            if hasattr(self, 'server_list') and self.server_list:
                server_item = self.server_list.servers.get(server_name)
                if server_item:
                    # Check if server is disabled (using string comparison for safety)
                    from mcp_config_manager.gui.models.server_list_item import ServerStatus
                    is_disabled = server_item.status == ServerStatus.DISABLED
                    # Load the server configuration into the details panel
                    self.server_details_panel.load_server(server_name, server_item.config, is_disabled)
    
    def _on_server_updated(self, server_name: str, config: dict):
        """Handle server update from details panel."""
        # Call the server controller to update the server
        result = self.server_controller.update_server(server_name, config)
        
        if result['success']:
            # Update the server in the list widget
            if hasattr(self, 'server_list') and self.server_list:
                server_item = self.server_list.servers.get(server_name)
                if server_item:
                    server_item.config = config
            
            # Mark configuration as changed
            self.set_unsaved_changes(True)
            self.set_status_message(f"Server '{server_name}' updated", timeout=3)
        else:
            self.set_status_message(f"Failed to update server: {result.get('error', 'Unknown error')}", timeout=5)
    
    def _on_server_deleted(self, server_name: str, is_disabled: bool = False):
        """Handle server deletion from details panel.

        Args:
            server_name: Name of the server to delete
            is_disabled: Whether the server is from the disabled list
        """
        # Call the server controller to delete the server (uses 'both' mode by default)
        result = self.server_controller.delete_server(server_name, 'both', from_disabled=is_disabled)
        
        if result['success']:
            # Refresh the server list to remove the deleted server
            self.refresh_server_list()
            
            # Mark configuration as changed
            self.set_unsaved_changes(True)
            self.set_status_message(f"Server '{server_name}' deleted successfully", timeout=3)
        else:
            self.set_status_message(f"Failed to delete server: {result.get('error', 'Unknown error')}", timeout=5)
    
    def _on_server_promoted(self, server_name: str):
        """Handle server promotion from project to global.

        Args:
            server_name: Name of the server to promote
        """
        try:
            # Get the server's current location info
            if hasattr(self, 'server_list') and self.server_list:
                server_item = self.server_list.servers.get(server_name)
                if server_item and getattr(server_item, 'is_project_server', False):
                    project_path = getattr(server_item, 'location', None)

                    # Call server manager to promote the server
                    result = self.server_controller.server_manager.promote_project_server(
                        server_name,
                        project_path,
                        remove_from_project=True
                    )

                    if result.get('success', False):
                        # Refresh the server list to show updated location
                        self.refresh_server_list(force_reload=True)
                        self.set_unsaved_changes(True)
                        self.set_status_message(f"✅ Server '{server_name}' promoted to global configuration", timeout=5000)
                    else:
                        error = result.get('error', 'Unknown error')
                        self.set_status_message(f"❌ Failed to promote server: {error}", timeout=5000)
                else:
                    self.set_status_message(f"⚠️ Server '{server_name}' is already global", timeout=3000)
        except Exception as e:
            self.set_status_message(f"❌ Error promoting server: {str(e)}", timeout=5000)

    # Mode change handler removed - no longer needed with per-client operations

    # Dispatcher event handlers
    def _handle_config_loaded(self, event: Event):
        """Handle configuration loaded event."""
        # Get server count from event data if available
        server_count = len(event.data.get('servers', [])) if event.data else 0
        status_msg = f"Configuration loaded - {server_count} servers"
        self.set_status_message(status_msg, timeout=0)  # Set timeout to 0 for persistent message
        self.set_unsaved_changes(False)
        self.refresh_server_list()
    
    def _handle_config_saved(self, event: Event):
        """Handle configuration saved event."""
        self.set_status_message("Configuration saved successfully", timeout=3)
        # Clear unsaved changes flag
        self.set_unsaved_changes(False)
        self.set_unsaved_changes(False)
    
    def _handle_config_error(self, event: Event):
        """Handle configuration error event."""
        error_msg = event.data.get('error', 'Unknown configuration error')
        self.set_status_message(f"Configuration error: {error_msg}", timeout=0)
        if USING_QT:
            QMessageBox.critical(self, "Configuration Error", error_msg)
        else:
            messagebox.showerror("Configuration Error", error_msg)
    
    def _handle_server_toggled(self, event: Event):
        """Handle server toggled event."""
        logging.debug(f"_handle_server_toggled called with event data: {event.data}")
        server = event.data.get('server')
        enabled = event.data.get('enabled')
        status = "enabled" if enabled else "disabled"
        self.set_status_message(f"Server '{server}' {status}", timeout=3)
        # Mark configuration as having unsaved changes
        self.set_unsaved_changes(True)
    
    def _handle_server_added(self, event: Event):
        """Handle server added event."""
        server = event.data.get('server')
        self.set_status_message(f"Server '{server}' added successfully", timeout=3)
        # Mark configuration as having unsaved changes
        self.set_unsaved_changes(True)
        self.set_unsaved_changes(True)
        self.refresh_server_list()
    
    def _handle_servers_bulk_toggled(self, event: Event):
        """Handle bulk server toggle event."""
        enabled = event.data.get('enabled')
        count = event.data.get('count', 0)
        action = "enabled" if enabled else "disabled"
        self.set_status_message(f"{count} servers {action}", timeout=3)
        self.set_unsaved_changes(True)
        self.refresh_server_list()
    
    def _handle_preset_applied(self, event: Event):
        """Handle preset applied event."""
        preset = event.data.get('preset')
        self.set_status_message(f"Preset '{preset}' applied", timeout=3)
        self.set_unsaved_changes(True)
        self.refresh_server_list()
    
    def _handle_preset_saved(self, event: Event):
        """Handle preset saved event."""
        preset = event.data.get('preset')
        self.set_status_message(f"Preset '{preset}' saved", timeout=3)
    
    # Mode changed handler removed - no longer needed with per-client operations
    
    def _handle_backup_created(self, event: Event):
        """Handle backup created event."""
        backup_file = event.data.get('file')
        self.set_status_message(f"Backup created: {backup_file}", timeout=3)
    
    def _handle_backup_restored(self, event: Event):
        """Handle backup restored event."""
        backup_file = event.data.get('file')
        self.set_status_message(f"Backup restored: {backup_file}", timeout=3)
        self.set_unsaved_changes(False)
        self.refresh_server_list()
    
    def _handle_app_error(self, event: Event):
        """Handle application error event."""
        error_msg = event.data.get('error', 'Unknown error')
        self.set_status_message(f"Error: {error_msg}", timeout=0)
        if USING_QT:
            QMessageBox.critical(self, "Application Error", error_msg)
        else:
            messagebox.showerror("Application Error", error_msg)
    
    def refresh_server_list(self, force_reload: bool = False):
        """Refresh the server list widget.

        Args:
            force_reload: If True, force a fresh read from disk bypassing caches
        """
        print("DEBUG: refresh_server_list called")
        if hasattr(self, 'server_list') and self.server_list:
            print("DEBUG: server_list exists, getting servers...")
            # Get current servers from controller - use 'both' to get all servers
            result = self.server_controller.get_servers('both', force_reload=force_reload)
            print(f"DEBUG: get_servers result: {result}")
            if result['success']:
                servers = result['data']['servers']
                print(f"DEBUG: Got {len(servers)} servers")
                self.server_list.load_servers(servers)

                # Count project servers for status display
                project_count = sum(1 for s in servers if getattr(s, 'is_project_server', False))
                global_count = len(servers) - project_count

                # Update status message to show project server count if any exist
                if project_count > 0:
                    status_msg = f"✅ {len(servers)} servers loaded ({global_count} global, {project_count} project)"
                else:
                    status_msg = f"✅ {len(servers)} servers loaded"
                self.set_status_message(status_msg, timeout=5000)
            else:
                print(f"DEBUG: get_servers failed: {result.get('error', 'Unknown error')}")
        else:
            print("DEBUG: server_list not found or None")
    
    def load_configuration(self):
        """Load configuration from file."""
        try:
            print("DEBUG: MainWindow.load_configuration called")
            self.set_status_message("Loading configuration...")
            # Always load both configs now
            result = self.config_controller.load_config()

            if result['success']:
                print("DEBUG: Configuration loaded successfully")
                dispatcher.emit_now(EventType.CONFIG_LOADED, result['data'], source='MainWindow')
                # Don't set status here - let the event handler do it
            else:
                print(f"DEBUG: Configuration load failed: {result['error']}")
                dispatcher.emit_now(EventType.CONFIG_ERROR, {'error': result['error']}, source='MainWindow')
                # Don't set status here - let the event handler do it
        except Exception as e:
            print(f"DEBUG: Exception in load_configuration: {e}")
            import traceback
            traceback.print_exc()
            self.set_status_message(f"Error loading configuration: {str(e)}", timeout=0)

    def reload_servers_from_disk(self):
        """Reload server configurations from disk, with unsaved changes protection."""
        # Show loading indicator in status bar
        self.set_status_message("🔄 Refreshing servers from disk...", timeout=0)

        # Check for unsaved changes in details panel
        if hasattr(self, 'server_details_panel') and self.server_details_panel and self.server_details_panel.has_changes:
            if USING_QT:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes in Details Panel",
                    "You have unsaved changes in the server details panel. Refreshing will discard them.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                from tkinter import messagebox
                if not messagebox.askyesno(
                    "Unsaved Changes in Details Panel",
                    "You have unsaved changes in the server details panel. Refreshing will discard them.\n\nDo you want to continue?"
                ):
                    return

        # Check for general unsaved changes
        if self._unsaved_changes:
            if USING_QT:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Refreshing will discard them.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                from tkinter import messagebox
                if not messagebox.askyesno(
                    "Unsaved Changes",
                    "You have unsaved changes. Refreshing will discard them.\n\nDo you want to continue?"
                ):
                    return

        # Save current state for comparison
        old_servers = {}
        selected_server = None
        selected_server_config = None

        if hasattr(self, 'server_list') and self.server_list:
            selected_server = self.server_list.selected_server
            # Get current server list for comparison
            for server_name in self.server_list.servers:
                old_servers[server_name] = self.server_list.servers.get(server_name)

            # Save selected server's configuration if in details panel
            if selected_server and hasattr(self, 'server_details_panel') and self.server_details_panel:
                if self.server_details_panel.current_server == selected_server:
                    selected_server_config = self.server_details_panel.original_data.copy() if hasattr(self.server_details_panel, 'original_data') and self.server_details_panel.original_data else None

        # Set loading message
        self.set_status_message("Refreshing servers from disk...")

        try:
            # Clear caches first to ensure fresh read
            if hasattr(self, 'server_controller'):
                self.server_controller.clear_caches()

            # Force reload from disk
            result = self.config_controller.reload_config()

            if result['success']:
                # Emit config loaded event to update all components
                dispatcher.emit_now(EventType.CONFIG_LOADED, result['data'], source='MainWindow')

                # Clear unsaved changes since we just reloaded
                self.set_unsaved_changes(False)

                # Get new server list for comparison
                new_servers = {}
                if hasattr(self, 'server_list') and self.server_list:
                    for server_name in self.server_list.servers:
                        new_servers[server_name] = self.server_list.servers.get(server_name)

                # Detect changes
                added_servers = set(new_servers.keys()) - set(old_servers.keys())
                removed_servers = set(old_servers.keys()) - set(new_servers.keys())

                # Check for configuration changes
                modified_servers = []
                for server_name in set(old_servers.keys()) & set(new_servers.keys()):
                    old_config = old_servers[server_name]
                    new_config = new_servers[server_name]
                    if old_config != new_config:
                        modified_servers.append(server_name)

                # Build status message
                status_parts = []
                server_count = len(result['data'].get('servers', []))
                status_parts.append(f"{server_count} servers loaded")

                if added_servers:
                    status_parts.append(f"{len(added_servers)} added")
                if removed_servers:
                    status_parts.append(f"{len(removed_servers)} removed")
                if modified_servers:
                    status_parts.append(f"{len(modified_servers)} modified")

                # Add refresh timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.set_status_message(f"✅ Refreshed at {timestamp}: {', '.join(status_parts)}", timeout=10)

                # Apply visual feedback for server changes
                if hasattr(self, 'server_list') and self.server_list:
                    # Highlight newly added servers in green
                    if added_servers:
                        self.server_list.highlight_new_servers(list(added_servers))

                    # Mark modified servers in orange
                    if modified_servers:
                        self.server_list.mark_modified_servers(list(modified_servers))

                    # Flash removed servers in red (if they're still in the list momentarily)
                    # Note: Removed servers are already gone from the list at this point

                # Handle selected server restoration or conflicts
                if selected_server:
                    if selected_server in removed_servers:
                        # Server was deleted externally - refresh details panel will handle notification
                        if hasattr(self, 'server_details_panel'):
                            self.server_details_panel.refresh_current_server(None)  # Signal deletion

                    elif selected_server in modified_servers or selected_server in new_servers:
                        # Server was modified or still exists, refresh the details panel
                        if hasattr(self, 'server_details_panel') and self.server_details_panel.current_server == selected_server:
                            # Get the updated server data
                            updated_server = None
                            claude_enabled = True
                            gemini_enabled = True

                            for srv in result['data'].get('servers', []):
                                if srv['name'] == selected_server:
                                    updated_server = srv.get('config', {})
                                    claude_enabled = srv.get('claude_enabled', True)
                                    gemini_enabled = srv.get('gemini_enabled', True)
                                    break

                            if updated_server:
                                # Refresh the details panel with new data
                                # The refresh method will handle conflict resolution if there are unsaved changes
                                self.server_details_panel.refresh_current_server(
                                    updated_server,
                                    claude_enabled,
                                    gemini_enabled
                                )

                        # Restore selection in the list
                        if hasattr(self, 'server_list') and self.server_list:
                            self.server_list.select_servers([selected_server])

                # Notify about newly added servers
                if added_servers and len(added_servers) <= 3:
                    # Show individual names if only a few
                    names = ', '.join(sorted(added_servers))
                    self.set_status_message(f"ℹ️ New servers detected: {names}", timeout=7)

            else:
                # Handle JSON parse errors specifically
                error_msg = result.get('error', 'Unknown error')

                if 'JSON' in error_msg or 'parse' in error_msg.lower():
                    # JSON parse error - offer to fix or ignore
                    msg = f"Failed to parse configuration files:\n\n{error_msg}\n\nThe current configuration will be kept. Please fix the JSON files and try again."
                    if USING_QT:
                        QMessageBox.warning(self, "Invalid JSON", msg)
                    else:
                        messagebox.showwarning("Invalid JSON", msg)
                    self.set_status_message("❌ Refresh failed: Invalid JSON", timeout=0)
                else:
                    # Other errors
                    self.set_status_message(f"❌ Refresh failed: {error_msg}", timeout=0)
                    if USING_QT:
                        QMessageBox.critical(
                            self,
                            "Refresh Error",
                            f"Failed to refresh configuration:\n{error_msg}"
                        )
                    else:
                        messagebox.showerror(
                            "Refresh Error",
                            f"Failed to refresh configuration:\n{error_msg}"
                        )

        except Exception as e:
            error_msg = str(e)
            self.set_status_message(f"❌ Refresh error: {error_msg}", timeout=0)

            if USING_QT:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Refresh Error",
                    f"An error occurred during refresh:\n{error_msg}"
                )
            else:
                messagebox.showerror(
                    "Refresh Error",
                    f"An error occurred during refresh:\n{error_msg}"
                )
    
    def save_configuration(self):
        """Save configuration to file."""
        self.set_status_message("Saving configuration...")
        # Save both configs by default
        result = self.config_controller.save_config(client=None)
        
        if result['success']:
            dispatcher.emit_now(EventType.CONFIG_SAVED, result.get('data', {}), source='MainWindow')
        else:
            dispatcher.emit_now(EventType.CONFIG_ERROR, {'error': result.get('error', 'Unknown error')}, source='MainWindow')
    
    def on_revert_changes(self):
        """Revert unsaved changes by reloading from file."""
        if USING_QT:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                "Revert Changes",
                "Are you sure you want to discard all unsaved changes and reload from file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            from tkinter import messagebox
            if not messagebox.askyesno("Revert Changes", "Are you sure you want to discard all unsaved changes and reload from file?"):
                return
        
        # Reload the configuration
        self.load_configuration()
        self.set_status_message("Changes reverted", timeout=3)
    
    def add_server(self):
        """Show add server dialog."""
        dialog = AddServerDialog(self if USING_QT else self.root)
        server_json = dialog.show()
        if server_json:
            # Add to both clients by default
            result = self.server_controller.add_server(server_json, 'both')
            if result['success']:
                server_names = result.get('server_names', [])
                # For now, emit event for each server added
                for server_name in server_names:
                    dispatcher.emit_now(EventType.SERVER_ADDED,
                                       {'server': server_name},
                                       source='MainWindow')
            else:
                dispatcher.emit_now(EventType.APP_ERROR,
                                   {'error': result['error']},
                                   source='MainWindow')
    
    def delete_servers(self):
        """Show delete servers dialog for bulk deletion."""
        # Get all servers from both clients
        result = self.server_controller.get_servers('both')
        
        if not result['success']:
            self.set_status_message(f"Failed to get servers: {result.get('error', 'Unknown error')}", timeout=5)
            return
        
        servers_list = result['data']['servers']
        if not servers_list:
            if USING_QT:
                QMessageBox.information(self, "No Servers", "There are no servers to delete.")
            else:
                messagebox.showinfo("No Servers", "There are no servers to delete.")
            return
        
        # Convert list of ServerListItem objects to dict with server names as keys
        servers = {}
        for server_item in servers_list:
            # ServerListItem has name and config attributes
            servers[server_item.name] = {
                'config': server_item.config,
                'status': server_item.status
            }
        
        # Show delete dialog
        dialog = DeleteServersDialog(self if USING_QT else self.root, servers)
        if dialog.exec() if USING_QT else dialog.show():
            selected_servers = dialog.get_selected_servers()
            
            if selected_servers:
                # Delete each selected server
                deleted_count = 0
                failed_servers = []
                
                for server_name in selected_servers:
                    delete_result = self.server_controller.delete_server(server_name, 'both')
                    if delete_result['success']:
                        deleted_count += 1
                    else:
                        failed_servers.append((server_name, delete_result.get('error', 'Unknown error')))
                
                # Refresh the server list
                self.refresh_server_list()
                
                # Mark configuration as changed
                if deleted_count > 0:
                    self.set_unsaved_changes(True)
                
                # Show results
                if deleted_count > 0 and not failed_servers:
                    self.set_status_message(f"Successfully deleted {deleted_count} server(s)", timeout=5)
                elif deleted_count > 0 and failed_servers:
                    error_msg = f"Deleted {deleted_count} server(s), but {len(failed_servers)} failed:\n"
                    error_msg += "\n".join(f"• {name}: {error}" for name, error in failed_servers)
                    if USING_QT:
                        QMessageBox.warning(self, "Partial Deletion", error_msg)
                    else:
                        messagebox.showwarning("Partial Deletion", error_msg)
                elif failed_servers:
                    error_msg = "Failed to delete servers:\n"
                    error_msg += "\n".join(f"• {name}: {error}" for name, error in failed_servers)
                    if USING_QT:
                        QMessageBox.critical(self, "Deletion Failed", error_msg)
                    else:
                        messagebox.showerror("Deletion Failed", error_msg)
    
    def enable_all_servers(self):
        """Enable all servers for both clients."""
        result = self.server_controller.bulk_toggle(True, 'both')
        if result['success']:
            count = result['data'].get('count', 0)
            dispatcher.emit_now(EventType.SERVERS_BULK_TOGGLED,
                               {'enabled': True, 'count': count},
                               source='MainWindow')
        else:
            dispatcher.emit_now(EventType.APP_ERROR,
                               {'error': result['error']},
                               source='MainWindow')
    
    def disable_all_servers(self):
        """Disable all servers for both clients."""
        result = self.server_controller.bulk_toggle(False, 'both')
        if result['success']:
            count = result['data'].get('count', 0)
            dispatcher.emit_now(EventType.SERVERS_BULK_TOGGLED,
                               {'enabled': False, 'count': count},
                               source='MainWindow')
        else:
            dispatcher.emit_now(EventType.APP_ERROR,
                               {'error': result['error']},
                               source='MainWindow')
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self if USING_QT else self.root)
        if dialog.exec() if USING_QT else dialog.show():
            # Settings saved in dialog, update UI config if needed
            self.ui_config = dialog.get_settings()
    
    def manage_presets(self):
        """Show preset manager dialog."""
        dialog = PresetManagerDialog(self if USING_QT else self.root)
        dialog.set_controller(self.preset_controller)
        if dialog.exec() if USING_QT else dialog.show():
            # Check if preset was applied
            if hasattr(dialog, 'applied_preset') and dialog.applied_preset:
                dispatcher.emit_now(EventType.PRESET_APPLIED,
                                   {'preset': dialog.applied_preset},
                                   source='MainWindow')
    
    def backup_configuration(self):
        """Create configuration backup."""
        self.set_status_message("Creating backup...")
        # Backup both configs by default
        result = self.backup_controller.create_backup('both')
        if result['success']:
            backup_file = result['data'].get('file')
            dispatcher.emit_now(EventType.BACKUP_CREATED,
                               {'file': backup_file},
                               source='MainWindow')
        else:
            dispatcher.emit_now(EventType.BACKUP_ERROR,
                               {'error': result['error']},
                               source='MainWindow')
    
    def quick_backup(self):
        """Quick backup using the BackupController to centralized backups directory."""
        try:
            self.set_status_message("Creating backup...")
            result = self.backup_controller.create_backup()
            
            if result['success']:
                backup_file = result.get('backup_file', '')
                all_backups = result.get('all_backups', [])
                
                if all_backups:
                    # Show all backed up files
                    files_str = ', '.join([name for name, path in all_backups])
                    self.set_status_message(f"✅ Backup created: {files_str}", timeout=5000)
                    
                    if USING_QT:
                        # Show only the filename, not the full path for cleaner display
                        backup_list = '\n'.join([f"{name}: {Path(path).name}" for name, path in all_backups])
                        backup_dir = Path.home() / 'Documents' / 'MCP Config Manager' / 'backups'
                        QMessageBox.information(self, "Backup Complete",
                                              f"Configuration backed up to:\n{backup_dir}\n\n{backup_list}")
                else:
                    self.set_status_message(f"✅ Backup created: {backup_file}", timeout=5000)
                    if USING_QT:
                        QMessageBox.information(self, "Backup Complete", 
                                              f"Configuration backed up to:\n{backup_file}")
                        
                # Emit backup created event
                dispatcher.emit_now(EventType.BACKUP_CREATED,
                                   {'file': backup_file, 'all_backups': all_backups},
                                   source='MainWindow')
            else:
                error_msg = result.get('error', 'Unknown backup error')
                self.set_status_message(f"❌ Backup failed: {error_msg}", timeout=0)
                if USING_QT:
                    QMessageBox.critical(self, "Backup Error", f"Backup failed: {error_msg}")
                    
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.set_status_message(f"❌ {error_msg}", timeout=0)
            if USING_QT:
                QMessageBox.critical(self, "Backup Error", error_msg)
    
    def quick_restore(self):
        """Quick restore from backup files in the backups directory."""
        import shutil
        from pathlib import Path
        from ..utils.file_utils import get_project_backups_dir, get_disabled_servers_path
        
        if USING_QT:
            from PyQt6.QtWidgets import QFileDialog
            
            backups_dir = get_project_backups_dir()
            
            # Show file selection dialog starting from backups directory
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Backup Files to Restore",
                str(backups_dir) if backups_dir.exists() else str(Path.cwd()),
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if not files:
                return
                
            # Ask for confirmation
            file_list = '\n'.join([Path(f).name for f in files])
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                f"This will replace your current configuration with:\n{file_list}\n\nAre you sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            try:
                restored = []
                for backup_file in files:
                    backup_path = Path(backup_file)
                    filename = backup_path.name.lower()
                    
                    # Determine destination based on filename
                    if filename.startswith('claude-backup'):
                        dest = Path.home() / '.claude.json'
                        shutil.copy2(backup_path, dest)
                        restored.append('Claude')
                    elif filename.startswith('gemini-backup'):
                        dest = Path.home() / '.gemini' / 'settings.json'
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, dest)
                        restored.append('Gemini')
                    elif filename.startswith('disabled-backup'):
                        dest = get_disabled_servers_path()
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, dest)
                        restored.append('Disabled Servers')
                
                if restored:
                    self.set_status_message(f"✅ Restored: {', '.join(restored)}", timeout=5000)
                    QMessageBox.information(self, "Restore Complete",
                                          f"Configuration restored for: {', '.join(restored)}\n\nReloading configuration...")
                    # Reload the configuration
                    self.load_configuration()
                else:
                    QMessageBox.warning(self, "No Files Restored",
                                       "Could not determine configuration type from filenames.\nFiles should start with 'claude-backup', 'gemini-backup', or 'disabled-backup'.")
                    
            except Exception as e:
                error_msg = f"Restore failed: {str(e)}"
                self.set_status_message(error_msg, timeout=0)
                QMessageBox.critical(self, "Restore Error", error_msg)
    
    def restore_configuration(self):
        """Show restore dialog."""
        dialog = BackupRestoreDialog(self if USING_QT else self.root)
        dialog.set_controller(self.backup_controller)
        if dialog.exec() if USING_QT else dialog.show():
            # Check if restore happened
            if hasattr(dialog, 'restored_backup') and dialog.restored_backup:
                dispatcher.emit_now(EventType.BACKUP_RESTORED,
                                   {'file': dialog.restored_backup},
                                   source='MainWindow')
    
    def validate_configuration(self):
        """Validate current configuration."""
        self.set_status_message("Validating configuration...")
        # Validate both configs
        result = self.config_controller.validate_configuration()
        if result['success']:
            if result['data'].get('valid'):
                self.set_status_message("Configuration is valid", timeout=0)
            else:
                errors = result['data'].get('errors', [])
                self.set_status_message(f"Configuration has {len(errors)} errors", 0)
                dispatcher.emit_now(EventType.CONFIG_VALIDATION_ERROR,
                                   {'errors': errors},
                                   source='MainWindow')
        else:
            self.set_status_message(f"Validation failed: {result['error']}", 0)
    
    def show_help(self):
        """Show help documentation."""
        help_text = """
MCP Config Manager - Keyboard Shortcuts

File Operations:
  Ctrl+O        Load configuration
  Ctrl+S        Save configuration
  Ctrl+N        Add new server
  Ctrl+Q        Quit application
  
Server Management:
  Ctrl+E        Enable all servers
  Ctrl+D        Disable all servers
  Ctrl+R / F5   Refresh server list
  
Tools:
  Ctrl+P        Manage presets
  Ctrl+B        Create backup
  Ctrl+Shift+R  Restore backup
  Ctrl+Shift+V  Validate configuration
  Ctrl+,        Settings
  
Edit:
  Ctrl+Z        Undo
  Ctrl+Y        Redo
  Ctrl+F        Search
  Escape        Clear selection
  
Help:
  F1            Show this help
        """
        
        if USING_QT:
            QMessageBox.information(self, "Keyboard Shortcuts", help_text)
        else:
            messagebox.showinfo("Keyboard Shortcuts", help_text)
    
    def quit_application(self):
        """Quit the application with unsaved changes check."""
        if self._unsaved_changes:
            if USING_QT:
                reply = QMessageBox.question(self, "Unsaved Changes",
                                            "You have unsaved changes. Do you want to save before quitting?",
                                            QMessageBox.StandardButton.Save |
                                            QMessageBox.StandardButton.Discard |
                                            QMessageBox.StandardButton.Cancel)
                
                if reply == QMessageBox.StandardButton.Save:
                    self.save_configuration()
                    QApplication.instance().quit()
                elif reply == QMessageBox.StandardButton.Discard:
                    QApplication.instance().quit()
            else:
                response = messagebox.askyesnocancel("Unsaved Changes",
                                                     "You have unsaved changes. Do you want to save before quitting?")
                if response is True:  # Yes - save
                    self.save_configuration()
                    self.root.quit()
                elif response is False:  # No - don't save
                    self.root.quit()
                # Cancel - do nothing
        else:
            if USING_QT:
                QApplication.instance().quit()
            else:
                self.root.quit()
    
    # Shortcut helper methods
    def _focus_search(self):
        """Focus the search field."""
        if hasattr(self, 'search_field'):
            if USING_QT:
                self.search_field.setFocus()
            else:
                self.search_field.focus_set()
        else:
            self.set_status_message("Search not available", 2)
    
    # Mode switching removed - no longer needed with per-client operations
    
    def _undo_action(self):
        """Undo the last action."""
        from .events.state_manager import get_state_manager
        state_mgr = get_state_manager()
        if state_mgr.undo():
            self.set_status_message("Undo successful", 2)
        else:
            self.set_status_message("Nothing to undo", 2)
    
    def _redo_action(self):
        """Redo the last undone action."""
        from .events.state_manager import get_state_manager
        state_mgr = get_state_manager()
        if state_mgr.redo():
            self.set_status_message("Redo successful", 2)
        else:
            self.set_status_message("Nothing to redo", 2)
    
    def _clear_selection(self):
        """Clear current selection."""
        if self.server_list_widget:
            self.server_list_widget.clear_selection()
        self.app_state.selected_server = None
        dispatcher.emit_now(EventType.UI_SELECTION_CHANGED,
                           {'selection': None},
                           source='MainWindow')
        self.set_status_message("Selection cleared", 2)
    
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
    
    def discover_project_servers(self):
        """Open the project server discovery dialog."""
        try:
            from .dialogs.discover_servers_dialog import DiscoverServersDialog

            if USING_QT:
                dialog = DiscoverServersDialog(self, self.server_controller)
                result = dialog.exec()

                if result:
                    # Refresh the server list to show newly promoted servers
                    self.refresh_server_list(force_reload=True)
                    self.set_status_message("✅ Project servers discovered and promoted", timeout=5000)
            else:
                # Tkinter version
                dialog = DiscoverServersDialog(self.root, self.server_controller)
                dialog.show()

                # After dialog closes, refresh the server list
                self.refresh_server_list(force_reload=True)

        except ImportError:
            # Dialog not available yet
            self.set_status_message("⚠️ Project discovery feature coming soon", timeout=3000)
        except Exception as e:
            self.set_status_message(f"❌ Error discovering servers: {str(e)}", timeout=5000)

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
            if result is True: # Yes - save
                self.save_configuration()
                self._save_window_state()
                self.root.destroy()
            elif result is False: # No - don't save
                self._save_window_state()
                self.root.destroy()
        else:
            self._save_window_state()
            self.root.destroy()


from mcp_config_manager.core.config_manager import ConfigManager

def run_gui_in_main_thread():
    """Run the GUI application in the main thread."""
    if USING_QT:
        app = QApplication(sys.argv)
        app.setApplicationName("MCP Config Manager")
        
        # NOTE: There is a known Qt bug on macOS where QTreeWidgetItem checkboxes
        # may render as solid blue squares. This is a Qt rendering issue that
        # should be fixed in future Qt versions. The application is using the
        # native macOS style correctly.
        
        config_manager = ConfigManager()
        window = MainWindow(config_manager)
        window.show()
        # Ensure window gets focus after showing
        window.raise_()
        window.activateWindow()
        app.exec()
    else:
        config_manager = ConfigManager()
        window = MainWindow(config_manager)
        window.run()


if __name__ == "__main__":
    run_gui_in_main_thread()
