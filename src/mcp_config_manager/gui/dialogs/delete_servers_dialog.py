"""Dialog for selecting and deleting multiple servers."""

from typing import Optional, List, Dict

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
        QListWidgetItem, QPushButton, QLabel, QMessageBox
    )
    from PyQt6.QtCore import Qt
    USING_QT = True
    HAS_TKINTER = False
except ImportError:
    USING_QT = False
    HAS_TKINTER = False
    QDialog = object
    QVBoxLayout = object
    QHBoxLayout = object
    QListWidget = object
    QListWidgetItem = object
    QPushButton = object
    QLabel = object
    QMessageBox = object
    Qt = None
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        HAS_TKINTER = True
    except ImportError:
        tk = None
        ttk = None
        messagebox = None
        HAS_TKINTER = False


class DeleteServersDialog(QDialog if USING_QT else object):
    """Dialog for selecting and deleting multiple servers."""
    
    def __init__(self, parent=None, servers: Dict[str, Dict] = None):
        """Initialize the delete servers dialog."""
        self.servers = servers or {}
        self.selected_servers = []
        
        if USING_QT:
            super().__init__(parent)
            self._setup_qt_dialog()
        elif HAS_TKINTER:
            self.root = tk.Toplevel(parent)
            self._setup_tk_dialog()
        else:
            raise RuntimeError("No GUI framework available")
    
    def _setup_qt_dialog(self):
        """Set up Qt dialog."""
        self.setWindowTitle("Delete Servers")
        self.setModal(True)
        self.resize(400, 500)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Instructions
        instructions = QLabel("Select servers to delete:")
        layout.addWidget(instructions)
        
        # Server list with checkboxes
        self.server_list = QListWidget()
        self.server_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Add servers to list
        for server_name in sorted(self.servers.keys()):
            item = QListWidgetItem(server_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.server_list.addItem(item)
        
        layout.addWidget(self.server_list)
        
        # Select/Deselect all buttons
        select_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(self.deselect_all_btn)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # Warning label
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.warning_label)
        
        # Button box
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Connect item changed signal to update warning
        self.server_list.itemChanged.connect(self._update_warning)
    
    def _setup_tk_dialog(self):
        """Set up tkinter dialog."""
        self.root.title("Delete Servers")
        self.root.transient(self.root.master)
        self.root.grab_set()
        self.root.geometry("400x500")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = ttk.Label(main_frame, text="Select servers to delete:")
        instructions.pack(anchor=tk.W, pady=(0, 5))
        
        # Server list frame with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox with checkboxes (simulated)
        self.server_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                                         yscrollcommand=scrollbar.set)
        self.server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.server_listbox.yview)
        
        # Add servers to listbox
        for server_name in sorted(self.servers.keys()):
            self.server_listbox.insert(tk.END, server_name)
        
        # Select/Deselect buttons
        select_frame = ttk.Frame(main_frame)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(select_frame, text="Select All",
                  command=self._select_all_tk).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="Deselect All",
                  command=self._deselect_all_tk).pack(side=tk.LEFT)
        
        # Warning label
        self.warning_var = tk.StringVar()
        self.warning_label = ttk.Label(main_frame, textvariable=self.warning_var,
                                      foreground="red", font=("", 10, "bold"))
        self.warning_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel",
                  command=self.root.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        delete_btn = ttk.Button(button_frame, text="Delete",
                               command=self._on_delete_tk)
        delete_btn.pack(side=tk.RIGHT)
        
        # Bind selection change
        self.server_listbox.bind("<<ListboxSelect>>", self._update_warning_tk)
    
    def _select_all(self):
        """Select all servers (Qt)."""
        for i in range(self.server_list.count()):
            item = self.server_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def _deselect_all(self):
        """Deselect all servers (Qt)."""
        for i in range(self.server_list.count()):
            item = self.server_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def _select_all_tk(self):
        """Select all servers (tkinter)."""
        self.server_listbox.select_set(0, tk.END)
        self._update_warning_tk()
    
    def _deselect_all_tk(self):
        """Deselect all servers (tkinter)."""
        self.server_listbox.select_clear(0, tk.END)
        self._update_warning_tk()
    
    def _update_warning(self, item=None):
        """Update warning label based on selection (Qt)."""
        checked_count = 0
        for i in range(self.server_list.count()):
            if self.server_list.item(i).checkState() == Qt.CheckState.Checked:
                checked_count += 1
        
        if checked_count > 0:
            self.warning_label.setText(f"⚠️ {checked_count} server(s) will be permanently deleted")
        else:
            self.warning_label.setText("")
    
    def _update_warning_tk(self, event=None):
        """Update warning label based on selection (tkinter)."""
        selected = self.server_listbox.curselection()
        if selected:
            self.warning_var.set(f"⚠️ {len(selected)} server(s) will be permanently deleted")
        else:
            self.warning_var.set("")
    
    def _on_delete(self):
        """Handle delete button click (Qt)."""
        # Get selected servers
        self.selected_servers = []
        for i in range(self.server_list.count()):
            item = self.server_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_servers.append(item.text())
        
        if not self.selected_servers:
            QMessageBox.warning(self, "No Selection",
                               "Please select at least one server to delete.")
            return
        
        # Confirm deletion
        server_list = "\n".join(f"• {s}" for s in self.selected_servers)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete these servers?\n\n{server_list}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def _on_delete_tk(self):
        """Handle delete button click (tkinter)."""
        # Get selected servers
        selected_indices = self.server_listbox.curselection()
        self.selected_servers = [self.server_listbox.get(i) for i in selected_indices]
        
        if not self.selected_servers:
            messagebox.showwarning("No Selection",
                                 "Please select at least one server to delete.")
            return
        
        # Confirm deletion
        server_list = "\n".join(f"• {s}" for s in self.selected_servers)
        if messagebox.askyesno("Confirm Deletion",
                              f"Are you sure you want to permanently delete these servers?\n\n{server_list}"):
            self.root.destroy()
    
    def get_selected_servers(self) -> List[str]:
        """Get the list of servers selected for deletion."""
        return self.selected_servers
    
    def exec(self):
        """Execute dialog (Qt compatibility)."""
        if USING_QT:
            return super().exec()
        else:
            self.root.wait_window()
            return bool(self.selected_servers)
    
    def show(self):
        """Show dialog (tkinter compatibility)."""
        if not USING_QT:
            self.root.wait_window()
            return bool(self.selected_servers)
        return False