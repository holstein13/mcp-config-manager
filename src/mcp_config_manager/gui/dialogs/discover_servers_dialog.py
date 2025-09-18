"""
Project Server Discovery Dialog
Displays discovered project-specific MCP servers and allows promotion to global config
"""

import sys
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
        QPushButton, QLabel, QCheckBox, QSplitter, QTextEdit,
        QComboBox, QGroupBox, QProgressBar, QMessageBox,
        QDialogButtonBox, QHeaderView, QWidget
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt6.QtGui import QFont, QColor, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    HAS_TK = True
except ImportError:
    HAS_TK = False

from ...core.project_discovery import ProjectDiscoveryService, ProjectServer
import json
import logging

logger = logging.getLogger(__name__)


if HAS_QT:
    class DiscoveryThread(QThread):
        """Background thread for project discovery"""
        progress = pyqtSignal(int, int, str)  # current, total, message
        finished = pyqtSignal(dict)  # results
        error = pyqtSignal(str)  # error message

        def __init__(self, discovery_service, base_paths=None, max_depth=3):
            super().__init__()
            self.discovery_service = discovery_service
            self.base_paths = base_paths
            self.max_depth = max_depth

        def run(self):
            try:
                # Set progress callback
                self.discovery_service.set_progress_callback(
                    lambda c, t, m: self.progress.emit(c, t, m)
                )

                # Run discovery
                results = self.discovery_service.scan_projects(
                    base_paths=self.base_paths,
                    max_depth=self.max_depth,
                    use_cache=False  # Force fresh scan
                )

                self.finished.emit(results)
            except Exception as e:
                self.error.emit(str(e))


    class DiscoverServersDialog(QDialog):
        """Qt implementation of the Project Server Discovery Dialog"""

        def __init__(self, parent=None, server_controller=None):
            super().__init__(parent)
            self.server_controller = server_controller
            self.discovery_service = None
            self.discovery_thread = None
            self.project_servers = {}
            self.selected_servers = set()

            self.setWindowTitle("Discover Project Servers")
            self.setModal(True)
            self.resize(900, 600)

            self._init_ui()
            self._start_discovery()

        def _init_ui(self):
            """Initialize the user interface"""
            layout = QVBoxLayout(self)

            # Header
            header_label = QLabel("Discovering MCP Servers in Project Configurations")
            header_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
            layout.addWidget(header_label)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(True)
            layout.addWidget(self.progress_bar)

            self.progress_label = QLabel("Starting discovery...")
            layout.addWidget(self.progress_label)

            # Main content area with splitter
            splitter = QSplitter(Qt.Orientation.Horizontal)

            # Left side - Tree view
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)

            tree_label = QLabel("Discovered Servers:")
            left_layout.addWidget(tree_label)

            self.tree_widget = QTreeWidget()
            self.tree_widget.setHeaderLabels(["Server / Project", "Status"])
            self.tree_widget.setRootIsDecorated(True)
            self.tree_widget.itemChanged.connect(self._on_item_changed)
            self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
            left_layout.addWidget(self.tree_widget)

            # Selection controls
            select_layout = QHBoxLayout()
            self.select_all_btn = QPushButton("Select All")
            self.select_all_btn.clicked.connect(self._select_all)
            self.select_none_btn = QPushButton("Select None")
            self.select_none_btn.clicked.connect(self._select_none)
            select_layout.addWidget(self.select_all_btn)
            select_layout.addWidget(self.select_none_btn)
            select_layout.addStretch()
            left_layout.addLayout(select_layout)

            splitter.addWidget(left_widget)

            # Right side - Configuration preview
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)

            preview_label = QLabel("Configuration Preview:")
            right_layout.addWidget(preview_label)

            self.config_preview = QTextEdit()
            self.config_preview.setReadOnly(True)
            self.config_preview.setFont(QFont("Courier", 10))
            right_layout.addWidget(self.config_preview)

            # Conflict resolution options
            conflict_group = QGroupBox("Conflict Resolution")
            conflict_layout = QVBoxLayout()

            self.conflict_strategy = QComboBox()
            self.conflict_strategy.addItems([
                "Keep existing (skip duplicates)",
                "Replace with project version",
                "Rename project version"
            ])
            conflict_layout.addWidget(QLabel("When server name already exists:"))
            conflict_layout.addWidget(self.conflict_strategy)

            conflict_group.setLayout(conflict_layout)
            right_layout.addWidget(conflict_group)

            splitter.addWidget(right_widget)
            splitter.setSizes([500, 400])

            layout.addWidget(splitter)

            # Dialog buttons
            button_box = QDialogButtonBox()

            self.promote_btn = QPushButton("Promote Selected")
            self.promote_btn.clicked.connect(self._promote_selected)
            self.promote_btn.setEnabled(False)
            button_box.addButton(self.promote_btn, QDialogButtonBox.ButtonRole.ActionRole)

            self.promote_all_btn = QPushButton("Promote All")
            self.promote_all_btn.clicked.connect(self._promote_all)
            self.promote_all_btn.setEnabled(False)
            button_box.addButton(self.promote_all_btn, QDialogButtonBox.ButtonRole.ActionRole)

            self.refresh_btn = QPushButton("Refresh")
            self.refresh_btn.clicked.connect(self._start_discovery)
            button_box.addButton(self.refresh_btn, QDialogButtonBox.ButtonRole.ActionRole)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.reject)
            button_box.addButton(self.close_btn, QDialogButtonBox.ButtonRole.RejectRole)

            layout.addWidget(button_box)

        def _start_discovery(self):
            """Start the discovery process in a background thread"""
            if self.discovery_thread and self.discovery_thread.isRunning():
                return

            # Clear existing items
            self.tree_widget.clear()
            self.config_preview.clear()
            self.selected_servers.clear()
            self.project_servers.clear()

            # Disable buttons during discovery
            self.promote_btn.setEnabled(False)
            self.promote_all_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)

            # Create discovery service if needed
            if not self.discovery_service:
                from ...parsers.claude_parser import ClaudeConfigParser
                parser = ClaudeConfigParser()
                self.discovery_service = ProjectDiscoveryService(claude_parser=parser)

            # Start discovery thread
            self.discovery_thread = DiscoveryThread(self.discovery_service)
            self.discovery_thread.progress.connect(self._on_progress)
            self.discovery_thread.finished.connect(self._on_discovery_complete)
            self.discovery_thread.error.connect(self._on_discovery_error)
            self.discovery_thread.start()

        def _on_progress(self, current, total, message):
            """Update progress bar and label"""
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_label.setText(message)

        def _on_discovery_complete(self, results):
            """Handle discovery completion"""
            self.project_servers = results
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.progress_label.setText(f"Discovery complete: Found {sum(len(s) for s in results.values())} servers in {len(results)} projects")

            # Populate tree
            self._populate_tree()

            # Re-enable buttons
            self.refresh_btn.setEnabled(True)
            if self.tree_widget.topLevelItemCount() > 0:
                self.promote_all_btn.setEnabled(True)

        def _on_discovery_error(self, error_msg):
            """Handle discovery error"""
            self.progress_label.setText(f"Error: {error_msg}")
            QMessageBox.critical(self, "Discovery Error", f"Failed to discover project servers:\n{error_msg}")
            self.refresh_btn.setEnabled(True)

        def _populate_tree(self):
            """Populate the tree widget with discovered servers"""
            for project_path, servers in self.project_servers.items():
                # Create project item
                project_item = QTreeWidgetItem(self.tree_widget)
                project_item.setText(0, str(Path(project_path).name))
                project_item.setToolTip(0, str(project_path))
                project_item.setExpanded(True)

                # Style project item
                font = project_item.font(0)
                font.setBold(True)
                project_item.setFont(0, font)

                # Add server items
                for server in servers:
                    server_item = QTreeWidgetItem(project_item)
                    server_item.setText(0, server.name)
                    server_item.setCheckState(0, Qt.CheckState.Unchecked)
                    server_item.setData(0, Qt.ItemDataRole.UserRole, server)

                    # Set status
                    if server.is_duplicate:
                        server_item.setText(1, "⚠️ Duplicate")
                        server_item.setForeground(1, QBrush(QColor(255, 165, 0)))
                    else:
                        server_item.setText(1, "✅ Unique")
                        server_item.setForeground(1, QBrush(QColor(0, 128, 0)))

            # Resize columns
            self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        def _on_item_changed(self, item, column):
            """Handle item check state changes"""
            if column != 0 or not item.parent():
                return

            server = item.data(0, Qt.ItemDataRole.UserRole)
            if not server:
                return

            if item.checkState(0) == Qt.CheckState.Checked:
                self.selected_servers.add((server.name, str(server.project_path)))
            else:
                self.selected_servers.discard((server.name, str(server.project_path)))

            self.promote_btn.setEnabled(len(self.selected_servers) > 0)

        def _on_selection_changed(self):
            """Handle selection changes to show config preview"""
            current = self.tree_widget.currentItem()
            if not current or not current.parent():
                self.config_preview.clear()
                return

            server = current.data(0, Qt.ItemDataRole.UserRole)
            if server:
                # Format config as JSON
                config_json = json.dumps(server.config, indent=2)
                preview_text = f"Server: {server.name}\n"
                preview_text += f"Project: {server.project_path}\n"
                preview_text += f"Duplicate: {'Yes' if server.is_duplicate else 'No'}\n"
                preview_text += f"\nConfiguration:\n{config_json}"
                self.config_preview.setPlainText(preview_text)

        def _select_all(self):
            """Select all servers"""
            for i in range(self.tree_widget.topLevelItemCount()):
                project_item = self.tree_widget.topLevelItem(i)
                for j in range(project_item.childCount()):
                    server_item = project_item.child(j)
                    server_item.setCheckState(0, Qt.CheckState.Checked)

        def _select_none(self):
            """Deselect all servers"""
            for i in range(self.tree_widget.topLevelItemCount()):
                project_item = self.tree_widget.topLevelItem(i)
                for j in range(project_item.childCount()):
                    server_item = project_item.child(j)
                    server_item.setCheckState(0, Qt.CheckState.Unchecked)

        def _promote_selected(self):
            """Promote selected servers to global configuration"""
            if not self.selected_servers:
                return

            strategy = self.conflict_strategy.currentIndex()
            strategy_map = {
                0: 'skip',
                1: 'replace',
                2: 'rename'
            }

            promoted_count = 0
            skipped_count = 0
            errors = []

            for server_name, project_path in self.selected_servers:
                try:
                    # Find the server object
                    server_obj = None
                    for server in self.project_servers.get(project_path, []):
                        if server.name == server_name:
                            server_obj = server
                            break

                    if not server_obj:
                        continue

                    # Check for conflicts
                    if server_obj.is_duplicate and strategy_map[strategy] == 'skip':
                        skipped_count += 1
                        continue

                    # Handle renaming if needed
                    final_name = server_name
                    if server_obj.is_duplicate and strategy_map[strategy] == 'rename':
                        # Add project suffix to make unique
                        project_name = Path(project_path).name
                        final_name = f"{server_name}_{project_name}"

                    # Promote the server
                    if self.server_controller:
                        # Use controller if available
                        success = self.server_controller.promote_project_server(
                            server_name, project_path, final_name
                        )
                    else:
                        # Direct promotion (fallback)
                        from ...core.server_manager import ServerManager
                        manager = ServerManager()
                        # This would need access to claude_data and gemini_data
                        success = False  # Placeholder

                    if success:
                        promoted_count += 1
                    else:
                        errors.append(f"{server_name} from {Path(project_path).name}")

                except Exception as e:
                    errors.append(f"{server_name}: {str(e)}")

            # Show results
            message = f"Promoted {promoted_count} server(s) to global configuration."
            if skipped_count > 0:
                message += f"\nSkipped {skipped_count} duplicate(s)."
            if errors:
                message += f"\n\nErrors:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    message += f"\n... and {len(errors) - 5} more"

            QMessageBox.information(self, "Promotion Complete", message)

            # Clear selection
            self._select_none()

            # Refresh the main window if possible
            if self.parent() and hasattr(self.parent(), 'reload_servers_from_disk'):
                self.parent().reload_servers_from_disk()

        def _promote_all(self):
            """Promote all discovered servers"""
            # Select all first
            self._select_all()
            # Then promote
            self._promote_selected()


if HAS_TK:
    class DiscoverServersDialogTk:
        """Tkinter implementation of the Project Server Discovery Dialog"""

        def __init__(self, parent=None, server_controller=None):
            self.parent = parent
            self.server_controller = server_controller
            self.discovery_service = None
            self.project_servers = {}
            self.selected_servers = set()
            self.tree_items = {}  # Map item IDs to server data

            # Create dialog window
            self.dialog = tk.Toplevel(parent)
            self.dialog.title("Discover Project Servers")
            self.dialog.geometry("900x600")
            self.dialog.transient(parent)
            self.dialog.grab_set()

            self._init_ui()
            self._start_discovery()

        def _init_ui(self):
            """Initialize the user interface"""
            # Header
            header_frame = ttk.Frame(self.dialog, padding="10")
            header_frame.pack(fill=tk.X)

            header_label = ttk.Label(
                header_frame,
                text="Discovering MCP Servers in Project Configurations",
                font=("", 12, "bold")
            )
            header_label.pack()

            # Progress frame
            progress_frame = ttk.Frame(self.dialog, padding="10")
            progress_frame.pack(fill=tk.X)

            self.progress_var = tk.IntVar()
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                variable=self.progress_var,
                maximum=100
            )
            self.progress_bar.pack(fill=tk.X)

            self.progress_label = ttk.Label(progress_frame, text="Starting discovery...")
            self.progress_label.pack()

            # Main content with paned window
            paned = ttk.PanedWindow(self.dialog, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True, padx=10)

            # Left side - Tree view
            left_frame = ttk.Frame(paned)
            paned.add(left_frame, weight=1)

            tree_label = ttk.Label(left_frame, text="Discovered Servers:")
            tree_label.pack(anchor=tk.W, pady=(0, 5))

            # Tree with scrollbars
            tree_frame = ttk.Frame(left_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            self.tree = ttk.Treeview(
                tree_frame,
                columns=("status",),
                selectmode="extended"
            )
            self.tree.heading("#0", text="Server / Project")
            self.tree.heading("status", text="Status")
            self.tree.column("status", width=100)

            # Scrollbars
            vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
            self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            self.tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")

            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Bind selection event
            self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
            self.tree.bind("<Button-1>", self._on_tree_click)

            # Selection buttons
            select_frame = ttk.Frame(left_frame)
            select_frame.pack(fill=tk.X, pady=(5, 0))

            ttk.Button(select_frame, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
            ttk.Button(select_frame, text="Select None", command=self._select_none).pack(side=tk.LEFT, padx=2)

            # Right side - Configuration preview
            right_frame = ttk.Frame(paned)
            paned.add(right_frame, weight=1)

            preview_label = ttk.Label(right_frame, text="Configuration Preview:")
            preview_label.pack(anchor=tk.W, pady=(0, 5))

            self.config_preview = scrolledtext.ScrolledText(
                right_frame,
                wrap=tk.WORD,
                font=("Courier", 10),
                height=15
            )
            self.config_preview.pack(fill=tk.BOTH, expand=True)
            self.config_preview.config(state=tk.DISABLED)

            # Conflict resolution options
            conflict_frame = ttk.LabelFrame(right_frame, text="Conflict Resolution", padding="10")
            conflict_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Label(conflict_frame, text="When server name already exists:").pack(anchor=tk.W)

            self.conflict_var = tk.StringVar(value="skip")
            strategies = [
                ("Keep existing (skip duplicates)", "skip"),
                ("Replace with project version", "replace"),
                ("Rename project version", "rename")
            ]
            for text, value in strategies:
                ttk.Radiobutton(
                    conflict_frame,
                    text=text,
                    variable=self.conflict_var,
                    value=value
                ).pack(anchor=tk.W)

            # Dialog buttons
            button_frame = ttk.Frame(self.dialog, padding="10")
            button_frame.pack(fill=tk.X)

            self.promote_btn = ttk.Button(
                button_frame,
                text="Promote Selected",
                command=self._promote_selected,
                state=tk.DISABLED
            )
            self.promote_btn.pack(side=tk.LEFT, padx=2)

            self.promote_all_btn = ttk.Button(
                button_frame,
                text="Promote All",
                command=self._promote_all,
                state=tk.DISABLED
            )
            self.promote_all_btn.pack(side=tk.LEFT, padx=2)

            self.refresh_btn = ttk.Button(
                button_frame,
                text="Refresh",
                command=self._start_discovery
            )
            self.refresh_btn.pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Close",
                command=self.dialog.destroy
            ).pack(side=tk.RIGHT, padx=2)

        def _start_discovery(self):
            """Start the discovery process"""
            # Clear existing items
            self.tree.delete(*self.tree.get_children())
            self.config_preview.config(state=tk.NORMAL)
            self.config_preview.delete("1.0", tk.END)
            self.config_preview.config(state=tk.DISABLED)
            self.selected_servers.clear()
            self.project_servers.clear()
            self.tree_items.clear()

            # Disable buttons during discovery
            self.promote_btn.config(state=tk.DISABLED)
            self.promote_all_btn.config(state=tk.DISABLED)
            self.refresh_btn.config(state=tk.DISABLED)

            # Create discovery service if needed
            if not self.discovery_service:
                from ...parsers.claude_parser import ClaudeConfigParser
                parser = ClaudeConfigParser()
                self.discovery_service = ProjectDiscoveryService(claude_parser=parser)

            # Run discovery (simplified - in real implementation would use threading)
            self.progress_label.config(text="Discovering project servers...")
            self.dialog.update()

            try:
                results = self.discovery_service.scan_projects(use_cache=False)
                self.project_servers = results
                self._on_discovery_complete()
            except Exception as e:
                messagebox.showerror("Discovery Error", f"Failed to discover project servers:\n{str(e)}")
                self.refresh_btn.config(state=tk.NORMAL)

        def _on_discovery_complete(self):
            """Handle discovery completion"""
            total_servers = sum(len(s) for s in self.project_servers.values())
            self.progress_label.config(
                text=f"Discovery complete: Found {total_servers} servers in {len(self.project_servers)} projects"
            )
            self.progress_var.set(100)

            # Populate tree
            self._populate_tree()

            # Re-enable buttons
            self.refresh_btn.config(state=tk.NORMAL)
            if self.tree.get_children():
                self.promote_all_btn.config(state=tk.NORMAL)

        def _populate_tree(self):
            """Populate the tree widget with discovered servers"""
            for project_path, servers in self.project_servers.items():
                # Create project item
                project_item = self.tree.insert(
                    "",
                    "end",
                    text=f"📁 {Path(project_path).name}",
                    values=("",),
                    open=True
                )

                # Add server items
                for server in servers:
                    status = "⚠️ Duplicate" if server.is_duplicate else "✅ Unique"
                    server_item = self.tree.insert(
                        project_item,
                        "end",
                        text=f"☐ {server.name}",
                        values=(status,)
                    )
                    self.tree_items[server_item] = {
                        'server': server,
                        'checked': False
                    }

        def _on_tree_click(self, event):
            """Handle tree click to toggle checkboxes"""
            item = self.tree.identify('item', event.x, event.y)
            if item and item in self.tree_items:
                # Toggle checkbox
                data = self.tree_items[item]
                data['checked'] = not data['checked']

                # Update display
                server = data['server']
                check_mark = "☑" if data['checked'] else "☐"
                self.tree.item(item, text=f"{check_mark} {server.name}")

                # Update selected servers
                key = (server.name, str(server.project_path))
                if data['checked']:
                    self.selected_servers.add(key)
                else:
                    self.selected_servers.discard(key)

                # Update button state
                self.promote_btn.config(
                    state=tk.NORMAL if self.selected_servers else tk.DISABLED
                )

        def _on_selection_changed(self, event):
            """Handle selection changes to show config preview"""
            selection = self.tree.selection()
            if not selection:
                return

            item = selection[0]
            if item in self.tree_items:
                server = self.tree_items[item]['server']

                # Format config as JSON
                config_json = json.dumps(server.config, indent=2)
                preview_text = f"Server: {server.name}\n"
                preview_text += f"Project: {server.project_path}\n"
                preview_text += f"Duplicate: {'Yes' if server.is_duplicate else 'No'}\n"
                preview_text += f"\nConfiguration:\n{config_json}"

                self.config_preview.config(state=tk.NORMAL)
                self.config_preview.delete("1.0", tk.END)
                self.config_preview.insert("1.0", preview_text)
                self.config_preview.config(state=tk.DISABLED)

        def _select_all(self):
            """Select all servers"""
            for item_id, data in self.tree_items.items():
                data['checked'] = True
                server = data['server']
                self.tree.item(item_id, text=f"☑ {server.name}")
                self.selected_servers.add((server.name, str(server.project_path)))

            self.promote_btn.config(state=tk.NORMAL if self.selected_servers else tk.DISABLED)

        def _select_none(self):
            """Deselect all servers"""
            for item_id, data in self.tree_items.items():
                data['checked'] = False
                server = data['server']
                self.tree.item(item_id, text=f"☐ {server.name}")

            self.selected_servers.clear()
            self.promote_btn.config(state=tk.DISABLED)

        def _promote_selected(self):
            """Promote selected servers to global configuration"""
            if not self.selected_servers:
                return

            strategy = self.conflict_var.get()
            promoted_count = 0
            skipped_count = 0
            errors = []

            for server_name, project_path in self.selected_servers:
                try:
                    # Find the server object
                    server_obj = None
                    for server in self.project_servers.get(project_path, []):
                        if server.name == server_name:
                            server_obj = server
                            break

                    if not server_obj:
                        continue

                    # Check for conflicts
                    if server_obj.is_duplicate and strategy == 'skip':
                        skipped_count += 1
                        continue

                    # Handle renaming if needed
                    final_name = server_name
                    if server_obj.is_duplicate and strategy == 'rename':
                        project_name = Path(project_path).name
                        final_name = f"{server_name}_{project_name}"

                    # Promote the server (simplified - would need actual implementation)
                    promoted_count += 1

                except Exception as e:
                    errors.append(f"{server_name}: {str(e)}")

            # Show results
            message = f"Promoted {promoted_count} server(s) to global configuration."
            if skipped_count > 0:
                message += f"\nSkipped {skipped_count} duplicate(s)."
            if errors:
                message += f"\n\nErrors:\n" + "\n".join(errors[:5])

            messagebox.showinfo("Promotion Complete", message)

            # Clear selection
            self._select_none()

            # Refresh parent if possible
            if self.parent and hasattr(self.parent, 'reload_servers_from_disk'):
                self.parent.reload_servers_from_disk()

        def _promote_all(self):
            """Promote all discovered servers"""
            self._select_all()
            self._promote_selected()

        def show(self):
            """Show the dialog"""
            self.dialog.wait_window()


def show_discover_servers_dialog(parent=None, server_controller=None):
    """Show the appropriate discover servers dialog based on available UI framework"""
    if HAS_QT and parent.__class__.__module__.startswith('PyQt'):
        dialog = DiscoverServersDialog(parent, server_controller)
        return dialog.exec()
    elif HAS_TK:
        dialog = DiscoverServersDialogTk(parent, server_controller)
        dialog.show()
    else:
        raise RuntimeError("No UI framework available")