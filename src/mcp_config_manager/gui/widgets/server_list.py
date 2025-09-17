"""Server list widget for MCP Config Manager."""

from typing import List, Optional, Dict, Any, Callable
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QMenu, QHeaderView, QCheckBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QPoint
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
    
    def _setup_qt_widget(self):
        """Set up Qt widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        # Apply custom stylesheet for blue selection highlight
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
        
        # Add master checkbox to header
        self._setup_master_checkbox()
        
        # Set column widths
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 70)  # Claude column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 70)  # Gemini column
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Server name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 100)  # Status column
        
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
    
    def _setup_master_checkbox(self):
        """Set up the master checkboxes in the header."""
        if not USING_QT:
            return

        # Set header labels initially
        self.tree.setHeaderLabels(["Claude", "Gemini", "Server", "Status"])

        # Store reference to header for updating checkbox display
        self.header = self.tree.header()
        self.header.setSectionsClickable(True)
        self.header.sectionClicked.connect(self._on_header_clicked)

        # Track master checkbox states
        self.claude_master_state = Qt.CheckState.Unchecked
        self.gemini_master_state = Qt.CheckState.Unchecked
    
    def _setup_tk_widget(self, parent):
        """Set up tkinter widget."""
        self.frame = ttk.Frame(parent)
        
        # Tree view for server list
        columns = ("claude", "gemini", "server", "status")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="tree headings")

        # Configure columns
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, stretch=False)

        self.tree.heading("claude", text="Claude")
        self.tree.column("claude", width=70)

        self.tree.heading("gemini", text="Gemini")
        self.tree.column("gemini", width=70)

        self.tree.heading("server", text="Server")
        self.tree.column("server", width=250)

        self.tree.heading("status", text="Status")
        self.tree.column("status", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
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
    
    def add_server(self, server: ServerListItem):
        """Add a server to the list."""
        self.servers[server.name] = server

        if USING_QT:
            # Temporarily block signals to prevent triggering events during initial setup
            self.tree.blockSignals(True)

            item = QTreeWidgetItem()

            # Add checkboxes for both Claude and Gemini columns
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Set checkbox states based on per-client enabled status
            claude_enabled = getattr(server, 'claude_enabled', server.status == ServerStatus.ENABLED)
            gemini_enabled = getattr(server, 'gemini_enabled', server.status == ServerStatus.ENABLED)

            item.setCheckState(0, Qt.CheckState.Checked if claude_enabled else Qt.CheckState.Unchecked)
            item.setCheckState(1, Qt.CheckState.Checked if gemini_enabled else Qt.CheckState.Unchecked)

            item.setText(2, server.name)
            item.setText(3, str(server.status.value) if hasattr(server.status, 'value') else str(server.status))

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
            values = (claude_mark, gemini_mark, server.name, server.status.value)
            item_id = self.tree.insert("", "end", values=values, tags=(server.status.value.lower(),))

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
        else:
            # Update both if no specific client
            server.status = status
            server.claude_enabled = (status == ServerStatus.ENABLED)
            server.gemini_enabled = (status == ServerStatus.ENABLED)

        if USING_QT:
            # Find and update the item
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == server_name:
                    item.setText(3, status.value if status else self._get_overall_status(server))
                    self._update_item_status(item, status if status else server.status)

                    # Block signals temporarily to avoid triggering unwanted events
                    self.tree.blockSignals(True)
                    # Update checkbox states
                    item.setCheckState(0, Qt.CheckState.Checked if server.claude_enabled else Qt.CheckState.Unchecked)
                    item.setCheckState(1, Qt.CheckState.Checked if server.gemini_enabled else Qt.CheckState.Unchecked)
                    self.tree.blockSignals(False)
                    break
        else:
            # Update tkinter tree
            if hasattr(server, '_tree_item'):
                claude_mark = "✓" if server.claude_enabled else ""
                gemini_mark = "✓" if server.gemini_enabled else ""
                overall_status = self._get_overall_status(server)
                values = (claude_mark, gemini_mark, server.name, overall_status)
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
        
        item.setForeground(2, QBrush(color))
    
    def _configure_tk_tags(self):
        """Configure tkinter tag colors."""
        if not USING_QT:
            self.tree.tag_configure("error", foreground="red")
            self.tree.tag_configure("loading", foreground="orange")
            self.tree.tag_configure("disabled", foreground="gray")
            self.tree.tag_configure("enabled", foreground="green")
    
    def _on_item_changed(self, item: 'QTreeWidgetItem', column: int):
        """Handle item changed event for checkbox state changes."""
        if not USING_QT or column > 1:  # Only handle checkbox columns (0 and 1)
            return

        server_name = item.data(0, Qt.ItemDataRole.UserRole)
        if server_name:
            client = "claude" if column == 0 else "gemini"
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
        # Columns 0 and 1 are checkbox columns, handled by itemChanged signal
        if column > 1:
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
            server_name = item['values'][2]  # Server name is now in third column
            # Toggle both for double-click
            claude_enabled = item['values'][0] == "✓"
            gemini_enabled = item['values'][1] == "✓"
            # If either is enabled, disable both; otherwise enable both
            new_state = not (claude_enabled or gemini_enabled)
            self._toggle_server(server_name, new_state, None)
    
    def _show_context_menu(self, position: QPoint):
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

        menu.addSeparator()

        # Add both enable/disable options
        enable_both = QAction("Enable for Both", self)
        enable_both.triggered.connect(lambda: self._toggle_server(server_name, True, None))
        menu.addAction(enable_both)

        disable_both = QAction("Disable for Both", self)
        disable_both.triggered.connect(lambda: self._toggle_server(server_name, False, None))
        menu.addAction(disable_both)

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
        server_name = item_data['values'][2]  # Server name is now in third column
        claude_enabled = item_data['values'][0] == "✓"
        gemini_enabled = item_data['values'][1] == "✓"
        
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

        menu.add_separator()
        menu.add_command(label="Enable for Both", command=lambda: self._toggle_server(server_name, True, None))
        menu.add_command(label="Disable for Both", command=lambda: self._toggle_server(server_name, False, None))
        
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

        if claude_enabled and gemini_enabled:
            return ServerStatus.ENABLED.value
        elif claude_enabled or gemini_enabled:
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
        if not USING_QT or logical_index > 1:  # Only handle checkbox columns
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

        self._update_master_checkbox_display()
    
    def _update_master_checkbox_state(self):
        """Update the master checkbox states based on individual checkboxes."""
        if not USING_QT:
            return

        claude_checked = 0
        gemini_checked = 0
        total_count = self.tree.topLevelItemCount()

        for i in range(total_count):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                claude_checked += 1
            if item.checkState(1) == Qt.CheckState.Checked:
                gemini_checked += 1

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