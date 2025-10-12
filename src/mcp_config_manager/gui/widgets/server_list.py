"""Server list widget for MCP Config Manager."""

from typing import List, Optional, Dict, Any, Callable
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QMenu, QHeaderView, QCheckBox, QComboBox,
        QLineEdit, QToolBar
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
    from PyQt6.QtGui import QAction, QIcon
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USING_QT = False

from ..models.server_list_item import ServerListItem, ServerStatus


class ServerListWidget(QWidget if USING_QT else object):
    """Widget for displaying and managing server list."""
    
    # Qt signals
    if USING_QT:
        server_toggled = pyqtSignal(str, str, bool)  # server_name, client, enabled
        server_selected = pyqtSignal(str)  # server_name
        servers_bulk_toggled = pyqtSignal(str, bool)  # client, enable_all
        server_added = pyqtSignal(dict)  # server_config
        server_removed = pyqtSignal(str)  # server_name
        server_promoted = pyqtSignal(str)  # server_name
    
    def __init__(self, parent=None):
        """Initialize the server list widget."""
        if USING_QT:
            super().__init__(parent)
            self._setup_qt_widget()
        else:
            self._setup_tk_widget(parent)

        self.servers: Dict[str, ServerListItem] = {}
        self.selected_server: Optional[str] = None
        self.selected_servers: List[str] = []  # For multi-selection
        self._toggle_callbacks: List[Callable] = []
        self._selection_callbacks: List[Callable] = []
        self._multi_selection_callbacks: List[Callable] = []
        self.multi_select_enabled = False
        self.claude_master_state = None  # Track Claude master checkbox state
        self.gemini_master_state = None  # Track Gemini master checkbox state
        self.codex_master_state = None  # Track Codex master checkbox state
        self.filter_location = "All"  # Current location filter
        self.group_by_location = False  # Whether to group by location
        self.search_text = ""  # Search filter text
    
    def _setup_qt_widget(self):
        """Set up Qt widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add filter toolbar
        self._create_filter_toolbar()
        layout.addWidget(self.filter_toolbar)

        # Tree widget for server list
        self.tree = QTreeWidget()
        # Don't set header labels yet - we'll do it in _setup_master_checkbox
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)  # Enable drag-drop
        self.tree.itemClicked.connect(self._on_item_clicked)
        # Connect itemChanged signal to handle checkbox state changes (only once)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed_qt)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # Apply theme-aware styling
        self._apply_theme_styles()

        # Add master checkbox to header
        self._setup_master_checkbox()
        
        # Set column widths
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 70)  # Claude column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 70)  # Gemini column
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(2, 70)  # Codex column
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Server name
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 100)  # Status column
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(5, 120)  # Location column
        
        # NOTE: There is a known Qt bug on macOS where QTreeWidgetItem checkboxes
        # may render as solid blue squares instead of proper checkboxes.
        # This appears to be a Qt rendering issue that should be fixed in future Qt versions.
        # We're using the native approach (Qt.ItemIsUserCheckable) which is correct.
        
        layout.addWidget(self.tree)
        
        # Status bar at bottom with server count
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        status_layout.addStretch()
        
        self.status_label = QLabel("")
        status_layout.addWidget(self.status_label)
        
        layout.addLayout(status_layout)

    def _apply_theme_styles(self):
        """Apply theme-aware styling to the tree widget."""
        if not USING_QT:
            return

        try:
            from ..themes import get_theme_manager
            theme_manager = get_theme_manager()
            colors = theme_manager.get_colors()

            # Theme-aware selection and hover styling
            self.tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {colors.bg_primary};
                    alternate-background-color: {colors.bg_primary};
                    color: {colors.text_primary};
                    selection-background-color: {colors.selection_bg};
                    selection-color: {colors.text_inverse};
                    outline: none;
                    border: none;
                }}
                QTreeWidget::item {{
                    background-color: {colors.bg_primary};
                    color: {colors.text_primary};
                    border: none;
                    padding: 4px;
                }}
                QTreeWidget::item:alternate {{
                    background-color: {colors.bg_primary};
                }}
                QTreeWidget::item:selected {{
                    background-color: {colors.selection_bg};
                    color: {colors.text_inverse};
                }}
                QTreeWidget::item:selected:active {{
                    background-color: {colors.selection_bg};
                    color: {colors.text_inverse};
                }}
                QTreeWidget::item:selected:!active {{
                    background-color: {colors.selection_bg};
                    color: {colors.text_inverse};
                }}
                QTreeWidget::item:hover {{
                    background-color: {colors.control_hover};
                }}
                QTreeWidget QScrollBar:vertical {{
                    background-color: {colors.bg_secondary};
                }}
                QTreeWidget::branch {{
                    background-color: {colors.bg_primary};
                }}
            """)

            # Apply transparent background to status label
            if hasattr(self, 'status_label'):
                self.status_label.setStyleSheet("background: transparent;")

        except ImportError:
            # Fallback to hardcoded colors if theme system not available
            self.tree.setStyleSheet("""
                QTreeWidget::item:selected {
                    background-color: #0078D4;
                    color: white;
                }
                QTreeWidget::item:selected:!active {
                    background-color: #0078D4;
                    color: white;
                }
                QTreeWidget::item:hover {
                    background-color: #E3F2FD;
                }
            """)

    def _setup_master_checkbox(self):
        """Set up the master checkboxes in the header."""
        if not USING_QT:
            return

        # Set header labels initially
        self.tree.setHeaderLabels(["Claude", "Gemini", "Codex", "Server", "Status", "Location"])

        # Store reference to header for updating checkbox display
        self.header = self.tree.header()
        self.header.setSectionsClickable(True)
        self.header.sectionClicked.connect(self._on_header_clicked)

        # Track master checkbox states
        self.claude_master_state = Qt.CheckState.Unchecked
        self.gemini_master_state = Qt.CheckState.Unchecked
        self.codex_master_state = Qt.CheckState.Unchecked

        # Track CLI availability
        self.cli_availability = {'claude': True, 'gemini': True, 'codex': True}

    def _create_filter_toolbar(self):
        """Create the filter toolbar for Qt."""
        self.filter_toolbar = QToolBar()
        self.filter_toolbar.setMovable(False)

        # Apply theme-aware styling to toolbar
        try:
            from ..themes import get_theme_manager
            theme_manager = get_theme_manager()
            colors = theme_manager.get_colors()

            self.filter_toolbar.setStyleSheet(f"""
                QToolBar {{
                    background-color: {colors.toolbar_bg};
                    border: 1px solid {colors.border_primary};
                    padding: 4px;
                    spacing: 8px;
                }}
                QToolBar QLabel {{
                    color: {colors.text_primary};
                    background: transparent;
                }}
                QToolBar QLineEdit {{
                    background-color: {colors.control_bg};
                    border: 1px solid {colors.control_border};
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: {colors.text_primary};
                }}
                QToolBar QComboBox {{
                    background-color: {colors.control_bg};
                    border: 1px solid {colors.control_border};
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: {colors.text_primary};
                }}
                QToolBar QCheckBox {{
                    color: {colors.text_primary};
                    background: transparent;
                }}
                QToolBar QPushButton {{
                    background-color: {colors.control_bg};
                    border: 1px solid {colors.control_border};
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: {colors.text_primary};
                }}
                QToolBar QPushButton:hover {{
                    background-color: {colors.control_hover};
                }}
                QToolBar::separator {{
                    background-color: {colors.separator};
                    width: 1px;
                    margin: 4px 2px;
                }}
            """)
        except ImportError:
            # Fallback styling if theme system not available
            self.filter_toolbar.setStyleSheet("""
                QToolBar {
                    background-color: #2d2d30;
                    border: 1px solid #3e3e42;
                    padding: 4px;
                }
                QToolBar QLabel {
                    color: #cccccc;
                    background: transparent;
                }
                QToolBar QLineEdit {
                    background-color: #3c3c3c;
                    border: 1px solid #5a5a5a;
                    color: #cccccc;
                }
                QToolBar QComboBox {
                    background-color: #3c3c3c;
                    border: 1px solid #5a5a5a;
                    color: #cccccc;
                }
                QToolBar QCheckBox {
                    color: #cccccc;
                    background: transparent;
                }
                QToolBar QPushButton {
                    background-color: #3c3c3c;
                    border: 1px solid #5a5a5a;
                    color: #cccccc;
                }
            """)

        # Search box
        search_label = QLabel("Search: ")
        self.filter_toolbar.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter servers...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self._apply_filters)
        self.filter_toolbar.addWidget(self.search_box)

        self.filter_toolbar.addSeparator()

        # Location filter
        location_label = QLabel("Location: ")
        self.filter_toolbar.addWidget(location_label)

        self.location_combo = QComboBox()
        self.location_combo.addItems(["All", "Global", "Project"])
        self.location_combo.setMaximumWidth(120)
        self.location_combo.currentTextChanged.connect(self._on_location_filter_changed)
        self.filter_toolbar.addWidget(self.location_combo)

        self.filter_toolbar.addSeparator()

        # Group by location checkbox
        self.group_checkbox = QCheckBox("Group by Location")
        self.group_checkbox.toggled.connect(self._on_group_by_changed)
        self.filter_toolbar.addWidget(self.group_checkbox)

        # Clear filters button
        self.filter_toolbar.addSeparator()
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.clicked.connect(self._clear_filters)
        self.filter_toolbar.addWidget(clear_btn)
    
    def _setup_tk_widget(self, parent):
        """Set up tkinter widget."""
        self.frame = ttk.Frame(parent)

        # Add filter toolbar
        self._create_tk_filter_toolbar()

        # Tree view for server list
        columns = ("claude", "gemini", "codex", "server", "status", "location")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="tree headings")

        # Configure columns
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, stretch=False)

        self.tree.heading("claude", text="Claude")
        self.tree.column("claude", width=70)

        self.tree.heading("gemini", text="Gemini")
        self.tree.column("gemini", width=70)

        self.tree.heading("codex", text="Codex")
        self.tree.column("codex", width=70)

        self.tree.heading("server", text="Server")
        self.tree.column("server", width=250)

        self.tree.heading("status", text="Status")
        self.tree.column("status", width=100)

        self.tree.heading("location", text="Location")
        self.tree.column("location", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack filter toolbar, tree and scrollbar
        self.filter_frame.pack(fill=tk.X, padx=5, pady=2)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status frame for server count
        status_frame = ttk.Frame(parent)
        
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self.tree.bind("<Button-3>", self._show_tk_context_menu)  # Right-click
        self.tree.bind("<Double-1>", self._on_double_click)

    def _create_tk_filter_toolbar(self):
        """Create the filter toolbar for tkinter."""
        self.filter_frame = ttk.Frame(self.frame)

        # Search box
        ttk.Label(self.filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._apply_filters())
        search_entry = ttk.Entry(self.filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Location filter
        ttk.Label(self.filter_frame, text="Location:").pack(side=tk.LEFT, padx=(0, 5))

        self.location_var = tk.StringVar(value="All")
        location_combo = ttk.Combobox(self.filter_frame, textvariable=self.location_var,
                                     values=["All", "Global", "Project"],
                                     state="readonly", width=10)
        location_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())
        location_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Group by location checkbox
        self.group_var = tk.BooleanVar(value=False)
        group_check = ttk.Checkbutton(self.filter_frame, text="Group by Location",
                                     variable=self.group_var,
                                     command=self._on_group_by_changed_tk)
        group_check.pack(side=tk.LEFT, padx=(0, 10))

        # Clear filters button
        clear_btn = ttk.Button(self.filter_frame, text="Clear",
                             command=self._clear_filters_tk)
        clear_btn.pack(side=tk.LEFT)
    
    def add_server(self, server: ServerListItem):
        """Add a server to the list."""
        self.servers[server.name] = server

        if USING_QT:
            # Temporarily block signals to prevent triggering events during initial setup
            self.tree.blockSignals(True)

            item = QTreeWidgetItem()

            # Add checkboxes for Claude, Gemini and Codex columns
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Set checkbox states based on per-client enabled status
            claude_enabled = getattr(server, 'claude_enabled', server.status == ServerStatus.ENABLED)
            gemini_enabled = getattr(server, 'gemini_enabled', server.status == ServerStatus.ENABLED)
            codex_enabled = getattr(server, 'codex_enabled', server.status == ServerStatus.ENABLED)

            # Set checkboxes, disabling if CLI not available
            if self.cli_availability.get('claude', True):
                item.setCheckState(0, Qt.CheckState.Checked if claude_enabled else Qt.CheckState.Unchecked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)  # Disable checkbox for column 0

            if self.cli_availability.get('gemini', True):
                item.setCheckState(1, Qt.CheckState.Checked if gemini_enabled else Qt.CheckState.Unchecked)
            else:
                item.setCheckState(1, Qt.CheckState.Unchecked)

            if self.cli_availability.get('codex', True):
                item.setCheckState(2, Qt.CheckState.Checked if codex_enabled else Qt.CheckState.Unchecked)
            else:
                item.setCheckState(2, Qt.CheckState.Unchecked)

            item.setText(3, server.name)
            item.setText(4, str(server.status.value) if hasattr(server.status, 'value') else str(server.status))

            # Set location text and apply visual indicators for project servers
            location_text = getattr(server, 'location', 'global')
            is_project = getattr(server, 'is_project_server', False)

            if is_project and location_text != 'global':
                # Show shortened project path for project servers
                if '/' in location_text:
                    # Show just the project folder name
                    item.setText(5, f"📁 {location_text.split('/')[-1]}")
                else:
                    item.setText(5, f"📁 {location_text}")
                # Set tooltip with full path
                item.setToolTip(5, f"Project: {location_text}")
                # Apply project server color (light blue background)
                from PyQt6.QtGui import QColor
                item.setBackground(3, QColor(230, 240, 255))  # Light blue for server name
                item.setBackground(5, QColor(230, 240, 255))  # Light blue for location
            else:
                item.setText(5, "Global")
                item.setToolTip(5, "Global Configuration")

            # Store server name in item data
            item.setData(0, Qt.ItemDataRole.UserRole, server.name)

            # Add to tree
            self.tree.addTopLevelItem(item)

            # Set status colors
            self._update_item_status(item, server.status)

            # Re-enable signals
            self.tree.blockSignals(False)
        else:
            # tkinter implementation
            claude_mark = "✓" if getattr(server, 'claude_enabled', server.status == ServerStatus.ENABLED) else ""
            gemini_mark = "✓" if getattr(server, 'gemini_enabled', server.status == ServerStatus.ENABLED) else ""
            codex_mark = "✓" if getattr(server, 'codex_enabled', server.status == ServerStatus.ENABLED) else ""

            # Set location text for project servers
            location_text = getattr(server, 'location', 'global')
            is_project = getattr(server, 'is_project_server', False)

            if is_project and location_text != 'global':
                # Show shortened project path for project servers
                if '/' in location_text:
                    location_display = f"📁 {location_text.split('/')[-1]}"
                else:
                    location_display = f"📁 {location_text}"
            else:
                location_display = "Global"

            values = (claude_mark, gemini_mark, codex_mark, server.name, server.status.value, location_display)
            tags = (server.status.value.lower(),)
            if is_project:
                tags = tags + ("project_server",)
            item_id = self.tree.insert("", "end", values=values, tags=tags)

            # Store mapping
            self.servers[server.name] = server
            server._tree_item = item_id

            # Configure tag colors
            self._configure_tk_tags()
    
    def remove_server(self, server_name: str):
        """Remove a server from the list."""
        if server_name not in self.servers:
            return
        
        if USING_QT:
            # Find and remove the item
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == server_name:
                    self.tree.takeTopLevelItem(i)
                    break
        else:
            # Remove from tkinter tree
            server = self.servers[server_name]
            if hasattr(server, '_tree_item'):
                self.tree.delete(server._tree_item)
        
        del self.servers[server_name]
        
        if USING_QT:
            self.server_removed.emit(server_name)
    
    def update_server_status(self, server_name: str, status: ServerStatus, client: str = None):
        """Update a server's status for a specific client or both."""
        if server_name not in self.servers:
            return

        server = self.servers[server_name]

        # Update the appropriate client state
        if client == "claude":
            server.claude_enabled = (status == ServerStatus.ENABLED)
        elif client == "gemini":
            server.gemini_enabled = (status == ServerStatus.ENABLED)
        elif client == "codex":
            server.codex_enabled = (status == ServerStatus.ENABLED)
        else:
            # Update all if no specific client
            server.status = status
            server.claude_enabled = (status == ServerStatus.ENABLED)
            server.gemini_enabled = (status == ServerStatus.ENABLED)
            server.codex_enabled = (status == ServerStatus.ENABLED)

        if USING_QT:
            # Find and update the item
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == server_name:
                    item.setText(4, status.value if status else self._get_overall_status(server))
                    self._update_item_status(item, status if status else server.status)

                    # Block signals temporarily to avoid triggering unwanted events
                    self.tree.blockSignals(True)
                    # Update checkbox states
                    item.setCheckState(0, Qt.CheckState.Checked if server.claude_enabled else Qt.CheckState.Unchecked)
                    item.setCheckState(1, Qt.CheckState.Checked if server.gemini_enabled else Qt.CheckState.Unchecked)
                    item.setCheckState(2, Qt.CheckState.Checked if getattr(server, 'codex_enabled', False) else Qt.CheckState.Unchecked)
                    self.tree.blockSignals(False)
                    break
        else:
            # Update tkinter tree
            if hasattr(server, '_tree_item'):
                claude_mark = "✓" if server.claude_enabled else ""
                gemini_mark = "✓" if server.gemini_enabled else ""
                codex_mark = "✓" if getattr(server, 'codex_enabled', False) else ""
                overall_status = self._get_overall_status(server)
                values = (claude_mark, gemini_mark, codex_mark, server.name, overall_status)
                self.tree.item(server._tree_item, values=values, tags=(overall_status.lower(),))
    
    def _update_item_status(self, item: 'QTreeWidgetItem', status: ServerStatus):
        """Update item appearance based on status."""
        if not USING_QT:
            return
        
        from PyQt6.QtGui import QBrush, QColor
        
        if status == ServerStatus.ERROR:
            color = QColor(255, 0, 0)  # Red
        elif status == ServerStatus.LOADING:
            color = QColor(255, 165, 0)  # Orange
        elif status == ServerStatus.DISABLED:
            color = QColor(128, 128, 128)  # Gray
        else:
            color = QColor(0, 128, 0)  # Green
        
        item.setForeground(3, QBrush(color))
    
    def _configure_tk_tags(self):
        """Configure tkinter tag colors."""
        if not USING_QT:
            self.tree.tag_configure("error", foreground="red")
            self.tree.tag_configure("loading", foreground="orange")
            self.tree.tag_configure("disabled", foreground="gray")
            self.tree.tag_configure("enabled", foreground="green")
            self.tree.tag_configure("project_server", background="#E6F0FF")  # Light blue for project servers
    
    def _on_item_changed(self, item: 'QTreeWidgetItem', column: int):
        """Handle item changed event for checkbox state changes."""
        if not USING_QT or column > 2:  # Only handle checkbox columns (0, 1, and 2)
            return

        server_name = item.data(0, Qt.ItemDataRole.UserRole)
        if server_name:
            if column == 0:
                client = "claude"
            elif column == 1:
                client = "gemini"
            else:
                client = "codex"
            enabled = item.checkState(column) == Qt.CheckState.Checked
            self._toggle_server(server_name, enabled, client)
            # Update master checkbox state when individual items change
            self._update_master_checkbox_state()
    
    def _toggle_server(self, server_name: str, enabled: bool, client: str = None):
        """Toggle server enabled/disabled state for a specific client."""
        if server_name not in self.servers:
            return

        new_status = ServerStatus.ENABLED if enabled else ServerStatus.DISABLED
        self.update_server_status(server_name, new_status, client)

        # Emit signal with client information
        if USING_QT:
            self.server_toggled.emit(server_name, client or 'both', enabled)

        # Call callbacks with client info
        for callback in self._toggle_callbacks:
            if len(callback.__code__.co_varnames) >= 3:  # Support new callbacks with client param
                callback(server_name, client, enabled)
            else:  # Backward compatibility
                callback(server_name, enabled)
    
    def _enable_all(self, client: str = None):
        """Enable all servers for a specific client or both."""
        for server_name in self.servers:
            self._toggle_server(server_name, True, client)

        if USING_QT:
            self.servers_bulk_toggled.emit(client or 'both', True)

    def _disable_all(self, client: str = None):
        """Disable all servers for a specific client or both."""
        for server_name in self.servers:
            self._toggle_server(server_name, False, client)

        if USING_QT:
            self.servers_bulk_toggled.emit(client or 'both', False)
    
    def _on_item_clicked(self, item: 'QTreeWidgetItem', column: int):
        """Handle item click (Qt)."""
        if not USING_QT:
            return

        # Only emit server_selected for non-checkbox columns
        # Columns 0, 1, and 2 are checkbox columns, handled by itemChanged signal
        if column > 2:
            server_name = item.data(0, Qt.ItemDataRole.UserRole)
            if server_name:
                self.selected_server = server_name
                self.server_selected.emit(server_name)

                for callback in self._selection_callbacks:
                    callback(server_name)
    
    
    def _on_selection_changed(self, event=None):
        """Handle selection change (tkinter)."""
        if USING_QT:
            return
        
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            server_name = item['values'][2]  # Server name is now in third column
            self.selected_server = server_name
            
            for callback in self._selection_callbacks:
                callback(server_name)
    
    def _on_double_click(self, event=None):
        """Handle double click (tkinter)."""
        if USING_QT:
            return
        
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            server_name = item['values'][3]  # Server name is now in fourth column
            # Toggle all for double-click
            claude_enabled = item['values'][0] == "✓"
            gemini_enabled = item['values'][1] == "✓"
            codex_enabled = item['values'][2] == "✓"
            # If any is enabled, disable all; otherwise enable all
            new_state = not (claude_enabled or gemini_enabled or codex_enabled)
            self._toggle_server(server_name, new_state, None)
    
    def _show_context_menu(self, position: 'QPoint'):
        """Show context menu (Qt)."""
        if not USING_QT:
            return

        item = self.tree.itemAt(position)
        if not item:
            return

        server_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not server_name:
            return

        menu = QMenu(self)

        server = self.servers[server_name]

        # Add per-client enable/disable options
        if getattr(server, 'claude_enabled', False):
            disable_claude = QAction("Disable for Claude", self)
            disable_claude.triggered.connect(lambda: self._toggle_server(server_name, False, "claude"))
            menu.addAction(disable_claude)
        else:
            enable_claude = QAction("Enable for Claude", self)
            enable_claude.triggered.connect(lambda: self._toggle_server(server_name, True, "claude"))
            menu.addAction(enable_claude)

        if getattr(server, 'gemini_enabled', False):
            disable_gemini = QAction("Disable for Gemini", self)
            disable_gemini.triggered.connect(lambda: self._toggle_server(server_name, False, "gemini"))
            menu.addAction(disable_gemini)
        else:
            enable_gemini = QAction("Enable for Gemini", self)
            enable_gemini.triggered.connect(lambda: self._toggle_server(server_name, True, "gemini"))
            menu.addAction(enable_gemini)

        if getattr(server, 'codex_enabled', False):
            disable_codex = QAction("Disable for Codex", self)
            disable_codex.triggered.connect(lambda: self._toggle_server(server_name, False, "codex"))
            menu.addAction(disable_codex)
        else:
            enable_codex = QAction("Enable for Codex", self)
            enable_codex.triggered.connect(lambda: self._toggle_server(server_name, True, "codex"))
            menu.addAction(enable_codex)

        menu.addSeparator()

        # Add all enable/disable options
        enable_all = QAction("Enable for All", self)
        enable_all.triggered.connect(lambda: self._toggle_server(server_name, True, None))
        menu.addAction(enable_all)

        disable_all = QAction("Disable for All", self)
        disable_all.triggered.connect(lambda: self._toggle_server(server_name, False, None))
        menu.addAction(disable_all)

        menu.addSeparator()

        # Add "Promote to Global" option for project servers
        if getattr(server, 'is_project_server', False):
            promote_action = QAction("🔄 Promote to Global", self)
            promote_action.triggered.connect(lambda: self._promote_to_global(server_name))
            menu.addAction(promote_action)
            menu.addSeparator()

        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(lambda: self.remove_server(server_name))
        menu.addAction(remove_action)

        menu.exec(self.tree.mapToGlobal(position))
    
    def _show_tk_context_menu(self, event):
        """Show context menu (tkinter)."""
        if USING_QT:
            return
        
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if not item:
            return

        self.tree.selection_set(item)
        item_data = self.tree.item(item)
        server_name = item_data['values'][3]  # Server name is now in fourth column
        claude_enabled = item_data['values'][0] == "✓"
        gemini_enabled = item_data['values'][1] == "✓"
        codex_enabled = item_data['values'][2] == "✓"
        
        # Create context menu
        menu = tk.Menu(self.frame, tearoff=0)

        # Add per-client options
        if claude_enabled:
            menu.add_command(label="Disable for Claude", command=lambda: self._toggle_server(server_name, False, "claude"))
        else:
            menu.add_command(label="Enable for Claude", command=lambda: self._toggle_server(server_name, True, "claude"))

        if gemini_enabled:
            menu.add_command(label="Disable for Gemini", command=lambda: self._toggle_server(server_name, False, "gemini"))
        else:
            menu.add_command(label="Enable for Gemini", command=lambda: self._toggle_server(server_name, True, "gemini"))

        if codex_enabled:
            menu.add_command(label="Disable for Codex", command=lambda: self._toggle_server(server_name, False, "codex"))
        else:
            menu.add_command(label="Enable for Codex", command=lambda: self._toggle_server(server_name, True, "codex"))

        menu.add_separator()
        menu.add_command(label="Enable for All", command=lambda: self._toggle_server(server_name, True, None))
        menu.add_command(label="Disable for All", command=lambda: self._toggle_server(server_name, False, None))
        
        menu.add_separator()

        # Add "Promote to Global" option for project servers
        server = self.servers.get(server_name)
        if server and getattr(server, 'is_project_server', False):
            menu.add_command(label="🔄 Promote to Global", command=lambda: self._promote_to_global(server_name))
            menu.add_separator()

        menu.add_command(label="Remove", command=lambda: self.remove_server(server_name))

        menu.post(event.x_root, event.y_root)
    
    def load_servers(self, servers: List[ServerListItem]):
        """Load a list of servers into the widget.
        
        Args:
            servers: List of ServerListItem objects to display
        """
        # Clear existing servers
        self.clear()
        
        # Add each server to the list
        for server in servers:
            self.add_server(server)
        
        # Update status count
        self.update_status_count()
        
        # Update master checkbox state
        self._update_master_checkbox_state()
    
    def clear(self):
        """Clear all servers from the list."""
        if USING_QT:
            self.tree.clear()
        else:
            for item in self.tree.get_children():
                self.tree.delete(item)
        
        self.servers.clear()
        self.selected_server = None
    
    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled server names."""
        return [name for name, server in self.servers.items() 
                if server.status == ServerStatus.ENABLED]
    
    def get_disabled_servers(self) -> List[str]:
        """Get list of disabled server names."""
        return [name for name, server in self.servers.items() 
                if server.status == ServerStatus.DISABLED]
    
    def set_filter(self, filter_text: str):
        """Filter servers by name."""
        filter_lower = filter_text.lower()
        
        if USING_QT:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                server_name = item.data(0, Qt.ItemDataRole.UserRole)
                visible = filter_lower in server_name.lower()
                item.setHidden(not visible)
        else:
            # tkinter doesn't have built-in hiding, so we need to rebuild
            # This is a simplified implementation
            pass

    def _get_overall_status(self, server: ServerListItem) -> str:
        """Get overall status based on per-client enablement."""
        claude_enabled = getattr(server, 'claude_enabled', False)
        gemini_enabled = getattr(server, 'gemini_enabled', False)
        codex_enabled = getattr(server, 'codex_enabled', False)

        if claude_enabled and gemini_enabled and codex_enabled:
            return ServerStatus.ENABLED.value
        elif claude_enabled or gemini_enabled or codex_enabled:
            return "Partial"
        else:
            return ServerStatus.DISABLED.value
    
    def update_status_count(self):
        """Update the status label with server counts."""
        enabled_count = len(self.get_enabled_servers())
        total_count = len(self.servers)
        
        status_text = f"{enabled_count}/{total_count} servers enabled"
        
        if USING_QT:
            self.status_label.setText(status_text)
        else:
            self.status_label.config(text=status_text)
    
    def add_toggle_callback(self, callback: Callable):
        """Add callback for server toggle events."""
        self._toggle_callbacks.append(callback)
    
    def add_selection_callback(self, callback: Callable):
        """Add callback for server selection events."""
        self._selection_callbacks.append(callback)
    
    def add_multi_selection_callback(self, callback: Callable):
        """Add callback for multi-selection events."""
        self._multi_selection_callbacks.append(callback)
    
    def enable_multi_selection(self, enabled: bool = True):
        """Enable or disable multi-selection mode."""
        self.multi_select_enabled = enabled
        
        if USING_QT:
            if enabled:
                self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
            else:
                self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        else:
            # tkinter tree supports multi-selection by default with Ctrl/Shift
            pass
    
    def get_selected_servers(self) -> List[str]:
        """Get list of currently selected server names."""
        selected = []
        
        if USING_QT:
            for item in self.tree.selectedItems():
                server_name = item.data(0, Qt.ItemDataRole.UserRole)
                if server_name:
                    selected.append(server_name)
        else:
            for item_id in self.tree.selection():
                item = self.tree.item(item_id)
                server_name = item['values'][2]  # Server name is now in third column
                selected.append(server_name)
        
        return selected
    
    def select_servers(self, server_names: List[str]):
        """Select multiple servers programmatically."""
        if USING_QT:
            self.tree.clearSelection()
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                server_name = item.data(0, Qt.ItemDataRole.UserRole)
                if server_name in server_names:
                    item.setSelected(True)
        else:
            # Clear current selection
            self.tree.selection_remove(self.tree.selection())
            
            # Select new items
            for server_name in server_names:
                server = self.servers.get(server_name)
                if server and hasattr(server, '_tree_item'):
                    self.tree.selection_add(server._tree_item)
    
    def toggle_selected_servers(self, enable: bool):
        """Toggle all selected servers to enabled/disabled state."""
        selected = self.get_selected_servers()
        for server_name in selected:
            self._toggle_server(server_name, enable)
    
    def _on_selection_changed_qt(self):
        """Handle selection change in Qt."""
        if not USING_QT:
            return
        
        selected = self.get_selected_servers()
        self.selected_servers = selected
        
        # Update single selection for compatibility
        if selected:
            self.selected_server = selected[0]
        else:
            self.selected_server = None
        
        # Notify multi-selection callbacks
        for callback in self._multi_selection_callbacks:
            callback(selected)
    
    def get_widget(self):
        """Get the underlying widget (for tkinter compatibility)."""
        if USING_QT:
            return self
        else:
            return self.frame
    
    def _on_header_clicked(self, logical_index):
        """Handle header click to toggle master checkbox."""
        if not USING_QT or logical_index > 2:  # Only handle checkbox columns
            return

        if logical_index == 0:  # Claude column
            # Cycle through states: Unchecked -> Checked -> Unchecked
            if self.claude_master_state == Qt.CheckState.Unchecked:
                self.claude_master_state = Qt.CheckState.Checked
                # Check all Claude items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(0, Qt.CheckState.Checked)
            else:
                self.claude_master_state = Qt.CheckState.Unchecked
                # Uncheck all Claude items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(0, Qt.CheckState.Unchecked)
        elif logical_index == 1:  # Gemini column
            # Cycle through states: Unchecked -> Checked -> Unchecked
            if self.gemini_master_state == Qt.CheckState.Unchecked:
                self.gemini_master_state = Qt.CheckState.Checked
                # Check all Gemini items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(1, Qt.CheckState.Checked)
            else:
                self.gemini_master_state = Qt.CheckState.Unchecked
                # Uncheck all Gemini items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(1, Qt.CheckState.Unchecked)
        elif logical_index == 2:  # Codex column
            # Cycle through states: Unchecked -> Checked -> Unchecked
            if self.codex_master_state == Qt.CheckState.Unchecked:
                self.codex_master_state = Qt.CheckState.Checked
                # Check all Codex items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(2, Qt.CheckState.Checked)
            else:
                self.codex_master_state = Qt.CheckState.Unchecked
                # Uncheck all Codex items
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    item.setCheckState(2, Qt.CheckState.Unchecked)

        self._update_master_checkbox_display()
    
    def _update_master_checkbox_state(self):
        """Update the master checkbox states based on individual checkboxes."""
        if not USING_QT:
            return

        claude_checked = 0
        gemini_checked = 0
        codex_checked = 0
        total_count = self.tree.topLevelItemCount()

        for i in range(total_count):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                claude_checked += 1
            if item.checkState(1) == Qt.CheckState.Checked:
                gemini_checked += 1
            if item.checkState(2) == Qt.CheckState.Checked:
                codex_checked += 1

        # Update Claude master state
        if claude_checked == 0:
            self.claude_master_state = Qt.CheckState.Unchecked
        elif claude_checked == total_count:
            self.claude_master_state = Qt.CheckState.Checked
        else:
            self.claude_master_state = Qt.CheckState.PartiallyChecked

        # Update Gemini master state
        if gemini_checked == 0:
            self.gemini_master_state = Qt.CheckState.Unchecked
        elif gemini_checked == total_count:
            self.gemini_master_state = Qt.CheckState.Checked
        else:
            self.gemini_master_state = Qt.CheckState.PartiallyChecked

        # Update Codex master state
        if codex_checked == 0:
            self.codex_master_state = Qt.CheckState.Unchecked
        elif codex_checked == total_count:
            self.codex_master_state = Qt.CheckState.Checked
        else:
            self.codex_master_state = Qt.CheckState.PartiallyChecked

        self._update_master_checkbox_display()
    
    def _update_master_checkbox_display(self):
        """Update the visual display of the master checkboxes in the header."""
        if not USING_QT:
            return

        # Update Claude header
        if self.claude_master_state == Qt.CheckState.Checked:
            self.tree.headerItem().setText(0, "☑ Claude")
        elif self.claude_master_state == Qt.CheckState.Unchecked:
            self.tree.headerItem().setText(0, "☐ Claude")
        else:  # PartiallyChecked
            self.tree.headerItem().setText(0, "⊟ Claude")

        # Update Gemini header
        if self.gemini_master_state == Qt.CheckState.Checked:
            self.tree.headerItem().setText(1, "☑ Gemini")
        elif self.gemini_master_state == Qt.CheckState.Unchecked:
            self.tree.headerItem().setText(1, "☐ Gemini")
        else:  # PartiallyChecked
            self.tree.headerItem().setText(1, "⊟ Gemini")

        # Update Codex header
        if self.codex_master_state == Qt.CheckState.Checked:
            self.tree.headerItem().setText(2, "☑ Codex")
        elif self.codex_master_state == Qt.CheckState.Unchecked:
            self.tree.headerItem().setText(2, "☐ Codex")
        else:  # PartiallyChecked
            self.tree.headerItem().setText(2, "⊟ Codex")

    def highlight_new_servers(self, server_names: List[str]):
        """Temporarily highlight newly added servers with green background.

        Args:
            server_names: List of server names to highlight
        """
        if USING_QT:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                server_name = item.text(3)
                if server_name in server_names:
                    # Set green background for new servers
                    from PyQt6.QtGui import QBrush, QColor
                    for col in range(self.tree.columnCount()):
                        item.setBackground(col, QBrush(QColor(200, 255, 200)))  # Light green

            # Schedule removal of highlight after 3 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self._clear_highlights(server_names))

        elif not USING_QT and hasattr(self, 'tree'):
            # Tkinter version
            for item in self.tree.get_children():
                server_name = self.tree.item(item, 'values')[2]
                if server_name in server_names:
                    # Add green tag for highlighting
                    self.tree.item(item, tags=('new_server',))

            # Configure the tag
            self.tree.tag_configure('new_server', background='#C8FFC8')  # Light green

            # Schedule removal after 3 seconds
            if hasattr(self, 'parent'):
                self.parent.after(3000, lambda: self._clear_tk_highlights(server_names))

    def mark_modified_servers(self, server_names: List[str]):
        """Temporarily mark modified servers with orange indicator.

        Args:
            server_names: List of server names to mark as modified
        """
        if USING_QT:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                server_name = item.text(3)
                if server_name in server_names:
                    # Set orange background for modified servers
                    from PyQt6.QtGui import QBrush, QColor
                    for col in range(self.tree.columnCount()):
                        item.setBackground(col, QBrush(QColor(255, 235, 200)))  # Light orange

            # Schedule removal of highlight after 3 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self._clear_highlights(server_names))

        elif not USING_QT and hasattr(self, 'tree'):
            # Tkinter version
            for item in self.tree.get_children():
                server_name = self.tree.item(item, 'values')[2]
                if server_name in server_names:
                    # Add orange tag for highlighting
                    self.tree.item(item, tags=('modified_server',))

            # Configure the tag
            self.tree.tag_configure('modified_server', background='#FFEBC8')  # Light orange

            # Schedule removal after 3 seconds
            if hasattr(self, 'parent'):
                self.parent.after(3000, lambda: self._clear_tk_highlights(server_names))

    def flash_removed_servers(self, server_names: List[str]):
        """Flash servers red before removing them.

        Args:
            server_names: List of server names to flash and remove
        """
        if USING_QT:
            for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
                item = self.tree.topLevelItem(i)
                server_name = item.text(3)
                if server_name in server_names:
                    # Set red background and strikethrough
                    from PyQt6.QtGui import QBrush, QColor, QFont
                    for col in range(self.tree.columnCount()):
                        item.setBackground(col, QBrush(QColor(255, 200, 200)))  # Light red
                        font = item.font(col)
                        font.setStrikeOut(True)
                        item.setFont(col, font)

            # Schedule removal after 1 second
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._remove_servers(server_names))

        elif not USING_QT and hasattr(self, 'tree'):
            # Tkinter version
            for item in self.tree.get_children():
                server_name = self.tree.item(item, 'values')[2]
                if server_name in server_names:
                    # Add red tag for highlighting
                    self.tree.item(item, tags=('removed_server',))

            # Configure the tag with strikethrough effect (simulated with overstrike font)
            self.tree.tag_configure('removed_server', background='#FFC8C8', foreground='#666666')

            # Schedule removal after 1 second
            if hasattr(self, 'parent'):
                self.parent.after(1000, lambda: self._remove_servers(server_names))

    def _clear_highlights(self, server_names: List[str]):
        """Clear highlight from specified servers (Qt version).

        Args:
            server_names: List of server names to clear highlights from
        """
        if not USING_QT:
            return

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            server_name = item.text(2)
            if server_name in server_names:
                # Clear background color
                from PyQt6.QtGui import QBrush
                for col in range(self.tree.columnCount()):
                    item.setBackground(col, QBrush())  # Clear background

    def _clear_tk_highlights(self, server_names: List[str]):
        """Clear highlight from specified servers (Tkinter version).

        Args:
            server_names: List of server names to clear highlights from
        """
        if USING_QT or not hasattr(self, 'tree'):
            return

        for item in self.tree.get_children():
            server_name = self.tree.item(item, 'values')[2]
            if server_name in server_names:
                # Remove highlight tags
                self.tree.item(item, tags=())

    def _promote_to_global(self, server_name: str):
        """Promote a project server to global configuration.

        Args:
            server_name: Name of the server to promote
        """
        if USING_QT:
            self.server_promoted.emit(server_name)

        # Notify callbacks
        for callback in self._toggle_callbacks:
            try:
                callback(server_name, 'promote', True)
            except TypeError:
                # Old-style callback without client parameter
                pass

    def _apply_filters(self):
        """Apply search and location filters to the server list."""
        if USING_QT:
            search_text = self.search_box.text().lower()
            location_filter = self.location_combo.currentText()
        else:
            search_text = self.search_var.get().lower()
            location_filter = self.location_var.get()

        self.search_text = search_text
        self.filter_location = location_filter

        # Apply filters
        for i in range(self.tree.topLevelItemCount() if USING_QT else len(self.tree.get_children())):
            if USING_QT:
                item = self.tree.topLevelItem(i)
                # Skip group headers when filtering
                if item.childCount() > 0:
                    continue
                server_name = item.text(3).lower()
                location = item.text(4)
            else:
                children = self.tree.get_children()
                if i >= len(children):
                    break
                item_id = children[i]
                # Skip group headers
                if self.tree.get_children(item_id):
                    continue
                values = self.tree.item(item_id, 'values')
                server_name = values[2].lower() if len(values) > 2 else ""
                location = values[4] if len(values) > 4 else "Global"

            # Check search filter
            show = True
            if search_text and search_text not in server_name:
                show = False

            # Check location filter
            if show and location_filter != "All":
                if location_filter == "Global" and location != "Global":
                    show = False
                elif location_filter == "Project" and location == "Global":
                    show = False

            # Show/hide item
            if USING_QT:
                item.setHidden(not show)
            else:
                # For tkinter, we need to be more careful with detach/reattach
                try:
                    if show and item_id not in self.tree.get_children():
                        self.tree.reattach(item_id, '', 'end')
                    elif not show and item_id in self.tree.get_children():
                        self.tree.detach(item_id)
                except:
                    pass

        self.update_status_count()

    def _on_location_filter_changed(self, location: str):
        """Handle location filter change."""
        self._apply_filters()

    def _on_group_by_changed(self, checked: bool):
        """Handle group by location change for Qt."""
        self.group_by_location = checked
        self._reorganize_by_location()

    def _on_group_by_changed_tk(self):
        """Handle group by location change for tkinter."""
        self.group_by_location = self.group_var.get()
        self._reorganize_by_location()

    def _reorganize_by_location(self):
        """Reorganize servers by location (group or ungroup)."""
        if self.group_by_location:
            # Group servers by location
            self._group_servers_by_location()
        else:
            # Ungroup servers (flat list)
            self._ungroup_servers()

    def _group_servers_by_location(self):
        """Group servers by their location."""
        if USING_QT:
            # Collect all items
            items_to_group = []
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.takeTopLevelItem(0)
                items_to_group.append(item)

            # Create location groups
            global_group = QTreeWidgetItem(["", "", "📂 Global Servers", "", ""])
            global_group.setExpanded(True)

            # Make group headers bold
            from PyQt6.QtGui import QFont
            font = QFont()
            font.setBold(True)
            for col in range(5):
                global_group.setFont(col, font)

            self.tree.addTopLevelItem(global_group)

            project_groups = {}

            # Add servers to groups
            for item in items_to_group:
                location = item.text(4)
                if location == "Global":
                    global_group.addChild(item)
                else:
                    # Project server
                    if location not in project_groups:
                        project_group = QTreeWidgetItem(["", "", f"📂 {location}", "", ""])
                        project_group.setExpanded(True)
                        for col in range(5):
                            project_group.setFont(col, font)
                        self.tree.addTopLevelItem(project_group)
                        project_groups[location] = project_group
                    project_groups[location].addChild(item)
        else:
            # Tkinter version
            # Store all items
            items = []
            for child in self.tree.get_children():
                values = self.tree.item(child, 'values')
                items.append(values)
                self.tree.delete(child)

            # Create groups
            global_group = self.tree.insert('', 'end', text="📂 Global Servers", values=("", "", "Global Servers", "", ""), open=True)
            project_groups = {}

            # Re-add items to groups
            for values in items:
                if not values or len(values) < 3 or not values[2]:  # Skip empty items
                    continue
                location = values[4] if len(values) > 4 else "Global"
                if location == "Global":
                    self.tree.insert(global_group, 'end', values=values)
                else:
                    if location not in project_groups:
                        project_group = self.tree.insert('', 'end', text=f"📂 {location}", values=("", "", location, "", ""), open=True)
                        project_groups[location] = project_group
                    self.tree.insert(project_groups[location], 'end', values=values)

    def _ungroup_servers(self):
        """Restore flat server list (remove grouping)."""
        if USING_QT:
            # Collect all child items from groups
            all_items = []
            for i in range(self.tree.topLevelItemCount()):
                group_item = self.tree.topLevelItem(i)
                if group_item.childCount() > 0:
                    # This is a group
                    while group_item.childCount() > 0:
                        child = group_item.takeChild(0)
                        all_items.append(child)

            # Clear and re-add items
            self.tree.clear()
            for item in all_items:
                self.tree.addTopLevelItem(item)

            # Recreate header after clear
            self._setup_master_checkbox()
        else:
            # Tkinter version
            # Collect all items from groups
            all_items = []
            for group in self.tree.get_children():
                children = self.tree.get_children(group)
                if children:
                    # This is a group
                    for child in children:
                        values = self.tree.item(child, 'values')
                        all_items.append(values)

            # Clear and re-add
            self.tree.delete(*self.tree.get_children())
            for values in all_items:
                if values and len(values) > 2 and values[2]:  # Has valid server name
                    self.tree.insert('', 'end', values=values)

    def _clear_filters(self):
        """Clear all filters for Qt."""
        self.search_box.clear()
        self.location_combo.setCurrentText("All")
        self.group_checkbox.setChecked(False)
        self._apply_filters()

    def _clear_filters_tk(self):
        """Clear all filters for tkinter."""
        self.search_var.set("")
        self.location_var.set("All")
        self.group_var.set(False)
        self._apply_filters()

    def get_location_stats(self) -> Dict[str, int]:
        """Get count of servers by location."""
        stats = {"Global": 0, "Project": 0}

        if USING_QT:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.childCount() == 0:  # Not a group
                    location = item.text(4)
                    if location == "Global":
                        stats["Global"] += 1
                    else:
                        stats["Project"] += 1
                else:  # It's a group, count children
                    for j in range(item.childCount()):
                        child = item.child(j)
                        location = child.text(4)
                        if location == "Global":
                            stats["Global"] += 1
                        else:
                            stats["Project"] += 1
        else:
            for child in self.tree.get_children():
                children = self.tree.get_children(child)
                if children:  # It's a group
                    for subchild in children:
                        values = self.tree.item(subchild, 'values')
                        location = values[4] if len(values) > 4 else "Global"
                        if location == "Global":
                            stats["Global"] += 1
                        else:
                            stats["Project"] += 1
                else:  # Regular item
                    values = self.tree.item(child, 'values')
                    if values and len(values) > 2 and values[2]:  # Has server name
                        location = values[4] if len(values) > 4 else "Global"
                        if location == "Global":
                            stats["Global"] += 1
                        else:
                            stats["Project"] += 1

        return stats

    def _remove_servers(self, server_names: List[str]):
        """Remove servers from the list after flash animation.

        Args:
            server_names: List of server names to remove
        """
        # This would be called by the main window's refresh method
        # to actually remove the servers from the list
        # For now, just clear any strikethrough formatting
        if USING_QT:
            for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
                item = self.tree.topLevelItem(i)
                server_name = item.text(3)
                if server_name in server_names:
                    # In a real implementation, we'd remove the item
                    # For now, just clear the formatting
                    from PyQt6.QtGui import QBrush, QFont
                    for col in range(self.tree.columnCount()):
                        item.setBackground(col, QBrush())
                        font = item.font(col)
                        font.setStrikeOut(False)
                        item.setFont(col, font)

    def set_cli_availability(self, availability: Dict[str, bool]):
        """Set CLI availability for all clients.

        Args:
            availability: Dict with keys 'claude', 'gemini', 'codex' and boolean values
        """
        self.cli_availability = availability

        # Update header display to show availability
        self._update_master_checkbox_display()

        # Refresh all server items to update checkbox states
        if USING_QT:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                server_name = item.data(0, Qt.ItemDataRole.UserRole)
                if server_name and server_name in self.servers:
                    server = self.servers[server_name]

                    # Update checkbox enabled states based on CLI availability
                    if not availability.get('claude', True):
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Unchecked)
                        item.setToolTip(0, "Claude not installed. Click Refresh to check again.")
                    else:
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Checked if server.claude_enabled else Qt.CheckState.Unchecked)
                        item.setToolTip(0, "Toggle Claude for this server")

                    if not availability.get('gemini', True):
                        item.setCheckState(1, Qt.CheckState.Unchecked)
                        item.setToolTip(1, "Gemini not installed. Click Refresh to check again.")
                    else:
                        item.setCheckState(1, Qt.CheckState.Checked if server.gemini_enabled else Qt.CheckState.Unchecked)
                        item.setToolTip(1, "Toggle Gemini for this server")

                    if not availability.get('codex', True):
                        item.setCheckState(2, Qt.CheckState.Unchecked)
                        item.setToolTip(2, "Codex not installed. Click Refresh to check again.")
                    else:
                        item.setCheckState(2, Qt.CheckState.Checked if getattr(server, 'codex_enabled', False) else Qt.CheckState.Unchecked)
                        item.setToolTip(2, "Toggle Codex for this server")