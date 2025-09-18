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
    server_deleted = pyqtSignal(str, bool) if USING_QT else None  # Added bool for is_disabled
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
        self.current_server_disabled = False  # Track if current server is disabled
        self.original_data = None
        self.field_editors = {}
        self.has_changes = False
        self.validation_errors = {}
        self.claude_enabled = False  # Track per-client enablement
        self.gemini_enabled = False
        self.codex_enabled = False

        # Callbacks for tkinter
        self.server_updated_callbacks = []
        self.server_deleted_callbacks = []
        self.changes_pending_callbacks = []
        self.client_enablement_changed_callbacks = []  # New callback for client enablement
    
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

        # Add client enablement checkboxes
        from PyQt6.QtWidgets import QCheckBox

        enablement_label = QLabel("Enabled for:")
        header_layout.addWidget(enablement_label)

        self.claude_checkbox = QCheckBox("Claude")
        self.claude_checkbox.setEnabled(False)
        self.claude_checkbox.stateChanged.connect(self._on_client_enablement_changed)
        header_layout.addWidget(self.claude_checkbox)

        self.gemini_checkbox = QCheckBox("Gemini")
        self.gemini_checkbox.setEnabled(False)
        self.gemini_checkbox.stateChanged.connect(self._on_client_enablement_changed)
        header_layout.addWidget(self.gemini_checkbox)

        self.codex_checkbox = QCheckBox("Codex")
        self.codex_checkbox.setEnabled(False)
        self.codex_checkbox.stateChanged.connect(self._on_client_enablement_changed)
        header_layout.addWidget(self.codex_checkbox)

        # Add field button
        self.add_field_btn = QPushButton("+ Add Field")
        self.add_field_btn.clicked.connect(self._on_add_field)
        self.add_field_btn.setEnabled(False)
        header_layout.addWidget(self.add_field_btn)

        layout.addWidget(header_frame)
        
        # Create a stacked widget for empty state and form
        from PyQt6.QtWidgets import QStackedWidget
        self.stacked_widget = QStackedWidget()
        
        # Empty state widget
        self.empty_state_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_state_widget)
        empty_layout.addStretch()
        
        empty_label = QLabel("👈 Select a server from the list to edit its configuration")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                padding: 20px;
            }
        """)
        empty_layout.addWidget(empty_label)
        
        tip_label = QLabel("💡 Tip: You can use Ctrl+S to save changes and Esc to cancel")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 13px;
                padding: 10px;
            }
        """)
        empty_layout.addWidget(tip_label)
        empty_layout.addStretch()
        
        # Scrollable form area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        scroll_area.setWidget(self.form_widget)
        
        # Add both to stacked widget
        self.stacked_widget.addWidget(self.empty_state_widget)
        self.stacked_widget.addWidget(scroll_area)
        self.stacked_widget.setCurrentWidget(self.empty_state_widget)
        
        layout.addWidget(self.stacked_widget, 1)
        
        # Button bar
        button_bar = QFrame()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        # Delete button on the left
        self.delete_btn = QPushButton("Delete Server")
        self.delete_btn.setDefault(False)
        self.delete_btn.setAutoDefault(False)
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        # Explicitly set to non-default button to prevent macOS blue styling
        self.save_btn.setDefault(False)
        self.save_btn.setAutoDefault(False)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(button_bar)
        
        # Add keyboard shortcuts
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+S or Cmd+S for save
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(lambda: self._on_save() if self.save_btn.isEnabled() else None)
        
        # Escape for cancel
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(lambda: self._on_cancel() if self.cancel_btn.isEnabled() else None)
    
    def _update_save_button_style(self, has_changes: bool):
        """Update save button style based on whether there are unsaved changes."""
        if USING_QT:
            if has_changes:
                # Green style when there are unsaved changes
                self.save_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28A745;
                        color: white;
                        padding: 6px 20px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                    QPushButton:disabled {
                        background-color: #CCCCCC;
                    }
                """)
            else:
                # Clear custom styles - let Qt use native styling
                self.save_btn.setStyleSheet("")
    
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

        # Add client enablement checkboxes
        enablement_frame = ttk.Frame(header_frame)
        enablement_frame.pack(side=tk.LEFT, padx=(20, 0))

        ttk.Label(enablement_frame, text="Enabled for:").pack(side=tk.LEFT)

        self.claude_var = tk.BooleanVar()
        self.claude_checkbox = ttk.Checkbutton(enablement_frame, text="Claude",
                                               variable=self.claude_var,
                                               command=self._on_client_enablement_changed,
                                               state='disabled')
        self.claude_checkbox.pack(side=tk.LEFT, padx=(5, 0))

        self.gemini_var = tk.BooleanVar()
        self.gemini_checkbox = ttk.Checkbutton(enablement_frame, text="Gemini",
                                               variable=self.gemini_var,
                                               command=self._on_client_enablement_changed,
                                               state='disabled')
        self.gemini_checkbox.pack(side=tk.LEFT, padx=(5, 0))

        self.codex_var = tk.BooleanVar()
        self.codex_checkbox = ttk.Checkbutton(enablement_frame, text="Codex",
                                              variable=self.codex_var,
                                              command=self._on_client_enablement_changed,
                                              state='disabled')
        self.codex_checkbox.pack(side=tk.LEFT, padx=(5, 0))

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
    
    def load_server(self, server_name: str, server_config: Dict[str, Any], is_disabled: bool = False,
                   claude_enabled: bool = True, gemini_enabled: bool = True, codex_enabled: bool = True):
        """Load a server configuration into the form.

        Args:
            server_name: Name of the server
            server_config: Server configuration dictionary
            is_disabled: Whether the server is currently disabled
            claude_enabled: Whether the server is enabled for Claude
            gemini_enabled: Whether the server is enabled for Gemini
            codex_enabled: Whether the server is enabled for Codex
        """
        self.current_server = server_name
        self.current_server_disabled = is_disabled  # Store disabled state
        self.original_data = json.loads(json.dumps(server_config))  # Deep copy
        self.claude_enabled = claude_enabled
        self.gemini_enabled = gemini_enabled
        self.codex_enabled = codex_enabled
        self.has_changes = False
        self.validation_errors.clear()

        # Update header
        if USING_QT:
            self.server_label.setText(f"Editing: {server_name}")
            self.add_field_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)  # Enable delete button
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self._update_save_button_style(False)  # Clear any custom styles

            # Update client checkboxes
            self.claude_checkbox.setEnabled(True)
            self.gemini_checkbox.setEnabled(True)
            self.codex_checkbox.setEnabled(True)
            self.claude_checkbox.setChecked(claude_enabled)
            self.gemini_checkbox.setChecked(gemini_enabled)
            self.codex_checkbox.setChecked(codex_enabled)

            # Switch to form view
            self.stacked_widget.setCurrentIndex(1)  # Show the form
        elif HAS_TKINTER:
            self.server_label.config(text=f"Editing: {server_name}")
            self.add_field_btn.config(state='normal')
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')

            # Update client checkboxes
            self.claude_checkbox.config(state='normal')
            self.gemini_checkbox.config(state='normal')
            self.codex_checkbox.config(state='normal')
            self.claude_var.set(claude_enabled)
            self.gemini_var.set(gemini_enabled)
            self.codex_var.set(codex_enabled)

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
        parent_widget = self.form_widget if USING_QT else self.form_frame
        
        if field_type == 'string':
            editor = StringEditor(field_name, value, required, parent_widget)
        elif field_type == 'number':
            editor = NumberEditor(field_name, value, required, parent_widget)
        elif field_type == 'boolean':
            editor = BooleanEditor(field_name, value, required, parent_widget)
        elif field_type == 'array':
            editor = ArrayEditor(field_name, value, required, parent_widget)
        elif field_type == 'keyvalue':
            editor = KeyValueEditor(field_name, value, required, parent_widget)
        elif field_type == 'path':
            editor = PathEditor(field_name, value, required, parent_widget)
        elif field_type == 'dropdown':
            editor = DropdownEditor(field_name, value, required, parent_widget)
            # Set dropdown options based on field
            if field_name == 'restart':
                editor.set_options(['never', 'on-failure', 'always'])
            elif field_name == 'transport':
                editor.set_options(['stdio', 'http', 'websocket'])
        
        if editor:
            
            # Connect change callbacks
            editor.add_change_callback(self._on_field_changed)
            
            # Add to form
            label_text = field_name.replace('_', ' ').title()
            if required:
                label_text += " *"
            
            if USING_QT:
                label = QLabel(label_text)
                if field_name in self.FIELD_DESCRIPTIONS:
                    label.setToolTip(self.FIELD_DESCRIPTIONS[field_name])
                self.form_layout.addRow(label, editor.get_widget())
            elif HAS_TKINTER:
                row_frame = ttk.Frame(self.form_frame)
                row_frame.pack(fill=tk.X, pady=2)
                
                label = ttk.Label(row_frame, text=label_text, width=15)
                label.pack(side=tk.LEFT, padx=(0, 10))
                
                editor.frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.field_editors[field_name] = editor
    
    def _on_client_enablement_changed(self):
        """Handle client enablement checkbox change."""
        if not self.current_server:
            return

        # Update enablement states
        if USING_QT:
            claude_enabled = self.claude_checkbox.isChecked()
            gemini_enabled = self.gemini_checkbox.isChecked()
            codex_enabled = self.codex_checkbox.isChecked()
        elif HAS_TKINTER:
            claude_enabled = self.claude_var.get()
            gemini_enabled = self.gemini_var.get()
            codex_enabled = self.codex_var.get()
        else:
            return

        # Check if client states have changed
        if (claude_enabled != self.claude_enabled or
            gemini_enabled != self.gemini_enabled or
            codex_enabled != self.codex_enabled):
            # Emit client enablement change
            if USING_QT:
                # We'll emit a signal for client enablement changes
                pass  # Signal will be emitted via callbacks

            # Call callbacks for client enablement changes
            for callback in self.client_enablement_changed_callbacks:
                callback(self.current_server, "claude", claude_enabled)
                callback(self.current_server, "gemini", gemini_enabled)
                callback(self.current_server, "codex", codex_enabled)

            # Update stored states
            self.claude_enabled = claude_enabled
            self.gemini_enabled = gemini_enabled
            self.codex_enabled = codex_enabled

            # Mark as having changes
            self.has_changes = True
            self._update_ui_for_changes()

    def _on_field_changed(self, field_name: str = None, value: Any = None):
        """Handle field value change."""
        if not self.current_server:
            return

        # Check if data has actually changed
        current_data = self.get_server_data()
        self.has_changes = current_data != self.original_data

        # Update UI for changes
        self._update_ui_for_changes()

    def _update_ui_for_changes(self):
        """Update UI based on whether there are unsaved changes."""
        # Enable/disable save and cancel buttons
        if USING_QT:
            self.save_btn.setEnabled(self.has_changes and not self.validation_errors)
            self._update_save_button_style(self.has_changes)
            self.cancel_btn.setEnabled(self.has_changes)

            # Update header styling for unsaved changes
            if self.has_changes:
                self.server_label.setStyleSheet("""
                    font-weight: bold;
                    font-size: 14px;
                    color: #FF6B00;
                """)
                self.server_label.setText(f"● Editing: {self.current_server} (unsaved)")
            else:
                self.server_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                self.server_label.setText(f"Editing: {self.current_server}")
        elif HAS_TKINTER:
            state = 'normal' if self.has_changes and not self.validation_errors else 'disabled'
            self.save_btn.config(state=state)
            self.cancel_btn.config(state='normal' if self.has_changes else 'disabled')

            # Update label for unsaved changes
            if self.has_changes:
                self.server_label.config(text=f"● Editing: {self.current_server} (unsaved)",
                                        foreground='#FF6B00')
            else:
                self.server_label.config(text=f"Editing: {self.current_server}",
                                        foreground='black')

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
            self._update_save_button_style(self.has_changes)
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
            self._update_save_button_style(False)  # Clear any custom styles
            # Reset header styling after save
            self.server_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.server_label.setText(f"Editing: {self.current_server}")
        elif HAS_TKINTER:
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            # Reset label styling after save
            self.server_label.config(text=f"Editing: {self.current_server}",
                                    foreground='black')
        
        self._emit_changes_pending(False)
    
    def _on_cancel(self):
        """Cancel changes and restore original data."""
        if not self.current_server or not self.has_changes:
            return
        
        # Reload original data
        self.load_server(self.current_server, self.original_data)
    
    def _on_delete(self):
        """Delete the current server."""
        if not self.current_server:
            return
        
        # Confirm deletion
        if USING_QT:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                "Delete Server",
                f"Are you sure you want to delete '{self.current_server}'?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Emit server deleted signal with disabled status
                self.server_deleted.emit(self.current_server, self.current_server_disabled)
                # Clear the panel
                self.clear()
        elif HAS_TKINTER:
            import tkinter.messagebox as messagebox
            if messagebox.askyesno("Delete Server", 
                                  f"Are you sure you want to delete '{self.current_server}'?\n\nThis action cannot be undone."):
                # Call callbacks for server deletion with disabled status
                for callback in self.server_deleted_callbacks:
                    callback(self.current_server, self.current_server_disabled)
                # Clear the panel
                self.clear()
    
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

    def add_client_enablement_changed_callback(self, callback: Callable):
        """Add callback for client enablement changed event.

        Args:
            callback: Function to call with (server_name, client, enabled)
        """
        self.client_enablement_changed_callbacks.append(callback)
    
    def refresh_current_server(self, updated_config: Optional[Dict[str, Any]] = None,
                              claude_enabled: Optional[bool] = None,
                              gemini_enabled: Optional[bool] = None,
                              codex_enabled: Optional[bool] = None) -> bool:
        """Refresh the current server configuration from disk or with provided data.

        Args:
            updated_config: New configuration data (if None, server was deleted)
            claude_enabled: New Claude enablement state
            gemini_enabled: New Gemini enablement state
            codex_enabled: New Codex enablement state

        Returns:
            True if refresh successful, False if server was deleted or error
        """
        if not self.current_server:
            return True

        # Handle server deletion case
        if updated_config is None:
            logger.debug(f"Server '{self.current_server}' no longer exists")

            # Check for unsaved changes
            if self.has_changes:
                # Warn user
                if USING_QT:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Server Deleted",
                        f"The server '{self.current_server}' has been deleted from disk.\n"
                        "Your unsaved changes will be lost."
                    )
                elif HAS_TKINTER:
                    import tkinter.messagebox as messagebox
                    messagebox.showwarning(
                        "Server Deleted",
                        f"The server '{self.current_server}' has been deleted from disk.\n"
                        "Your unsaved changes will be lost."
                    )

            # Clear the panel
            self.clear()
            return False

        # Check if configuration changed externally
        config_changed = (json.dumps(updated_config, sort_keys=True) !=
                         json.dumps(self.original_data, sort_keys=True))

        # Check if client states changed
        client_states_changed = False
        if claude_enabled is not None and claude_enabled != self.claude_enabled:
            client_states_changed = True
        if gemini_enabled is not None and gemini_enabled != self.gemini_enabled:
            client_states_changed = True
        if codex_enabled is not None and codex_enabled != self.codex_enabled:
            client_states_changed = True

        if config_changed or client_states_changed:
            # Handle unsaved changes
            if self.has_changes:
                # Offer conflict resolution
                if USING_QT:
                    from PyQt6.QtWidgets import QMessageBox

                    message = f"The server '{self.current_server}' has been modified externally.\n\n"
                    if config_changed:
                        message += "• Configuration changed\n"
                    if client_states_changed:
                        message += "• Client enablement states changed\n"
                    message += "\nWhat would you like to do?"

                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("External Changes Detected")
                    msg_box.setText(message)
                    msg_box.setIcon(QMessageBox.Icon.Question)

                    keep_btn = msg_box.addButton("Keep My Changes", QMessageBox.ButtonRole.AcceptRole)
                    accept_btn = msg_box.addButton("Accept External Changes", QMessageBox.ButtonRole.RejectRole)
                    msg_box.setDefaultButton(keep_btn)

                    msg_box.exec()

                    if msg_box.clickedButton() == accept_btn:
                        # Accept external changes
                        self.load_server(
                            self.current_server,
                            updated_config,
                            self.current_server_disabled,
                            claude_enabled or self.claude_enabled,
                            gemini_enabled or self.gemini_enabled,
                            codex_enabled or self.codex_enabled
                        )
                        logger.debug(f"Accepted external changes for server '{self.current_server}'")
                    else:
                        # Keep current changes
                        logger.debug(f"Keeping local changes for server '{self.current_server}'")

                elif HAS_TKINTER:
                    import tkinter.messagebox as messagebox

                    message = f"The server '{self.current_server}' has been modified externally.\n\n"
                    if config_changed:
                        message += "• Configuration changed\n"
                    if client_states_changed:
                        message += "• Client enablement states changed\n"
                    message += "\n\nAccept external changes? (Choose No to keep your changes)"

                    if messagebox.askyesno("External Changes Detected", message):
                        # Accept external changes
                        self.load_server(
                            self.current_server,
                            updated_config,
                            self.current_server_disabled,
                            claude_enabled or self.claude_enabled,
                            gemini_enabled or self.gemini_enabled,
                            codex_enabled or self.codex_enabled
                        )
                        logger.debug(f"Accepted external changes for server '{self.current_server}'")
                    else:
                        # Keep current changes
                        logger.debug(f"Keeping local changes for server '{self.current_server}'")
            else:
                # No unsaved changes, just reload
                self.load_server(
                    self.current_server,
                    updated_config,
                    self.current_server_disabled,
                    claude_enabled or self.claude_enabled,
                    gemini_enabled or self.gemini_enabled
                )
                logger.debug(f"Reloaded server '{self.current_server}' from external changes")
        else:
            logger.debug(f"No external changes for server '{self.current_server}'")

        return True

    def clear_cache(self):
        """Clear any cached data for the current server."""
        # Currently no cache in the details panel, but this method
        # provides a hook for future caching implementations
        logger.debug(f"Clearing cache for details panel (server: {self.current_server})")

    def clear(self):
        """Clear the panel and show empty state."""
        self.current_server = None
        self.current_server_disabled = False
        self.original_data = None
        self.has_changes = False
        self.validation_errors.clear()
        self.claude_enabled = False
        self.gemini_enabled = False
        self.codex_enabled = False

        self._clear_form()

        if USING_QT:
            self.server_label.setText("Select a server to edit")
            self.add_field_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)  # Disable delete button
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self._update_save_button_style(False)  # Clear any custom styles
            # Disable client checkboxes
            self.claude_checkbox.setEnabled(False)
            self.gemini_checkbox.setEnabled(False)
            self.codex_checkbox.setEnabled(False)
            self.claude_checkbox.setChecked(False)
            self.gemini_checkbox.setChecked(False)
            self.codex_checkbox.setChecked(False)
            # Switch back to empty state
            self.stacked_widget.setCurrentWidget(self.empty_state_widget)
        elif HAS_TKINTER:
            self.server_label.config(text="Select a server to edit")
            self.add_field_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            # Disable client checkboxes
            self.claude_checkbox.config(state='disabled')
            self.gemini_checkbox.config(state='disabled')
            self.codex_checkbox.config(state='disabled')
            self.claude_var.set(False)
            self.gemini_var.set(False)
            self.codex_var.set(False)

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