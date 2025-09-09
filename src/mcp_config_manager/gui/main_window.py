"""Main window for MCP Config Manager GUI."""

import sys
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
from .widgets.mode_selector import ModeSelectorWidget
from .dialogs.add_server_dialog import AddServerDialog
from .dialogs.preset_manager_dialog import PresetManagerDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.backup_restore_dialog import BackupRestoreDialog


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
        
        logging.debug("Initializing controllers")
        # Initialize controllers
        self.config_controller = ConfigController()
        self.server_controller = ServerController()
        self.preset_controller = PresetController()
        self.backup_controller = BackupController()
        
        logging.debug("Initializing widgets")
        # Initialize widgets
        self.server_list_widget = None
        self.mode_selector_widget = None
        
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
        
        # Content splitter (for future server list and details)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Server list widget
        self.server_list = ServerListWidget()
        self.splitter.addWidget(self.server_list)
        
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
        
        # Server list widget
        self.server_list = ServerListWidget(self.paned)
        self.paned.add(self.server_list.frame, weight=7)
        
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
        from PyQt6.QtWidgets import QPushButton, QToolBar
        from PyQt6.QtCore import QSize
        
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Set toolbar style to show buttons with text
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(24, 24))
        
        # Create actual buttons with proper styling
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self.load_configuration)
        toolbar.addWidget(load_btn)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        # Removed stylesheet to preserve native macOS rendering of checkboxes
        # The stylesheet was causing Qt to switch from native to synthetic rendering
        toolbar.addWidget(save_btn)
        
        toolbar.addSeparator()
        
        add_btn = QPushButton("Add Server")
        add_btn.clicked.connect(self.add_server)
        toolbar.addWidget(add_btn)
        
        toolbar.addSeparator()
        
        enable_all_btn = QPushButton("Enable All")
        enable_all_btn.clicked.connect(self.enable_all_servers)
        toolbar.addWidget(enable_all_btn)
        
        disable_all_btn = QPushButton("Disable All")
        disable_all_btn.clicked.connect(self.disable_all_servers)
        toolbar.addWidget(disable_all_btn)
        
        toolbar.addSeparator()
        
        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self.validate_configuration)
        toolbar.addWidget(validate_btn)
    
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
        if USING_QT:
            # Qt shortcuts are set up in menu actions, but we add additional ones here
            from PyQt6.QtGui import QShortcut
            
            # Additional shortcuts not in menus
            QShortcut(QKeySequence("Ctrl+R"), self, self.refresh_server_list)
            QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
            QShortcut(QKeySequence("Ctrl+E"), self, self.enable_all_servers)
            QShortcut(QKeySequence("Ctrl+D"), self, self.disable_all_servers)
            QShortcut(QKeySequence("Ctrl+P"), self, self.manage_presets)
            QShortcut(QKeySequence("Ctrl+B"), self, self.backup_configuration)
            QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.restore_configuration)
            QShortcut(QKeySequence("Ctrl+Shift+V"), self, self.validate_configuration)
            QShortcut(QKeySequence("F1"), self, self.show_help)
            QShortcut(QKeySequence("F5"), self, self.refresh_server_list)
            QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_action)
            QShortcut(QKeySequence("Ctrl+Y"), self, self._redo_action)
            QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo_action)
            QShortcut(QKeySequence("Escape"), self, self._clear_selection)
            
            # Mode switching shortcuts
            QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._switch_mode('claude'))
            QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._switch_mode('gemini'))
            QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._switch_mode('both'))
        else:
            # Tkinter key bindings
            self.root.bind("<Control-o>", lambda e: self.load_configuration())
            self.root.bind("<Control-s>", lambda e: self.save_configuration())
            self.root.bind("<Control-n>", lambda e: self.add_server())
            self.root.bind("<Control-comma>", lambda e: self.show_settings())
            self.root.bind("<Control-q>", lambda e: self.quit_application())
            self.root.bind("<Control-r>", lambda e: self.refresh_server_list())
            self.root.bind("<Control-f>", lambda e: self._focus_search())
            self.root.bind("<Control-e>", lambda e: self.enable_all_servers())
            self.root.bind("<Control-d>", lambda e: self.disable_all_servers())
            self.root.bind("<Control-p>", lambda e: self.manage_presets())
            self.root.bind("<Control-b>", lambda e: self.backup_configuration())
            self.root.bind("<Control-Shift-R>", lambda e: self.restore_configuration())
            self.root.bind("<Control-Shift-V>", lambda e: self.validate_configuration())
            self.root.bind("<F1>", lambda e: self.show_help())
            self.root.bind("<F5>", lambda e: self.refresh_server_list())
            self.root.bind("<Control-z>", lambda e: self._undo_action())
            self.root.bind("<Control-y>", lambda e: self._redo_action())
            self.root.bind("<Control-Shift-Z>", lambda e: self._redo_action())
            self.root.bind("<Escape>", lambda e: self._clear_selection())
            
            # Mode switching shortcuts
            self.root.bind("<Control-Key-1>", lambda e: self._switch_mode('claude'))
            self.root.bind("<Control-Key-2>", lambda e: self._switch_mode('gemini'))
            self.root.bind("<Control-Key-3>", lambda e: self._switch_mode('both'))
    
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
            else:
                # For tkinter callbacks
                self.server_list._toggle_callbacks.append(self._on_server_toggled)
                self.server_list._selection_callbacks.append(self._on_server_selected)
            
        if self.mode_selector_widget:
            self.mode_selector_widget.mode_changed_callback = self._on_mode_changed
    
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
        
        # Mode events
        dispatcher.subscribe(EventType.MODE_CHANGED, self._handle_mode_changed)
        
        # Backup events
        dispatcher.subscribe(EventType.BACKUP_CREATED, self._handle_backup_created)
        dispatcher.subscribe(EventType.BACKUP_RESTORED, self._handle_backup_restored)
        
        # Application events
        dispatcher.subscribe(EventType.APP_ERROR, self._handle_app_error)
    
    # Widget event callbacks
    def _on_server_toggled(self, server_name: str, enabled: bool):
        """Handle server toggle from widget."""
        mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
        # Use bulk_operation with 'enable' or 'disable' for individual servers
        operation = 'enable' if enabled else 'disable'
        result = self.server_controller.bulk_operation(operation, [server_name], mode_value)
        
        if result['success']:
            self.set_unsaved_changes(True)
            dispatcher.emit_now(EventType.SERVER_TOGGLED, 
                                {'server': server_name, 'enabled': enabled},
                                source='MainWindow')
        else:
            self.set_status_message(f"Error: {result['error']}", timeout=5)
    
    def _on_server_selected(self, server_name: str):
        """Handle server selection from widget."""
        self.app_state.selected_server = server_name
        dispatcher.emit_now(EventType.UI_SELECTION_CHANGED,
                           {'selection': server_name},
                           source='MainWindow')
    
    def _on_mode_changed(self, mode: str):
        """Handle mode change from widget."""
        # Mode switching handled by changing app_state.mode
        self.app_state.mode = mode
        result = {'success': True}
        if result['success']:
            self.app_state.mode = mode
            dispatcher.emit_now(EventType.MODE_CHANGED,
                               {'mode': mode},
                               source='MainWindow')
            self.refresh_server_list()
        else:
            self.set_status_message(f"Error: {result['error']}", timeout=5)
    
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
        server = event.data.get('server')
        enabled = event.data.get('enabled')
        status = "enabled" if enabled else "disabled"
        self.set_status_message(f"Server '{server}' {status}", timeout=3)
    
    def _handle_server_added(self, event: Event):
        """Handle server added event."""
        server = event.data.get('server')
        self.set_status_message(f"Server '{server}' added successfully", timeout=3)
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
    
    def _handle_mode_changed(self, event: Event):
        """Handle mode changed event."""
        mode = event.data.get('mode')
        self.app_state.mode = mode
        self.set_status_message(f"Switched to {mode} mode", timeout=3)
        self.refresh_server_list()
    
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
    
    def refresh_server_list(self):
        """Refresh the server list widget."""
        print("DEBUG: refresh_server_list called")
        if hasattr(self, 'server_list') and self.server_list:
            print("DEBUG: server_list exists, getting servers...")
            # Get current servers from controller
            # Convert Mode enum to string value
            mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
            result = self.server_controller.get_servers(mode_value)
            print(f"DEBUG: get_servers result: {result}")
            if result['success']:
                servers = result['data']['servers']
                print(f"DEBUG: Got {len(servers)} servers")
                self.server_list.load_servers(servers)
            else:
                print(f"DEBUG: get_servers failed: {result.get('error', 'Unknown error')}")
        else:
            print("DEBUG: server_list not found or None")
    
    def load_configuration(self):
        """Load configuration from file."""
        try:
            print("DEBUG: MainWindow.load_configuration called")
            self.set_status_message("Loading configuration...")
            result = self.config_controller.load_config(self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else self.app_state.mode)
            
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
    
    def save_configuration(self):
        """Save configuration to file."""
        self.set_status_message("Saving configuration...")
        result = self.config_controller.save_config()
        
        if result['success']:
            dispatcher.emit_now(EventType.CONFIG_SAVED, result['data'], source='MainWindow')
        else:
            dispatcher.emit_now(EventType.CONFIG_ERROR, {'error': result['error']}, source='MainWindow')
    
    def add_server(self):
        """Show add server dialog."""
        dialog = AddServerDialog(self if USING_QT else self.root)
        if dialog.exec() if USING_QT else dialog.show():
            server_json = dialog.get_server_json()
            if server_json:
                mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
                result = self.server_controller.add_server(server_json, mode_value)
                if result['success']:
                    server_name = result['data'].get('server')
                    dispatcher.emit_now(EventType.SERVER_ADDED, 
                                       {'server': server_name},
                                       source='MainWindow')
                else:
                    dispatcher.emit_now(EventType.APP_ERROR,
                                       {'error': result['error']},
                                       source='MainWindow')
    
    def enable_all_servers(self):
        """Enable all servers."""
        mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
        result = self.server_controller.bulk_toggle(True, mode_value)
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
        """Disable all servers."""
        mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
        result = self.server_controller.bulk_toggle(False, mode_value)
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
        mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
        result = self.backup_controller.create_backup(mode_value)
        if result['success']:
            backup_file = result['data'].get('file')
            dispatcher.emit_now(EventType.BACKUP_CREATED,
                               {'file': backup_file},
                               source='MainWindow')
        else:
            dispatcher.emit_now(EventType.BACKUP_ERROR,
                               {'error': result['error']},
                               source='MainWindow')
    
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
        mode_value = self.app_state.mode.value if hasattr(self.app_state.mode, 'value') else str(self.app_state.mode)
        result = self.config_controller.validate_configuration(mode_value)
        if result['success']:
            if result['data'].get('valid'):
                self.set_status_message("Configuration is valid", 3)
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
  
Mode Switching:
  Ctrl+1        Claude mode
  Ctrl+2        Gemini mode
  Ctrl+3        Both mode
  
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
    
    def _switch_mode(self, mode: str):
        """Switch to a specific mode."""
        if self.mode_selector_widget:
            self.mode_selector_widget.set_mode(mode)
            self._on_mode_changed(mode)
        else:
            self.set_status_message(f"Cannot switch to {mode} mode", 2)
    
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
        sys.exit(app.exec())
    else:
        config_manager = ConfigManager()
        window = MainWindow(config_manager)
        window.run()


if __name__ == "__main__":
    run_gui_in_main_thread()