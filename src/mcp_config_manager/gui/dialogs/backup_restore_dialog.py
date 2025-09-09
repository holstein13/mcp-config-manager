"""Dialog for backup and restore operations."""

from typing import List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QDialogButtonBox, QMessageBox, QGroupBox,
        QLabel, QSplitter, QHeaderView
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    USING_QT = False


@dataclass
class BackupItem:
    """Information about a backup."""
    filename: str
    timestamp: datetime
    size_bytes: int
    server_count: int
    mode: str  # Claude, Gemini, Both
    is_auto: bool = False


class BackupRestoreDialog:
    """Dialog for managing backups and restore operations."""
    
    def __init__(self, parent=None):
        """Initialize the Backup/Restore dialog.
        
        Args:
            parent: Parent widget/window
        """
        self.parent = parent
        self.backups: List[BackupItem] = []
        self.selected_backup: Optional[BackupItem] = None
        self.on_backup_created_callbacks = []
        self.on_backup_restored_callbacks = []
        self.on_backup_deleted_callbacks = []
        
        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("Backup & Restore")
        self.dialog.setModal(True)
        self.dialog.resize(800, 500)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Top buttons
        top_button_layout = QHBoxLayout()
        
        self.create_backup_btn = QPushButton("Create Backup")
        self.create_backup_btn.clicked.connect(self._on_qt_create_backup)
        top_button_layout.addWidget(self.create_backup_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_backup_list)
        top_button_layout.addWidget(self.refresh_btn)
        
        top_button_layout.addStretch()
        
        layout.addLayout(top_button_layout)
        
        # Backup list table
        list_group = QGroupBox("Available Backups")
        list_layout = QVBoxLayout()
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels([
            "Timestamp", "Mode", "Servers", "Size", "Type"
        ])
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.itemSelectionChanged.connect(self._on_qt_selection_changed)
        
        list_layout.addWidget(self.backup_table)
        
        # Action buttons
        action_button_layout = QHBoxLayout()
        
        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.clicked.connect(self._on_qt_restore_backup)
        self.restore_btn.setEnabled(False)
        action_button_layout.addWidget(self.restore_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._on_qt_delete_backup)
        self.delete_btn.setEnabled(False)
        action_button_layout.addWidget(self.delete_btn)
        
        self.delete_old_btn = QPushButton("Delete Old Backups...")
        self.delete_old_btn.clicked.connect(self._on_qt_delete_old_backups)
        action_button_layout.addWidget(self.delete_old_btn)
        
        action_button_layout.addStretch()
        
        list_layout.addLayout(action_button_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.dialog.reject)
        layout.addWidget(button_box)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Backup & Restore")
        self.dialog.geometry("800x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top buttons
        top_button_frame = ttk.Frame(main_frame)
        top_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_backup_btn = ttk.Button(
            top_button_frame,
            text="Create Backup",
            command=self._on_tk_create_backup
        )
        self.create_backup_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(
            top_button_frame,
            text="Refresh",
            command=self._refresh_backup_list
        )
        self.refresh_btn.pack(side=tk.LEFT)
        
        # Backup list
        list_frame = ttk.LabelFrame(main_frame, text="Available Backups", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for table
        columns = ("Mode", "Servers", "Size", "Type")
        self.backup_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.backup_tree.heading("#0", text="Timestamp")
        self.backup_tree.column("#0", width=200)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=100)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.backup_tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.backup_tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.backup_tree.configure(xscrollcommand=hsb.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.backup_tree.bind("<<TreeviewSelect>>", self._on_tk_selection_changed)
        
        # Action buttons
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.restore_btn = ttk.Button(
            action_button_frame,
            text="Restore Selected",
            command=self._on_tk_restore_backup,
            state=tk.DISABLED
        )
        self.restore_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(
            action_button_frame,
            text="Delete Selected",
            command=self._on_tk_delete_backup,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_old_btn = ttk.Button(
            action_button_frame,
            text="Delete Old Backups...",
            command=self._on_tk_delete_old_backups
        )
        self.delete_old_btn.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=(10, 0))
        
        # Dialog buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT)
    
    def set_backups(self, backups: List[BackupItem]):
        """Set the list of available backups.
        
        Args:
            backups: List of backup items
        """
        self.backups = sorted(backups, key=lambda b: b.timestamp, reverse=True)
        self._refresh_backup_list()
    
    def _refresh_backup_list(self):
        """Refresh the backup list display."""
        if USING_QT:
            self.backup_table.setRowCount(len(self.backups))
            
            for row, backup in enumerate(self.backups):
                # Timestamp
                timestamp_item = QTableWidgetItem(
                    backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )
                self.backup_table.setItem(row, 0, timestamp_item)
                
                # Mode
                mode_item = QTableWidgetItem(backup.mode)
                self.backup_table.setItem(row, 1, mode_item)
                
                # Server count
                servers_item = QTableWidgetItem(str(backup.server_count))
                self.backup_table.setItem(row, 2, servers_item)
                
                # Size
                size_str = self._format_size(backup.size_bytes)
                size_item = QTableWidgetItem(size_str)
                self.backup_table.setItem(row, 3, size_item)
                
                # Type
                type_item = QTableWidgetItem("Auto" if backup.is_auto else "Manual")
                self.backup_table.setItem(row, 4, type_item)
            
            # Update status
            self.status_label.setText(f"Total backups: {len(self.backups)}")
        else:
            # Clear existing items
            for item in self.backup_tree.get_children():
                self.backup_tree.delete(item)
            
            # Add backups
            for backup in self.backups:
                timestamp_str = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                size_str = self._format_size(backup.size_bytes)
                type_str = "Auto" if backup.is_auto else "Manual"
                
                self.backup_tree.insert(
                    "",
                    "end",
                    text=timestamp_str,
                    values=(backup.mode, backup.server_count, size_str, type_str),
                    tags=(backup.filename,)
                )
            
            # Update status
            self.status_label.config(text=f"Total backups: {len(self.backups)}")
    
    def _format_size(self, bytes_size: int) -> str:
        """Format size in bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def _on_qt_selection_changed(self):
        """Handle selection change in Qt version."""
        selected_rows = self.backup_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.selected_backup = self.backups[row]
            self.restore_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.selected_backup = None
            self.restore_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def _on_tk_selection_changed(self, event):
        """Handle selection change in tkinter version."""
        selection = self.backup_tree.selection()
        if selection:
            item = self.backup_tree.item(selection[0])
            # Find backup by filename stored in tags
            if item['tags']:
                filename = item['tags'][0]
                self.selected_backup = next(
                    (b for b in self.backups if b.filename == filename),
                    None
                )
                if self.selected_backup:
                    self.restore_btn.config(state=tk.NORMAL)
                    self.delete_btn.config(state=tk.NORMAL)
                    return
        
        self.selected_backup = None
        self.restore_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
    
    def _on_qt_create_backup(self):
        """Handle create backup in Qt version."""
        reply = QMessageBox.question(
            self.dialog,
            "Create Backup",
            "Create a backup of the current configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for callback in self.on_backup_created_callbacks:
                callback()
            
            QMessageBox.information(
                self.dialog,
                "Backup Created",
                "Backup has been created successfully."
            )
            
            # Refresh the list
            self._refresh_backup_list()
    
    def _on_tk_create_backup(self):
        """Handle create backup in tkinter version."""
        result = messagebox.askyesno(
            "Create Backup",
            "Create a backup of the current configuration?"
        )
        
        if result:
            for callback in self.on_backup_created_callbacks:
                callback()
            
            messagebox.showinfo(
                "Backup Created",
                "Backup has been created successfully."
            )
            
            # Refresh the list
            self._refresh_backup_list()
    
    def _on_qt_restore_backup(self):
        """Handle restore backup in Qt version."""
        if self.selected_backup:
            reply = QMessageBox.question(
                self.dialog,
                "Restore Backup",
                f"Restore configuration from backup?\n\n"
                f"Timestamp: {self.selected_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Mode: {self.selected_backup.mode}\n"
                f"Servers: {self.selected_backup.server_count}\n\n"
                f"This will replace your current configuration.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for callback in self.on_backup_restored_callbacks:
                    callback(self.selected_backup.filename)
                
                QMessageBox.information(
                    self.dialog,
                    "Backup Restored",
                    "Configuration has been restored from backup."
                )
                
                self.dialog.accept()
    
    def _on_tk_restore_backup(self):
        """Handle restore backup in tkinter version."""
        if self.selected_backup:
            message = (
                f"Restore configuration from backup?\n\n"
                f"Timestamp: {self.selected_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Mode: {self.selected_backup.mode}\n"
                f"Servers: {self.selected_backup.server_count}\n\n"
                f"This will replace your current configuration."
            )
            
            result = messagebox.askyesno("Restore Backup", message)
            
            if result:
                for callback in self.on_backup_restored_callbacks:
                    callback(self.selected_backup.filename)
                
                messagebox.showinfo(
                    "Backup Restored",
                    "Configuration has been restored from backup."
                )
                
                self.dialog.destroy()
    
    def _on_qt_delete_backup(self):
        """Handle delete backup in Qt version."""
        if self.selected_backup:
            reply = QMessageBox.question(
                self.dialog,
                "Delete Backup",
                f"Delete this backup?\n\n"
                f"Timestamp: {self.selected_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for callback in self.on_backup_deleted_callbacks:
                    callback(self.selected_backup.filename)
                
                # Remove from list
                self.backups = [b for b in self.backups if b.filename != self.selected_backup.filename]
                self._refresh_backup_list()
    
    def _on_tk_delete_backup(self):
        """Handle delete backup in tkinter version."""
        if self.selected_backup:
            message = (
                f"Delete this backup?\n\n"
                f"Timestamp: {self.selected_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"This action cannot be undone."
            )
            
            result = messagebox.askyesno("Delete Backup", message)
            
            if result:
                for callback in self.on_backup_deleted_callbacks:
                    callback(self.selected_backup.filename)
                
                # Remove from list
                self.backups = [b for b in self.backups if b.filename != self.selected_backup.filename]
                self._refresh_backup_list()
    
    def _on_qt_delete_old_backups(self):
        """Handle delete old backups in Qt version."""
        # Simple dialog to get days
        from PyQt6.QtWidgets import QInputDialog
        
        days, ok = QInputDialog.getInt(
            self.dialog,
            "Delete Old Backups",
            "Delete backups older than (days):",
            value=30,
            min=1,
            max=365
        )
        
        if ok:
            cutoff_date = datetime.now().timestamp() - (days * 86400)
            old_backups = [b for b in self.backups if b.timestamp.timestamp() < cutoff_date]
            
            if old_backups:
                reply = QMessageBox.question(
                    self.dialog,
                    "Delete Old Backups",
                    f"Delete {len(old_backups)} backups older than {days} days?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    for backup in old_backups:
                        for callback in self.on_backup_deleted_callbacks:
                            callback(backup.filename)
                    
                    self.backups = [b for b in self.backups if b not in old_backups]
                    self._refresh_backup_list()
                    
                    QMessageBox.information(
                        self.dialog,
                        "Backups Deleted",
                        f"Deleted {len(old_backups)} old backups."
                    )
            else:
                QMessageBox.information(
                    self.dialog,
                    "No Old Backups",
                    f"No backups older than {days} days found."
                )
    
    def _on_tk_delete_old_backups(self):
        """Handle delete old backups in tkinter version."""
        from tkinter import simpledialog
        
        days = simpledialog.askinteger(
            "Delete Old Backups",
            "Delete backups older than (days):",
            parent=self.dialog,
            minvalue=1,
            maxvalue=365,
            initialvalue=30
        )
        
        if days:
            cutoff_date = datetime.now().timestamp() - (days * 86400)
            old_backups = [b for b in self.backups if b.timestamp.timestamp() < cutoff_date]
            
            if old_backups:
                result = messagebox.askyesno(
                    "Delete Old Backups",
                    f"Delete {len(old_backups)} backups older than {days} days?"
                )
                
                if result:
                    for backup in old_backups:
                        for callback in self.on_backup_deleted_callbacks:
                            callback(backup.filename)
                    
                    self.backups = [b for b in self.backups if b not in old_backups]
                    self._refresh_backup_list()
                    
                    messagebox.showinfo(
                        "Backups Deleted",
                        f"Deleted {len(old_backups)} old backups."
                    )
            else:
                messagebox.showinfo(
                    "No Old Backups",
                    f"No backups older than {days} days found."
                )
    
    def on_backup_created(self, callback: Callable[[], None]):
        """Register callback for backup creation.
        
        Args:
            callback: Function to call when backup is created
        """
        self.on_backup_created_callbacks.append(callback)
    
    def on_backup_restored(self, callback: Callable[[str], None]):
        """Register callback for backup restoration.
        
        Args:
            callback: Function to call with backup filename
        """
        self.on_backup_restored_callbacks.append(callback)
    
    def on_backup_deleted(self, callback: Callable[[str], None]):
        """Register callback for backup deletion.
        
        Args:
            callback: Function to call with backup filename
        """
        self.on_backup_deleted_callbacks.append(callback)
    
    def show(self):
        """Show the dialog."""
        if USING_QT:
            self.dialog.exec()
        else:
            self.dialog.wait_window()