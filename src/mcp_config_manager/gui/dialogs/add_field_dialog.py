"""Dialog for adding optional MCP fields to a server configuration."""

from typing import Optional, Tuple, Dict, Any
import logging

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QComboBox, QDialogButtonBox,
        QFormLayout, QFrame
    )
    from PyQt6.QtCore import Qt
    USING_QT = True
except ImportError:
    QDialog = object
    QVBoxLayout = None
    QHBoxLayout = None
    QLabel = None
    QPushButton = None
    QComboBox = None
    QDialogButtonBox = None
    QFormLayout = None
    QFrame = None
    Qt = None
    USING_QT = False

try:
    import tkinter as tk
    from tkinter import ttk, simpledialog
    HAS_TKINTER = True
except ImportError:
    tk = None
    ttk = None
    simpledialog = None
    HAS_TKINTER = False

logger = logging.getLogger(__name__)


class AddFieldDialog(QDialog if USING_QT else object):
    """Dialog for selecting and adding optional MCP fields."""
    
    # Available MCP fields with their types and descriptions
    AVAILABLE_FIELDS = {
        'args': {
            'type': 'array',
            'description': 'Command line arguments for the server',
            'default': []
        },
        'env': {
            'type': 'keyvalue',
            'description': 'Environment variables for the server process',
            'default': {}
        },
        'cwd': {
            'type': 'path',
            'description': 'Working directory for the server process',
            'default': ''
        },
        'timeout': {
            'type': 'number',
            'description': 'Timeout in milliseconds for server operations',
            'default': 30000
        },
        'capabilities': {
            'type': 'array',
            'description': 'List of server capabilities',
            'default': []
        },
        'trust': {
            'type': 'boolean',
            'description': 'Whether to trust this server',
            'default': False
        },
        'disabled': {
            'type': 'boolean',
            'description': 'Whether this server is disabled',
            'default': False
        },
        'restart': {
            'type': 'dropdown',
            'description': 'Restart policy for the server',
            'default': 'never',
            'options': ['never', 'on-failure', 'always']
        },
        'transport': {
            'type': 'dropdown',
            'description': 'Transport protocol for communication',
            'default': 'stdio',
            'options': ['stdio', 'http', 'websocket']
        },
        'type': {
            'type': 'dropdown',
            'description': 'Server type (stdio, sse, http)',
            'default': 'stdio',
            'options': ['stdio', 'sse', 'http']
        },
        'url': {
            'type': 'string',
            'description': 'Server URL (for SSE/HTTP servers)',
            'default': ''
        }
    }
    
    def __init__(self, parent=None, existing_fields=None):
        """Initialize the add field dialog.
        
        Args:
            parent: Parent widget
            existing_fields: List of field names already in use
        """
        if USING_QT:
            super().__init__(parent)
            self.setWindowTitle("Add Field")
            self.setModal(True)
            self.setMinimumWidth(400)
            self._init_qt_ui()
        elif HAS_TKINTER:
            self.parent = parent
            self.result = None
            self._init_tk_ui()
        
        self.existing_fields = existing_fields or []
        self.selected_field = None
        self.selected_type = None
        self.selected_default = None
        
        # Populate available fields
        self._populate_fields()
    
    def _init_qt_ui(self):
        """Initialize Qt UI components."""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel("Select an optional field to add to the server configuration:")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Form layout for field selection
        form_layout = QFormLayout()
        
        # Field combo box
        self.field_combo = QComboBox()
        self.field_combo.currentTextChanged.connect(self._on_field_selected)
        form_layout.addRow("Field:", self.field_combo)
        
        # Field type label
        self.type_label = QLabel("")
        self.type_label.setStyleSheet("color: #666;")
        form_layout.addRow("Type:", self.type_label)
        
        # Field description
        self.desc_frame = QFrame()
        self.desc_frame.setFrameStyle(QFrame.Shape.Box)
        self.desc_frame.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        self.desc_frame.setMinimumHeight(60)  # Ensure enough height for wrapped text
        desc_layout = QVBoxLayout(self.desc_frame)
        desc_layout.setContentsMargins(5, 5, 5, 5)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #333;")
        self.desc_label.setMinimumWidth(350)  # Ensure label has width for proper wrapping
        desc_layout.addWidget(self.desc_label)
        
        form_layout.addRow("Description:", self.desc_frame)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
    
    def _init_tk_ui(self):
        """Initialize tkinter UI components."""
        if not self.parent:
            return
        
        # Create top-level window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Field")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Select an optional field to add to the server configuration:",
                              wraplength=380)
        desc_label.pack(pady=(0, 10))
        
        # Field selection frame
        field_frame = ttk.LabelFrame(main_frame, text="Field Selection", padding="10")
        field_frame.pack(fill=tk.BOTH, expand=True)
        
        # Field combo
        ttk.Label(field_frame, text="Field:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.field_var = tk.StringVar()
        self.field_combo = ttk.Combobox(field_frame, textvariable=self.field_var,
                                        state='readonly', width=30)
        self.field_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.field_combo.bind('<<ComboboxSelected>>', self._on_field_selected_tk)
        
        # Type label
        ttk.Label(field_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_label = ttk.Label(field_frame, text="", foreground="gray")
        self.type_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Description
        ttk.Label(field_frame, text="Description:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.desc_label = ttk.Label(field_frame, text="", wraplength=250,
                                    background="#f0f0f0", relief=tk.SOLID, borderwidth=1)
        self.desc_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, pady=(10, 0))
        
        self.ok_button = ttk.Button(button_frame, text="OK", 
                                    command=self._on_ok_tk, state='disabled')
        self.ok_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_cancel_tk).pack(side=tk.LEFT)
    
    def _populate_fields(self):
        """Populate the field combo box with available fields."""
        available = []
        for field_name in self.AVAILABLE_FIELDS:
            if field_name not in self.existing_fields:
                available.append(field_name)
        
        if USING_QT:
            self.field_combo.clear()
            if available:
                self.field_combo.addItem("-- Select a field --")
                self.field_combo.addItems(available)
            else:
                self.field_combo.addItem("(No fields available)")
                self.ok_button.setEnabled(False)
        elif HAS_TKINTER:
            if available:
                values = ["-- Select a field --"] + available
                self.field_combo['values'] = values
                self.field_combo.current(0)
            else:
                self.field_combo['values'] = ["(No fields available)"]
                self.field_combo.current(0)
                self.ok_button.config(state='disabled')
    
    def _on_field_selected(self, field_name: str):
        """Handle field selection in Qt.
        
        Args:
            field_name: Selected field name
        """
        if not USING_QT:
            return
        
        if field_name.startswith("--") or field_name.startswith("("):
            self.selected_field = None
            self.type_label.setText("")
            self.desc_label.setText("")
            self.ok_button.setEnabled(False)
        else:
            self.selected_field = field_name
            field_info = self.AVAILABLE_FIELDS.get(field_name, {})
            self.selected_type = field_info.get('type', 'string')
            self.selected_default = field_info.get('default')
            
            self.type_label.setText(self.selected_type)
            self.desc_label.setText(field_info.get('description', ''))
            self.ok_button.setEnabled(True)
    
    def _on_field_selected_tk(self, event=None):
        """Handle field selection in tkinter."""
        if not HAS_TKINTER:
            return
        
        field_name = self.field_var.get()
        
        if field_name.startswith("--") or field_name.startswith("("):
            self.selected_field = None
            self.type_label.config(text="")
            self.desc_label.config(text="")
            self.ok_button.config(state='disabled')
        else:
            self.selected_field = field_name
            field_info = self.AVAILABLE_FIELDS.get(field_name, {})
            self.selected_type = field_info.get('type', 'string')
            self.selected_default = field_info.get('default')
            
            self.type_label.config(text=self.selected_type)
            self.desc_label.config(text=field_info.get('description', ''))
            self.ok_button.config(state='normal')
    
    def _on_ok_tk(self):
        """Handle OK button in tkinter."""
        if self.selected_field:
            self.result = (self.selected_field, self.selected_type, self.selected_default)
            self.dialog.destroy()
    
    def _on_cancel_tk(self):
        """Handle Cancel button in tkinter."""
        self.result = None
        self.dialog.destroy()
    
    def get_selected_field(self) -> Optional[Tuple[str, str, Any]]:
        """Get the selected field information.
        
        Returns:
            Tuple of (field_name, field_type, default_value) or None if cancelled
        """
        if USING_QT:
            if self.exec() == QDialog.DialogCode.Accepted and self.selected_field:
                return (self.selected_field, self.selected_type, self.selected_default)
        elif HAS_TKINTER:
            # Wait for dialog to close
            if hasattr(self, 'dialog'):
                self.dialog.wait_window()
                return self.result
        
        return None


class TkinterAddFieldDialog:
    """Tkinter wrapper for AddFieldDialog compatibility."""
    
    def __init__(self, parent, existing_fields=None):
        """Initialize the tkinter add field dialog.
        
        Args:
            parent: Parent widget
            existing_fields: List of field names already in use
        """
        self.dialog = AddFieldDialog(parent, existing_fields)
    
    def get_selected_field(self) -> Optional[Tuple[str, str, Any]]:
        """Get the selected field information.
        
        Returns:
            Tuple of (field_name, field_type, default_value) or None if cancelled
        """
        return self.dialog.get_selected_field()


def show_add_field_dialog(parent, existing_fields=None) -> Optional[Tuple[str, str, Any]]:
    """Show the add field dialog and return the selected field.
    
    Args:
        parent: Parent widget
        existing_fields: List of field names already in use
    
    Returns:
        Tuple of (field_name, field_type, default_value) or None if cancelled
    """
    if USING_QT:
        dialog = AddFieldDialog(parent, existing_fields)
        return dialog.get_selected_field()
    elif HAS_TKINTER:
        dialog = TkinterAddFieldDialog(parent, existing_fields)
        return dialog.get_selected_field()
    
    return None