"""Dialog for adding new servers via JSON paste."""

import json
from typing import Dict, Any, Optional, Callable

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QDialogButtonBox, QMessageBox, QGroupBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    USING_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    USING_QT = False


class AddServerDialog:
    """Dialog for adding new MCP servers via JSON configuration."""
    
    def __init__(self, parent=None):
        """Initialize the Add Server dialog.
        
        Args:
            parent: Parent widget/window
        """
        self.parent = parent
        self.result = None
        self.on_server_added_callbacks = []
        
        if USING_QT:
            self._init_qt()
        else:
            self._init_tk()
    
    def _init_qt(self):
        """Initialize Qt version of the dialog."""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("Add Server")
        self.dialog.setModal(True)
        self.dialog.resize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self.dialog)
        
        # Instructions
        instructions = QLabel(
            "Paste the server JSON configuration below.\n"
            "Format: {\"server_name\": {\"command\": \"...\", \"args\": [...], \"env\": {...}}}"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # JSON input area
        input_group = QGroupBox("Server Configuration (JSON)")
        input_layout = QVBoxLayout()
        
        self.json_input = QTextEdit()
        self.json_input.setFont(QFont("Courier", 10))
        self.json_input.setPlaceholderText(
            '{\n'
            '  "my-server": {\n'
            '    "command": "node",\n'
            '    "args": ["path/to/server.js"],\n'
            '    "env": {"NODE_ENV": "production"}\n'
            '  }\n'
            '}'
        )
        input_layout.addWidget(self.json_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Validation status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_qt_accept)
        button_box.rejected.connect(self.dialog.reject)
        
        # Validate button
        validate_btn = QPushButton("Validate JSON")
        validate_btn.clicked.connect(self._validate_json_qt)
        button_box.addButton(validate_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
        # Connect text change for live validation
        self.json_input.textChanged.connect(self._on_qt_text_changed)
    
    def _init_tk(self):
        """Initialize tkinter version of the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Server")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="Paste the server JSON configuration below.\n"
                 "Format: {\"server_name\": {\"command\": \"...\", \"args\": [...], \"env\": {...}}}",
            wraplength=550
        )
        instructions.pack(pady=(0, 10))
        
        # JSON input area
        input_frame = ttk.LabelFrame(main_frame, text="Server Configuration (JSON)", padding="5")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.json_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            width=60,
            height=15,
            font=("Courier", 10)
        )
        self.json_input.pack(fill=tk.BOTH, expand=True)
        
        # Add placeholder text
        placeholder = (
            '{\n'
            '  "my-server": {\n'
            '    "command": "node",\n'
            '    "args": ["path/to/server.js"],\n'
            '    "env": {"NODE_ENV": "production"}\n'
            '  }\n'
            '}'
        )
        self.json_input.insert("1.0", placeholder)
        self.json_input.tag_add("placeholder", "1.0", "end")
        self.json_input.tag_config("placeholder", foreground="gray")
        
        # Clear placeholder on focus
        def clear_placeholder(event):
            if "placeholder" in self.json_input.tag_names("1.0"):
                self.json_input.delete("1.0", "end")
                self.json_input.tag_remove("placeholder", "1.0", "end")
        
        self.json_input.bind("<FocusIn>", clear_placeholder)
        
        # Validation status
        self.status_label = ttk.Label(main_frame, text="", foreground="red")
        self.status_label.pack(pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Buttons
        validate_btn = ttk.Button(
            button_frame,
            text="Validate JSON",
            command=self._validate_json_tk
        )
        validate_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = ttk.Button(
            button_frame,
            text="Add Server",
            command=self._on_tk_accept
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Bind text change for live validation
        self.json_input.bind("<KeyRelease>", self._on_tk_text_changed)
    
    def _validate_json_qt(self) -> bool:
        """Validate JSON input for Qt version."""
        json_text = self.json_input.toPlainText().strip()
        
        if not json_text or json_text == self.json_input.placeholderText():
            self.status_label.setText("Please enter server configuration")
            self.status_label.setStyleSheet("color: orange;")
            return False
        
        try:
            config = json.loads(json_text)
            
            # Validate structure
            if not isinstance(config, dict):
                self.status_label.setText("JSON must be an object")
                self.status_label.setStyleSheet("color: red;")
                return False
            
            if not config:
                self.status_label.setText("JSON must contain at least one server")
                self.status_label.setStyleSheet("color: red;")
                return False
            
            # Validate each server
            for name, server in config.items():
                if not isinstance(server, dict):
                    self.status_label.setText(f"Server '{name}' must be an object")
                    self.status_label.setStyleSheet("color: red;")
                    return False
                
                if 'command' not in server:
                    self.status_label.setText(f"Server '{name}' missing 'command' field")
                    self.status_label.setStyleSheet("color: red;")
                    return False
            
            self.status_label.setText("✓ Valid JSON configuration")
            self.status_label.setStyleSheet("color: green;")
            return True
            
        except json.JSONDecodeError as e:
            self.status_label.setText(f"Invalid JSON: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            return False
    
    def _validate_json_tk(self) -> bool:
        """Validate JSON input for tkinter version."""
        json_text = self.json_input.get("1.0", "end").strip()
        
        # Check if it's placeholder text
        if not json_text or "placeholder" in self.json_input.tag_names("1.0"):
            self.status_label.config(text="Please enter server configuration", foreground="orange")
            return False
        
        try:
            config = json.loads(json_text)
            
            # Validate structure
            if not isinstance(config, dict):
                self.status_label.config(text="JSON must be an object", foreground="red")
                return False
            
            if not config:
                self.status_label.config(text="JSON must contain at least one server", foreground="red")
                return False
            
            # Validate each server
            for name, server in config.items():
                if not isinstance(server, dict):
                    self.status_label.config(text=f"Server '{name}' must be an object", foreground="red")
                    return False
                
                if 'command' not in server:
                    self.status_label.config(text=f"Server '{name}' missing 'command' field", foreground="red")
                    return False
            
            self.status_label.config(text="✓ Valid JSON configuration", foreground="green")
            return True
            
        except json.JSONDecodeError as e:
            self.status_label.config(text=f"Invalid JSON: {str(e)}", foreground="red")
            return False
    
    def _on_qt_text_changed(self):
        """Handle text change in Qt version."""
        # Provide live validation feedback
        if self.json_input.toPlainText().strip():
            self._validate_json_qt()
    
    def _on_tk_text_changed(self, event):
        """Handle text change in tkinter version."""
        # Provide live validation feedback
        if self.json_input.get("1.0", "end").strip():
            self._validate_json_tk()
    
    def _on_qt_accept(self):
        """Handle accept action in Qt version."""
        if self._validate_json_qt():
            json_text = self.json_input.toPlainText().strip()
            self.result = json.loads(json_text)
            
            # Notify callbacks
            for callback in self.on_server_added_callbacks:
                callback(self.result)
            
            self.dialog.accept()
        else:
            QMessageBox.warning(
                self.dialog,
                "Invalid Configuration",
                "Please fix the JSON configuration before proceeding."
            )
    
    def _on_tk_accept(self):
        """Handle accept action in tkinter version."""
        if self._validate_json_tk():
            json_text = self.json_input.get("1.0", "end").strip()
            self.result = json.loads(json_text)
            
            # Notify callbacks
            for callback in self.on_server_added_callbacks:
                callback(self.result)
            
            self.dialog.destroy()
        else:
            messagebox.showwarning(
                "Invalid Configuration",
                "Please fix the JSON configuration before proceeding."
            )
    
    def on_server_added(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for when server is added.
        
        Args:
            callback: Function to call with server config
        """
        self.on_server_added_callbacks.append(callback)
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show the dialog and return the result.
        
        Returns:
            Dictionary with server configuration or None if cancelled
        """
        if USING_QT:
            self.dialog.exec()
            return self.result
        else:
            self.dialog.wait_window()
            return self.result
    
    def get_server_json(self) -> Optional[Dict[str, Any]]:
        """Get the server JSON configuration.
        
        Returns:
            Dictionary with server configuration or None if cancelled
        """
        return self.result
    
    def set_initial_json(self, json_text: str):
        """Set initial JSON text in the input field.
        
        Args:
            json_text: JSON string to populate
        """
        if USING_QT:
            self.json_input.setPlainText(json_text)
        else:
            self.json_input.delete("1.0", "end")
            self.json_input.insert("1.0", json_text)