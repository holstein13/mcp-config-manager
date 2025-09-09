"""Server details panel for viewing and editing MCP server configurations."""

from typing import Dict, Any, Optional, List, Callable
import json
import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, 
        QLabel, QPushButton, QFormLayout, QFrame,
        QMessageBox, QSizePolicy
    )
    from PyQt6.QtCore import pyqtSignal, Qt
    from PyQt6.QtGui import QPalette
    USING_QT = True
except ImportError:
    QWidget = object
    QScrollArea = None
    QVBoxLayout = None
    QHBoxLayout = None
    QLabel = None
    QPushButton = None
    QFormLayout = None
    QFrame = None
    QMessageBox = None
    QSizePolicy = None
    pyqtSignal = lambda *args: None
    Qt = None
    QPalette = None
    USING_QT = False

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    HAS_TKINTER = True
except ImportError:
    tk = None
    ttk = None
    messagebox = None
    scrolledtext = None
    HAS_TKINTER = False

from .field_editors import (
    StringEditor, NumberEditor, BooleanEditor,
    ArrayEditor, KeyValueEditor, PathEditor,
    DropdownEditor
)

logger = logging.getLogger(__name__)


class ServerDetailsPanel(QWidget if USING_QT else object):
    """Panel for displaying and editing server configuration details."""
    
    # Qt signals
    server_updated = pyqtSignal(str, dict) if USING_QT else None
    changes_pending = pyqtSignal(bool) if USING_QT else None
    
    # Required MCP fields that are always shown
    REQUIRED_FIELDS = ['command']
    
    # Optional MCP fields with their editor types
    OPTIONAL_FIELDS = {
        'args': 'array',
        'env': 'keyvalue',
        'cwd': 'path',
        'timeout': 'number',
        'capabilities': 'array',
        'trust': 'boolean',
        'disabled': 'boolean',
        'restart': 'dropdown',
        'transport': 'dropdown'
    }
    
    # Field descriptions for tooltips
    FIELD_DESCRIPTIONS = {
        'command': 'Command to execute the MCP server',
        'args': 'Command line arguments',
        'env': 'Environment variables',
        'cwd': 'Working directory',
        'timeout': 'Timeout in milliseconds',
        'capabilities': 'Server capabilities',
        'trust': 'Trust this server',
        'disabled': 'Disable this server',
        'restart': 'Restart policy (never, on-failure, always)',
        'transport': 'Transport type (stdio, http, websocket)'
    }
    
    def __init__(self, parent=None):
        """Initialize the server details panel."""
        if USING_QT:
            super().__init__(parent)
            self._init_qt_ui()
        elif HAS_TKINTER:
            self.parent = parent
            self._init_tk_ui()
        
        self.current_server = None
        self.original_data = None
        self.field_editors = {}
        self.has_changes = False
        self.validation_errors = {}
        
        # Callbacks for tkinter
        self.server_updated_callbacks = []
        self.changes_pending_callbacks = []
    
    def _init_qt_ui(self):
        """Initialize Qt UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with server name
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.Box)
        header_layout = QHBoxLayout(header_frame)
        
        self.server_label = QLabel("Select a server to edit")
        self.server_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.server_label)
        
        header_layout.addStretch()
        
        # Add field button
        self.add_field_btn = QPushButton("+ Add Field")
        self.add_field_btn.clicked.connect(self._on_add_field)
        self.add_field_btn.setEnabled(False)
        header_layout.addWidget(self.add_field_btn)
        
        layout.addWidget(header_frame)
        
        # Scrollable form area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        scroll_area.setWidget(self.form_widget)
        layout.addWidget(scroll_area, 1)
        
        # Button bar
        button_bar = QFrame()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                padding: 6px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(button_bar)
    
    def _init_tk_ui(self):
        """Initialize tkinter UI components."""
        if not self.parent:
            return
            
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.server_label = ttk.Label(header_frame, text="Select a server to edit",
                                      font=('', 12, 'bold'))
        self.server_label.pack(side=tk.LEFT)
        
        self.add_field_btn = ttk.Button(header_frame, text="+ Add Field",
                                        command=self._on_add_field, state='disabled')
        self.add_field_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Scrollable form area
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.form_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        
        self.form_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        
        # Button bar
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.save_btn = ttk.Button(button_frame, text="Save",
                                  command=self._on_save, state='disabled')
        self.save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel",
                                     command=self._on_cancel, state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT)
    
    def load_server(self, server_name: str, server_config: Dict[str, Any]):
        """Load a server configuration into the form.
        
        Args:
            server_name: Name of the server
            server_config: Server configuration dictionary
        """
        self.current_server = server_name
        self.original_data = json.loads(json.dumps(server_config))  # Deep copy
        self.has_changes = False
        self.validation_errors.clear()
        
        # Update header
        if USING_QT:
            self.server_label.setText(f"Editing: {server_name}")
            self.add_field_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        elif HAS_TKINTER:
            self.server_label.config(text=f"Editing: {server_name}")
            self.add_field_btn.config(state='normal')
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
        
        # Clear existing form
        self._clear_form()
        
        # Add required fields
        for field_name in self.REQUIRED_FIELDS:
            value = server_config.get(field_name, '')
            self._add_field_editor(field_name, 'string', value, required=True)
        
        # Add optional fields that exist in config
        for field_name, field_type in self.OPTIONAL_FIELDS.items():
            if field_name in server_config:
                value = server_config[field_name]
                self._add_field_editor(field_name, field_type, value, required=False)
        
        # Emit changes pending signal
        self._emit_changes_pending(False)
    
    def _clear_form(self):
        """Clear all field editors from the form."""
        # Remove all widgets
        for editor in self.field_editors.values():
            if USING_QT and hasattr(editor, 'deleteLater'):
                editor.deleteLater()
            elif HAS_TKINTER and hasattr(editor, 'destroy'):
                editor.frame.destroy()
        
        self.field_editors.clear()
        
        if USING_QT:
            # Clear layout
            while self.form_layout.rowCount() > 0:
                self.form_layout.removeRow(0)
        elif HAS_TKINTER:
            # Clear frame
            for widget in self.form_frame.winfo_children():
                widget.destroy()
    
    def _add_field_editor(self, field_name: str, field_type: str, 
                          value: Any, required: bool = False):
        """Add a field editor to the form.
        
        Args:
            field_name: Name of the field
            field_type: Type of editor to use
            value: Initial value
            required: Whether field is required
        """
        # Create appropriate editor
        editor = None
        
        if field_type == 'string':
            editor = StringEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'number':
            editor = NumberEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'boolean':
            editor = BooleanEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'array':
            editor = ArrayEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'keyvalue':
            editor = KeyValueEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'path':
            editor = PathEditor(self.form_widget if USING_QT else self.form_frame)
        elif field_type == 'dropdown':
            editor = DropdownEditor(self.form_widget if USING_QT else self.form_frame)
            # Set dropdown options based on field
            if field_name == 'restart':
                editor.set_options(['never', 'on-failure', 'always'])
            elif field_name == 'transport':
                editor.set_options(['stdio', 'http', 'websocket'])
        
        if editor:
            editor.set_value(value)
            editor.set_required(required)
            
            # Connect change signal
            if USING_QT:
                editor.value_changed.connect(self._on_field_changed)
                editor.validation_error.connect(lambda field, error: 
                                               self._on_validation_error(field_name, error))
            else:
                editor.add_change_callback(self._on_field_changed)
                editor.add_validation_callback(lambda error: 
                                              self._on_validation_error(field_name, error))
            
            # Add to form
            label_text = field_name.replace('_', ' ').title()
            if required:
                label_text += " *"
            
            if USING_QT:
                label = QLabel(label_text)
                if field_name in self.FIELD_DESCRIPTIONS:
                    label.setToolTip(self.FIELD_DESCRIPTIONS[field_name])
                self.form_layout.addRow(label, editor)
            elif HAS_TKINTER:
                row_frame = ttk.Frame(self.form_frame)
                row_frame.pack(fill=tk.X, pady=2)
                
                label = ttk.Label(row_frame, text=label_text, width=15)
                label.pack(side=tk.LEFT, padx=(0, 10))
                
                editor.frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.field_editors[field_name] = editor
    
    def _on_field_changed(self, value: Any = None):
        """Handle field value change."""
        if not self.current_server:
            return
        
        # Check if data has actually changed
        current_data = self.get_server_data()
        self.has_changes = current_data != self.original_data
        
        # Enable/disable save and cancel buttons
        if USING_QT:
            self.save_btn.setEnabled(self.has_changes and not self.validation_errors)
            self.cancel_btn.setEnabled(self.has_changes)
        elif HAS_TKINTER:
            state = 'normal' if self.has_changes and not self.validation_errors else 'disabled'
            self.save_btn.config(state=state)
            self.cancel_btn.config(state='normal' if self.has_changes else 'disabled')
        
        # Emit changes pending signal
        self._emit_changes_pending(self.has_changes)
    
    def _on_validation_error(self, field_name: str, error: Optional[str]):
        """Handle field validation error.
        
        Args:
            field_name: Field with error
            error: Error message or None if valid
        """
        if error:
            self.validation_errors[field_name] = error
        else:
            self.validation_errors.pop(field_name, None)
        
        # Update save button state
        if USING_QT:
            self.save_btn.setEnabled(self.has_changes and not self.validation_errors)
        elif HAS_TKINTER:
            state = 'normal' if self.has_changes and not self.validation_errors else 'disabled'
            self.save_btn.config(state=state)
    
    def _on_add_field(self):
        """Show dialog to add a new optional field."""
        from ..dialogs.add_field_dialog import show_add_field_dialog
        
        # Get list of existing fields
        existing_fields = list(self.field_editors.keys())
        
        # Show dialog
        result = show_add_field_dialog(self, existing_fields)
        
        if result:
            field_name, field_type, default_value = result
            
            # Add the field to the form
            self._add_field_editor(field_name, field_type, default_value, required=False)
            
            # Mark as changed
            self._on_field_changed()
    
    def _on_save(self):
        """Save the current server configuration."""
        if not self.current_server or not self.has_changes:
            return
        
        # Get current data
        server_data = self.get_server_data()
        
        # Emit server updated signal
        if USING_QT:
            self.server_updated.emit(self.current_server, server_data)
        else:
            for callback in self.server_updated_callbacks:
                callback(self.current_server, server_data)
        
        # Update original data
        self.original_data = json.loads(json.dumps(server_data))
        self.has_changes = False
        
        # Update UI
        if USING_QT:
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        elif HAS_TKINTER:
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
        
        self._emit_changes_pending(False)
    
    def _on_cancel(self):
        """Cancel changes and restore original data."""
        if not self.current_server or not self.has_changes:
            return
        
        # Reload original data
        self.load_server(self.current_server, self.original_data)
    
    def get_server_data(self) -> Dict[str, Any]:
        """Get the current server configuration from the form.
        
        Returns:
            Dictionary with server configuration
        """
        data = {}
        
        for field_name, editor in self.field_editors.items():
            value = editor.get_value()
            # Only include non-empty values
            if value or field_name in self.REQUIRED_FIELDS:
                data[field_name] = value
        
        return data
    
    def _emit_changes_pending(self, has_changes: bool):
        """Emit changes pending signal.
        
        Args:
            has_changes: Whether there are unsaved changes
        """
        if USING_QT:
            self.changes_pending.emit(has_changes)
        else:
            for callback in self.changes_pending_callbacks:
                callback(has_changes)
    
    def add_server_updated_callback(self, callback: Callable):
        """Add callback for server updated event (tkinter).
        
        Args:
            callback: Function to call with (server_name, server_data)
        """
        if not USING_QT:
            self.server_updated_callbacks.append(callback)
    
    def add_changes_pending_callback(self, callback: Callable):
        """Add callback for changes pending event (tkinter).
        
        Args:
            callback: Function to call with (has_changes)
        """
        if not USING_QT:
            self.changes_pending_callbacks.append(callback)
    
    def clear(self):
        """Clear the panel and show empty state."""
        self.current_server = None
        self.original_data = None
        self.has_changes = False
        self.validation_errors.clear()
        
        self._clear_form()
        
        if USING_QT:
            self.server_label.setText("Select a server to edit")
            self.add_field_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        elif HAS_TKINTER:
            self.server_label.config(text="Select a server to edit")
            self.add_field_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
        
        self._emit_changes_pending(False)


class TkinterServerDetailsPanel:
    """Tkinter wrapper for ServerDetailsPanel compatibility."""
    
    def __init__(self, parent):
        """Initialize the tkinter server details panel."""
        self.panel = ServerDetailsPanel(parent)
        self.frame = self.panel.frame if hasattr(self.panel, 'frame') else ttk.Frame(parent)
    
    def load_server(self, server_name: str, server_config: Dict[str, Any]):
        """Load server configuration."""
        self.panel.load_server(server_name, server_config)
    
    def get_server_data(self) -> Dict[str, Any]:
        """Get current server data."""
        return self.panel.get_server_data()
    
    def clear(self):
        """Clear the panel."""
        self.panel.clear()
    
    def add_server_updated_callback(self, callback):
        """Add server updated callback."""
        self.panel.add_server_updated_callback(callback)
    
    def add_changes_pending_callback(self, callback):
        """Add changes pending callback."""
        self.panel.add_changes_pending_callback(callback)